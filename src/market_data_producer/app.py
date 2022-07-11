import os
import csv
import sqlite3
from logging.config import dictConfig
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'standard': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'standard']
    }
})


class MarketDataCommon:
    def __init__(self):
        self.DATABASE = 'data/market_prices.db'
        self.INITIAL_FX_DATA = 'data/initial_fx.csv'
        self.INITIAL_BOND_DATA = 'data/bond_details.csv'

    @staticmethod
    def close_connection():
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

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

    def init_db(self):
        try:
            os.stat(self.DATABASE)
        except FileNotFoundError:
            try:
                conn = sqlite3.connect(self.DATABASE)
                cursor = conn.cursor()
                self.init_bond_table(cursor)
                self.init_fx_table(cursor)
                conn.commit()
                conn.close()
            except Exception:
                app.logger.error("Error initializing database")

    def get_db(self):
        self.init_db()
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(self.DATABASE)
        return db


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

    def update_bond(self, conn, bondID, price):
        conn.execute(f'''
            UPDATE BondPrices
            SET price = {price}
            WHERE bondID = {bondID}
        ''')
        conn.commit()

    def update_fx(self, conn, currency, rate):
        conn.execute(f'''
            INSERT OR REPLACE INTO FxRates(currency, rate)
            VALUES ("{currency}", {rate})
        ''')
        conn.commit()

    def post(self):
        req = request.json
        eventType = req['EventType']
        db = self.get_db()

        if eventType == 'PriceEvent':
            self.validate_price_event(req)
            bondID = req['BondID']
            price = float(req['MarketPrice'])
            self.update_bond(db, bondID, price)
        if eventType == 'FXEvent':
            self.validate_fx_event(req)
            currency = req['ccy']
            rate = float(req['rate'])
            self.update_fx(db, currency, rate)
        self.close_connection()
        return jsonify({}), 200


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
        res = dict()
        fxRates = self.get_fx_rates(cursor)
        bondPrices = self.get_bond_prices(cursor)

        res['FX'] = dict(fxRates)
        res['Bond'] = dict(
            ((bondID, (currency, price))
            for bondID, currency, price in bondPrices)
        )
        return res

    def get(self):
        cursor = self.get_db().cursor()
        res = self.get_market_prices(cursor)
        self.close_connection()
        return jsonify(res), 200


class TradeDataEnricher(Resource, MarketDataCommon):
    def __init__(self):
        super().__init__()

    def get_bond_details(self, cursor, bondID):
        try:
            return cursor.execute(f'''
                SELECT currency, price
                FROM BondPrices
                WHERE BondID = "{bondID}"
            ''').fetchall()[0]
        except Exception as err:
            app.logger.error(f"error: {err}. Error getting bond details")
            raise err

    def get_fx_rate(self, cursor, currency):
        try:
            return cursor.execute(f'''
                SELECT rate
                FROM FxRates
                WHERE currency = "{currency}"
            ''').fetchall()[0]
        except Exception as err:
            app.logger.error(f"error: {err}. Error getting fx rates")
            raise err

    def enrich_request(self, cursor, res):
        currency, marketPrice = self.get_bond_details(
            cursor, res.get('BondID')
        )
        fxRate = self.get_fx_rate(cursor, currency)
        res['MarketPrice'] = marketPrice
        res['FxRate'] = fxRate
        return res

    def get(self):
        req = request.json
        cursor = self.get_db().cursor()
        res = self.enrich_request(cursor, req)
        self.close_connection()
        return jsonify(res), 200

if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(MarketDataSubscriber, "/publish_price_event")
    api.add_resource(MarketDataPublisher, "/market_data")
    api.add_resource(TradeDataEnricher, "/enrich_trade")

    app.run(port=os.getenv('MARKET_DATA_PRODUCER_PORT'))
