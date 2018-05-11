from asyncio import AbstractEventLoop

from MaxValue.api_handler.apis.okex import OKEXRESTTradeAPI, OKEXWSTradeAPI
from MaxValue.api_handler.base import TradeAPI, Trade, Term, BaseOrder, BasePosition
import arrow

from MaxValue.api_handler.apis.orders import order_manager
from MaxValue.api_handler.apis.orders import Order
import asyncio
from MaxValue.utils.logger import logger
import traceback


class BuyError(Exception):
    pass


class SellError(Exception):
    pass


class OKEXTrade(Trade):

    def check(self):
        if self._match_price:
            self._price = "0"
        elif not self._price:
            raise Exception("没有设置价格参数")

        if not self._symbol:
            raise Exception("没有设置symbol参数")

        if not self._amount:
            raise Exception("没有设置amount参数")

        if not self._contract_type:
            raise Exception("没有设置contract_type参数")

    """
       1:买涨 开多 2:卖跌  开空 3:卖涨  平多 4:买跌  平空
       """

    def gen_match_price(self):
        return "1" if self._match_price else "0"

    async def _buy(self):
        if self.term_type == Term.Long:
            return await self._api.future_trade(symbol=self._symbol, contract_type=self._contract_type, price=self._price, amount=self._amount, type="1", match_price=self.gen_match_price(),
                                                lever_rate=str(self._lever_rate))
        else:
            return await self._api.future_trade(symbol=self._symbol, contract_type=self._contract_type, price=self._price, amount=self._amount, type="4", match_price=self.gen_match_price(),
                                                lever_rate=str(self._lever_rate))

    async def _sell(self):
        if self.term_type == Term.Long:
            return await self._api.future_trade(symbol=self._symbol, contract_type=self._contract_type, price=self._price, amount=self._amount, type="3", match_price=self.gen_match_price(),
                                                lever_rate=str(self._lever_rate))
        else:
            return await self._api.future_trade(symbol=self._symbol, contract_type=self._contract_type, price=self._price, amount=self._amount, type="2", match_price=self.gen_match_price(),
                                                lever_rate=str(self._lever_rate))


class OKEXOrder(BaseOrder):

    def __init__(self, api, **kwargs):
        super(OKEXOrder, self).__init__(api)
        self.tag = "okex交易"
        self.symbol = None
        self.contract_type = None

    def add_args(self, **kwargs):
        self.order_id = kwargs["order_id"]
        self.symbol = kwargs["symbol"]
        self.contract_type = kwargs["contract_type"]
        return self

    def check(self):
        if not self.symbol or not self.contract_type:
            raise Exception("okex需要设置symbol,contract_type两个变量先")

    async def info(self):
        self.check()
        result = await self.api.future_order_info(symbol=self.symbol, contract_type=self.contract_type, order_id=self.order_id)
        logger.debug(result)
        return result

    async def list(self, **filter):
        """
        okex的这个api需要传入
        filter = {"order_ids"=[123,321],"symbol":"btc_usd","contract_type":"quarter"}
        :param filter:
        :return:
        """
        order_ids = filter["order_ids"]
        symbol = filter["symbol"]
        contract_type = filter["contract_type"]
        self.check()
        result = await self.api.future_orders_info(symbol=symbol, contract_type=contract_type, order_id=",".join(order_ids))
        logger.debug(result)
        return result

    async def cancel(self):
        self.check()
        result = await self.api.future_cancel(order_id=self.order_id, symbol=self.symbol, contract_type=self.contract_type)
        logger.debug(result)
        return result


class OKEXPostition(BasePosition):
    def __init__(self, api):
        self.api = api
        self.tag = "okex全仓"

    async def get(self, symbol, contract_type):
        result = await self.api.future_position(symbol=symbol, contract_type=contract_type)
        logger.debug(result)
        return result


class OKEXFixPostition(BasePosition):
    def __init__(self, api):
        self.tag = "okex逐仓"
        self.api = api

    async def get(self, symbol, contract_type):
        result = await self.api.future_position_4fix(symbol=symbol, contract_type=contract_type)
        logger.debug(result)
        return result


