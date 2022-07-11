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


class PortfolioEngineCommon:
    def __init__(self):
        self.DATABASE = 'data/portfolio_data.db'

    @staticmethod
    def close_connection():
        db = getattr(g, '_database', None)
        if db is not None:
            db.commit()
            db.close()

    def init_portfolio_table(self, cursor):
        cursor.execute('''
        CREATE TABLE PortfolioData (
            Desk TEXT Primary,
            Trader TEXT Primary,
            Book TEXT Primary,
            BondID TEXT Primary,
            Positions TEXT Primary,
            Cash REAL,
        )
        ''')

    def init_db(self):
        try:
            os.stat(self.DATABASE)
        except FileNotFoundError:
            try:
                conn = sqlite3.connect(self.DATABASE)
                cursor = conn.cursor()
                self.init_portfolio_table(cursor)
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

    def adjust_position(self, cursor, book, bondID, qty):
        cursor.execute('''
            
        ''')


class SellManager(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def get_positions(self, cursor, book, bondID):
        return int(cursor.execute('''
            SELECT Positions FROM PortfolioData
            WHERE
                BondID = "{bondID}"
                AND Book = "{book}"
        ''').fetchall()[0])

    def is_valid(self, cursor, book, bondID, qty):
        return self.get_positions(cursor, book, bondID) >= qty

    def post(self):
        payload = dict()
        req = request.json
        desk, qty = req['Desk'], int(req['Quantity'])
        cursor = self.get_db().cursor()
        if self.is_valid(cursor, book, bondID, qty):
            self.adjust_position(cursor, book, bondID, -1*txnValue)
            payload['Desk'] = req['Desk']
            payload['TxnValue'] = req['TxnValue']
            request.post(
                url=f"localhost:{os.getenv('PORTFOLIO_ENGINE_PORT')}/sell_adjustment",
                data=payload,
            )
        else:
            res['ExclusionType'] = 'QUANTITY_OVERLIMIT'

        self.close_connection()
        if 'ExclusionType' in res:
            return jsonify(res), 400
        return jsonify(res), 200


class SellManager(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        desk, txnValue = req['Desk'], float(req['TxnValue'])
        cursor = self.get_db().cursor()
        self.adjust_desk_cash(cursor, desk, txnValue)
        self.close_connection()
        return jsonify({}), 200


class DeskDataPublisher(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def get_all_desk_cash(self, cursor):
        return cursor.execute('''
            SELECT Desk, Trader, Book, BondID, Quantity
            FROM PortfolioData
        ''').fetchall()

    def get(self):
        res = dict()
        cursor = self.get_db().cursor()
        res['Desks'] = self.get_all_desk_cash(cursor)
        self.close_connection()
        return jsonify(res), 200


if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(PurchaseManager, '/sell')
    api.add_resource(SellManager, '/buy_adjustment')
    api.add_resource(PortfolioDataPublisher, '/get_book_data')

    app.run(port=os.getenv('CASH_ADJUSTER_PORT'))
