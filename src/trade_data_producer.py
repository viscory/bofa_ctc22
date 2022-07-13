import os
import requests
from flask import Flask, request, jsonify
from flask_restful import Api, Resource


class TradeDataSubscriber(Resource):
    def __init__(self):
        super().__init__()

    def post(self):
        req = request.json
        tradeData = requests.get(
            url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('MARKET_DATA_PRODUCER_PORT')}/enrich_trade",
            json=req
        )
        tradeData = tradeData.json()
        if 'ExclusionType' in tradeData:
            response = jsonify(tradeData)
            response.status_code = 400
            return response

        req['FxRate'], req['MarketPrice'] = tradeData['FxRate'], tradeData['MarketPrice'] 
        signalType = req['BuySell']
        if signalType == 'sell':
            res = requests.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('PORTFOLIO_ENGINE_PORT')}/sell",
                json=req
            )
        if signalType == 'buy':
            res = requests.post(
                url=f"http://{os.getenv('FLASK_HOST')}:{os.getenv('CASH_ADJUSTER_PORT')}/buy",
                json=req
            )
        res = res.json()
        if 'ExclusionType' in res:
            response = jsonify(res)
            response.status_code = 400
            return response
        else:
            response = jsonify({'msg': 'success'})
            response.status_code = 200
        return response


if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(TradeDataSubscriber, '/publish_trade_event')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('TRADE_DATA_PRODUCER_PORT'), debug=True)
