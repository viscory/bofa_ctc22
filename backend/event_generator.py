import json
import os
import time
import requests
from flask import Flask, g, jsonify, request
from flask_restful import Api, Resource

from common import Common

MARKET_DATA_EVENTS = ["FXEvent", "PriceEvent"]
TRADE_EVENTS = ["TradeEvent"]
ALLOWED_EVENTS = TRADE_EVENTS + MARKET_DATA_EVENTS


class EventGeneratorCommon(Common):
    def __init__(self):
        super().__init__('backend/data/exclusions.db', g)

    def init_data(self, cursor):
        self.init_exclusion_table(cursor)
        self.init_tracker_table(cursor)

    def init_exclusion_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Exclusions (
                EventID TEXT PRIMARY KEY,
                Desk TEXT,
                Trader TEXT,
                Book TEXT,
                BondID TEXT,
                BuySell TEXT,
                Quantity INTEGER,
                Price TEXT,
                ExclusionType TEXT
            )
        ''')

    def init_tracker_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EventsToTrack (
                EventID TEXT,
                Status TEXT,
                Info TEXT
            )
        ''')


class EventGenerator(Resource, EventGeneratorCommon):
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
                "{bondID}",
                "{signal}",
                {int(quantity)},
                "{price}",
                "{exclusionType}"
            )
        ''')

    def tracked_events(self, eventID, cursor):
        return cursor.execute(f'''
            SELECT * FROM EventsToTrack
            WHERE
                EventID = {eventID-1}
        ''').fetchall()

    def generate_report(eventID, info):
        if 'special' in info:
            requests.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('REPORT_GENERATOR_PORT')}/generate_report/{eventID-1}"
            )
        else:
            request.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('REPORT_GENERATOR_PORT')}/generate_custom_report",
                json=jsonify({'EventID': eventID, 'Params': info})
            )

    def update_tracked_event_status(self, eventID, cursor):
        cursor.execute(f'''
            UPDATE EventsToTrack
            SET
                Status = "generated"
            WHERE
                EventID = {eventID}
        ''')

    def get(self):
        count = 0
        with open(os.getenv('EVENTS_DIR'), 'r') as dataFile:
            events = json.loads(dataFile.read())
            for event in events:
                count += 1
                eventType, eventID = event['EventType'], event['EventID']

                cursor = self.get_db().cursor()
                for eventID, status, info in self.tracked_events(eventID, cursor):
                    self.update_tracked_event_status(eventID, cursor)
                    self.generate_report(eventID, info)
                self.close_connection()

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


class ExclusionPublisher(Resource, EventGeneratorCommon):
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


class EventTracker(Resource, EventGeneratorCommon):
    def __init__(self):
        super().__init__()

    def track_event(self, cursor, eventID, params):
        cursor.execute(f'''
            INSERT INTO EventsToTrack
            VALUES ({eventID+1}, "tracking", "{params}")
        ''')

    def post(self):
        req = request.json()
        eventID = req['EventID']
        categories = req['Measures']
        measures = req['Categories']

        if 'NV' in measures and len(measures) != 1:
            response = jsonify({'msg': 'bad measures/categories'})
            response.status_code = 400
            return response
        params = f"{','.join(categories)}+{','.join(measures)}"

        try:
            eventID = int(eventID)
        except ValueError:
            response = jsonify({'msg': 'bad eventID'})
            response.status_code = 400
            return response

        cursor = self.get_db().cursor()
        self.track_event(cursor, eventID, params)
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        self.close_connection()
        return response


class EventTrackerStatus(Resource, EventGeneratorCommon):
    def __init__(self):
        super().__init__()

    def get_tracked_events(self, cursor):
        return cursor.execute('''
            SELECT * FROM EventToTrack
        ''').fetchall()

    def get(self):
        cursor = self.get_db().cursor()
        result = self.get_tracked_events(cursor)
        self.close_connection()
        response = jsonify(result)
        response.status_code = 200
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(EventGenerator, '/start_simulation')
    api.add_resource(ExclusionPublisher, '/get_exclusions')
    api.add_resource(EventTracker, '/track')

    # called by dashboard to get status of tracked events
    api.add_resource(EventTrackerStatus, '/get_track_status')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('EVENT_GENERATOR_PORT'), debug=True)
