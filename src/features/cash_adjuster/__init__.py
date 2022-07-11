import os
import csv
import sqlite3
from logging.config import dictConfig
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource

from features.common import FiccCommon

class CashAdjusterCommon(FiccCommon):
    def __init__(self):
        super().__init__('data/cash_adjuster.db', 'cashAdjuster')
        self.INITIAL_FX_DATA = 'data/initial_cash.csv'

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


class BuyManager(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def is_valid(self, cursor, desk, value):
        return self.get_cash(cursor, desk) >= value

    def post(self):
        payload = dict()
        req = request.json
        desk, txnValue = req['Desk'], float(req['TxnValue'])
        cursor = self.get_db().cursor()
        if self.is_valid(cursor, desk, txnValue):
            self.adjust_cash(cursor, desk, -1*txnValue)
            
            request.post(
                url=f"{os.getenv('FLASK_HOST')}:{os.getenv('PORTFOLIO_ENGINE_PORT')}/buy_adjustment",
                data=req,
            )
        else:
            res['ExclusionType'] = 'CASH_OVERLIMIT'

        self.close_connection()
        if 'ExclusionType' in res:
            return jsonify(res), 400
        return jsonify(res), 200


class SellAdjuster(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        desk, txnValue = req['Desk'], float(req['TxnValue'])
        cursor = self.get_db().cursor()
        self.adjust_cash(cursor, desk, txnValue)
        self.close_connection()
        return jsonify({
            'msg': 'success'
        }), 200


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
