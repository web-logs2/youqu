import asyncio
import base64
import time
import traceback

from flask import request, jsonify
from flask_socketio import SocketIO

from channel.channel import Channel
from channel.http import auth
from channel.http.http_api import handle_text
from common import const, log

from common.db.dbconfig import db
from common.db.document_record import DocumentRecord
from common.db.user import User
from common.functions import num_tokens_from_string
from common.menu_functions.public_train_methods import public_query_documents
from config import model_conf
from model.azure.azure_model import AZURE
from model.openai.chatgpt_model import Session
from service.global_values import addStopMessages


class socket_handler():
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        # self.azure = AZURE()

    def register_socketio_events(self):
        self.socketio.on_event('connect', self.connect, namespace='/chat')
        self.socketio.on_event('disconnect', self.disconnect, namespace='/chat')
        self.socketio.on_event('message', self.message, namespace='/chat')
        self.socketio.on_event('update_conversation', self.update_conversation, namespace='/chat')
        self.socketio.on_event('stop', self.stop, namespace='/chat')
        self.socketio.on_event('disconnect', self.disconnect, namespace='/chat')
        self.socketio.on_event('heartbeat', self.heart_beat, namespace='/chat')

    async def return_stream(self, data, user: User):

        # test api method
        # data['user'] = user
        # reply = handle_text(data)
        # self.socketio.server.emit(
        #                 'final',
        #                 {'content': reply, 'messageID': data['messageID'],
        #                  'conversation_id': data['conversation_id'],
        #                  'final': True, "response_type": data.get("response_type", "text")}, request.sid,
        #                 namespace="/chat")

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
            'msg': data.get("msg", ""),
            'conversation_type': data.get("conversation_type", "chat"),
            'document': data.get("document", ""),
            'function_call': data.get("function_call", ""),
        }

        if context['model'] not in user.get_available_models():
            context['model'] = const.MODEL_GPT_35_TURBO
        if num_tokens_from_string(context['system_prompt']) > 2048:
            context['system_prompt'] = model_conf(const.OPEN_AI).get("character_desc", "")
        # if context['request_type'] == "voice":
        # context["msg"] = await get_voice_text(data["voice_message"])
        log.info("message:" + context["msg"])
        log.info("user:" + user.email)
        # if context['response_type']=='voice':
        #     addStopMessages(context['msg'])
        if context["msg"] == "":
            yield True, "请说话"
            return

        if context['conversation_type'] == 'reading':

            records = DocumentRecord.select().where(DocumentRecord.id == context['document'])
            if records.count() <= 0:
                log.error("文档未找到")
                yield True, "文档未找到"
                return
            if records[0].trained == 0:
                log.error("书籍未训练完成")
                yield True, "书籍未训练完成"
                return
            log.info("Trained file path:" + records[0].trained_file_path)
            start_time = time.time()
            try:
                res = public_query_documents(records[0].trained_file_path, context["msg"], context['document'])
                response = ""
                for token in res.response_gen:
                    response += token
                    yield False, response
                yield True, response
                end_time = time.time()
                log.info("Total time elapsed: {}".format(end_time - start_time))
                return
            except Exception as e:
                log.error(traceback.format_exc())
                yield True, "文档查询失败"
                return

        if context['response_type'] == "picture":
            yield True, Channel.build_picture_reply_content(context)
        else:
            async for final, reply in Channel.build_reply_stream(context):
                if context['response_type'] == 'text':
                    final and log.info("reply:" + reply)
                    yield final, reply
                elif context['response_type'] == 'voice' and final:
                    log.info("reply:" + reply)
                    audio_data = AZURE().synthesize_speech(reply).audio_data
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    yield final, audio_base64

    def message(self, data):
        user = self.verify_stream()
        if user and data:
            if user.available_balance < 0:
                self.socketio.emit('final', {'content': "余额不足，请及时充值"}, room=request.sid, namespace='/chat')
                return
            asyncio.run(self.return_stream(data, user))

    def stop(self, data):
        user = self.verify_stream()
        if user:
            addStopMessages(user.user_id)
            log.info("{} messages stopped",user.user_id)
            #self.socketio.emit('stop', {'info': "stopped"}, room=request.sid, namespace='/chat')

    def update_conversation(self, data):
        user = self.verify_stream()
        if user and data:
            conversation_id = data['conversation_id']
            log.info("update_conversation:" + conversation_id)
            Session.clear_session(user.user_id + conversation_id)
            self.socketio.emit('update_conversation', {'info': "conversation updated"}, room=request.sid,
                               namespace='/chat')

    def connect(self):
        user = self.verify_stream()
        if user:
            log.info('{} connected', user.email)
            self.socketio.emit('connected', {'info': "connected"}, room=request.sid, namespace='/chat')

    def heart_beat(self, message):
        log.info("heart beat:{}", message)
        user = self.verify_stream()
        if user:
            log.info('{} heart beat', user.user_id)
            self.socketio.server.emit(
                'heartbeat',
                'pang', request.sid,
                namespace="/chat")

    def disconnect(self):
        log.info('disconnect')
        self.socketio.server.disconnect(request.sid, namespace="/chat")
        db.close()

    def verify_stream(self):
        token = request.args.get('token', '')
        user = auth.identify(token)
        if user is None:
            log.info("Token error")
            self.socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
            time.sleep(10)
            self.disconnect()
        return user
