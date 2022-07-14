import json
import os
import time
import requests
from flask import Flask, g, jsonify
from flask_restful import Api, Resource

from common import DbCommon

MARKET_DATA_EVENTS = ["FXEvent", "PriceEvent"]
TRADE_EVENTS = ["TradeEvent"]
ALLOWED_EVENTS = TRADE_EVENTS + MARKET_DATA_EVENTS


class EventGeneratorDbCommon(DbCommon):
    def __init__(self):
        super().__init__('backend/data/exclusions.db', g)

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


class EventGenerator(Resource, EventGeneratorDbCommon):
    def __init__(self):
        super().__init__()

    def insert_exclusion(
        self,
        cursor,
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

    def get(self):
        count = 0
        with open(os.getenv('EVENTS_DIR'), 'r') as dataFile:
            events = json.loads(dataFile.read())
            for event in events:
                count += 1
                eventType, eventID = event['EventType'], event['EventID']
                requests.post(
                    url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('REPORT_GENERATOR_PORT')}/generate_report/{eventID}"
                )
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
                        cursor = self.get_db().cursor()
                        exclusionType = resJson['ExclusionType']
                        marketPrice = resJson['MarketPrice']
                        self.insert_exclusion(
                            cursor,
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
                        self.close_connection()
                else:
                    app.logger.error(f"EventID: {event.get('EventID')}, invalid event type")
                time.sleep(int(os.getenv('EVENT_PRODUCTION_DELAY'))/1000)
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


class ExclusionPublisher(Resource, EventGeneratorDbCommon):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_exclusions(cursor):
        return cursor.execute('''
            SELECT * FROM Exclusions
        ''').fetchall()

    def get(self):
        cursor = self.get_db().cursor()
        data = self.get_exclusions(cursor)
        self.close_connection()
        response = jsonify(data)
        response.status_code = 200
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(EventGenerator, '/start_simulation')
    api.add_resource(ExclusionPublisher, '/get_exclusions')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('EVENT_GENERATOR_PORT'), debug=True)
