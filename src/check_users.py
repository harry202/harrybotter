import itchat, time
import pandas as pd

itchat.auto_login(True)

chatroomUserName = '@1234567'
friends = itchat.get_friends(update = True)

for friend in friends.items():
    name = friend['UserName']
    r = itchat.add_member_into_chatroom(name, [friend])
    if r['BaseResponse']['ErrMsg'] == '':
        status = r['MemberList'][0]['MemberStatus']
        itchat.delete_member_from_chatroom(chatroom['UserName'], [friend])
        return { 3: '该好友已经将你加入黑名单。',
            4: '该好友已经将你删除。', }.get(status,
            '该好友仍旧与你是好友关系。')