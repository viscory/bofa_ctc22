import csv
import sqlite3
from flask import Flask, request, jsonify
from flask_restful import Resource
from features.common import FiccCommon

class MarketDataCommon(FiccCommon):
    def __init__(self):
        super().__init__('data/market_prices.db', 'marketPrices')
        self.INITIAL_FX_DATA = 'data/initial_fx.csv'
        self.INITIAL_BOND_DATA = 'data/bond_details.csv'

    def init_bond_table(self, cursor):
        cursor.execute('''
        CREATE TABLE BondPrices (
            bondID TEXT PRIMARY,
            currency TEXT,
            price REAL
        )
        ''')
        with open(self.INITIAL_BOND_DATA, 'r') as handle:
            reader = csv.reader(handle)
            next(reader)
            for (bondID, currency) in reader:
                cursor.execute(f'''
                    INSERT INTO BondPrices
                    VALUES ("{bondID}", {currency}, -1)
                ''')

    def init_fx_table(self, cursor):
        cursor.execute('''
            CREATE TABLE FxRates (
                currency TEXT PRIMARY,
                rate REAL
            )
        ''')
        with open(self.INITIAL_FX_DATA, 'r') as handle:
            reader = csv.reader(handle)
            next(reader)
            for (currency, rate) in reader:
                cursor.execute(f'''
                    INSERT INTO FxRates
                    VALUES ("{currency}", {rate})
                ''')

    def init_data(self, cursor):
        self.init_bond_table(cursor)
        self.init_fx_table(cursor)


class MarketDataSubscriber(Resource, MarketDataCommon):
    def __init__(self):
        super().__init__()

    @staticmethod
    def validate_fx_event(event):
        try:
            assert len(event) == 4
            assert float(event.get("rate"))
        except Exception:
            app.logger.error(f"EventID: {event.get('EventID')}, invalid FX event")

    @staticmethod
    def validate_price_event(event):
        try:
            assert len(event) == 3
            assert float(event.get("MarketPrice"))
        except Exception:
            app.logger.error(f"EventID: {event.get('EventID')}, invalid price event")

    def update_bond(self, cursor, bondID, price):
        # trading restricted to 30 given bonds/ bond_details.csv
        cursor.execute(f'''
            UPDATE BondPrices
            SET price = {price}
            WHERE bondID = {bondID}
        ''')

    def update_fx(self, cursor, currency, rate):
        # insert or replace as new currencies can be trades
        cursor.execute(f'''
            INSERT OR REPLACE INTO FxRates(currency, rate)
            VALUES ("{currency}", {rate})
        ''')

    def post(self):
        req = request.json
        eventType = req.get('EventType')
        cursor = self.get_db().cursor()

        if eventType == 'PriceEvent':
            self.validate_price_event(req)
            bondID, price = req['BondID'], float(req['MarketPrice'])
            self.update_bond(cursor, bondID, price)
        if eventType == 'FXEvent':
            self.validate_fx_event(req)
            currency, rate = req['ccy'], float(req['rate'])
            self.update_fx(cursor, currency, rate)
        self.close_connection()
        return jsonify({'msg': 'success'}), 200


class MarketDataPublisher(Resource, MarketDataCommon):
    def __init__(self):
        super().__init__()

    def get_fx_rates(self, cursor):
        return cursor.execute('''
            SELECT currency, rate
            FROM FxRates
        ''').fetchall()

    def get_bond_prices(self, cursor):
        return cursor.execute('''
            SELECT bondID, currency, price
            FROM BondPrices
        ''').fetchall()

    def get_market_prices(self, cursor):
        result = dict()
        fxRates = self.get_fx_rates(cursor)
        bondPrices = self.get_bond_prices(cursor)

        result['FX'] = dict(fxRates)
        result['Bond'] = dict(
            ((bondID, (currency, price))
            for bondID, currency, price in bondPrices)
        )
        return result

    def get(self):
        cursor = self.get_db().cursor()
        result = self.get_market_prices(cursor)
        self.close_connection()
        return jsonify(result), 200


class TradeDataEnricher(Resource, MarketDataCommon):
    def __init__(self):
        super().__init__()

    def get_bond_details(self, cursor, bondID):
        # possible to not have a bond price event
        # not possible for bondID to be new
        result = cursor.execute(f'''
            SELECT currency, price
            FROM BondPrices
            WHERE BondID = "{bondID}"
        ''').fetchall()
        if result[1] == -1:
            app.logger.error(f"Error: No Price History for {bondID}")
            return 'NO_MARKET_PRICE', 1
        return result[0], 0  

    def get_fx_rate(self, cursor, currency):
        # possible to not have an FX price event
        result = cursor.execute(f'''
            SELECT rate
            FROM FxRates
            WHERE currency = "{currency}"
        ''').fetchall()
        if len(result) == 0:
            app.logger.error(f"No Price History for {currency}")
            return 'NO_MARKET_PRICE', 1
        return float(result), 0  

    def enrich_request(self, cursor, bondID, result):
        res, err = self.get_bond_details(
            cursor, bondID
        )
        if err:
            result['ExclusionType'] = result
            return result, 1
        currency, marketPrice = res
        res, err = self.get_fx_rate(cursor, currency)
        if err:
            result['ExclusionType'] = result
            return result, 1
        fxRate = res

        result['MarketPrice'] = marketPrice
        result['FxRate'] = fxRate
        return result, 0

    def get(self):
        req = request.json
        cursor = self.get_db().cursor()
        bondID = req.get('BondID')
        result, err = self.enrich_request(cursor, bondID, req)
        self.close_connection()
        if err:
            return jsonify(result), 400
        return jsonify(result), 200
