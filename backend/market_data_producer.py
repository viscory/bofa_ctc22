import os
import csv
from flask import Flask, request, jsonify, g
from flask_restful import Resource, Api

from common import DbCommon


class MarketDataDbCommon(DbCommon):
    def __init__(self):
        super().__init__('backend/data/market_prices.db', g)

    def init_data(self, cursor):
        self.init_bond_table(cursor)
        self.init_fx_table(cursor)

    def init_bond_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BondPrices (
                BondID TEXT PRIMARY KEY,
                Currency TEXT,
                Price REAL
            )
        ''')
        with open(os.getenv('INITIAL_BOND_DATA'), 'r') as handle:
            reader = csv.reader(handle)
            next(reader)
            for (bondID, currency) in reader:
                cursor.execute(f'''
                    INSERT INTO BondPrices
                    VALUES ("{bondID.replace(' ', '')}", "{currency.replace(' ', '')}", -1)
                ''')

    def init_fx_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS FxRates (
                Currency TEXT PRIMARY KEY,
                Rate REAL
            )
        ''')
        with open(os.getenv('INITIAL_FX_DATA'), 'r') as handle:
            reader = csv.reader(handle)
            next(reader)
            for (currency, rate) in reader:
                cursor.execute(f'''
                    INSERT INTO FxRates
                    VALUES ("{currency.replace(' ', '')}", {rate})
                ''')


class MarketDataSubscriber(Resource, MarketDataDbCommon):
    def __init__(self):
        super().__init__()

    def update_bond(self, cursor, bondID, price):
        # trading restricted to 30 given bonds/ bond_details.csv
        cursor.execute(f'''
            UPDATE BondPrices
            SET Price = {price}
            WHERE BondID = "{bondID}"
        ''')

    def update_fx(self, cursor, currency, rate):
        # insert or replace as new currencies can be trades
        cursor.execute(f'''
            INSERT OR REPLACE INTO FxRates
            VALUES ('{currency}', {rate})
        ''')

    def post(self):
        req = request.json
        eventType = req.get('EventType')
        cursor = self.get_db().cursor()
        if eventType == 'PriceEvent':
            bondID, price = req['BondID'], float(req['MarketPrice'])
            self.update_bond(cursor, bondID, price)
        if eventType == 'FXEvent':
            currency, rate = req['ccy'], float(req['rate'])
            self.update_fx(cursor, currency, rate)
        self.close_connection()
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


class MarketDataPublisher(Resource, MarketDataDbCommon):
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
            WHERE price != -1
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
        response = jsonify(result)
        response.status_code = 200
        return response


class TradeDataEnricher(Resource, MarketDataDbCommon):
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
        if result[0][1] == -1:
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
        return float(result[0][0]), 0

    def enrich_request(self, cursor, bondID):
        result = {'MarketPrice': -1}
        res, err = self.get_bond_details(
            cursor, bondID
        )
        # if no bond price, NO_MARKET_PRICE
        if err:
            result['ExclusionType'] = res
            return result, 1
        currency, marketPrice = res
        res, err = self.get_fx_rate(cursor, currency)
        # if no fx price, NO_MARKET_PRICE
        if err:
            result['ExclusionType'] = res
            return result, 1
        fxRate = res

        result['MarketPrice'] = marketPrice
        result['FxRate'] = fxRate
        return result, 0

    def get(self):
        req = request.json
        cursor = self.get_db().cursor()
        bondID = req['BondID']
        result, err = self.enrich_request(cursor, bondID)
        self.close_connection()
        response = jsonify(result)
        response.status_code = 200
        if err:
            response.status_code = 402
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(MarketDataPublisher, '/get_market_data')
    api.add_resource(MarketDataSubscriber, '/publish_price_event')
    api.add_resource(TradeDataEnricher, '/enrich_trade')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('MARKET_DATA_PRODUCER_PORT'), debug=True)
