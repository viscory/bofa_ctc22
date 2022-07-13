import json
import os
import time
import sqlite3
import requests
from flask import Flask, g, jsonify
from flask_restful import Api, Resource

MARKET_DATA_EVENTS = ["FXEvent", "PriceEvent"]
TRADE_EVENTS = ["TradeEvent"]
ALLOWED_EVENTS = TRADE_EVENTS + MARKET_DATA_EVENTS
EVENT_DELAY = int(os.getenv("EVENT_PRODUCTION_DELAY"))/1000
EVENT_DELAY = 0.2


class EventGeneratorCommon:
    def __init__(self):
        self.DATABASE = 'data/exclusions.db'

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
        self.init_exclusion_table(cursor)

    def init_exclusion_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Exclusions (
                EventID TEXT PRIMARY KEY,
                Desk TEXT,
                Trader TEXT,
                Book TEXT,
                BuySell TEXT,
                Quantity INTEGER,
                BondID TEXT,
                Price TEXT,
                ExclusionType TEXT
            )
        ''')


class EventGenerator(Resource, EventGeneratorCommon):
    def __init__(self):
        super().__init__()
        self.dataDir = 'data/events.json'
        self.DATABASE = 'data/exclusions.db'

    def insert_exclusion(
        self,
        eventID,
        desk,
        trader,
        book,
        signal,
        quantity,
        bondID,
        marketPrice,
        exclusionType
    ):
        self.init_db()
        db = sqlite3.connect(self.DATABASE)
        cursor = db.cursor()
        # assuming no primary key assumptions
        # as evens.json is assumed to be valid
        price = str(float(marketPrice))
        if exclusionType == 'NO_MARKET_PRICE':
            price = ''
        cursor.execute(f'''
            INSERT OR REPLACE INTO Exclusions
            VALUES (
                "{eventID}",
                "{desk}",
                "{trader}",
                "{book}",
                "{signal}",
                {int(quantity)},
                "{bondID}",
                "{price}",
                "{exclusionType}"
            )
        ''')
        db.commit()
        db.close()

    def get(self):
        with open(self.dataDir, 'r') as dataFile:
            events = json.loads(dataFile.read())
            for event in events:
                eventType, eventID = event['EventType'], event['EventID']
                if eventType in MARKET_DATA_EVENTS:
                    requests.post(
                        url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/publish_price_event",
                        json=event
                    )
                elif eventType in TRADE_EVENTS:
                    desk, trader, book, signal, quantity, bondID = (
                        event['Desk'],
                        event['Trader'],
                        event['Book'],
                        event['BuySell'],
                        event['Quantity'],
                        event['BondID'],
                    )
                    resJson = requests.post(
                        url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('TRADE_DATA_PRODUCER_PORT')}/publish_trade_event",
                        json=event
                    ).json()
                    if 'ExclusionType' in resJson:
                        exclusionType = resJson['ExclusionType']
                        marketPrice = resJson['MarketPrice']
                        self.insert_exclusion(
                            eventID,
                            desk,
                            trader,
                            book,
                            signal,
                            quantity,
                            bondID,
                            marketPrice,
                            exclusionType
                        )
                else:
                    app.logger.error(f"EventID: {event.get('EventID')}, invalid event type")
                time.sleep(EVENT_DELAY)
        self.close_connection()

        return jsonify({'msg': 'success'}), 200


class ExclusionPublisher(Resource, EventGeneratorCommon):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_exclusions(cursor):
        return cursor.execute('''
            SELECT * FROM Exclusions
        ''').fetchall()

    def get(self):
        conn = self.get_db()
        cursor = conn.cursor()
        data = self.get_exclusions(cursor)
        conn.close()
        response = jsonify(data)
        response.status_code = 200
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(EventGenerator, '/start_simulation')
    api.add_resource(ExclusionPublisher, '/get_exclusions')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('EVENT_GENERATOR_PORT'), debug=True)
