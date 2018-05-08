from asyncio import AbstractEventLoop

from MaxValue.api_handler.base import TradeAPI, WSAPI
from functools import wraps
import aiohttp
import async_timeout
import asyncio
from copy import deepcopy
import json
from MaxValue.utils.proxy import proxy
from MaxValue.utils.logger import logger


def check(*args, **kwargs):
    def decorator(f):
        @wraps(f)
        def warp(*args, **kwargs):
            return f(*args, **kwargs)

        return warp

    return decorator


class OKEXRESTTradeAPI(object):
    def __init__(self, loop):
        self.api_key = None
        self.secret_key = None
        self.loop = loop
        self.proxy = proxy
        self.base_payload = None
        self.base_payload = {
            "api_key": self.api_key
        }

    def set_auth(self, api_key, sign):
        self.api_key = api_key
        self.sign = sign
        self.base_payload = {
            "api_key": self.api_key
        }

    async def create_session(self):
        headers = {"content-type": "application/x-www-form-urlencoded"}
        self.session = aiohttp.ClientSession(headers=headers);

    async def future_devolve(self, **kwargs):
        return await self._execute_request('future_devolve', 'post', kwargs)

    async def future_position_4fix(self, **kwargs):
        return await self._execute_request('future_position_4fix', 'post', kwargs)

    async def future_userinfo_4fix(self, **kwargs):
        return await self._execute_request('future_userinfo_4fix', 'post', kwargs)

    async def future_order_info(self, **kwargs):
        return await self._execute_request('future_order_info', 'post', kwargs)

    async def future_cancel(self, **kwargs):
        return await self._execute_request('future_cancel', 'post', kwargs)

    async def future_orders_info(self, **kwargs):
        return await self._execute_request('future_orders_info', 'post', kwargs)

    async def future_trades_history(self, **kwargs):
        return await self._execute_request('future_trades_history', 'post', kwargs)

    async def future_batch_trade(self, **kwargs):
        return await self._execute_request('future_batch_trade', 'post', kwargs)

    async def future_trade(self, **kwargs):
        return await self._execute_request('future_trade', 'post', kwargs)

    async def future_ticker(self, **kwargs):
        return await self._execute_request('future_ticker', 'get', kwargs)

    async def exchange_rate(self, **kwargs):
        return await self._execute_request('exchange_rate', 'get', kwargs)

    async def future_estimated_price(self, **kwargs):
        return await self._execute_request('future_estimated_price', 'get', kwargs)

    async def future_hold_amount(self, **kwargs):
        return await self._execute_request('future_hold_amount', 'get', kwargs)

    async def future_price_limit(self, **kwargs):
        return await self._execute_request('future_price_limit', 'get', kwargs)

    async def future_estimated_price(self, **kwargs):
        return await self._execute_request('future_estimated_price', 'get', kwargs)

    async def future_depth(self, **kwargs):
        return await self._execute_request('future_depth', 'get', kwargs)

    async def future_trades(self, **kwargs):
        return await self._execute_request('future_trades', 'get', kwargs)

    async def future_index(self, **kwargs):
        return await self._execute_request('future_index', 'get', kwargs)

    async def future_userinfo(self, **kwargs):
        return await self._execute_request('future_userinfo', 'post', kwargs)

    async def future_position(self, **kwargs):
        return await self._execute_request('future_position', 'post', kwargs)

    async def _execute_request(self, method, request_type, kwargs):
        try:
            if request_type == "post":
                payload = self.base_payload.copy()
                payload.update(kwargs)
                from MaxValue.utils.sign import okex_build_sign
                payload.update({"sign": okex_build_sign(self.secret_key, payload)})
                logger.debug(payload)
                async with self.session.post(f"{self.base_url}/{method}.do",
                                             proxy=self.proxy, data=payload, timeout=10) as resp:
                    return await resp.json()
            else:
                payload = {}
                payload.update(kwargs)
                logger.debug(payload)
                async with self.session.get(f"{self.base_url}/{method}.do",
                                            proxy=self.proxy, params=payload, timeout=10) as resp:
                    return await resp.json()
        except Exception as e:
            print(e)

    def connect_type(self):
        return "rest"

    @property
    def base_url(self):
        return "https://www.okex.com/api/v1"

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value


class RestMessageHandler(object):
    def __init__(self):
        pass


class AuthError(Exception):
    def __str__(self):
        return repr("没有权限")


class OKEXWSTradeAPI(WSAPI):
    def __init__(self, loop: AbstractEventLoop):
        """
        _connect_status_flag ：代表连接的状态
        0:未连接
        1:成功连接
        2:断开连接
        3
        :param loop:
        """
        super().__init__()
        self.api_key = None
        self.secret_key = None
        self.sign = ""
        self._session = None
        self._connect_status_flag = 0
        self._loop = loop
        self.current_sub_channels = set()
        self.is_auth = False

    def set_msg_handler(self, handler):
        self._msg_hander = handler

    async def sub_channels(self, *channels):
        if self._connect_status_flag != 1:
            await asyncio.sleep(2)
            await self.sub_channels(*channels)
            return
        self.current_sub_channels.update(set(channels))
        for channel in channels:
            await self.session.send_str(
                "{{'event':'addChannel','channel':'{0}'}}".format(channel))

    async def sub_auth_channel(self, channel, **param):
        if not self.is_auth:
            raise AuthError
        else:
            from MaxValue.utils.sign import okex_build_sign
            json.dumps(okex_build_sign)
            await self.session.send_str(
                "{{'event':'addChannel','channel':'{0}','parameters':}}".format(channel))

    async def send_str(self, event, params):
        await self.session.send_str(
            '{{"event":"{0}","parameters":{1}}}'.format(event, params))

    def connect_type(self):
        return "ws"

    @property
    def base_url(self):
        return "wss://real.okex.com:10440/websocket/okexapi"

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value


class MessageSwitcher(object):
    def __init__(self, handler):
        self.handler = handler

    def load(self, json=None, str=None):
        if json:
            self._switch_json_message(json)

    def _switch_json_message(self, data=None):
        self.handler


class RestMessageHandler(object):
    pass


class WSMessageHandler(object):
    def __init__(self):
        channels = {
            "ok_sub_futureusd_trades": self.ok_sub_futureusd_trades
        }

    def ok_sub_futureusd_trades(self, data):
        pass
