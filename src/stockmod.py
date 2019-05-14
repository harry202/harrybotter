import tushare as ts
from pytdx.hq import TdxHq_API
import random
import time
import pprint
from robotutils import oplogs
import pandas as pd
import os

blacklist = ['300292', '002761', '603777', '002656', '002316', '300526', '300442', '300310', '300344', '600682', '002418', '300050', '600175', 
            '600751', '002740', '300608', '300299', '002759', '600260', '600804', '002359', '300362', '600355', '300264', '300056', '300459', '002252', 
            '300221', '300166', '300364','300143', '603990', '300578', '603568', '600242', '002357', '000922', '300004', '603169', '300688', '300392', 
            '002377', '600249', '600207', '002715', '600983', '300148', '002231', '300277', '300297', '002373', '002226', '600649', '002434', '000732', 
            '002766', '000606', '300086', '600771', '300664', '603355', '002622', '002602', '600703', '600575', '002813', '600146', '300137', '300134', 
            '300182', '300399', '000593', '603727', '600880', '600666', '600614', '600594', '600593', '600485', '600069', '300426', '300216', '002872', 
            '002667', '002625', '002573', '002382', '000711', '000519', '300598', '600645', '603718', '300663', '601777', '002585', '300027', '002694', 
            '000782', '603838', '002437', '600177', '002735', '000506', '600080', '300008', '603988', '600100', '600300', '300080', '002426', '002072', 
            '300647', '600487', '600525', '600157', '002131', '603987', '600601', '300682', '603518', '300432', '002619', '600155', '000526', '002486', 
            '000545', '300413', '002524', '601717', '002278', '002657', '600745', '002647', '002431', '300117', '300702', '600418', '600397', '002763', 
            '002312', '300296', '002413', '600710', '603030', '603056', '600744', '000018', '600112', '002848', '000039', '002010', '300071', '002721', 
            '002491', '600381', '600887', '300592', '000802', '601519', '002366', '300215', '600076', '603598', '601919', '300518', '600576', '300077', 
            '002473', '002162', '600598', '300345', '002519', '601311', '000662', '600812', '300431', '002576', '600532', '002617', '300312', '000793', 
            '600405', '603016', '002356', '600079', '002574', '600358', '002490', '002180', '600281', '000408', '000898', '002693', '002292', '000056', 
            '601808', '600267', '000040', '603555', '000518', '000933', '600754', '000835', '603955', '600250', '603080', '300055', '300601', '000587', 
            '300676', '300111', '002765', '300269', '000036', '000042', '600566', '600256', '002337', '600010', '600011', '603001', '300072', '002342', 
            '002112', '000659', '600121', '002584', '002384', '002665', '600898', '000591', '002343', '000540', '000413', '600393', '000534', '300076', '002568', 
            '300116', '002420', '300132', '601012', '300332', '300256', '601258', '600371', '600695', '603711', '002502', '000504', '002650', '000980', '002571', 
            '600699', '002239', '002751', '300069', '002291', '300268', '600721', '603032', '000691', '000636', '603603', '002005', '000889', '002769', '000976', 
            '000790', '600313', '000611', '300267', '600518', '600165', '002684', '600129', '002464', '603389', '002045', '600290', '002575', '600240', '002041', 
            '002164', '603377', '600139', '002021', '300234', '002071', '002069', '002442', '600136', '600319', '002501', '300225', '002011', '600896', '002509', 
            '002219', '600759', '000760', '300255', '300106', '000622', '000567', '300043', '000673', '300138', '000792', '002354', '002739', '002862', '002118', 
            '000576', '002044', '600226', '300266', '002840', '000798', '002708', '300156', '002700', '600777', '002002', '600235', '600225', '600868', '002512', 
            '603168', '002569', '600094','300313', '300238', '000981', '300090']

