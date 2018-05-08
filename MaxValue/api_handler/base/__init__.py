from abc import ABC, abstractmethod
import aiohttp

from MaxValue.utils.logger import logger
import asyncio
from MaxValue.utils.proxy import proxy
import json
import inspect


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
