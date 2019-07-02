import time
import itchat
from itchat.content import TEXT
import requests
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from simplejson import JSONDecodeError
import threading
import random
Grace_PERIOD=15*60
reply_name_uuid_list=[]
class Message:
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/67.0.3396.87 Safari/537.36',
    }
    def __init__(self):
        self.receiver_list,self.alarm_hour,self.alarm_minute,self.sentence_list=self.get_init_data()

    def get_init_data(self):
        with open('_config.yaml','r',encoding='utf-8') as file:
            config=yaml.load(file,Loader=yaml.Loader)

        alarm_timed=config.get('alarm_timed').strip()


        receiver_list = []
        receiver_infos = config.get('receiver_infos')

        for receiver in receiver_infos:
            receiver.get('wechat_name').strip()
            receiver_list.append(receiver)
        hour, minute = [int(x) for x in alarm_timed.split(':')]
        rand_hour=hour+random.randint(-1,1)
        rand_minute=minute+random.randint(0,60)
        if rand_minute>=60:
            rand_minute-=60
        print('今天天定时发送时间：{}\n'.format(str(rand_hour)+':'+str(rand_minute)))
        sentence_list=config.get('sentences')
        return receiver_list,rand_hour,rand_minute,sentence_list

    @staticmethod
    def is_online(auto_login=False):

        def _online():
            try:
                if itchat.search_friends():
                    return True
            except IndexError:
                return False
            return True

        if _online():
            return True
        if not auto_login:
            return _online()

        for _ in range(3):
            itchat.auto_login(enableCmdQR=2, hotReload=True)

            if _online():
                print('登录成功')
                return True

        print('登录成功')
        return False

    def run(self):

        global reply_name_uuid_list
        if not self.is_online(auto_login=True):
            return
        for reciver in self.receiver_list:
            wechat_name=reciver.get('wechat_name')
            friends=itchat.search_friends(name=wechat_name)
            if not friends:
                print('昵称『{}』有误。'.format(wechat_name))
                return
            name_uuid=friends[0].get('UserName')
            reciver['name_uuid']=name_uuid
            if name_uuid not in reply_name_uuid_list:
                reply_name_uuid_list.append(name_uuid)
        scheduler=BlockingScheduler()
        scheduler.add_job(self.start_today_info,'cron',hour=self.alarm_hour,
                          minute=self.alarm_minute,misfire_grace_time=Grace_PERIOD)
        scheduler.start()

    @itchat.msg_register([TEXT])
    def start_today_info(self,is_test=False):
        print('*'*50)
        print('获取相关信息...')
        msg='父母让我每日报下平安，我想到了用程序去完成它。  这应该是不对的吧，其实说句话也不麻烦。  但我还是想继续完善它，毕竟这件事情深究下去也是挺有意思的---send by him'
        #msg=self.sentence_list[random.randint(0,len(self.sentence_list)-1)]
        for receiver in self.receiver_list:
            name_uuid=receiver.get('name_uuid')
            wechat_name=receiver.get('wechat_name')
            print('给『{}』发送的内容是:\n{}'.format(wechat_name, msg))
            if not is_test:
                if self.is_online(auto_login=True):
                    itchat.send(msg,toUserName=name_uuid)
                time.sleep(5)
        print('send success...\n')

    @staticmethod
    def is_json(resp):
        """
        判断数据是否能被 Json 化。 True 能，False 否。
        :param resp: request.
        :return: bool, True 数据可 Json 化；False 不能 JOSN 化。
        """
        try:
            resp.json()
            return True
        except JSONDecodeError:
            return False