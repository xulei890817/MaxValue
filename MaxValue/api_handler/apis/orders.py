from MaxValue.utils.proxy import proxy
from MaxValue.utils.logger import logger


class OrderManager(object):
    def __init__(self):
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)

    def get_order(self, index=0):
        return self.orders[index]

    def remove_order(self):
        pass


class PairOrder(object):
    def __init__(self):
        self.is_in_waiting = False
        self.is_waiting_for_buy = False
        self.is_waiting_for_sell = False
        self.buy_order = None
        self.sell_order = None
        self.buy_sell_order = None
        self.sell_buy_order = None

    def reset(self):
        self.is_in_waiting = False
        self.is_waiting_for_buy = False
        self.is_waiting_for_sell = False
        self.buy_order = None
        self.sell_order = None
        self.buy_sell_order = None
        self.sell_buy_order = None

    def set_buy_order(self, order):
        if self.is_waiting_for_buy and (not self.is_waiting_for_sell):
            logger.debug("set_buy_order")
            self.buy_order = order  # type Order
        elif self.is_waiting_for_sell:
            self.set_sell_buy_order(order)

    def replace_buy_order(self, order):
        self.buy_order = order

    def replace_sell_order(self, order):
        self.sell_order = order

    def replace_buy_sell_order(self, order):
        self.buy_sell_order = order

    def replace_sell_buy_order(self, order):
        self.sell_buy_order = order

    def set_buy_sell_order(self, order):
        logger.debug("set_buy_sell_order")
        self.buy_sell_order = order

    def set_sell_order(self, order):
        if self.is_waiting_for_buy and (not self.is_waiting_for_sell):
            logger.debug("set_sell_order")
            self.sell_order = order
        elif self.is_waiting_for_sell:
            self.set_buy_sell_order(order)

    def set_sell_buy_order(self, order):
        logger.debug("set_sell_buy_order")
        self.sell_buy_order = order


class PairsOrder(object):
    def __init__(self):
        self.is_in_waiting = False
        self.is_waiting_for_buy = False
        self.is_waiting_for_sell = False
        self.buy_flag = None
        self.sell_flag = None
        self.buy_orders = []
        self.sell_orders = []
        self.buy_sell_orders = []
        self.sell_buy_orders = []

    def reset(self):
        self.is_in_waiting = False
        self.is_waiting_for_buy = False
        self.is_waiting_for_sell = False
        self.buy_flag = None
        self.sell_flag = None
        self.buy_orders = []
        self.sell_orders = []
        self.buy_sell_orders = []
        self.sell_buy_orders = []

    def add_buy_order(self, order):
        if self.is_waiting_for_buy and (not self.is_waiting_for_sell):
            logger.debug("set_buy_order")
            self.buy_order = order  # type Order
        elif self.is_waiting_for_sell:
            self.set_sell_buy_order(order)

    def replace_buy_sell_order(self, order):
        self.buy_sell_order = order

    def replace_sell_buy_order(self, order):
        self.sell_buy_order = order

    def set_buy_sell_order(self, order):
        logger.debug("set_buy_sell_order")
        self.buy_sell_order = order

    def set_sell_order(self, order):
        if self.is_waiting_for_buy and (not self.is_waiting_for_sell):
            logger.debug("set_sell_order")
            self.sell_order = order
        elif self.is_waiting_for_sell:
            self.set_buy_sell_order(order)

    def set_sell_buy_order(self, order):
        logger.debug("set_sell_buy_order")
        self.sell_buy_order = order


class Order(object):
    def __init__(self):
        self.id = None
        self.host = None
        self.symbol = None
        self.result = None

    def set_type(self, type):
        self.type = type

    def set_amount(self, amount):
        self.amount = amount

    def set_price(self, price):
        self.price = price


order_manager = PairOrder()
