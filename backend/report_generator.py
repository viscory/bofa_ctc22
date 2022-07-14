import shutil
import os
import requests
import pandas as pd
from flask import Flask, jsonify, request
from flask_restful import Api, Resource


class ReportGeneratorCommon:
    # the following generate dataframes for the csv files required in the tech spec
    # primarily, they are simple groupby-summations according to different criteria
    # some custom logic is required to format the data to the right decimal points
    def generate_bond_level_report(self, df):
        targetHeaders = ['Desk', 'Trader', 'Book', 'BondID', 'Positions', 'NV']
        final = df[targetHeaders]
        final['NV'] = final['NV'].apply(
            lambda x: '{:.2f}'.format(float(x))
        )
        final = final.sort_values(by=['Desk', 'Trader', 'Book', 'BondID'])
        return final

    def generate_currency_level_report(self, df):
        targetHeaders = ['Desk', 'Currency', 'Positions', 'NV']
        groupbyColumns = ['Desk', 'Currency']

        final = df[targetHeaders].groupby(groupbyColumns).sum().reset_index()[:]
        final['Positions'] = final['Positions'].apply(
            lambda x: '{:.3f}'.format(float(x))
        )
        final['NV'] = final['NV'].apply(
            lambda x: '{:.2f}'.format(float(x))
        )
        final = final.sort_values(by=['Desk', 'Currency'])
        return final

    def generate_position_level_report(self, df):
        targetHeaders = ['Desk', 'Trader', 'Book', 'BondID', 'Positions', 'NV']
        groupbyColumns = ['Desk', 'Trader', 'Book']

        final = df[targetHeaders].groupby(groupbyColumns).sum().reset_index()[:]
        final['Positions'] = final['Positions'].apply(
            lambda x: '{:.3f}'.format(float(x))
        )
        final['NV'] = final['NV'].apply(
            lambda x: '{:.2f}'.format(float(x))
        )
        final = final.sort_values(by=['Desk', 'Trader', 'Book'])
        return final

    # data is first collected from the relevant components, then they undergo
    # the necessary transformations
    def generate_cash_level_report(self):
        responseJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('CASH_ADJUSTER_PORT')}/get_desk_data"
        ).json()
        headers = ['Desk', 'Cash']

        final = pd.DataFrame(responseJson)
        final.columns = headers
        final['Cash'] = final['Cash'].apply(
            lambda x: '{:.2f}'.format(float(x))
        )
        final = final.sort_values(by=['Desk'])

        return final

    def generate_exclusion_report(self):
        responseJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('EVENT_GENERATOR_PORT')}/get_exclusions"
        ).json()
        headers = [
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

        df = pd.DataFrame(responseJson)
        df.columns = headers
        df['Price'] = df['Price'].apply(lambda x: '' if x == '' else '{:.2f}'.format(float(x)))
        return df

    def get_data(self):
        headers = [
            'Desk',
            'Trader',
            'Book',
            'BondID',
            'Positions',
            'Currency',
            'Price',
            'NV',
        ]

        deskJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('CASH_ADJUSTER_PORT')}/get_desk_data"
        ).json()
        bookJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('PORTFOLIO_ENGINE_PORT')}/get_book_data"
        ).json()
        fxJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/get_data/fx"
        ).json()
        bondJson = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/get_data/bonds"
        ).json()

        fxDict = {k: v for (k,v) in fxJson}
        bondCurrencyDict = {k: v for (k,v,z) in bondJson}
        bondPriceDict = {k: fxDict[v]*z for (k,v,z) in bondJson}

        df = pd.DataFrame(bookJson)
        df[5] = df[3].map(bondCurrencyDict)
        df[6] = df[3].map(bondPriceDict)
        df[7] = df[4]*df[6]
        df.columns = headers
        return df


# this class exports the aforementioned dataframes into their relevant csv files
# as per the filename format specified in the tech spec
class ReportGenerator(Resource, ReportGeneratorCommon):
    def __init__(self):
        super().__init__()

    def export_to_csv(self, eventID, reportType, df):
        df.to_csv(
            f"backend/outputs/output_{eventID}/{reportType}_{eventID}.csv",
            index=False
        )

    # this abstraction removed around 30-40 lines of code, so it was worthwhile
    # for the last three reports, the same data is used, so it is passes as an arg
    def create_reports(self, eventID, reportType, data):
        if reportType == 'exclusions':
            df = self.generate_exclusion_report()
        elif reportType == 'cash_level_portfolio':
            df = self.generate_cash_level_report()
        elif reportType == 'position_level_portfolio':
            df = self.generate_position_level_report(data)
        elif reportType == 'bond_level_portfolio':
            df = self.generate_bond_level_report(data)
        elif reportType == 'currency_level_portfolio':
            df = self.generate_currency_level_report(data)
        self.export_to_csv(eventID, reportType, df)

    # if the directory exists, it is removed to purge old report data
    # if outputs doesnt exist, it is made, primitive fault tolerance
    def create_output_folder(self, eventID):
        if not os.path.isdir("backend/outputs"):
            os.mkdir('backend/outputs')
        elif os.path.isdir(f"backend/outputs/output_{eventID}"):
            shutil.rmtree(f"backend/outputs/output_{eventID}")
        os.mkdir(f'backend/outputs/output_{eventID}')

    def create_reports(self, eventID):
        targetID = eventID-1
        self.create_output_folder(targetID)
        data = self.get_data()
        reportTypes = [
            'exclusions',
            'cash_level_portfolio',
            'position_level_portfolio',
            'bond_level_portfolio',
            'currency_level_portfolio'
        ]
        for reportType in reportTypes:
            self.create_report(eventID, reportType, data)

    def post(self, eventID):
        try:
            eventID = int(eventID)
        except ValueError:
            response = jsonify({'msg': 'bad eventID'})
            response.status_code = 400
            return response
        self.create_reports(eventID)
        response = jsonify({'msg': 'success'})
        response.status_code = 200
        return response


# this class is meant to serve requests from the portfolio dashboard
# this is required as the previous class is meant to only export the data
# more refactoring is possible here
class DashboardReporter(Resource, ReportGeneratorCommon):
    def __init__(self):
        super().__init__()

    def get(self, reportType):
        if reportType == 'cash':
            df = self.generate_cash_level_report()
        else:
            data = self.get_data()
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


# this class is meant to satisfy additional component #1
# categories and measures data is passes from the frontend to here
# this is then processed to create the relevant csv file
class CustomReporter(Resource, ReportGeneratorCommon):
    def __init__(self):
        super().__init__()

    def custom_report(self, categories, measures):
        BookDf = self.get_data()
        DeskDf = self.generate_cash_level_report()
        import pdb; pdb.set_trace()
        headers = categories + measures

    def post(self):
        import pdb; pdb.set_trace()
        req = request.json()
        eventID = req['EventID']
        param = req['Params'].split('+')
        categories, measures = param[0], param[1]
        categories, measures = (categories.split(','), measures.split(','))
        if not isinstance(categories, list):
            categories = [categories]
        if not isinstance(measures, list):
            measures = [measures]
        df = self.custom_report(categories, measures)


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(ReportGenerator, '/generate_report/<string:eventID>')
    api.add_resource(DashboardReporter, '/get_report/<string:reportType>')
    api.add_resource(CustomReporter, '/generate_custom_report')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('REPORT_GENERATOR_PORT'), debug=True)
