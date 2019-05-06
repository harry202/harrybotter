import time,random
import sqlite3

from apscheduler.schedulers.background import BackgroundScheduler
from stockmod import StockMod
from robotutils import oplogs
 

HR__VERSION = "Released on 2019.5.5"

syscmd = ['/cfg','/help', '/show','/add','/delete','/test','/restart','/start','/stop','/use', 'ping']
cmdhelp = ['/cfg 配置','/help 显示帮助']
USER_CMD = 'harry'

auto_replys = ["莫西莫西","你猜我是机器人吗","啥事？",
        "命令格式：\n[添加监控]harry 股票名\n[删除监控]harry del 股票名\n[显示群推荐]harry 本群推荐\n[显示群数据统计]harry stat\n[显示报告]harry report"]
class HarryBotter(object):
    def __init__(self, debug= False,stopcb=None):
        oplogs("Harry Botter is rebooting")
        self.__init_robot(debug)
        self.stopcb = stopcb
        self.__load_mods()        
        #self.__init_db()
        #self.__init_jobs()
        oplogs("Harry Botter is online")

    def __del__(self):
        oplogs("Harry Botter is shutting down~~~")
        self.stop_jobs()
        #self.close_db()

    def __init_robot(self,debug):
        self.enable = True
        self.mouth = None # output callback
        self.ear = None   # input for text and audio callback
        self.eye = None   # input for graph callback
        self.brain = None # processor modules
        self.memory = []  # memory for what heard or seen

        self.support_groups = []
        self.debug = debug
        self.sched = None

    def subscribe(self,msgSend):
        self.mouth = msgSend
        oplogs('Robot unmuted.')
    def unsubscribe(self):
        self.mouth = None   
        oplogs('Robot muted.')
    def __load_mods(self):
        self.stockmod = StockMod(self.debug)

    def __init_db(self):
        # 创建数据库数据库用于永久记忆
        self.conn = sqlite3.connect('messages.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('create table if not exists msgqueue (id integer primary key autoincrement, date TEXT, group TEXT, user TEXT, msg TEXT)')
        self.cursor.execute('create table if not exists monitorstocks (id integer primary key autoincrement, group TEXT, code TEXT)')
        self.cursor.commit()
        
        oplogs("[%s]messages.db connected")

    def __close_db(self):
        self.conn.close()

    def __init_jobs(self):
        self.sched = BackgroundScheduler()

        # 添加任务作业

        # 每天清理一次缓存
        #self.sched.add_job(self.job_clean_cache, trigger='cron', day_of_week='*',hour=1, minute=0, second=0)

        # 提供给group的5分钟检测
        self.sched.add_job(self.job_stock_monitor, trigger='cron', id='job_stock_monitor', minute="*/5", next_run_time=None)

        # 交易日9:30:15生成开盘报告
        self.sched.add_job(self.job_open_scan, trigger='cron', day_of_week='0-4',hour=9, minute=30, second=15)
        
        # 交易日15:05生成收盘报告
        self.sched.add_job(self.job_close_scan, trigger='cron', day_of_week='0-4',hour=15, minute=5, second=0)
        
        # 启动调度器
        self.sched.start()

        oplogs("schedulers started")

    def stop_jobs(self):
        if self.sched == None:
            self.sched.shutdown()
        oplogs("schedulers stopped")

    def job_stock_monitor(self,valve=2.0):
        oplogs("job_stock_monitor triggerred")
        group_alarms = self.stockmod.get_alarms(valve)
        for (group, alarms) in group_alarms.items():
            notice = ""
            for alarm in alarms:
                # alarm = [stockname,price,change,highlow,closeopen]
                alarm_content = "[%s %.2f%%]5分钟涨跌幅：%.2f%%, 波动:%.2f%%\n" %(alarm[0],alarm[2],alarm[4],alarm[3])
                notice  += alarm_content
            if len(notice)>0:
                print(notice)
                self.mouth(group, notice)
                time.sleep(1)

    def job_open_scan(self):
        oplogs("job_open_scan triggerred")
        self.job_stock_monitor(valve=5.0)
        self.sched.resume_job(job_id = "job_stock_monitor")

    def job_close_scan(self):
        oplogs("job_close_scan triggerred")
        self.sched.pause_job(job_id = "job_stock_monitor")
        
    def job_forget(self, persist = False):
        # 清除记忆
        if persist is True:
            #save memory before forget them
            pass 
        self.memory.clear()
        oplogs("memory erased")

    def listen(self, group, user, msg):
        # 添加一条记录到记忆中
        record = [time.strftime("%Y-%m-%d %H:%M:%S"),group,user,msg]
        self.stockmod.scan_stock(group, msg)
        self.memory.append(record)

    def save_to_db(self):
        oplogs("save_to_db called")
        # 保存消息
        for msg in self.memory:
            sql = "INSERT INTO msgqueue VALUES (%s,%s,%s,%s)" %(msg[0],msg[1],msg[2], msg[3])
            self.cursor.execute(sql)
        
        # 保存监控列表
        for (key, value) in self.stockmod.monitor_queue.items():
            for code in value:
                # date TEXT, group TEXT, code TEXT
                # date = time.strftime("%Y-%m-%d %H:%M:%S")
                sql = "INSERT INTO monitorstocks VALUES (%s,%s)" %(key, code)
                self.cursor.execute(sql)

        self.conn.commit()
                
    def load_from_db(self):
        pass

    def isCmd(self,cmd):        
        if USER_CMD in cmd:
            return True
        for keyword in syscmd:
            if keyword in cmd:
                return True

        return False

    def action_user(self, cmd, group, user):
        cmds = cmd.lower().split()

        #"命令格式：
        # [添加监控]harry 股票名
        # [删除监控]harry del 股票名
        # [显示群推荐]harry 本群推荐
        # [显示群数据统计]harry stat
        # [显示报告]harry report"]
        # user 用户命令
        if len(cmds)==1:
            return random.choice(auto_replys)
        
        if '本群推荐' in cmds[1]:
            oplogs("action_user:本群推荐 [%s]" %cmd)
            return self.stockmod.get_group_stock_price(group)
        elif 'stat' in cmds[1]:
            stat = "共有群消息 条\n"
            stat = stat + ""
            return "建设中"
        elif 'report' in cmds[1]:
            return "建设中"
        elif 'help' in cmds[1]:
            oplogs("action_user:help called")
            return 'harry [股票名|本群推荐|stat*|report*|help|ver]'
        elif 'ver' in cmds[1]:
            return HR__VERSION
        else:
            oplogs("action_user:harry [stock] called %s" %cmd)
            if self.stockmod.isvalid_stock(cmds[1]):
                self.add_stock(group, cmds[1])      
                return self.show_stock(cmds[1])

        return ""
      
    def action(self, cmd):
        cmds = cmd.split()

        # 管理员后台控制命令
        if not self.isCmd(cmds[0]):
            return ""

        # 去除'/',提取控制命令函数名
        _cmd = cmds[0].strip('/')
        if len(cmds)>1:
            return eval("self.{}({})".format(_cmd,cmds[1:]))
        else:
            return eval("self.{}()".format(_cmd))

    def ping(self,cmds=[]):
        #self.mouth('量化技术讨论','test')
        return 'pong'

    def help(self,cmds=[]):
        # 显示命令帮助
        return ("Help\n"+",".join(syscmd))
    def show(self,cmds=[]):
        # 显示在线信息和数据
        # show gmsg/stock [stockname]/monitor/stats
        print("/show called")
        if cmds[0] == 'memory':
            return "Robot has %d messages in memory" %(len(self.memory))
        if cmds[0] == 'stock':
            return self.show_stock(cmds[1])
        if cmds[0] == 'groups': # 显示所有支持的群
            return ",".join(self.support_groups)
        if cmds[0] == 'group':  # 显示指定群支持的股票
            if len(cmds)>1 and cmds[1].isdigit():
                groupid = int(cmds[1])
            else:
                groupid = 0
            return self.action_user("harry 本群推荐",self.support_groups[groupid],"robot")            
        if cmds[0] == 'mq':
            return str(self.stockmod.monitor_queue)
        if cmds[0] == 'stats':
            return "no supported cmd"
        return "no supported cmd"
    
    def show_stock(self,stock):
        if '机器人' in stock or '300024' in stock:
            return "harry拒绝关注其他机器人"       
        
        if stock.isdigit():  
            return self.stockmod.get_stock_price(stock)
        else:
            return self.stockmod.get_stock_price_by_name(stock)

    def cfg(self):
        # 修改在线配置
        return ("/cfg called")
    def add(self,cmds=[]):
        if len(cmds)>=2:
            # /add group [groupname], 添加支持的group
            if cmds[0] is "group":
                self.support_groups.append(cmds[1])        
                return "group added"
        return "not supprt command"
    def add_stock(self, group, stock):
        self.stockmod.add_to_monitor_group(group, stock)

    def delete(self,cmds=[]):
        if len(cmds)>0:
            # 删除支持的group
            if cmds[0] is "group":
                self.support_groups.remove(cmds[1])        
                return "group deleted"
        return "not supprt command"
    def is_support_group(self, group):
        return group in self.support_groups
    def test(self, cmd):
        return "test"
    def restart(self):
        # 重启机器人
        return "restarted"
    def start(self):
        # 启动机器人
        self.enable = True
        return "started"
    def stop(self):
        print("stop called")
        # 离线机器人
        self.enable = False
        self.stopcb()
    def use(self):
        # 加载模块控制
        # module management to be implemented here
        return "All mods loaded"

    def add_msg(self, msg):
        # save message
        self.memory.append(msg)

    def add_groups(self, groups):
        for group in groups:
            if group not in self.support_groups:
                self.support_groups.append(group)

def debug_print(group,msg):
    print(group,":")
    print(msg)
    print('-'*20)

if __name__ == '__main__':
    mybot = HarryBotter(debug = True)
    mybot.subscribe(debug_print)
    mybot.stockmod.add_to_monitor_group("testgroup1","600518")
    mybot.stockmod.add_to_monitor_group("testgroup1","002496")
    mybot.stockmod.add_to_monitor_group("testgroup1","000000")
    mybot.stockmod.add_to_monitor_group("testgroup2","002456")
    mybot.stockmod.add_to_monitor_group("testgroup2","600477")
    mybot.stockmod.add_to_monitor_group("testgroup2","002496")

    mybot.job_stock_monitor(valve=0)


