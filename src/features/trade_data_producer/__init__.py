import csv
import sqlite3
import requests
from flask import Flask, request, jsonify, g
from flask_restful import Api, Resource

class TradeDataSubscriber(Resource):
    def __init__(self):
        super().__init__()

    @staticmethod
    def validate_trade_event(event):
        try:
            assert len(event) == 7
            assert float(event.get("Quantity")) == int(event.get("Quantity"))
        except:
            app.logger.error(f"EventID: {event.get('EventID')}, malformed trade event")

    def post(self):
        req = request.json
        self.validate_trade_event(req)
       
        tradeData, status = requests.post(
            url=f"{os.getenv('FLASK_HOST')}:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/enrich_trade",
            data=req
        )
        if 'ExclusionType' in tradeData:
            return jsonify(event), 400

        signalType = req['EventType']
        if signalType == 'sell':
            event, status = requests.post(
                url=f"{os.getenv('FLASK_HOST')}:{os.getenv('FLASK_PORT')}/sell",
                data=tradeData
            )
        if signalType == 'buy':
            event, status = requests.post(
                url=f"{os.getenv('FLASH_HOST')}:{os.getenv('FLASK_PORT')}/buy",
                data=tradeData
            )

        if 'ExclusionType' in event:
            return jsonify(event), 400
        return jsonify({'msg':'success'}), 200