# 杭州电信服务器
HZ_HOST_IPS = ["60.191.117.167", "115.238.56.198", "218.75.126.9", "115.238.90.165"]
class StockMod(object):    
    def __init__(self,debug=False):
        # 初始化tdx
        self.debug = debug
        oplogs("Loading stock mod...")
        self.api = TdxHq_API(heartbeat=(not debug),auto_retry=True)
        self.connect_to_tdx()
        self.load_stocklist()
        self.monitor_queue = dict()
    def __del__(self):
        oplogs("Unloading stock mod...")
        self.api.disconnect()
        #self.stop_jobs()
    def connect_to_tdx(self):
        random.shuffle(HZ_HOST_IPS)
        for ip in HZ_HOST_IPS:
            if self.api.connect(ip, 7709):
                oplogs("Connected to %s success" %ip)    
                return            
            else:
                oplogs("Connected to %s failed!!" %ip)
    def load_stocklist(self):
        
        try:
            oplogs("get_stock_basics() ...")        
            self.stocklist = ts.get_stock_basics()
            oplogs("get_stock_basics() load from remote success")
        except:
            # 如果加载远程股票列表失败, 从本地列表读取
            oplogs("get_stock_basics() timeout, use local cached file instead")
            cur_path=os.path.dirname(os.path.realpath(__file__)) 
            stocklist_path=os.path.join(cur_path,'all.csv')
            df = pd.read_csv(stocklist_path, dtype={'code':'object'},encoding='GBK')
            df = df.set_index('code')
            self.stocklist = df
        
        # remove space in stock name
        self.stocklist['name'] = self.stocklist['name'].replace(' ','')

        # create dict and list to shorten search time
        self.stockdict = self.stocklist.to_dict()["name"]        
        self.stockrdict = {value:key for key,value in self.stockdict.items()}
        self.stockcode = self.stocklist.index.to_list()
        self.stockname = self.stocklist.name.to_list()

    def get_market(self, code):
        # 计算市场代码,1=sh, 0=sz
        market = 0
        if code[0] == '6':
            market = 1
        return market
        
    def get_stock_price(self, code):
        if code not in self.stockcode:
            return ""
        market = self.get_market(code)
        oplogs("get_stock_price called,code=%s,market=%s" %(code,market))        
        
        price = self.api.get_security_quotes([(market,code)])
        
        last_close = price[0]['last_close']
        current_price = price[0]['price']
        if last_close >0:
            change = (current_price/last_close - 1)*100
        else:
            change = 0
        
        result = "[%s]%.2f 涨幅:%.2f%%" %(self.stockdict[code],current_price,change )
        
        return result
    def get_stock_price_by_name(self, stockname):
        if stockname in self.stockname:
            return self.get_stock_price(self.stockrdict[stockname])
        
        return ""

    def get_fast_alarms(self):
        pass
    def scan_stock(self, group, msg):
        info = msg.lower()
        for code in self.stockcode:
            if code in info:
                self.add_to_monitor_group(group, code)

        for name in self.stockname:
            if name in info:
                return self.add_to_monitor_group(group, self.stockrdict[name])
    
    def isvalid_stock(self, stock):
        if stock.isdigit():
            return stock in self.stockcode
        else:
            return stock in self.stockname

    def extract_stock_from_msg(self, msg):
        stocklist = []
        for code in self.stockcode:
            if code in msg:
                stocklist.append(code)

        for name in self.stockname:
            if name in msg:
                stocklist.append(self.stockrdict[name])

        return stocklist

    def add_to_monitor_group(self,group,stock):
        if stock.isdigit():
            code = stock
        else:
            code = self.stockrdict[stock]

        if group in self.monitor_queue.keys():
            if code not in self.monitor_queue[group]:
                self.monitor_queue[group].append(code)
        else:
            self.monitor_queue[group] = [code]

        oplogs("add_to_monitor_group called:%s %s" %(group, stock))
    def get_group_stock_price(self, group):
        if group in self.monitor_queue.keys():
            stocks = []
            for code in self.monitor_queue[group]:
                price, change = self.get_stock_daily(code)
                stocks.append([code,price,change])

            sorted_alarms = sorted(stocks, key=lambda x: x[2],reverse=True)
            result = "本群关注：\n"
            for record in sorted_alarms:
                if record[1] == 0:
                    result += "[%s]停盘\n" %self.stockdict[record[0]]
                else:
                    newprice = "%.2f" %record[1]
                    newchange = "%.2f%%" %record[2]
                    result += "[%s]%s 涨幅:%s\n" %(self.stockdict[record[0]],
                                                        newprice, newchange)
            return result
        return ""

    def get_stock_daily(self, code):
        # 计算当日涨跌
        market = self.get_market(code)    
        data_day = self.api.get_security_quotes([(market,code)])    # get daily changes
        if self.debug:
            oplogs("get_stock_daily called")
            #print(self.api.to_df(data_day).ix[:,0:8])

        last_close = data_day[0]['last_close']
        current_price = data_day[0]['price']

        if last_close >0: #正常情况
            change = (current_price/last_close - 1)*100
        else:
            change = 0
        
        return current_price, change
    def get_stock_min(self, code, min=5):
        market = self.get_market(code)   
        data_min = self.api.get_security_bars(0,market, code, 0, 1) # 5 min K bar
        if self.debug:
            oplogs("get_stock_min called")
            #print(self.api.to_df(data_min).ix[:,0:8])
            
        open = data_min[0]['open']
        close = data_min[0]['close']
        high = data_min[0]['high']
        low = data_min[0]['low']
        
        if low >0 and open>0:
            # 波动范围
            change_high_low = (high-low)/low*100

            # 涨跌幅
            change_close_open = (close-open)/open*100
        else:
            change_high_low = 0
            change_close_open = 0
        
        return change_high_low, change_close_open
    def get_alarms(self,valve=3.0):
        # timeslice , slice in time series, default =5 min
        # range, monitor change range, default = 3%. Actual change range = abs((high-low)/low)
        groupalarms = dict()
        for (key, value) in self.monitor_queue.items():
            # 获取单个group监控的股票报警
            alarms = []
            for code in value:
                # 当日涨跌
                price, change = self.get_stock_daily(code)
                if price <= 0: # 停盘不监控
                    continue
                
                # 5分钟涨跌
                highlow, closeopen = self.get_stock_min(code)

                # 判断波动幅度是否超过阈值
                if abs(highlow) >=valve:
                    alarm = [self.stockdict[code],price,change,highlow,closeopen]                    
                    alarms.append(alarm)
            
            # 按5分钟涨跌幅排序
            sorted_alarms = sorted(alarms, key=lambda x: (x[4],x[2]),reverse=True)
            
            # 打包所有group的报警列表
            groupalarms[key] = sorted_alarms           

        return groupalarms
    def test(self):        
        data = self.api.get_security_bars(0,1, '600477', 0, 48) # 5 min K bar
        df = self.api.to_df(data)
        df['change_high_low'] = (df['high']-df['low'])/df['low']*100
        df['change_close_open'] = (df['close']-df['open'])/df['open']*100
        
        print(df)

if __name__ == '__main__':
    cur_path=os.path.dirname(os.path.realpath(__file__)) 
    stocklist_path=os.path.join(cur_path,'all.csv')
    df = pd.read_csv(stocklist_path, dtype={'code':'object'},encoding='GBK')
    df = df.set_index('code')
    print(df.head())
    