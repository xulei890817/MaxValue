import bitmex
from bravado.exception import HTTPServerError, HTTPServiceUnavailable, HTTPBadRequest

from MaxValue.api_handler.apis.my_bitmex import BITMEXWSTradeAPI
from MaxValue.api_handler.base import TradeAPI, Trade, Term
import arrow
from MaxValue.api_handler.apis.orders import order_manager
from MaxValue.api_handler.apis.orders import Order
import json

from MaxValue.api_handler.base.Exception import BitmexBaseException
from MaxValue.utils.logger import logger
import functools
import asyncio
from RetryMe.retryme import error_retry, SLEEPRULE

result_check_flag = 0x13849948
max_try_time = 5


class EmptyResultError(BitmexBaseException):
    def __init__(self, msg):
        super(EmptyResultError, self).__init__()


class BitMexTrade(Trade):

    def check(self):
        if self._match_price:
            self._price = "0"
        elif not self._price:
            raise Exception("没有设置价格参数")

        if not self._symbol:
            raise Exception("没有设置symbol参数")

        if not self._amount:
            raise Exception("没有设置amount参数")

    """
       1:买涨 开多 2:卖跌  开空 3:卖涨  平多 4:买跌  平空
       """

    def gen_match_price(self):
        return "1" if self._match_price else "0"

    async def _buy(self):
        if self._match_price:
            return self._api.Order.Order_new(symbol=self._symbol, orderQty=self._amount).result()
        else:
            return self._api.Order.Order_new(symbol=self._symbol, orderQty=self._amount, price=self._price).result()

    async def _sell(self):
        if self._match_price:
            return self._api.Order.Order_new(symbol=self._symbol, orderQty=self._amount).result()
        else:
            return self._api.Order.Order_new(symbol=self._symbol, orderQty=self._amount, price=self._price).result()


class BitMexAPI(TradeAPI):

    def __init__(self, loop):
        super(BitMexAPI, self).__init__()
        self.api_key = None
        self.sign = None
        self.loop = loop
        self.market_refresh_handler = None
        self.rest_api = bitmex.bitmex(test=False, api_key=self.api_key, api_secret=self.sign)
        self.ws_api = BITMEXWSTradeAPI(loop)
        self.ws_api.set_msg_handler(self)
        self.market_info = {"quote": {}, "quote_new_flag": False}
        loop.create_task(self.create_session())

    async def set_fresh_market_info_handler(self, handler):
        self.market_refresh_handler = handler

    async def create_session(self):
        await self.ws_api.create_session()

    async def sub_info(self):
        logger.info("订阅频道")
        # await self.wsapi.sub_channels("instrument", "quote")
        await self.ws_api.sub_channels("quote")

    async def _on_message(self, msg):
        async def trade(data_item):
            pass
            # logger.debug("####111" + str(data_item))

        async def quote(data_item):
            for i in data_item["data"]:
                if i["symbol"] == "XBTUSD":
                    self.market_info["quote"].update({"XBTUSD": i})
                    self.market_info.update({"quote_new_flag": True})
                if i["symbol"] == "XBTM18":
                    self.market_info["quote"].update({"XBTM18": i})
                    self.market_info.update({"quote_new_flag": True})
            self.market_refresh_handler(self.market_info)

        async def orderBook10(data_item):
            for i in data_item["data"]:
                if i["symbol"] == "XBTUSD":
                    self.market_info.update({
                        "XBTUSD": {
                            "time": arrow.get(),
                            "top_sell": i["bids"],
                            "top_buy": i["asks"]

                        }
                    })
                elif i["symbol"] == "XBTM18":
                    self.market_info.update({
                        "XBTM18": {
                            "time": arrow.get(),
                            "top_sell": i["bids"],
                            "top_buy": i["asks"]
                        }
                    })

        async def order(data_item):
            logger.debug(data_item)

        async def instrument(data_item):
            for i in data_item["data"]:
                if i["symbol"] == "XBTUSD":
                    self.market_info.update({
                        "base_info": i
                    })

        if "info" in msg and "version" in msg:
            return
        if "table" in msg:
            try:
                await eval(f'{msg["table"]}(msg)')
            except Exception as e:
                logger.warn(e)

    def get_market_info(self):
        return self.market_info

    async def login(self):
        pass

    @error_retry(exceptions=[HTTPServiceUnavailable], retry_times=5, sleep_seconds=0.2)
    async def buy(self, price, symbol, amount):
        result = self.rest_api.Order.Order_new(symbol=symbol, orderQty=amount, price=price).result()
        logger.debug(result)
        if result[0]:
            order = Order()
            order.id = result[0]["orderID"]
            order.symbol = symbol
            order.host = 'bitmex'
            order.result = result[0]
            order_manager.set_buy_order(order)
            return order
        else:
            return None

    @error_retry(exceptions=[HTTPServiceUnavailable], retry_times=5, sleep_seconds=0.2)
    async def sell(self, price, symbol, amount):
        if amount > 0:
            amount = -amount
        result = self.rest_api.Order.Order_new(symbol=symbol, orderQty=amount, price=price).result()
        logger.debug(result)
        if result[0]:
            order = Order()
            order.id = result[0]["orderID"]
            order.symbol = symbol
            order.host = 'bitmex'
            order.result = result[0]
            order_manager.set_sell_order(order)
            return order
        else:
            return None

    async def sell_market_price(self, symbol='XBTM18', amount=100):
        if amount > 0:
            amount = -amount
        result = self.rest_api.Order.Order_new(symbol=symbol, orderQty=amount).result()
        logger.debug(result)
        return None

    async def buy_market_price(self, symbol='XBTM18', amount=100):
        result = self.rest_api.Order.Order_new(symbol=symbol, orderQty=amount).result()
        logger.debug(result)
        return None

    @error_retry(exceptions=[HTTPServiceUnavailable], retry_times=10, sleep_seconds=1)
    async def get_orderBook(self, symbol, depth):
        result = self.rest_api.OrderBook.OrderBook_getL2(symbol=symbol, depth=depth).result()
        return result[0]

    async def get_trade_info(self, symbol='XBTM18'):
        result = self.rest_api.Order.Order_getOrders(symbol=symbol).result()
        logger.debug(result[0])
        return result[0]

    async def get_all_my_new_orders(self, symbol='XBTM18'):
        result = self.rest_api.Order.Order_getOrders(filter=json.dumps({'symbol': symbol, 'ordStatus': 'New'})).result()
        logger.debug(result[0])
        return result[0]

    @error_retry(exceptions=[HTTPServiceUnavailable, EmptyResultError], retry_times=3, sleep_seconds=0.2)
    async def get_order_info(self, order_id=None):
        result = self.rest_api.Order.Order_getOrders(filter=json.dumps({'orderID': order_id})).result()
        logger.debug(result[0])
        if result[0]:
            return result[0][0]
        else:
            raise EmptyResultError("Empty Result")

    @error_retry(exceptions=[HTTPServiceUnavailable], retry_times=10, sleep_seconds=1, sleep_rule=SLEEPRULE.INCREASE, sleep_rule_args={"step": 1})
    async def cancel_future(self, order_id):
        result = self.rest_api.Order.Order_cancel(orderID=order_id).result()
        logger.debug(result[0])
        return result[0]

    @error_retry(exceptions=[HTTPServiceUnavailable], retry_times=5, sleep_seconds=0.2)
    async def update_order(self, order_id, price):
        try:
            result = self.rest_api.Order.Order_amend(orderID=order_id, price=price).result()
            logger.debug(result[0])
            return result[0]
        except Exception as e:
            if isinstance(e, HTTPBadRequest):
                pass
            else:
                raise e

    async def test_get(self, symbol='XBTM18'):
        result = self.rest_api.Instrument.Instrument_get(symbol=symbol).result()
        logger.debug(result[0])

    async def get_all_my_positions(self, symbol='XBTM18'):
        result = self.rest_api.Position.Position_get(filter=json.dumps({'symbol': symbol})).result()
        logger.debug(result[0])

    async def get_all_my_trades(self, symbol='XBTM18'):
        result = self.rest_api.Trade.Trade_get(filter=json.dumps({'symbol': symbol})).result()
        logger.debug(result)


