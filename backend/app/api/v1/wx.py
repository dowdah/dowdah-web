from flask import jsonify, request, g, abort, current_app, Blueprint
from ...security import WXBizMsgCrypt, WXBizMsgCryptError
from ...models import User
from ... import redis_client
import xml.etree.ElementTree as ET
import hashlib
import time
import re


wx_bp = Blueprint('wx', __name__)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@wx_bp.route('/', methods=['GET', 'POST'])
def view():
    # 校验请求是否来自微信服务器
    token = current_app.config['WECHAT_TOKEN']
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    if not all([signature, timestamp, nonce]):
        return abort(400)
    tmp_list = [token, timestamp, nonce]
    tmp_list.sort()
    tmp_str = ''.join(tmp_list)
    try:
        hashcode = hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()
    except:
        return abort(403)
    if hashcode != signature:
        return abort(403)

    # 微信服务器验证成功
    if request.method == 'GET':
        return request.args.get('echostr', '')
    elif request.method == 'POST':
        # r_msg = parse_xml(request.data)
        # if r_msg.msg_type == 'text':
        #     raw_send_msg = sTextMsg(r_msg, content=f"你说得对：{r_msg.content}").send()
        # else:
        #     raw_send_msg = sTextMsg(r_msg, content='现在不支持这种类型的消息！').send()
        # return raw_send_msg
        aes_key = current_app.config['WECHAT_AES_KEY']
        app_id = current_app.config['WECHAT_APP_ID']
        msg_signature = request.args.get('msg_signature')
        if not msg_signature:
            return abort(400)
        wx_crypt = WXBizMsgCrypt(token, aes_key, app_id)
        try:
            decrypted_msg = parse_xml(wx_crypt.decrypt_msg(request.data,
                                                 msg_signature,
                                                 timestamp,
                                                 nonce))
        except WXBizMsgCryptError as e:
            return abort(403)
        if not redis_client.exists(f"msg_{decrypted_msg.unique_id}"):
            # 记录消息的唯一 ID，为耗时长异步任务作准备
            redis_client.set(f"msg_{decrypted_msg.unique_id}", 1, ex=20)
        if decrypted_msg.msg_type == 'text':
            # 处理文本消息
            if decrypted_msg.is_command:
                send_content = handle_command(decrypted_msg.from_user_name, decrypted_msg.command, decrypted_msg.args)
                # send_content = f"你正在执行命令：{decrypted_msg.command}, 参数：{str(decrypted_msg.args)}"
                raw_send_msg = sTextMsg(decrypted_msg, content=send_content).send()
            else:
                raw_send_msg = sTextMsg(decrypted_msg, content=f"收到您的内容：{decrypted_msg.content}").send()
        elif decrypted_msg.msg_type == 'event':
            if decrypted_msg.event == 'subscribe':
                raw_send_msg = sTextMsg(decrypted_msg, content='欢迎关注，发送“/帮助”了解如何使用本服务号。').send()
            elif decrypted_msg.event == 'unsubscribe':
                return 'success'
            else:
                raw_send_msg = sTextMsg(decrypted_msg, content='现在不支持这种类型的消息！').send()
        else:
            raw_send_msg = sTextMsg(decrypted_msg, content='现在不支持这种类型的消息！').send()
        encrypted_send_msg = wx_crypt.encrypt_msg(raw_send_msg, nonce=nonce)
        return encrypted_send_msg


@wx_bp.route('/check-bind-request')
def check_bind_request():
    email = request.args.get('email')
    if email and EMAIL_REGEX.match(email):
        if redis_client.exists(f"bind_{email}"):
            response_json = {
                'success': True,
                'code': 200,
                'exists': True
            }
        else:
            response_json = {
                'success': True,
                'code': 200,
                'exists': False
            }
        return jsonify(response_json), response_json['code']
    else:
        return abort(400)


def parse_xml(web_data):
    if not web_data:
        return None
    xml_data = ET.fromstring(web_data)
    msg_type = xml_data.find('MsgType').text
    if msg_type == 'text':
        return rTextMsg(xml_data)
    elif msg_type == 'image':
        return rImageMsg(xml_data)
    elif msg_type == 'event':
        return rEventMsg(xml_data)


