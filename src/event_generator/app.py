import json
import os
import time
import sqlite
import logging as log

from routes import app

ALLOWED_EVENTS = ['FxEvent', 'PriceEvent', 'TradeEvent']
MARKET_DATA_EVENTS = ['FxEvent', 'PriceEvent']
TRADE_EVENTS = ['TradeEvent']
EVENT_DELAY = os.getenv('EVENT_PRODUCTION_DELAY')/1000


class EventProducer(Resource):
    def get():
        with open('data/events.json', 'r') as data_file:
            data = json.loads(data_file)
            for event in data:
                event_type = event.get('EventType')
                if event_type not in ALLOWED_EVENTS:
                    continue
                elif event_type in MARKET_DATA_EVENTS:
                    print("sent to market data producer")
                elif event_type in TRADE_EVENTS:
                    print("sent to trade data producer")
                time.sleep(EVENT_DELAY)


class ExclusionRecorder(Resource):
    def post():
        pass

    def get():
        pass
        
