import os
import csv
import requests
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource

from common import Common


# cash_adjuster and portfolio_engine are highly similar classes
# common functions related to properly initializing the database
# as well as utility functions to query for and adjust the cash in each desk
class CashAdjusterCommon(Common):
    def __init__(self):
        super().__init__('backend/data/cash_adjuster.db', g)

    def init_data(self, cursor):
        self.init_desk_table(cursor)

    def init_desk_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DeskLiquidity (
                Desk TEXT PRIMARY KEY,
                Cash REAL
            )
        ''')
        with open(os.getenv('INITIAL_DESK_DATA'), 'r') as handle:
            reader = csv.reader(handle)
            next(reader)
            for (desk, cash) in reader:
                cursor.execute(f'''
                    INSERT INTO DeskLiquidity
                    VALUES ("{desk}", {float(cash)})
                ''')

    def get_cash(self, cursor, desk):
        result = (cursor.execute(f'''
            SELECT Cash FROM DeskLiquidity
            WHERE Desk == "{desk}"
        ''').fetchall())
        if len(result) == 0:
            return 0
        return float(result[0][0])

    def adjust_cash(self, cursor, desk, value):
        initial = self.get_cash(cursor, desk)
        cursor.execute(f'''
            INSERT OR REPLACE INTO DeskLiquidity
            VALUES ("{desk}", {initial+value})
        ''')


# this class is responsible for:
# querying the db if enough cash is available in the desk for purchase
# alerting event generator if this isnt possible
# if possible, alert portfolio engine that new positions are available
class BuyManager(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def sufficient_liquidity(self, cursor, desk, value):
        return self.get_cash(cursor, desk) >= value

    def post(self):
        req = request.json
        cursor = self.get_db().cursor()

        desk, trader, book, bondID, qty, marketPrice, fxRate = (
            req['Desk'],
            req['Trader'],
            req['Book'],
            req['BondID'],
            int(req.get('Quantity')),
            float(req.get('MarketPrice')),
            float(req.get('FxRate'))
        )
        txnValue = self.calculate_net_value(qty, marketPrice, fxRate)

        if self.sufficient_liquidity(cursor, desk, txnValue):
            payload = {
                'Desk': desk,
                'Trader': trader,
                'Book': book,
                'BondID': bondID,
                'Quantity': qty,
            }
            requests.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('PORTFOLIO_ENGINE_PORT')}/buy_adjustment",
                json=payload
            )
            self.adjust_cash(cursor, desk, -1*txnValue)
        else:
            self.close_connection()
            response = jsonify({
                'ExclusionType': 'CASH_OVERLIMIT',
                'MarketPrice': float(req['MarketPrice'])
            })
            response.status_code = 401
            return response
        self.close_connection()
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


# this class is a helper function
# it is called by portflio engine if a sale has been made,
# so new liquidity is released into the desk
class SellAdjuster(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        cursor = self.get_db().cursor()

        desk, qty, marketPrice, fxRate = (
            req['Desk'],
            int(req.get('Quantity')),
            float(req.get('MarketPrice')),
            float(req.get('FxRate'))
        )
        txnValue = self.calculate_net_value(qty, marketPrice, fxRate)

        self.adjust_cash(cursor, desk, txnValue)
        self.close_connection()
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


# this class is responsivle for keeping track of the cash in each desk
# it also publishes this data to report generator to create reports
# or to the dashboard for display
class DeskDataPublisher(Resource, CashAdjusterCommon):
    def __init__(self):
        super().__init__()

    def get_all_desk_cash(self, cursor):
        return cursor.execute('''
            SELECT Desk, Cash
            FROM DeskLiquidity
        ''').fetchall()

    def get(self):
        cursor = self.get_db().cursor()
        result = self.get_all_desk_cash(cursor)
        self.close_connection()
        response = jsonify(result)
        response.status_code = 200
        return response


if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(BuyManager, '/buy')
    api.add_resource(SellAdjuster, '/sell_adjustment')
    api.add_resource(DeskDataPublisher, '/get_desk_data')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('CASH_ADJUSTER_PORT'), debug=True)