class OKEXAPI(TradeAPI):
    market_info = {}

    def __init__(self, loop: AbstractEventLoop):
        super(OKEXAPI, self).__init__()
        self.loop = loop
        self.rest_api = OKEXRESTTradeAPI(loop)
        self.ws_api = OKEXWSTradeAPI(loop)
        self.ws_api.set_msg_handler(self)
        loop.create_task(self.create_session())

    async def create_session(self):
        await self.rest_api.create_session()
        await self.ws_api.create_session()

    async def sub_info(self):
        # 订阅市场消息
        # ok_sub_futureusd_X_ticker_Y 订阅合约行情
        # ok_sub_futureusd_X_trade_Y 订阅合约交易信息
        logger.info("订阅市场消息")
        await self.ws_api.sub_channels("ok_sub_futureusd_btc_ticker_quarter")

    async def sub_channel(self, channel):
        await self.ws_api.sub_channels(channel)

    async def login_and_sub_trades(self):
        await self.ws_api.send_str("login", {
            "api_key": self.api_key,
            "sign": self.secret_key
        })
        while True:
            if self.ws_api.is_auth:
                self.ws_api.sub_auth_channel()

    async def _on_message(self, msg):
        if msg == {"event": "pong"}:
            logger.info("get pong from okexserver")
        else:
            for data_item in msg:
                try:
                    if "ticker" in data_item["channel"]:
                        getattr(self.update_handler, "ticker")(data_item)
                    elif "kline" in data_item["channel"]:
                        getattr(self.update_handler, "k_line")(data_item)
                    elif "depth" in data_item["channel"]:
                        getattr(self.update_handler, "depth")(data_item)
                    elif "addChannel" == data_item["channel"]:
                        logger.info(f"频道{data_item['data']['channel']}订阅成功")
                except Exception as e:
                    logger.warn(e)

    def trade(self):
        return OKEXTrade(self.rest_api)

    def order(self, order_id, symbol, contract_type):
        return OKEXOrder(self.rest_api).add_args(order_id=order_id, symbol=symbol, contract_type=contract_type)

    def position(self):
        return OKEXPostition(self.rest_api)

    def fixposition(self):
        return OKEXFixPostition(self.rest_api)

    def get_market_info(self):
        return self.market_info

    def login(self, api_key, secret_key):
        self.rest_api.set_auth(api_key, secret_key)
        self.ws_api.api_key = api_key
        self.ws_api.secret_key = secret_key

    """
      1:买涨 开多 2:卖跌  开空 3:卖涨  平多 4:买跌  平空
      """

    async def buy(self, price, amount, type=1, match_price="0"):
        try:
            result = await self.rest_api.future_trade(symbol="btc_usd", contract_type="quarter",
                                                      price=str(price), amount=str(amount), type=str(type),
                                                      match_price=match_price,
                                                      lever_rate="10")
            logger.debug(result)
            if result["result"]:
                order = Order()
                order.id = result["order_id"]
                order.type = type
                order.amount = amount
                order.price = price
                order.host = 'okex'
                order_manager.set_buy_order(order)
        except Exception as e:
            traceback.print_exc()
            logger.warn(e)

    def person_trade_info(self):
        pass

    async def sell(self, price, amount, type=2, match_price="0"):
        try:
            result = await self.rest_api.future_trade(symbol="btc_usd", contract_type="quarter",
                                                      price=str(price), amount=str(amount), type=str(type),
                                                      match_price=match_price,
                                                      lever_rate="10")
            logger.debug(result)
            if result["result"]:
                order = Order()
                order.id = result["order_id"]
                order.host = 'okex'
                order.type = type
                order.amount = amount
                order.price = price
                order_manager.set_sell_order(order)
        except Exception as e:
            traceback.print_exc()
            logger.warn(e)

    async def get_position(self):
        result = await self.rest_api.future_position_4fix(symbol="btc_usd", contract_type="quarter")
        logger.debug(result)

    async def get_userinfo(self):
        result = await self.rest_api.future_userinfo_4fix()
        logger.debug(result)
        return result

    async def get_future_ticker(self):
        result = await self.rest_api.future_ticker(symbol="btc_usd", contract_type="quarter")
        logger.debug(result)
        return result

    async def get_trades_history(self):
        result = await self.rest_api.future_trades_history(symbol="btc_usd", date="2018-06-29", since=111111111111)
        logger.debug(result)
        return result

    async def get_order_info_by_status(self, status="2"):
        result = await self.rest_api.future_order_info(symbol="btc_usd", contract_type="quarter", order_id="-1",
                                                       status=status, current_page="1", page_length="50")
        logger.debug(result)
        return result

    async def cancel_future(self, order_id, symbol, contract_type):
        result = await self.rest_api.future_cancel(order_id=order_id, symbol=symbol, contract_type=contract_type)
        logger.debug(result)
        return result

    async def get_order_info_by_id(self, order_id):
        result = await self.rest_api.future_order_info(symbol="btc_usd", contract_type="quarter", order_id=order_id)
        logger.debug(result)
        return result["orders"][0]

    async def get_order_info(self, symbol, contract_type, order_id):
        result = await self.rest_api.future_order_info(symbol=symbol, contract_type=contract_type, order_id=order_id)
        logger.debug(result)
        return result

    async def get_order_list(self):
        pass


