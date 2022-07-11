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


class CashAdjusterCommon:
    def __init__(self):
        self.DATABASE = 'data/cash_adjuster.db'
        self.INITIAL_FX_DATA = 'data/initial_cash.csv'

    @staticmethod
    def close_connection():
        db = getattr(g, '_database', None)
        if db is not None:
            db.commit()
            db.close()

    def init_desk_table(self, cursor):
        cursor.execute('''
        CREATE TABLE DeskCash (
            desk TEXT Primary,
            cash REAL,
        )
        ''')
        with open(self.INITIAL_DESK_DATA, 'r') as handle:
            reader = csv.reader(handle)
            next(reader)
            for (desk, cash) in reader:
                cursor.execute(f'''
                    INSERT INTO DeskCash
                    VALUES ("{desk}", {cash})
                ''')


    def init_data(self, cursor):
        self.init_desk_table(cursor)

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
                app.logger.error("Error initializing database")

    def get_db(self):
        self.init_db()
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(self.DATABASE)
        return db

    def get_cash(self, cursor, desk):
        result = (cursor.execute(f'''
            SELECT cash from DeskCash
            WHERE desk == {desk}
        ''').fetchall())
        if len(result) == 0:
            cursor.execute('''
                INSERT INTO DeskCash (desk, cash)
                VALUES ("{desk}", 0)
            ''')
            return 0
        return float(result[0])

    def adjust_cash(self, cursor, desk, value):
        initial = self.get_cash(cursor, desk)
        cursor.execute(f'''
            UPDATE DeskCash
            SET cash = {initial+value}
            WHERE desk == "{desk}"
        ''')


class PurchaseManager(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def is_valid(self, cursor, desk, value):
        return self.get_cash(cursor, desk) >= value

    def post(self):
        req = res = request.json
        desk, txnValue = req['Desk'], float(req['TxnValue'])
        cursor = self.get_db().cursor()
        if self.is_valid(cursor, desk, txnValue):
            self.adjust_cash(cursor, desk, -1*txnValue)
            request.post(
                url=f"localhost:{os.getenv('PORTFOLIO_ENGINE_PORT')}/buy_adjustment",
                data=req,
            )
        else:
            res['ExclusionType'] = 'CASH_OVERLIMIT'

        self.close_connection()
        if 'ExclusionType' in res:
            return jsonify(res), 400
        return jsonify(res), 200


class SellManager(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        desk, txnValue = req['Desk'], float(req['TxnValue'])
        cursor = self.get_db().cursor()
        self.adjust_cash(cursor, desk, txnValue)
        self.close_connection()
        return jsonify({}), 200


class DeskDataPublisher(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def get_all_desk_cash(self, cursor):
        return cursor.execute('''
            SELECT Desk, Cash
            FROM DeskCash
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

    api.add_resource(PurchaseManager, '/buy')
    api.add_resource(SellManager, '/sell_adjustment')
    api.add_resource(DeskDataPublisher, '/get_desk_data')

    app.run(port=os.getenv('CASH_ADJUSTER_PORT'))
