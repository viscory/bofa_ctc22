import os
import requests
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource

from common import Common


# portfolio_engine and cash_adjuster are highly similar classes
# common functions related to properly initializing the database
# as well as utility functions to query for and adjust the cash in each desk
class PortfolioEngineCommon(Common):
    def __init__(self):
        super().__init__('backend/data/portfolio_data.db', g)

    def init_data(self, cursor):
        self.init_portfolio_table(cursor)

    # only book, bondID are primary keys
    # because each book name must be unique
    # (as multiple traders cannot have the same book)
    # there is no need to set the other as primary keys
    # since book, bondID MUST be unique
    def init_portfolio_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PortfolioData (
                Desk TEXT,
                Trader TEXT,
                Book TEXT,
                BondID TEXT,
                Positions INTEGER,
                PRIMARY KEY (Book, BondID)
            )
        ''')

    def get_positions(self, cursor, book, bondID):
        result = cursor.execute(f'''
            SELECT Positions FROM PortfolioData
            WHERE
                BondID = "{bondID}"
                AND Book = "{book}"
        ''').fetchall()
        if len(result) == 0:
            return 0
        return int(result[0][0])

    def adjust_positions(self, cursor, desk, trader, book, bondID, quantity):
        initial = self.get_positions(cursor, book, bondID)
        cursor.execute(f'''
            INSERT OR REPLACE INTO PortfolioData
            VALUES (
                "{desk}",
                "{trader}",
                "{book}",
                "{bondID}",
                {initial+quantity}
            )
        ''')


# this class is responsible for:
# querying the db if enough position is available in the desk for sale
# alerting event generator if this isnt possible
# if possible, alert cash adjuster that more liquidity is available
class SellManager(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def sufficient_positions(self, cursor, book, bondID, qty):
        return self.get_positions(cursor, book, bondID) >= qty

    def post(self):
        req = request.json
        cursor = self.get_db().cursor()
        desk, trader, book, bondID, qty = (
            req['Desk'],
            req['Trader'],
            req['Book'],
            req['BondID'],
            int(req['Quantity'])
        )
        if self.sufficient_positions(cursor, book, bondID, qty):
            payload = {
                'Desk':  req['Desk'],
                'Quantity':  int(req['Quantity']),
                'MarketPrice':  float(req['MarketPrice']),
                'FxRate':  float(req['FxRate'])
            }
            requests.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('CASH_ADJUSTER_PORT')}/sell_adjustment",
                json=payload,
            )
            self.adjust_positions(cursor, desk, trader, book, bondID, -1*qty)
            self.close_connection()
        else:
            response = jsonify({
                'ExclusionType': 'QUANTITY_OVERLIMIT',
                'MarketPrice': float(req['MarketPrice'])
            })
            response.status_code = 400
            return response
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


# this class is a helper function
# it is called by cash adjuster if a purchase has been made,
# so new positions are available for the book
class BuyAdjuster(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        cursor = self.get_db().cursor()

        desk, trader, book, bondID, qty = (
            req['Desk'],
            req['Trader'],
            req['Book'],
            req['BondID'],
            int(req['Quantity'])
        )
        self.adjust_positions(cursor, desk, trader, book, bondID, qty)
        self.close_connection()
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


# this class publishes this data to report generator to create reports
class PortfolioDataPublisher(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def get_all_data(self, cursor):
        return cursor.execute('''
            SELECT Desk, Trader, Book, BondID, Positions
            FROM PortfolioData
        ''').fetchall()

    def get(self):
        cursor = self.get_db().cursor()
        result = self.get_all_data(cursor)
        self.close_connection()
        response = jsonify(result)
        response.status_code = 200
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(SellManager, '/sell')
    api.add_resource(BuyAdjuster, '/buy_adjustment')
    api.add_resource(PortfolioDataPublisher, '/get_book_data')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('PORTFOLIO_ENGINE_PORT'), debug=True)
