#!/usr/bin/env python

# encoding: utf-8

'''
 * Create File market_collections
 * Created by leixu on 2018/5/7
 * IDE PyCharm
'''
from MaxValue.api_handler.apis.bitmex_api import BitMexAPI
from MaxValue.api_handler.apis.okex_api import OKEXAPI
from MaxValue.market import Market


class OKEXMarket(Market):

    def __init__(self, loop):
        super(OKEXMarket, self).__init__()
        self.tag = "okex"
        self.api = OKEXAPI(loop)

    def update_k_line(self, data):
        pass

    def update_ticker(self, data):
        pass

    def update_depth(self, data):
        pass

    def login(self, api_key, sign):
        self.api.login(api_key, sign)


class BitMexMarket(Market):
    def __init__(self, loop):
        super(BitMexMarket, self).__init__()
        self.tag = "bitmex"
        self.api = BitMexAPI(loop)

    def login(self, api_key, sign):
        self.api.api_key = api_key
        self.api.sign = sign

    def update_k_line(self, data):
        pass

    def update_ticker(self, data):
        pass

    def update_depth(self, data):
        pass
