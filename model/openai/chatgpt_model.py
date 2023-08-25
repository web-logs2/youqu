# encoding:utf-8
import datetime
import json
import re
import time
import traceback

import openai
import tiktoken
from expiring_dict import ExpiringDict
from flask import request
from typing import List

from requests.exceptions import ChunkedEncodingError

from common import const
from common import log
from common.db.conversation import Conversation
from common.db.query_record import QueryRecord
from common.db.user import User
from common.functions import num_tokens_from_messages, num_tokens_from_string, get_max_token
from common.menu_functions.function_call_library import detect_function_and_call, functions_definition
from service.global_values import inStopMessages, removeStopMessages
from config import model_conf
from common.menu_functions.document_list import DocumentList
from common.menu_functions.pre_train_documnt import PreTrainDcoumnet
from common.menu_functions.query_document import QueryDcoumnet
from model.model import Model

from common.menu_functions.cnblogs_query_document import CnblogsQueryDcoumnet
from common.menu_functions.cnblogs_pre_train_document import CnblogsPreTrainDocument

from common.menu_functions.wx_pre_train_document import WxPreTrainDocument
from common.menu_functions.wx_query_document import WxQueryDocument
from common.menu_functions.clear_memory import ClearMemory

if model_conf(const.OPEN_AI).get('expires_in_seconds'):
    user_session = ExpiringDict(model_conf(const.OPEN_AI).get('expires_in_seconds'))
    # logging.info("Set dict expire time "+model_conf(const.OPEN_AI).get('expires_in_seconds'))
else:
    user_session = ExpiringDict(3600)


