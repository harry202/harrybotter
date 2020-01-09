

class StockModMock(object):
    def __init__(self):
        print("StockModMock initialized")
    def get_group_stock_price(self, groupname):
        if groupname == "test":
            return "test passed"
        else:
            return "no list"