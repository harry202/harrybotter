import time
from robotutils import oplogs

import itchat
from itchat.content import TEXT
import pandas as pd

def get_myvip(up = True):
    friends=itchat.get_friends(update = up)
    df = pd.DataFrame(friends)
    df = df.query("RemarkName != ''")[['RemarkName','NickName']]
    tf = df[df['RemarkName'].str.startswith(('C','c'))]
    #tf = [name for name in flist if name.startswith(('C','c'))]    
    return tf

@itchat.msg_register(itchat.content.TEXT)
def text_reply(msg):
    # use filehelper as control console
    if msg.user['UserName'] == "filehelper":        
        if msg.Text == 'f':
            friends=itchat.get_friends(update = True)
            print(friends)
        if msg.Text == 'c':
            tf = get_myvip(False)

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


def init_robot():
    pass

def main(): 
    itchat.auto_login(enableCmdQR=2,hotReload=True)
    #itchat.start_receiving()    
    itchat.run()
    
    oplogs("Harry Botter offline")

main()