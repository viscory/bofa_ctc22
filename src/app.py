import os
from logging.config import dictConfig
from flask import Flask
from flask_restful import Api, Resource

from features.event_generator import EventGenerator, ExclusionPublisher
from features.market_data_producer import MarketDataSubscriber, MarketDataPublisher, TradeDataEnricher
from features.trade_data_producer import TradeDataSubscriber
from features.portfolio_engine import SellManager, BuyAdjuster, PortfolioDataPublisher
from features.cash_adjuster import BuyManager, SellAdjuster, DeskDataPublisher


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

if __name__ == "__main__":
    app = Flask(__name__)
    api = Api(app)

    # get request starts endpoint
    api.add_resource(EventGenerator, "/start_simulation")

    # TradeDataEvents are enriched with latest FxRates+MarketPrices
    api.add_resource(TradeDataEnricher, "/enrich_trade")
    # events are streamed into these components
    api.add_resource(MarketDataSubscriber, "/publish_price_event")
    api.add_resource(TradeDataSubscriber, "/publish_trade_event") 

    # actual endpoints for buy/sell
    api.add_resource(BuyManager, '/buy')
    api.add_resource(SellManager, '/sell')
    # adjusters to adjust the desk cash db if stuff is sold,
    # or the portfolio db if stuff is bought
    # indirect causation
    api.add_resource(BuyAdjuster, '/buy_adjustment')
    api.add_resource(SellAdjuster, '/sell_adjustment')

    # endpoints to be queried by ReportGenerator, PortfolioDashboard
    api.add_resource(DeskDataPublisher, '/get_desk_data')
    api.add_resource(ExclusionPublisher,  '/get_exclusions')
    api.add_resource(PortfolioDataPublisher, '/get_book_data')
    api.add_resource(MarketDataPublisher, '/get_market_data')

    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('FLASK_PORT'), debug=True)
