from MaxValue.api_handler.base import TradeAPI, WSAPI
import aiohttp
import json
import asyncio
from MaxValue.utils.proxy import proxy
from MaxValue.utils.logger import logger


class BITMEXWSTradeAPI(WSAPI):
    def __init__(self, loop):
        """
        _connect_status_flag ：代表连接的状态
        0:未连接
        1:成功连接
        2:断开连接
        3
        :param loop:
        """
        super().__init__()
        self._session = None
        self._connect_status_flag = 0
        self._loop = loop
        super(BITMEXWSTradeAPI, self).__init__()

    def set_msg_handler(self, handler):
        self._msg_hander = handler

    async def sub_channels(self, *channels):
        if self._connect_status_flag != 1:
            await asyncio.sleep(2)
            await self.sub_channels(*channels)
            return
        self.current_sub_channels.update(set(channels))
        for channel in channels:
            logger.debug("{{'op':'subscribe','args':['{0}']}}".format(channel))
            await self.session.send_str(
                '{{"op":"subscribe","args":["{0}"]}}'.format(channel))

    async def send_str(self, str):
        await self.session.send_str(
            '{{"op":"subscribe","args":["{0}"]}}'.format(str))

    def connect_type(self):
        return "ws"

    @property
    def base_url(self):
        return "wss://www.bitmex.com/realtime"

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value
