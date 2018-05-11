from abc import ABC, abstractmethod
import aiohttp

from MaxValue.utils.logger import logger
import asyncio
from MaxValue.utils.proxy import proxy
import json
import inspect
from enum import Enum


class Term(Enum):
    Long = "long"
    Short = "short"


class Trade(object):
    def __init__(self, api):
        self.tag = None
        self._api = api
        self.trade_type = None
        self._match_price = False
        self._price = None
        self._symbol = None
        self._amount = None
        self._contract_type = None
        self.term_type = None
        self._lever_rate = 1

    def start(self, trade_type, term_type):
        if trade_type == "buy" or trade_type == "sell":
            self.trade_type = trade_type
        else:
            raise Exception("错误!trade_type只能设置成buy或者sell")

        if isinstance(term_type, Term):
            self.term_type = trade_type
        elif isinstance(term_type, str):
            if term_type == "long":
                self.term_type = Term.Long
            elif term_type == "short":
                self.term_type = Term.Short
        return self

    def price(self, price):
        self._price = price
        return self

    def symbol(self, symbol):
        self._symbol = symbol
        return self

    def amount(self, amount):
        self._amount = amount
        return self

    def contract_type(self, contract_type):
        self._contract_type = contract_type
        return self

    def lever_rate(self, lever_rate):
        self._lever_rate = lever_rate
        return self

    def as_market_price(self):
        self._match_price = True
        return self

    @abstractmethod
    def check(self):
        pass

    async def go(self):
        self.check()
        if self.trade_type == "buy":
            return await self._buy()
        elif self.trade_type == "sell":
            return await self._sell()

    @abstractmethod
    async def _buy(self):
        return self

    @abstractmethod
    async def _sell(self):
        return self


class BaseOrder(object):
    def __init__(self, api):
        self.api = api
        self.order_id = None

    @abstractmethod
    def info(self):
        pass

    @abstractmethod
    def list(self):
        pass

    @abstractmethod
    def cancel(self):
        pass


class BasePosition(object):
    def __init__(self, api):
        self.api = api
        self.tag = None

    @abstractmethod
    def get(self):
        pass


class TradeAPI(ABC):
    def __init__(self):
        self.update_handler = None

    def add_update_handler(self, handler):
        if inspect.isfunction(handler):
            self.update_handler = handler()
        else:
            self.update_handler = handler

    @abstractmethod
    async def sub_channel(self):
        pass

    @abstractmethod
    def trade(self):
        pass

    @abstractmethod
    def order(self):
        pass

    @abstractmethod
    async def sell(self, symbol, term_type, amount, market_price=False, price=None, **kwargs):
        pass

    @abstractmethod
    async def buy(self, symbol, term_type, amount, market_price=False, price=None, **kwargs):
        pass

    @abstractmethod
    async def get_order_info(self, order_id, **kwargs):
        pass

    @abstractmethod
    async def get_order_list(self):
        pass


class WSAPI(object):
    def __init__(self):
        self.current_sub_channels = set()
        self.ping_pong_task = None
        self.session = None
        self._connect_status_flag = None
        self.update_handler = None

    async def create_session(self, auto_reconnect=True):
        logger.debug("连接websocket")
        client_session = aiohttp.ClientSession()
        try:
            ws = await client_session.ws_connect(self.base_url, proxy=proxy, timeout=10, autoping=True)
            self._connect_status_flag = 1
            self.session = ws
            self.ping_pong_task = self._loop.create_task(self.send_ping())
            while True:
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close cmd':
                        await ws.close()
                        break
                    else:
                        await self._msg_hander._on_message(json.loads(msg.data))
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.debug(msg.type)
                    self._connect_status_flag = 2
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.debug(msg.type)
                    self._connect_status_flag = 3
                    break
        except Exception as e:
            logger.warn(e)
        finally:
            logger.debug("退出后重试重试")
            if client_session and not client_session.closed:
                await client_session.close()
                self.session = None
            if auto_reconnect:
                await asyncio.sleep(10)
                await self.reconnect()

    async def reconnect(self):
        logger.debug("重新连接websocket")
        self.ping_pong_task.cancel()

        async def sub_all_channel():
            await asyncio.sleep(20)
            logger.debug("重新 加载已经定义的频道:{}".format(self.current_sub_channels))
            await self.sub_channels(*self.current_sub_channels)

        self._loop.create_task(self.create_session())
        self._loop.create_task(sub_all_channel())

    async def send_ping(self):
        while True:
            await asyncio.sleep(29)
            await self.session.send_str("{'event':'ping'}")
