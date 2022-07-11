import os
import csv
import sqlite3
import requests
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
       
        try:
            tradeData, status = requests.post(
                url=f"localhost:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/enrich_trade",
                data=req
            )
        except:
            app.logger.error(f"EventID: {event.get('EventID')}, cannot enrich trade event")
            return jsonify({}), 400

        signalType = req['EventType']
        if signalType == 'sell':
            exclusionJson, status = requests.post(
                url=f"localhost:{os.getenv('PORTFOLIO_ENGINE_PORT')}/sell",
                data=tradeData
            )
        if signalType == 'buy'
            exclusionJson, status = requests.post(
                url=f"localhost:{os.getenv('CASH_ADJUSTER_PORT')}/buy",
                data=tradeData
            )

        if status != 200:
            return exclusionJson, 400
        return jsonify({}), 200


if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(TradeDataSubscriber, "/publish_trade_event")

    app.run(port=os.getenv('MARKET_DATA_PRODUCER_PORT'))