import csv


class BitMexAPI2(BitMexAPI):
    def __init__(self, loop):
        super(BitMexAPI2, self).__init__(loop)
        fieldnames = ['timestamp', 'symbol', 'bidSize', 'bidPrice', 'askPrice', 'askSize']
        self.file1 = open("bitmex_quote.csv", "w", newline='')
        self.csv_writer = csv.DictWriter(self.file1, fieldnames=fieldnames)
        self.csv_writer.writeheader()

        self.file2 = open("bitmex_instrument.txt", "w", newline='')

    async def _on_message(self, msg):
        async def trade(data_item):
            pass
            # logger.debug("####111" + str(data_item))

        async def quote(data_item):
            for i in data_item["data"]:
                self.csv_writer.writerow(i)
            self.file1.flush()

        async def orderBook10(data_item):
            for i in data_item["data"]:
                if i["symbol"] == "XBTUSD":
                    self.market_info.update({
                        "XBTUSD": {
                            "time": arrow.get(),
                            "top_sell": i["bids"],
                            "top_buy": i["asks"]

                        }
                    })
                elif i["symbol"] == "XBTM18":
                    self.market_info.update({
                        "XBTM18": {
                            "time": arrow.get(),
                            "top_sell": i["bids"],
                            "top_buy": i["asks"]
                        }
                    })

        async def order(data_item):
            logger.debug(data_item)

        async def instrument(data_item):
            self.file2.write(json.dumps(data_item, ensure_ascii=True))
            self.file2.write("\r\n")
            self.file2.flush()

        if "info" in msg and "version" in msg:
            return
        if "table" in msg:
            try:
                await eval(f'{msg["table"]}(msg)')
            except Exception as e:
                logger.warn(e)


if __name__ == "__main__":
    import asyncio

    c_loop = asyncio.get_event_loop()
    # oo = OKEXWSTradeAPI(c_loop)
    # c_loop.create_task(oo.create_session())
    # asyncio.ensure_future(oo.sub_futureusd_X_ticker_Y(), loop=c_loop)

    plan_a = BitMexAPI(c_loop)


    # async def do():
    #     await asyncio.sleep(3)
    #     await plan_a.sub_info()
    async def do():
        order = await plan_a.buy(symbol="XBTM18", price=8690, amount=1)
        await plan_a.update_order(order_id=order.id, price=8558)


    # asyncio.ensure_future(plan_a.buy(price=6309, amount=1), loop=c_loop)
    # asyncio.ensure_future(plan_a.sell(price=6312, amount=1), loop=c_loop)
    asyncio.ensure_future(do(), loop=c_loop)

    c_loop.run_forever()
