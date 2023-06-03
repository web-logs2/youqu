import asyncio
import base64
import time
import traceback

from flask import request
from flask_socketio import SocketIO

from channel.channel import Channel
from channel.http import auth
from common import const, log

from common.db.dbconfig import db
from common.db.user import User
from common.functions import num_tokens_from_string
from config import model_conf
from model.azure.azure_model import AZURE
from model.openai.chatgpt_model import Session
from service.global_values import addStopMessages


class socket_handler():
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.azure = AZURE()

    def register_socketio_events(self):
        self.socketio.on_event('connect', self.connect, namespace='/chat')
        self.socketio.on_event('disconnect', self.disconnect, namespace='/chat')
        self.socketio.on_event('message', self.message, namespace='/chat')
        self.socketio.on_event('update_conversation', self.update_conversation, namespace='/chat')
        self.socketio.on_event('stop', self.stop, namespace='/chat')
        self.socketio.on_event('disconnect', self.disconnect, namespace='/chat')
        self.socketio.on_event('heartbeat', self.heart_beat, namespace='/chat')

    async def return_stream(self, data, user: User):
        try:
            async for final, response in self.handle_stream(data=data, user=user):
                if final:
                    # log.info("Final:" + response)
                    self.socketio.server.emit(
                        'final',
                        {'content': response, 'messageID': data['messageID'],
                         'conversation_id': data['conversation_id'],
                         'final': final, "response_type": data.get("response_type", "text")}, request.sid,
                        namespace="/chat")
                else:
                    self.socketio.sleep(0.001)
                    self.socketio.server.emit(
                        'reply',
                        {'content': response, 'messageID': data['messageID'],
                         'conversation_id': data['conversation_id'],
                         'final': final, "response_type": data.get("response_type", "text")}, request.sid,
                        namespace="/chat")
        except Exception as e:
            log.error(traceback.format_exc())

    async def handle_stream(self, data, user: User):
        context = {
            'conversation_id': str(data.get("conversation_id")),
            'user': user,
            'response_type': data.get("response_type", "text"),
            'request_type': data.get("request_type", "text"),
            'model': data.get("model", const.MODEL_GPT_35_TURBO),
            'system_prompt': data.get("system_prompt", model_conf(const.OPEN_AI).get("character_desc", "")),
            'msg': data.get("msg", "")
        }

        if context['model'] not in user.get_available_models():
            context['model'] = const.MODEL_GPT_35_TURBO
        if num_tokens_from_string(context['system_prompt']) > 2048:
            context['system_prompt'] = model_conf(const.OPEN_AI).get("character_desc", "")
        # if context['request_type'] == "voice":
        # context["msg"] = await get_voice_text(data["voice_message"])
        log.info("message:" + data["msg"])
        # if context['response_type']=='voice':
        #     addStopMessages(context['msg'])
        if context['response_type'] == "picture":
            yield True, Channel.build_picture_reply_content(context)
        else:
            async for final, reply in Channel.build_reply_stream(context):
                if context['response_type'] == 'text':
                    final and log.info("reply:" + reply)
                    yield final, reply
                elif context['response_type'] == 'voice' and final:
                    log.info("reply:" + reply)
                    audio_data = self.azure.synthesize_speech(reply).audio_data
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    yield final, audio_base64

    # async def get_voice_text(voice_message):
    #     try:
    #         session = Session()
    #         text = session.stt(voice_message)
    #         return text
    #     except Exception as e:
    #         log.error("get_voice_text error:{}", e)
    #         return ""

    def message(self, data):
        token = request.args.get('token', '')
        user = auth.identify(token)
        if user is None:
            log.info("Token error")
            self.socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
        # data = json.loads(data)
        if data:
            asyncio.run(self.return_stream(data, user))

    def stop(self, data):
        token = request.args.get('token', '')
        user = auth.identify(token)
        if user is None:
            log.info("Token error")
            self.socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
        addStopMessages(user.user_id)
        self.socketio.server.emit('stop', {'info': "stopped"}, room=request.sid, namespace='/chat')

    def update_conversation(self, data):
        token = request.args.get('token', '')
        user = auth.identify(token)
        if user is None:
            log.info("Token error")
            self.socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
        conversation_id = data['conversation_id']
        log.info("update_conversation:" + conversation_id)
        Session.clear_session(user.user_id + conversation_id)
        self.socketio.emit('update_conversation', {'info': "conversation updated"}, room=request.sid, namespace='/chat')

    def connect(self):
        token = request.args.get('token', '')
        user = auth.identify(token)
        if user is None:
            log.info("Token error")
            self.disconnect()
            return
        log.info('{} connected', user.email)
        self.socketio.emit('connected', {'info': "connected"}, room=request.sid, namespace='/chat')

    def heart_beat(self, message):
        log.info("heart beat:{}", message)
        token = request.args.get('token', '')
        user_id = auth.identify_token(token)
        if user_id is None:
            log.info("Token error")
            self.socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
            self.disconnect()
            return
        log.info('{} heart beat', user_id)
        self.socketio.server.emit(
            'heartbeat',
            'pang', request.sid,
            namespace="/chat")

    def disconnect(self):
        log.info('disconnect')
        time.sleep(1)
        self.socketio.server.disconnect(request.sid, namespace="/chat")
        db.close()
