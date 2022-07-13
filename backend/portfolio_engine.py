import os
import sqlite3
import requests
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource


class PortfolioEngineCommon():
    def __init__(self):
        self.DATABASE = 'data/portfolio_data.db'

    def close_connection(self):
        db = getattr(g, "_database", None)
        if db is not None:
            db.commit()
            db.close()

    def get_db(self):
        self.init_db()
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(self.DATABASE)
        return db

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
        self.init_portfolio_table(cursor)

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


class PortfolioDataPublisher(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def get_all_data(self, cursor):
        return cursor.execute('''
            SELECT Desk, Trader, Book, BondID, Positions
            FROM PortfolioData
        ''').fetchall()

    def get_market_prices(self):
        responseJson = requests.get(f"http://{os.getenv('FLASK_HOST')}:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/get_market_data").json()
        return responseJson['Bond'], responseJson['FX']

    @staticmethod
    def calculate_net_value(quantity, marketPrice, fxRate):
        return quantity * (marketPrice / fxRate)

    def get_info(self, cursor):
        res = []
        bondPrices, fxRates = self.get_market_prices()
        for (desk, trader, book, bondID, positions) in self.get_all_data(cursor):
            bondCurrency, bondPrice = bondPrices.get(bondID)
            res.append([desk, trader, book, bondID, positions])
            res[-1].append(self.calculate_net_value(
                positions, bondPrice, fxRates[bondCurrency]
            ))
        return res

    def get(self):
        cursor = self.get_db().cursor()
        result = self.get_info(cursor)
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