def handle_command(from_user_name, command, args):
    if command == '帮助':
        return "命令列表：\n" \
               "/帮助 - 显示本帮助信息\n" \
               "/回显 <内容> - 回显内容\n" \
               "/绑定 <邮箱> - 绑定邮箱。注意：使用本命令后，要使用对应的账户在官网确认绑定才能生效。\n" \
               "/我 - 显示账户信息\n"
    elif command == '回显':
        if args:
            return f"你说的内容是：{args[0]}"
        else:
            return "请提供要回显的内容！"
    elif command == '绑定':
        if args:
            email = args[0]
            if EMAIL_REGEX.match(email):
                email_user = User.query.filter_by(email=email).first()
                me = User.query.filter_by(wechat_openid=from_user_name).first()
                if email_user and email_user.wechat_bound:
                    return "该邮箱已被绑定！"
                elif me:
                    return f"你已绑定账户: {me.username}(UID: {me.id})，无法重复绑定。"
                else:
                    redis_client.set(f"bind_{email}", from_user_name, ex=600)
                    return (f"您已申请将 {email} 绑定到您的微信账号，"
                            f"请在 10 分钟内于官网完成确认操作。若超时请重新发送绑定命令。\n"
                            f"注意：若您未在期限内未于官网确认绑定，本次申请将不会作出任何改变。")
            else:
                return "请提供有效的邮箱地址！"
        else:
            return "请提供要绑定的邮箱地址！"
    elif command == '我':
        user = User.query.filter_by(wechat_openid=from_user_name).first()
        if user:
            return f"你的Dowdah账户信息\n" \
                   f"UID：{user.id}\n" \
                   f"用户名：{user.username}\n" \
                   f"邮箱：{user.email}\n" \
                   f"注册时间：{user.formatted_created_at}\n"
        else:
            return "你尚未绑定Dowdah账户。请前往官网创建账户或绑定已有账户。"
    else:
        return f"未知命令：{command}，请发送“/帮助”查看帮助信息！"


class rMsg:
    def __init__(self, xml_data):
        self.to_user_name = xml_data.find('ToUserName').text
        self.from_user_name = xml_data.find('FromUserName').text
        self.create_time = xml_data.find('CreateTime').text
        self.msg_type = xml_data.find('MsgType').text


class rTextMsg(rMsg):
    def __init__(self, xml_data):
        super().__init__(xml_data)
        self.content = xml_data.find('Content').text
        self.is_command = self.content.startswith('/')
        self.msg_id = xml_data.find('MsgId').text
        self.unique_id = self.msg_id
        if self.is_command:
            parts = re.findall(r'\S+', self.content)
            if len(parts) > 1:
                self.command = parts[0][1:]
                self.args = parts[1:]
            else:
                self.command = parts[0][1:]
                self.args = []


class rImageMsg(rMsg):
    def __init__(self, xml_data):
        super().__init__(xml_data)
        self.pic_url = xml_data.find('PicUrl').text
        self.media_id = xml_data.find('MediaId').text
        self.msg_id = xml_data.find('MsgId').text
        self.unique_id = self.msg_id


class rEventMsg(rMsg):
    def __init__(self, xml_data):
        super().__init__(xml_data)
        self.event = xml_data.find('Event').text
        self.event_key = xml_data.find('EventKey').text if xml_data.find('EventKey') is not None else None
        self.unique_id = self.from_user_name + self.create_time


class sMsg:
    def __init__(self, r_msg):
        self.to_user_name = r_msg.from_user_name
        self.from_user_name = r_msg.to_user_name

    def send(self):
        return "success"


class sTextMsg(sMsg):
    def __init__(self, r_msg, content):
        super().__init__(r_msg)
        self.data = {
            'ToUserName': self.to_user_name,
            'FromUserName': self.from_user_name,
            'CreateTime': int(time.time()),
            'Content': content
        }

    def send(self):
        xml_form = """
<xml>
    <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
    <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
    <CreateTime>{CreateTime}</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[{Content}]]></Content>
</xml>
"""
        return xml_form.format(**self.data)


class sImageMsg(sMsg):
    def __init__(self, r_msg, media_id):
        super().__init__(r_msg)
        self.data = {
            'ToUserName': self.to_user_name,
            'FromUserName': self.from_user_name,
            'CreateTime': int(time.time()),
            'MediaId': media_id
        }

    def send(self):
        xml_form = """
<xml>
    <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
    <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
    <CreateTime>{CreateTime}</CreateTime>
    <MsgType><![CDATA[image]]></MsgType>
    <Image>
        <MediaId><![CDATA[{MediaId}]]></MediaId>
    </Image>
</xml>
"""
        return xml_form.format(**self.data)
