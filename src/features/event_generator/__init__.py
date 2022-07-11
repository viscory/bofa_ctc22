import json
import os
import time
import sqlite3
import requests
from logging.config import dictConfig
from flask import Flask
from flask_restful import Api, Resource

from features.common import FiccCommon

MARKET_DATA_EVENTS = ["FXEvent", "PriceEvent"]
TRADE_EVENTS = ["TradeEvent"]
ALLOWED_EVENTS = TRADE_EVENTS + MARKET_DATA_EVENTS
EVENT_DELAY = int(os.getenv("EVENT_PRODUCTION_DELAY"))/1000


class EventGeneratorCommon(FiccCommon):
    def __init__(self):
        super().__init__('data/exclusions.db', 'exclusions')

    def init_exclusion_table(self, cursor):
        cursor.execute('''
            CREATE TABLE Exclusions (
                EventID TEXT PRIMARY,
                Desk TEXT,
                Trader TEXT,
                Book TEXT,
                BuySell TEXT,
                Quantity TEXT,
                BondID TEXT,
                Price TEXT,
                ExclusionType TEXT
            )
        ''')

    def init_data(cursor):
        self.init_exclusion_table(cursor)


class EventGenerator(Resource, EventGeneratorCommon):
    def __init__(self):
        super().__init__()
        self.dataDir = 'data/events.json'

    def insert_exclusion(self, cursor, event):
        # assuming no primary key assumptions
        # as evens.json is assumed to be valid
        price = str(event.get('MarketPrice'))
        if event.get('ExclusionType') == 'NO_MARKET_PRICE':
            price = ''
        cursor.execute(f'''
            INSERT INTO Exclusions
            VALUES (
                "{event.get('EventID')}",
                "{event.get('Desk')}",
                "{event.get('Trader')}",
                "{event.get('Book')}",
                "{event.get('BuySell')}",
                "{event.get('Quantity')}",
                "{event.get('BondID')}",
                "{price}",
                "{event.get('ExclusionType')}",
            )
        ''')

    def get(self):
        with open(self.dataDir, 'r') as dataFile:
            events = json.loads(dataFile.read())
            for event in events:
                eventType = event.get('EventType')
                if eventType in MARKET_DATA_EVENTS:
                    requests.post(
                        url=f"{os.getenv('FLASK_HOST')}:{os.getenv('FLASK_PORT')}/publish_price_event",
                        data=event
                    )
                elif eventType in TRADE_EVENTS:
                    response, status = requests.post(
                        url=f"{os.getenv('FLASK_HOST')}:{os.getenv('FLASK_PORT')}/publish_trade_event",
                        data=event
                    )
                    if 'ExclusionType' in response:
                        cursor = self.get_db().cursor()
                        self.insert_exclusion(response)
                        self.close_connection()
                else:
                    app.logger.error(f"EventID: {event.get('EventID')}, invalid event type")
                time.sleep(EVENT_DELAY)
        return {'msg': 'success'}, 200


class ExclusionPublisher(Resource, FiccCommon):
    def __init__(self):
        super().__init__()
    
    def get_exclusions(self, cursor):
        return cursor.execute('''
            SELECT * FROM Exclusions
        ''').fetchall()
    
    def get(self):
        cursor = self.get_db().cursor()
        data = self.get_exclusions(self, cursor)
        self.close_connection()
        return jsonify({"data": data}), 200