# OpenAI对话模型API (可用)
class ChatGPTModel(Model):
    def __init__(self):
        openai.api_key = model_conf(const.OPEN_AI).get('api_key')
        proxy = model_conf(const.OPEN_AI).get('proxy')
        if proxy:
            openai.proxy = proxy

    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            log.info("[CHATGPT] query={}".format(query))
            from_user_id = context['from_user_id']
            if query == '#清除记忆':
                Session.clear_session_by_user(from_user_id)
                return '记忆已清除'
            system_prompt = context['system_prompt']
            new_query = Session.build_session_query(query, from_user_id, system_prompt)
            log.debug("userid:{} [CHATGPT] session query={}".format(from_user_id, new_query))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, from_user_id)

            reply_content = self.reply_text(new_query, from_user_id, 0)
            log.debug("[CHATGPT] new_query={}, user={}, reply_cont={}".format(new_query, from_user_id, reply_content))
            return reply_content

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_text(self, context, retry_count=0):

        try:
            user: User = context['user']
            conversation_id = context['conversation_id']
            system_prompt = context['system_prompt']
            model = context['model']
            query = context['msg']

            user_session_id = user.user_id + conversation_id
            if query == '#清除记忆':
                # Session.clear_session(user_session_id)
                Session.clear_session(user_session_id)
                return "记忆已清除"
            new_query = Session.build_session_query(query, user_session_id, system_prompt, model=model)

            ip = request.headers.get("X-Forwarded-For", request.remote_addr)

            start_time = time.time()  # 记录结束时间
            query_record = QueryRecord(
                user_id=context['user'].user_id,
                conversation_id=context['conversation_id'],
                query=query,
                reply="",
                ip=ip,
                model_name=model,
                prompt_count=num_tokens_from_messages(new_query, model),
                created_time=datetime.datetime.now(),
                updated_time=datetime.datetime.now(),
            )
            query_record.update_ip_location()
            query_record.set_query_trail(new_query)

            log.info("[chatgpt]: model={} query={}", model, new_query)

            response = self.  get_non_stream_full_response_for_one_question(model, new_query)
            reply_content = response.choices[0]['message']['content']

            end_time = time.time()  # 记录结束时间
            execution_time = end_time - start_time  # 计算执行时间
            log.info("[Execution Time] {:.4f} seconds", execution_time)  # 打印执行时间
            used_token = response['usage']['total_tokens']
            log.info("total tokens usage:{}".format(used_token))
            log.debug(response)
            # log.info("[CHATGPT] reply={}", reply_content)
            if reply_content:
                # save conversation
                Session.save_session(reply_content, user_session_id, model)
            return reply_content



        except openai.error.RateLimitError as e:
            # rate limit exception
            log.warn(e)
            if retry_count < 1:
                time.sleep(5)
                log.warn("[CHATGPT] RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.reply_text(context, retry_count + 1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except openai.error.APIConnectionError as e:
            log.warn(e)
            log.warn("[CHATGPT] APIConnection failed")
            return "我连接不到网络，请稍后重试"
        except openai.error.Timeout as e:
            log.warn(e)
            log.warn("[CHATGPT] Timeout")
            return "我没有收到消息，请稍后重试"
        except Exception as e:
            # unknown exception
            log.exception(e)
            Session.clear_session_by_user(user_session_id)
            return "请再问我一次吧"

    async def reply_text_stream(self, context, retry_count=0):
        try:
            user: User = context['user']
            conversation_id = context['conversation_id']
            system_prompt = context['system_prompt']
            model = context['model']
            query = context['msg']

            user_session_id = user.user_id + conversation_id
            if query == '#清除记忆':
                # Session.clear_session(user_session_id)
                Session.clear_session(user_session_id)
                yield True, '记忆已清除'
                return
            new_query = Session.build_session_query(query, user_session_id, system_prompt, model=model)

            #
            # headers = request.headers
            # # 遍历请求头并打印
            # for key in headers:
            #     print(f"{key}: {headers[key]}")

            # for header in request.headers:
            #     log.info(header)
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            # ip_location = ""
            # try:
            #     ip_location = ip_reader.city(ip).city.names.get('zh-CN', '')
            # except Exception as e:
            #     log.error("[http]ip:{}", e)

            query_record = QueryRecord(
                user_id=context['user'].user_id,
                conversation_id=context['conversation_id'],
                query=query,
                reply="",
                ip=ip,
                model_name=model,
                prompt_count=num_tokens_from_messages(new_query, model),
                created_time=datetime.datetime.now(),
                updated_time=datetime.datetime.now(),
            )
            query_record.update_ip_location()
            query_record.set_query_trail(new_query)

            log.info("[chatgpt]: model={} query={}", model, new_query)

            async for final, reply in self.get_stream_full_response_for_one_question(user, model, new_query):
                if final:
                    full_response = reply
                    Session.save_session(full_response, user_session_id, model=model)
                    conversation = Conversation.select().where(Conversation.conversation_id == conversation_id).first()
                    if conversation is None:
                        conversation = Conversation(
                            conversation_id=conversation_id,
                            user_id=user.user_id,
                            promote=system_prompt,
                            total_query=1,
                            created_time=datetime.datetime.now(),
                            updated_time=datetime.datetime.now()
                        )
                    else:
                        conversation.updated_time = datetime.datetime.now()
                        conversation.total_query = conversation.total_query + 1;
                    conversation.save()
                    query_record.reply = full_response
                    query_record.complication_count = num_tokens_from_string(full_response)
                    query_record.save()
                    removeStopMessages(user.user_id)
                yield final, reply

        except openai.error.RateLimitError as e:
            # rate limit exception
            log.warn(e)
            if retry_count < 1:
                yield False, "[CHATGPT] Connection broken, 第{}次重试，等待{}秒".format(retry_count + 1, 5)
                time.sleep(5)
                log.warn("[CHATGPT] RateLimit exceed, 第{}次重试".format(retry_count + 1))
                yield True, self.reply_text_stream(context, retry_count + 1)
            else:
                yield True, "提问太快啦，请休息一下再问我吧"
        except openai.error.APIConnectionError as e:
            log.warn(e)
            log.warn("[CHATGPT] APIConnection failed")
            yield True, "我连接不到网络，请稍后重试"
        except openai.error.Timeout as e:
            log.warn(e)
            log.warn("[CHATGPT] Timeout")
            yield True, "我没有收到消息，请稍后重试"
        except ChunkedEncodingError as e:
            log.warn(e)
            if retry_count < 1:
                wait_time = (retry_count + 1) * 5
                yield False, "[CHATGPT] Connection broken, 第{}次重试，等待{}秒".format(retry_count + 1, wait_time)
                log.warn("[CHATGPT] Connection broken, 第{}次重试，等待{}秒".format(retry_count + 1, wait_time))
                time.sleep(wait_time)
                yield True, self.reply_text_stream(context, retry_count + 1)
            else:
                yield True, "我连接不到网络，请稍后重试"
        except Exception as e:
            # unknown exception
            log.error(traceback.format_exc())
            Session.clear_session_by_user(user_session_id)
            yield True, "请再问我一次吧"

    def create_img(self, query, retry_count=0):
        try:
            log.info("[OPEN_AI] image_query={}".format(query))
            response = openai.Image.create(
                prompt=query,  # 图片描述
                n=1,  # 每次生成图片的数量
                size="1024x1024"  # 图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response['data'][0]['url']
            log.info("[OPEN_AI] image_url={}".format(image_url))
            return image_url
        except openai.error.RateLimitError as e:
            log.warn(e)
            if retry_count < 1:
                time.sleep(5)
                log.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.reply_text(query, retry_count + 1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            log.error(traceback.format_exc())
            return None

    def get_non_stream_full_response_for_one_question(self, model, new_query):
        is_stream = False
        response = self.get_GPT_answer(model, new_query, is_stream)

        function_call = {
            "name": "",
            "arguments": "",
        }

        # count = 0

        while True:
            # log.info("count time: {}".format(count))
            # count = count + 1

            reply_message = response.choices[0]['message']
            if "function_call" in reply_message:
                if "name" in reply_message["function_call"]:
                    function_call["name"] = reply_message["function_call"]["name"]
                if "arguments" in reply_message["function_call"]:
                    function_call["arguments"] = reply_message["function_call"]["arguments"]

                response = self.get_GPT_function_call_answer(model, new_query, function_call, is_stream)
            else:
                return response

    async def get_stream_full_response_for_one_question(self, user, model, new_query):
        is_stream = True
        res = self.get_GPT_answer(model, new_query, is_stream)

        full_response = ""

        function_call = {
            "name": "",
            "arguments": "",
        }
        # count = 0

        final = False

        while not final:
            # log.info("count time: {}".format(count))
            # count = count + 1
            for chunk in res:
                # log.info("chunk No.{}, {}".format(count, chunk))
                if "function_call" in chunk['choices'][0]['delta']:
                    function_call_flag = True
                    if "name" in chunk['choices'][0]['delta']["function_call"]:
                        function_call["name"] += chunk['choices'][0]['delta']["function_call"]["name"]
                    if "arguments" in chunk['choices'][0]['delta']["function_call"]:
                        function_call["arguments"] += chunk['choices'][0]['delta']["function_call"]["arguments"]
                if chunk.choices[0].finish_reason == "function_call":
                    if function_call_flag:
                        log.info("function call={}", function_call)
                        res = self.get_GPT_function_call_answer(model, new_query, function_call, is_stream)
                        function_call = {
                            "name": "",
                            "arguments": "",
                        }
                    break
                # if not chunk.get("content", None):
                #     continue

                if (chunk["choices"][0]["finish_reason"] == "stop"):
                    # break
                    final = True
                    yield final, full_response
                    return
                chunk_message = chunk['choices'][0]['delta'].get("content")
                # log.info("chunk_message = {}".format(chunk_message))
                if (chunk_message):
                    full_response += chunk_message
                    yield final, full_response
                if inStopMessages(user.user_id):
                    break

    def get_GPT_answer(self, model, new_query, is_stream):
        return openai.ChatCompletion.create(
            # model="gpt-3.5-turbo-0613",
            model=model,
            function_call="auto",
            functions=functions_definition,
            messages=new_query,

            temperature=model_conf(const.OPEN_AI).get("temperature", 0.8),
            # 熵值，在[0,1]之间，越大表示选取的候选词越随机，回复越具有不确定性，建议和top_p参数二选一使用，创意性任务越大越好，精确性任务越小越好
            # max_tokens=8100,  # 回复最大的字符数，为输入和输出的总数
            # top_p=model_conf(const.OPEN_AI).get("top_p", 0.7),,  #候选词列表。0.7 意味着只考虑前70%候选词的标记，建议和temperature参数二选一使用
            frequency_penalty=model_conf(const.OPEN_AI).get("frequency_penalty", 0.0),
            # [-2,2]之间，该值越大则越降低模型一行中的重复用词，更倾向于产生不同的内容
            presence_penalty=model_conf(const.OPEN_AI).get("presence_penalty", 1.0),
            # [-2,2]之间，该值越大则越不受输入限制，将鼓励模型生成输入中不存在的新词，更倾向于产生不同的内容
            stream=is_stream,
            timeout=5,
            # stop=["\n", "。", "？", "！"],
        )

    def get_GPT_function_call_answer(self, model, new_query, function_call, is_stream):
        new_query.append({
            "role": "assistant", "content": None, "function_call": function_call
        })

        function_name = function_call["name"]
        parameters = json.loads(function_call["arguments"])

        # call function
        content = detect_function_and_call(function_name, parameters)
        # log.info("content={}", content)

        new_query.append({
            "role": "function", "name": function_name, "content": content
        })

        return openai.ChatCompletion.create(
            model=model,
            functions=functions_definition,
            messages=new_query,

            temperature=model_conf(const.OPEN_AI).get("temperature", 0.8),
            frequency_penalty=model_conf(const.OPEN_AI).get("frequency_penalty", 0.0),
            presence_penalty=model_conf(const.OPEN_AI).get("presence_penalty", 1.0),
            stream=is_stream,
            timeout=5,
        )

    def menuList(self, arg):
        return [PreTrainDcoumnet(), QueryDcoumnet(), DocumentList(),
                CnblogsQueryDcoumnet(), CnblogsPreTrainDocument(),
                WxQueryDocument(), WxPreTrainDocument(), ClearMemory()]


class Session(object):
    @staticmethod
    def build_session_query(query, user_id, system_prompt, model=const.MODEL_GPT_35_TURBO):
        '''
        build query with conversation history
        e.g.  [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "assistant", "content": null,
                "function_call": {"name": "send_mail", "arguments":
                    {"mail": "", "msg": "The Los Angeles Dodgers won the World Series in 2020."}}},
            {"role": "user", "content": "Where was it played?"}
            {"role": "function", "name": "send_mail", "content": "Mail Sent!"}
        ]
        :param query: query content
        :param user_id: from user id
        :return: query content with conversaction
        '''

        max_tokens = get_max_token(model)
        session = user_session.get(user_id, [])
        if len(session) == 0:
            # system_prompt = model_conf(const.OPEN_AI).get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            user_session[user_id] = session
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        prompt_count = num_tokens_from_messages(session, model)
        while prompt_count > max_tokens:
            # pop first conversation (TODO: more accurate calculation)
            try:
                session.pop(1)
                session.pop(1)
                prompt_count = num_tokens_from_messages(session, model)
            except Exception as e:
                log.error(traceback.format_exc())
                break
        log.info("Prompt count:{}", prompt_count)
        return session

    @staticmethod
    def save_session(answer, sid, model=const.MODEL_GPT_35_TURBO):
        session = user_session.get(sid)
        max_tokens = get_max_token(model)
        if session:
            # append conversation
            gpt_item = {'role': 'assistant', 'content': answer}
            log.info("answer:{} Used tokens:{}".format(answer, num_tokens_from_string(answer)))
            session.append(gpt_item)
            # if used_tokens == 0:
            #     used_tokens = Session.count_words(session)
            #     log.info("Session:{} Used tokens:{}".format(session, used_tokens))
            while num_tokens_from_messages(session, model) > max_tokens:
                # pop first conversation (TODO: more accurate calculation)
                session.pop(1)
                session.pop(1)

    @staticmethod
    def clear_session(session_id):
        if session_id in user_session:
            user_session[session_id] = []

    @staticmethod
    def clear_session_by_user(user_id):
        # list all key
        for key in user_session.keys():
            # if key start with user_id
            if key.startswith(user_id):
                user_session[key] = []
                log.info("clear session:{}".format(key))
