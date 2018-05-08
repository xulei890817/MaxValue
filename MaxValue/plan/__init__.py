from MaxValue.market import MarketManager, MarketClass, Market
from abc import abstractmethod

from MaxValue.market.market_collections import BitMexMarket, OKEXMarket


class UpdateHandler(object):
    @abstractmethod
    def ticker(self, data):
        pass

    @abstractmethod
    def k_line(self, data):
        pass

    @abstractmethod
    def depth(self, data):
        pass


class BasePlan(object):
    def __init__(self, loop):
        self.market_manager = MarketManager()
        self._loop = loop
        self.login_market()

    @abstractmethod
    def login_market(self):
        pass

    def login_into_market(self, _market, api_key=None, sign=None, update_handler=None, **kwargs):
        if api_key and sign:
            need_sign = True
        else:
            need_sign = False
        if _market == MarketClass.BITMEX:
            market = BitMexMarket(self._loop)
            self.market_manager.add_market(market)
        elif _market == MarketClass.OKEX:
            market = OKEXMarket(self._loop)
            self.market_manager.add_market(market)
        else:
            raise Exception("market not support!")

        if need_sign:
            market.login(api_key, sign)
        if update_handler:
            market.add_update_handler(update_handler)
        return market

    def register_on_update_handler(self, market: Market):
        self
