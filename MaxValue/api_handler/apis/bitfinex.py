from MaxValue.api_handler.base import TradeAPI
import aiohttp
import json
import asyncio


class BITMEXWSTradeAPI(TradeAPI):

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
        self.current_sub_channels = set()

    def set_msg_handler(self, handler):
        self._msg_hander = handler

    async def create_session(self):
        client_session = aiohttp.ClientSession()
        try:
            async with client_session.ws_connect(self.base_url, proxy="http://192.168.2.24:1001") as ws:
                self._connect_status_flag = 1
                self.session = ws
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == 'close cmd':
                            await ws.close()
                            break
                        else:
                            await self._msg_hander._on_message(json.loads(msg.data))
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        self._connect_status_flag = 2
                        await self.reconnect()
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        self._connect_status_flag = 3
                        break
        except Exception as e:
            await asyncio.sleep(5)
            await self.create_session()



    async def reconnect(self):
        await self.create_session()
        for channel in self.current_sub_channels:
            self.sub_channel(channel)

    async def sub_channels(self, *channels):
        if self._connect_status_flag != 1:
            await asyncio.sleep(2)
            await self.sub_channels(*channels)
            return
        self.current_sub_channels.update(set(channels))
        for channel in channels:
            await self.session.send_str(
                '{{"event":"subscribe","channel":"{}"'.format(channel))

    def connect_type(self):
        return "ws"

    @property
    def base_url(self):
        return "wss://api.bitfinex.com/ws/2"

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value