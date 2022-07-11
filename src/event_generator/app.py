import json
import os
import time
import sqlite3
from logging.config import dictConfig
from flask import Flask
from flask_restful import Api, Resource

MARKET_DATA_EVENTS = ["FXEvent", "PriceEvent"]
TRADE_EVENTS = ["TradeEvent"]
ALLOWED_EVENTS = TRADE_EVENTS + MARKET_DATA_EVENTS
EVENT_DELAY = int(os.getenv("EVENT_PRODUCTION_DELAY"))/1000

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


class EventGeneratorCommon:
    def __init__(self):
        self.DATABASE = 'data/exclusions.db'

    @staticmethod
    def close_connection():
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

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
                Price REAL,
                ExclusionType TEXT
            )
        ''')

    def init_db(self):
        try:
            os.stat(self.DATABASE)
        except FileNotFoundError:
            try:
                conn = sqlite3.connect(self.DATABASE)
                cursor = conn.cursor()
                self.init_exclusion_table(cursor)
                conn.commit()
                conn.close()
            except Exception:
                app.logger.error("Error initializing database")

    def get_db(self):
        self.init_db()
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(self.DATABASE)
        return db


class EventGenerator(Resource, EventGeneratorCommon):
    def __init__(self):
        super().__init__()

    def insert_exclusion(self, exclusionJson, exclusion):
        cursor = self.get_db().cursor()
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
                {event.get('TxnValue')},
                "{event.get('ExclusionType')}",
            )
        ''')
        self.close_connection()

    def get(self):
        with open("data/events.json", "r") as dataFile:
            events = json.loads(dataFile.read())
            for event in events:
                eventType = event.get("EventType")
                if eventType in MARKET_DATA_EVENTS:
                    requests.post(
                        url=f"localhost:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/publish_price_event",
                        data=event
                    )
                elif eventType in TRADE_EVENTS:
                    exclusionJson, status = requests.post(
                        url=f"localhost:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/publish_trade_event",
                        data=event
                    )
                    if status != 200:
                        self.insert_exclusion(exclusinJson, exclusion)
                else:
                    app.logger.error(f"EventID: {event.get('EventID')}, invalid event type")
                time.sleep(EVENT_DELAY)


class ExclusionPublisher(Resource):
    def __init__(self):
        super().__init__()
    
    def get_exclusions(self):
        cursor = self.get_db().cursor()
        self.close_connection()
        return cursor.execute('''
            SELECT * FROM Exclusions
        ''').fetchall()
    
    def get(self):
        return jsonify(self.get_exclusions()), 200


if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(EventGenerator, "/start_simulation")
    api.add_resource(ExclusionPublisher,  "/get_exclusions")

    app.run()
