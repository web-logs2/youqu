import asyncio
import base64
import re
import time

from flask import request
from flask_socketio import SocketIO

from channel import channel
from channel.channel import Channel
from channel.http import auth
from channel.http.http_api import http_app
from common import const, log

from common.db.dbconfig import db
from common.db.user import User
from config import model_conf
from model.azure.azure_model import AZURE
from model.openai.chatgpt_model import Session
from service.global_values import addStopMessages

# log = log.info("socketIO_api")
socketio = SocketIO(http_app, ping_timeout=5 * 60, ping_interval=30, cors_allowed_origins="*")


async def return_stream(data, user: User):
    # try:
    async for final, response in handle_stream(data=data, user=user):
        if final:
            # log.info("Final:" + response)
            socketio.server.emit(
                'final',
                {'content': response, 'messageID': data['messageID'], 'conversation_id': data['conversation_id'],
                 'final': final, "response_type": data.get("response_type", "text")}, request.sid,
                namespace="/chat")
        else:
            socketio.sleep(0.001)
            socketio.server.emit(
                'reply',
                {'content': response, 'messageID': data['messageID'],
                 'conversation_id': data['conversation_id'],
                 'final': final, "response_type": data.get("response_type", "text")}, request.sid,
                namespace="/chat")


# except Exception as e:
#     log.error("[http]emit:{}", e)




async def handle_stream(data, user: User):
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
    if len(re.findall(r'\w+|[\u4e00-\u9fa5]|[^a-zA-Z0-9\u4e00-\u9fa5\s]', context['system_prompt'])) > 500:
        context['system_prompt'] = model_conf(const.OPEN_AI).get("character_desc", "")
    # if context['request_type'] == "voice":
    # context["msg"] = await get_voice_text(data["voice_message"])
    log.info("message:" + data["msg"])
    # if context['response_type']=='voice':
    #     addStopMessages(context['msg'])
    if context['response_type'] == "picture":
        yield True,Channel.build_picture_reply_content(context)
    else:
        async for final, reply in Channel.build_reply_stream(context):
            if context['response_type'] == 'text':
                final and log.info("reply:" + reply)
                yield final, reply
            elif context['response_type'] == 'voice' and final:
                log.info("reply:" + reply)
                azure = AZURE()
                audio_data = azure.synthesize_speech(reply).audio_data
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

@socketio.on('message', namespace='/chat')
def message(data):
    token = request.args.get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
    # data = json.loads(data)
    if data:
        asyncio.run(return_stream(data, user))


@socketio.on('stop', namespace='/chat')
def stop(data):
    token = request.args.get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
    addStopMessages(user.user_id)
    socketio.server.emit('stop', {'info': "stopped"}, room=request.sid, namespace='/chat')


@socketio.on('update_conversation', namespace='/chat')
def update_conversation(data):
    token = request.args.get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
    conversation_id = data['conversation_id']
    log.info("update_conversation:" + conversation_id)
    Session.clear_session(user.user_id + conversation_id)
    socketio.emit('update_conversation', {'info': "conversation updated"}, room=request.sid, namespace='/chat')


@socketio.on('connect', namespace='/chat')
def connect():
    token = request.args.get('token', '')
    user = auth.identify(token)
    if user is None:
        log.info("Token error")
        disconnect()
        return
    log.info('{} connected', user.email)
    socketio.emit('connected', {'info': "connected"}, room=request.sid, namespace='/chat')


@socketio.on('heartbeat', namespace='/chat')
def heart_beat(message):
    log.info("heart beat:{}", message)
    token = request.args.get('token', '')
    user_id = auth.identify_token(token)
    if user_id is None:
        log.info("Token error")
        socketio.emit('logout', {'error': "invalid cookie"}, room=request.sid, namespace='/chat')
        disconnect()
        return
    log.info('{} heart beat', user_id)
    socketio.server.emit(
        'heartbeat',
        'pang', request.sid,
        namespace="/chat")


@socketio.on('disconnect', namespace='/chat')
def disconnect():
    log.info('disconnect')
    time.sleep(1)
    socketio.server.disconnect(request.sid, namespace="/chat")
    db.close()
