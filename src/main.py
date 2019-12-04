import time,os
import psutil
import configparser
from robotutils import oplogs

import itchat
from itchat.content import TEXT
from harrybotter import HarryBotter, USER_CMD

gRobot = None
supportgroup = []

@itchat.msg_register(itchat.content.TEXT)
def text_reply(msg):
    # use filehelper as control console
    if msg.user['UserName'] == "filehelper":        
        oplogs("['filehelper']%s" %(msg['Text'])) 

        ret = gRobot.action(msg.Text)
        time.sleep(1)
        if ret is not "":
            msg.user.send(ret)


@itchat.msg_register([TEXT],isGroupChat=True)
def group_reply(msg):
    # 处理support group中的命令
    if gRobot.is_support_group(msg.User.NickName):
        oplogs("[%s:%s]%s" %(msg.User.NickName, msg.ActualNickName, msg['Text']))
        #忽略at我的命令
        if msg.isAt:
            return

        if USER_CMD in msg['Text']: # 用户命令
            ret = gRobot.action_user(msg.Text, 
                                     msg.User.NickName, 
                                     msg.ActualNickName)

            time.sleep(1)
            if ret is not "":
                msg.user.send(ret)
        else:# 群消息监控
            gRobot.listen(msg.User.NickName,  # 群名
                          msg.ActualNickName, # 用户名
                          msg['Text'])

def sendto(subscriber, msg):
    # callback function for robot send message to subscribers
    if subscriber is 'filehelper':
        itchat.send(msg,'filehelper')
    else:
        itchat.get_chatrooms(update=True, contactOnly= True)
        chatrooms = itchat.search_chatrooms(name=subscriber)
        if len(chatrooms)>0:
            oplogs('sending message to %s' %(chatrooms[0]['UserName']))
            chatrooms[0].send(msg)
    #itchat.send(msg, chatrooms[0]['UserName'])

def quitwx():
    oplogs("About to shutdown Harry Botter")
    itchat.send("harry botter stopped",'filehelper')
    itchat.logout()

def loadcfg():
    global supportgroup
    cur_path=os.path.dirname(os.path.realpath(__file__)) 
 
    #获取config.ini的路径
    config_path=os.path.join(cur_path,'config.ini')
    conf=configparser.ConfigParser()
    conf.read(config_path, encoding='utf-8')
    
    supportgroup=conf.get('default', 'supportgroups').split(',')
    oplogs("supportgroups loaded")

def init_robot():
    global gRobot
    # 默认在windows下开启调试模式
    loadcfg()
    gRobot = HarryBotter(debug = (os.name is 'nt'),stopcb=quitwx)
    gRobot.add_groups(supportgroup)
    gRobot.subscribe(sendto)
    oplogs("Harry bot init accomplished")
      

def main(): 
    itchat.auto_login(enableCmdQR=2,hotReload=True,loginCallback=init_robot)
    #itchat.start_receiving()    
    oplogs("Harry bot is ready to run")
    itchat.run()
    
    oplogs("Harry Botter offline")

main()