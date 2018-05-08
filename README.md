# MaxValue
treasure  in the  deep sea.find the light in dark.

# install

pip install git+https://github.com/xulei890817/MaxValue.git

#sample code
```python

#!/usr/bin/env python

# encoding: utf-8

'''
 * Create File plan_test
 * Created by leixu on 2018/5/7
'''
from MaxValue.market import MarketClass
from MaxValue.plan import BasePlan, UpdateHandler
import asyncio
import arrow


class OkexUpdateHandler(UpdateHandler):

    def ticker(self, data):
        pass

    def k_line(self, data):
        pass

    def depth(self, data):
        pass


class PlanA(BasePlan):
    def __init__(self, loop):
        super(PlanA, self).__init__(loop)
    
    #登录到市场
    def login_market(self):
        #数据采用被动更新方式，也可使用
        def okex_update_handler():
            def ticker(data):
                print(data)

            def k_line(data):
                print(data)

            def depth(data):
                print(data)

            setattr(okex_update_handler, "ticker", ticker)
            setattr(okex_update_handler, "k_line", k_line)
            setattr(okex_update_handler, "depth", depth)
            return okex_update_handler
        #两种方式都可以用
        #okex_update_handler = OkexUpdateHandler()
        self.okex_market = self.login_into_market(MarketClass.OKEX, api_key=None, sign=None, update_handler=okex_update_handler)
    
    #计划的主入口
    async def start_rule(self):
        # 订阅频道
        
        #具体的频道订阅方式，详细查看市场的api说明
        await self.okex_market.api.sub_channel("ok_sub_futureusd_btc_ticker_quarter")
        await self.okex_market.api.sub_channel("ok_sub_futureusd_btc_kline_this_week_1min")
        await self.okex_market.api.sub_channel("ok_sub_futureusd_btc_depth_this_week")

        # 保持程序运行
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    c_loop = asyncio.get_event_loop()
    # oo = OKEXWSTradeAPI(c_loop)
    # c_loop.create_task(oo.create_session())
    # asyncio.ensure_future(oo.sub_futureusd_X_ticker_Y(), loop=c_loop)

    plan_a = PlanA(c_loop)
    print("开始运行计划" + str(arrow.get()))
    asyncio.ensure_future(plan_a.start_rule(), loop=c_loop)

    c_loop.run_forever()
```

use proxy
```python
from MaxValue.utils.proxy import proxy
proxy = "http://proxy_ip:proxy_port"
```

以okex的接口调用为例 

https://github.com/okcoin-okex/API-docs-OKEx.com/tree/master/API-For-Futures-CN

买卖简介
```python
    # 下单 
    # 以看多的方式以市场价买入杠杆为10倍的1张 btc_usd的季度合约
    # start("sell","short") 看跌
    # 如需定价  trade.start("buy", "long").symbol("btc_usd").contract_type("quarter").amount(1).lever_rate(10).price(7300)
    # 由于市场问题，只能存在一个杠杆
    trade = self.okex_market.api.trade()
    trade.start("buy", "long").symbol("btc_usd").contract_type("quarter").amount(1).lever_rate(10).as_market_price()
    result = await trade.go()
    print(result.order_id)
    print(result)
    
    #print    {'result': True, 'order_id': 123123123123}
```

获取订单详情
```python
result = await self.okex_market.api.get_order_info(order_id=123123123123,symbol="btc_usd", contract_type="quarter")
print(result)

#print {'result': True, 'orders': [{'symbol': 'btc_usd', 'lever_rate': 10, 'amount': 1, 'fee': -5.31e-06, 'contract_name': 'BTC0629', 'unit_amount': 100, 'type': 1, 'price_avg': 9415.15, 'deal_amount': 1, 'price': 9415.16, 'create_date': 1525778802000, 'order_id': 123123123123, 'status': 2}]}
```

删除订单
```python
result = await self.okex_market.api.cancel_future(order_id=123123123123,symbol="btc_usd", contract_type="quarter")
print(result)

#print 
```



