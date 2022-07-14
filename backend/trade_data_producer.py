import os
import requests
from flask import Flask, request, jsonify
from flask_restful import Api, Resource


# this class receives trade events from event generator
class TradeDataSubscriber(Resource):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        # it first enriches the trade event with the bond's market price, the underlying
        # currency's market rate failing to find either of this leads to the NO_MARKET_PRICE exclusion
        tradeData = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/enrich_trade",
            json=req
        )
        tradeData = tradeData.json()
        # if the trade event is an exclusion, the padded trade event data is returned to event generator for record
        if 'ExclusionType' in tradeData:
            response = jsonify(tradeData)
            response.status_code = 402
            return response

        # the new data is padded to the original POST request
        req['FxRate'], req['MarketPrice'] = tradeData['FxRate'], tradeData['MarketPrice']
        signalType = req['BuySell']

        # if txn is a sell, what determines its feasiblity is whether enough positions are available to be sold
        # portfolio engine keeps record of that
        if signalType == 'sell':
            resJson = requests.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('PORTFOLIO_ENGINE_PORT')}/sell",
                json=req
            ).json()
        # if txn is a buy, what determines its feasiblity is whether enough cash is available in the desk
        # cash adjuster keeps record of that
        elif signalType == 'buy':
            resJson = requests.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('CASH_ADJUSTER_PORT')}/buy",
                json=req
            ).json()
        else:
            response = jsonify({'msg': 'invalid signal'})
            response.status_code = 400

        if 'ExclusionType' in resJson:
            response = jsonify(resJson)
            response.status_code = 401
        else:
            response = jsonify({'msg': 'success'})
            response.status_code = 200
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    # event generator
    api.add_resource(TradeDataSubscriber, '/publish_trade_event')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('TRADE_DATA_PRODUCER_PORT'), debug=True)
