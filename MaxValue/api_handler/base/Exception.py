class BitmexException(Exception):
    def __init__(self, msg):
        super(BitmexException, self).__init__(msg)
        self.msg = msg


class BitmexBaseException(BitmexException):
    def __init__(self, msg):
        super(BitmexBaseException, self).__init__(msg)
