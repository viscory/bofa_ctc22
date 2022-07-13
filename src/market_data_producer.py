import os
import csv
import sqlite3
from flask import Flask, request, jsonify, g
from flask_restful import Resource, Api


class MarketDataCommon:
    def __init__(self):
        self.DATABASE = 'data/market_prices.db'
        self.INITIAL_FX_DATA = 'data/initial_fx.csv'
        self.INITIAL_BOND_DATA = 'data/bond_details.csv'

    def get_db(self):
        self.init_db()
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(self.DATABASE)
        return db

    def close_connection(self):
        db = getattr(g, "_database", None)
        if db is not None:
            g._database = None
            db.commit()
            db.close()

    def init_db(self):
        try:
            os.stat(self.DATABASE)
        except FileNotFoundError:
            try:
                conn = sqlite3.connect(self.DATABASE)
                cursor = conn.cursor()
                self.init_data(cursor)
                conn.commit()
                conn.close()
            except Exception:
                print("Error initializing database")

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
        with open(self.INITIAL_BOND_DATA, 'r') as handle:
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
        with open(self.INITIAL_FX_DATA, 'r') as handle:
            reader = csv.reader(handle)
            next(reader)
            for (currency, rate) in reader:
                cursor.execute(f'''
                    INSERT INTO FxRates
                    VALUES ("{currency.replace(' ', '')}", {rate})
                ''')


class MarketDataSubscriber(Resource, MarketDataCommon):
    def __init__(self):
        super().__init__()

    def update_bond(self, conn, bondID, price):
        # trading restricted to 30 given bonds/ bond_details.csv
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE BondPrices
            SET Price = {price}
            WHERE BondID = "{bondID}"
        ''')
        conn.commit()

    def update_fx(self, conn, currency, rate):
        # insert or replace as new currencies can be trades
        cursor = conn.cursor()
        sql = f'''
            INSERT OR REPLACE INTO FxRates
            VALUES ('{currency}', {rate})
        '''
        cursor.execute(sql)
        conn.commit()

    def post(self):
        req = request.json
        eventType = req.get('EventType')
        conn = self.get_db()
        if eventType == 'PriceEvent':
            bondID, price = req['BondID'], float(req['MarketPrice'])
            self.update_bond(conn, bondID, price)
        if eventType == 'FXEvent':
            currency, rate = req['ccy'], float(req['rate'])
            self.update_fx(conn, currency, rate)
        self.close_connection()
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


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
        conn = self.get_db()
        cursor = conn.cursor()
        result = self.get_market_prices(cursor)
        conn.close()
        response = jsonify(result)
        response.status_code = 200
        return response


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
