#!/usr/bin/env python

# encoding: utf-8

'''
 * Create File __init__.py
 * Created by leixu on 2018/5/5
 * IDE PyCharm
'''
from enum import Enum
from abc import abstractmethod

from MaxValue.api_handler.base import TradeAPI


class MarketClass(Enum):
    OKEX = 1
    BITMEX = 2


class MarketManager(object):
    def __init__(self):
        self._market_list = []
        pass

    def _check_market_existed(self):
        pass

    def get_market(self):
        return self._market_list

    def add_market(self, market):
        self._market_list.append(market)


class Market(object):
    def __init__(self):
        self.tag = None
        self.api: TradeAPI = None

    def add_update_handler(self, handler):
        self.api.add_update_handler(handler)

    @abstractmethod
    def login(self, api_key, sign):
        pass

    @abstractmethod
    def update_ticker(self, data):
        pass

    @abstractmethod
    def update_k_line(self, data):
        pass

    @abstractmethod
    def update_ticker(self, data):
        pass

    @abstractmethod
    def update_depth(self, data):
        pass
