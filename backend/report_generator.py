import shutil
import os
import requests
import pandas as pd
from flask import Flask, jsonify, g
from flask_restful import Api, Resource

from common import DbCommon


class ReportGeneratorCommon(DbCommon):
    def __init__(self):
        super().__init__('backend/data/report_generator.db', g)

    def init_data(self, cursor):
        self.init_event_tracker(cursor)
        self.init_latest_event(cursor)

    def init_event_tracker(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EventsToTrack (
                EventID INTEGER PRIMARY KEY
            )
        ''')

    def generate_currency_level_report(self, df):
        final = df[['Desk', 'Currency', 'Positions', 'NV']].groupby(
            ['Desk', 'Currency']
        ).sum().reset_index()[:]
        final['Positions'] = final['Positions'].apply(
            lambda x: '{:.3f}'.format(float(x))
        )
        final['NV'] = final['NV'].apply(
            lambda x: '{:.2f}'.format(float(x))
        )
        final = final.sort_values(by=['Desk', 'Currency'])
        return final

    def generate_bond_level_report(self, df):
        final = df[['Desk', 'Trader', 'Book', 'BondID', 'Positions', 'NV']]
        final['NV'] = final['NV'].apply(
            lambda x: '{:.2f}'.format(float(x))
        )
        final = final.sort_values(by=['Desk', 'Trader', 'Book', 'BondID'])
        return final

    def generate_position_level_report(self, df):
        final = df[['Desk', 'Trader', 'Book', 'BondID', 'Positions', 'NV']].groupby(
            ['Desk', 'Trader', 'Book']
        ).sum().reset_index()[:]
        final['Positions'] = final['Positions'].apply(
            lambda x: '{:.3f}'.format(float(x))
        )
        final['NV'] = final['NV'].apply(
            lambda x: '{:.2f}'.format(float(x))
        )
        final = final.sort_values(by=['Desk', 'Trader', 'Book'])
        return final

    def generate_cash_level_report(self):
        responseJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('CASH_ADJUSTER_PORT')}/get_desk_data"
        ).json()
        final = pd.DataFrame(responseJson)
        final.columns = ['Desk', 'Cash']
        final['Cash'] = final['Cash'].apply(lambda x: '{:.2f}'.format(float(x)))
        final = final.sort_values(by=['Desk'])

        return final

    def generate_exclusion_report(self):
        responseJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('EVENT_GENERATOR_PORT')}/get_exclusions"
        ).json()

        df = pd.DataFrame(responseJson)
        df.columns = [
            'EventID',
            'Desk',
            'Trader',
            'Book',
            'BuySell',
            'Quantity',
            'BondID',
            'Price',
            'ExclusionType'
        ]
        df['Price'] = df['Price'].apply(lambda x: '' if x == '' else '{:.2f}'.format(float(x)))
        return df

    def get_book_data(self):
        responseJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('PORTFOLIO_ENGINE_PORT')}/get_book_data"
        ).json()
        df = pd.DataFrame(responseJson)
        df.columns = [
            'Desk',
            'Trader',
            'Book',
            'BondID',
            'Positions',
            'Currency',
            'Price',
            'NV',
        ]
        return df


class ReportGenerator(Resource, ReportGeneratorCommon):
    def __init__(self):
        super().__init__()

    def create_currency_level_report(self, eventID, df):
        final = self.generate_currency_level_report(df)
        final.to_csv(
            f"backend/outputs/output_{eventID}/currency_level_portfolio_{eventID}.csv",
            index=False
        )

    def create_bond_level_report(self, eventID, df):
        final = self.generate_bond_level_report(df)
        final.to_csv(
            f"backend/outputs/output_{eventID}/bond_level_portfolio_{eventID}.csv",
            index=False
        )

    def create_position_level_report(self, eventID, df):
        final = self.generate_currency_level_report(df)
        final.to_csv(
            f"backend/outputs/output_{eventID}/position_level_portfolio_{eventID}.csv",
            index=False
        )


    def create_cash_level_report(self, eventID):
        final = self.generate_cash_level_report()
        final.to_csv(
            f"backend/outputs/output_{eventID}/cash_level_portfolio_{eventID}.csv",
            index=False
        )

    def create_exclusion_report(self, eventID):
        final = self.generate_exclusion_report()
        final.to_csv(
            f"backend/outputs/output_{eventID}/exclusions_{eventID}.csv",
            index=False
        )

    def create_output_folder(self, eventID):
        if os.path.isdir(f"backend/outputs/output_{eventID}"):
            shutil.rmtree(f"backend/outputs/output_{eventID}")
        os.mkdir(f'backend/outputs/output_{eventID}')

    def create_reports(self, eventID):
        targetID = eventID-1
        self.create_output_folder(targetID)
        self.create_exclusion_report(targetID)
        self.create_cash_level_report(targetID)

        data = self.get_book_data()
        self.create_currency_level_report(targetID, data)
        self.create_bond_level_report(targetID, data)
        self.create_position_level_report(targetID, data)

    def being_tracked(self, cursor, eventID):
        result = cursor.execute(f'''
            SELECT * FROM EventsToTrack
            WHERE
                EventID = {eventID}
        ''').fetchall()
        is_tracked = len(result) > 0
        if is_tracked:
            cursor.execute(f'''
                DELETE FROM EventsToTrack
                WHERE EventID = {eventID}
            ''')
            return True
        return False

    def post(self, eventID):
        try:
            eventID = int(eventID)
        except ValueError:
            response = jsonify({'msg': 'bad eventID'})
            response.status_code = 400
            return response

        cursor = self.get_db().cursor()
        if self.being_tracked(cursor, eventID):
            self.close_connection()
            self.create_reports(eventID)
        self.close_connection()
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


class EventTracker(Resource, ReportGeneratorCommon):
    def __init__(self):
        super().__init__()

    def track_event(self, cursor, eventID):
        cursor.execute(f'''
            INSERT OR REPLACE INTO EventsToTrack
            VALUES ({eventID+1})
        ''')

    def get_events(self, cursor):
        return cursor.execute('''
            SELECT EventID from EventsToTrack
        ''').fetchall()

    def post(self, eventID):
        try:
            eventID = int(eventID)
        except ValueError:
            response = jsonify({'msg': 'bad eventID'})
            response.status_code = 400
            return response

        cursor = self.get_db().cursor()
        self.track_event(cursor, eventID)
        response = jsonify({'tracking': self.get_events(cursor)})
        response.status_code = 200
        self.close_connection()
        return response


class DashboardReporter(Resource, ReportGeneratorCommon):
    def __init__(self):
        super().__init__()

    def get(self, reportType):
        if reportType == 'cash':
            df = self.generate_cash_level_report()
        else:
            data = self.get_book_data()
            if reportType == 'currency':
                df = self.generate_currency_level_report(data)
            elif reportType == 'bond':
                df = self.generate_bond_level_report(data)
            elif reportType == 'position':
                df = self.generate_position_level_report(data)
            else:
                response = jsonify({'msg': 'bad report param'})
                response.status_code = 400
                return response
        response = jsonify([df.columns.tolist()]+df.values.tolist())
        response.status_code = 200
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(ReportGenerator, '/generate_report/<string:eventID>')
    api.add_resource(EventTracker, '/generate_for/<string:eventID>')
    api.add_resource(DashboardReporter, '/get_report/<string:reportType>')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('REPORT_GENERATOR_PORT'), debug=True)