import csv


class OKEXAPI2(OKEXAPI):
    def __init__(self, loop):
        super(OKEXAPI2, self).__init__(loop)
        fieldnames = ['timestamp', 'high', 'limitLow', 'vol', 'last', 'low', 'buy', 'hold_amount', 'sell', 'contractId',
                      'unitAmount', 'limitHigh']
        self.file1 = open("okex.csv", "w", newline='')
        self.csv_writer = csv.DictWriter(self.file1, fieldnames=fieldnames)
        self.csv_writer.writeheader()

        self.file2 = open('okex_kline.csv', 'w')
        self.k_line_csv_writer = csv.writer(self.file2)
        self.k_line_csv_writer.writerow(["时间", "开盘价", "最高价", "最低价", "收盘价", "成交量(张)", "成交量(币)"])

    async def _on_message(self, msg):
        async def ok_sub_futureusd_btc_ticker_quarter(data_item):
            data_row = {"timestamp": arrow.get().float_timestamp}
            data_row.update(data_item["data"])
            self.csv_writer.writerow(data_row)  #:type csv
            self.file1.flush()

        async def ok_sub_futureusd_btc_kline_quarter_1min(data_item):
            for i in data_item["data"]:
                self.k_line_csv_writer.writerow(i)
            self.file2.flush()

        async def addChannel(data_item):
            logger.debug(f"频道{data_item['data']['channel']}订阅成功")

        async def pong():
            logger.debug("获取到服务器的pong回复")

        if msg == {"event": "pong"}:
            await pong()
        else:
            for data_item in msg:
                try:
                    await eval(f'{data_item["channel"]}(data_item)')
                except Exception as e:
                    logger.warn(e)


if __name__ == "__main__":
    c_loop = asyncio.get_event_loop()
    a = OKEXAPI2(c_loop)


    async def do():
        await asyncio.sleep(3)
        await a.sub_info()
        await a.sub_channel("ok_sub_futureusd_btc_kline_quarter_1min")
        # print(await a.get_position())
        # print(await a.get_order_info_by_status(status=1))
        # await a.sell(amount=1, type=2, price=6600)
        # await a.buy(amount=1, type=4, price=6590)
        # result = await a.get_future_ticker()
        # result = await a.get_future_ticker()
        # await a.get_userinfo()
        # for i in range(10):
        #     await asyncio.sleep(0.3)
        #     await a.get_position()
        #     await a.get_trades_history()
        #     await a.get_orders_info()


    asyncio.ensure_future(do(), loop=c_loop)
    c_loop.run_forever()
