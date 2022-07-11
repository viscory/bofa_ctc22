import os
import csv
import sqlite3
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource
from features.common import FiccCommon


class PortfolioEngineCommon(FiccCommon):
    def __init__(self):
        super().__init__('data/portfolio_data.db', 'portfolioData')

    def init_portfolio_table(self, cursor):
        cursor.execute('''
        CREATE TABLE PortfolioData (
            desk TEXT Primary,
            trader TEXT Primary,
            book TEXT Primary,
            bondID TEXT Primary,
            positions TEXT Primary,
            cash REAL,
        )
        ''')

    def init_data(self, cursor):
        self.init_portfolio_table(cursor)

    def get_positions(self, cursor, book, bondID):
        result = cursor.execute(f'''
            SELECT positions FROM PortfolioData
            WHERE
                bondID = "{bondID}"
                AND book = "{book}"
        ''').fetchall()
        if len(result) == 0:
            return 0
        return int(result[0])


    def adjust_positions(self, cursor, book, bondID, qty):
        initial = self.get_position(cursor, book, bondID)
        cursor.execute(f'''
            UPDATE PortfolioData
            SET positions = {initial+qty}
            WHERE book = {book}
                AND bondID = {bondID}
        ''')


class SellManager(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def is_valid(self, cursor, book, bondID, qty):
        return self.get_positions(cursor, book, bondID) >= qty

    def post(self):
        req = request.json
        cursor = self.get_db().cursor()

        desk, qty = req['Desk'], int(req['Quantity'])
        if self.is_valid(cursor, book, bondID, qty):
            payload = dict()
            payload['Desk'] = req['Desk']
            payload['TxnValue'] = req['TxnValue']
            request.post(
                url=f"{os.getenv('FLASK_HOST')}:{os.getenv('FLASK_PORT')}/sell_adjustment",
                data=payload,
            )
            self.adjust_position(cursor, book, bondID, -1*qty)
        else:
            req['ExclusionType'] = 'QUANTITY_OVERLIMIT'

        self.close_connection()
        if 'ExclusionType' in req:
            return jsonify(req), 400
        return jsonify({'msg': 'success'}), 200


class BuyAdjuster(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        cursor = self.get_db().cursor()

        desk, qty = req['Desk'], float(req['Quantity'])
        self.adjust_desk(cursor, desk, qty)
        self.close_connection()
        return jsonify({'msg': 'success'}), 200


class PortfolioDataPublisher(Resource, PortfolioEngineCommon):
    def __init__(self):
        super().__init__()

    def get_all_desk_cash(self, cursor):
        return cursor.execute('''
            SELECT Desk, Trader, Book, BondID, Positions
            FROM PortfolioData
        ''').fetchall()

    def get_market_prices(self):
        return request.get(f"{os.getenv('FLASK_HOST')}:{os.getenv('FLASK_PORT')}/get_market_data")

    def get_info(self, cursor):
        res = dict()
        res['Desk'] = self.get_all_desk_cash(cursor)
        res['Bond'], res['FX'] = self.get_market_prices()

    def get(self):
        cursor = self.get_db().cursor()

        res = self.get_info(cursor)
        self.close_connection()
        return jsonify(res), 200
