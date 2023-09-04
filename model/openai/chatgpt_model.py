# encoding:utf-8
import datetime
import json
import os
import re
import subprocess
import tempfile
import time
import traceback

import openai
import tiktoken
from expiring_dict import ExpiringDict
from flask import request
from typing import List

from requests.exceptions import ChunkedEncodingError

import common.log
from common import const
from common import log
from common.db.conversation import Conversation
from common.db.function import Function
from common.db.query_record import QueryRecord
from common.db.user import User
from common.functions import num_tokens_from_messages, num_tokens_from_string, get_max_token
from common.menu_functions.function_call_library import detect_function_and_call
from model.openai.chat_session import Session
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


# OpenAI对话模型API (可用)
class ChatGPTModel(Model):
    STREAM_LOOP_BREAK_OUT_LIMIT = 100

    def __init__(self):
        openai.api_key = model_conf(const.OPEN_AI).get('api_key')
        proxy = model_conf(const.OPEN_AI).get('proxy')
        if proxy:
            openai.proxy = proxy

    def reply_text(self, context, retry_count=0):

        try:
            user: User = context['user']
            conversation_id = context['conversation_id']
            system_prompt = context['system_prompt']
            model = context['model']
            query = context['msg']
            functions_dict = Function.get_function_by_owner_and_function_id(user.user_id,
                                                                            context.get('function_call', None))
            # functions_definition 是functions_dict 的value或者none

            functions_definition = list(functions_dict.values()) if functions_dict else None
            functions_name = list(functions_dict | functions_dict.keys()) if functions_dict else None
            user_session_id = user.user_id + conversation_id

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
                prompt_count=0,
                complication_count=0,
                created_time=datetime.datetime.now(),
                updated_time=datetime.datetime.now(),
            )
            query_record.update_ip_location()
            query_record.set_query_trail(new_query)
            query_record.set_functions(functions_name)

            if query == '#清除记忆':
            # Session.clear_session(user_session_id)
                Session.clear_session(user_session_id)
                query_record.reply = "记忆已清除"
                query_record.save()
                return query_record

            log.info("[chatgpt]: model={} query={}", model, new_query)

            response = self.get_non_stream_full_response_for_one_question(model, new_query, functions_definition,
                                                                          query_record)
            reply_content = response.choices[0]['message']['content']

            end_time = time.time()  # 记录结束时间
            execution_time = end_time - start_time  # 计算执行时间
            log.info("[Execution Time] {:.4f} seconds", execution_time)  # 打印执行时间
            log.debug(response)
            # log.info("[CHATGPT] reply={}", reply_content)
            if reply_content:
                # save conversation
                Session.save_session(reply_content, user_session_id, model)
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
                query_record.reply = reply_content
                # query_record.complication_count = response['usage']['completion_tokens']
                # query_record.prompt_count = response['usage']['prompt_tokens']
                query_record.set_cost()
                query_record.save()
                User.update(available_balance=User.available_balance - query_record.cost).where(
                    User.id == user.id).execute()
            return query_record

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
            query_record.reply = "我连接不到网络，请稍后重试"
            query_record.save()
            return query_record
        except openai.error.Timeout as e:
            log.warn(e)
            log.warn("[CHATGPT] Timeout")
            query_record.reply = "我没有收到消息，请稍后重试"
            query_record.save()
            return query_record
        except Exception as e:
            # unknown exception
            log.exception(e)
            Session.clear_session_by_user(user_session_id)
            query_record.reply = "请再问我一次吧"
            query_record.save()
            return query_record

    async def reply_text_stream(self, context, retry_count=0):
        try:
            user: User = context['user']
            conversation_id = context['conversation_id']
            system_prompt = context['system_prompt']
            model = context['model']
            query = context['msg']
            functions_dict = Function.get_function_by_owner_and_function_id(user.user_id,
                                                                            context.get('function_call', None))
            # functions_definition 是functions_dict 的value或者none

            functions_definition = list(functions_dict.values()) if functions_dict else None
            functions_name = list(functions_dict | functions_dict.keys()) if functions_dict else None
            user_session_id = user.user_id + conversation_id
            new_query = Session.build_session_query(query, user_session_id, system_prompt, model=model)
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            query_record = QueryRecord(
                user_id=context['user'].user_id,
                conversation_id=context['conversation_id'],
                query=query,
                reply="",
                ip=ip,
                model_name=model,
                # prompt_count=num_tokens_from_messages(new_query, model) + num_tokens_from_string(
                #     str(functions_definition)),
                prompt_count=0,
                complication_count=0,
                created_time=datetime.datetime.now(),
                updated_time=datetime.datetime.now(),
            )
            query_record.update_ip_location()
            query_record.set_query_trail(new_query)
            query_record.set_functions(functions_name)
            if query == '#清除记忆':
            # Session.clear_session(user_session_id)
                Session.clear_session(user_session_id)
                query_record.reply = "记忆已清除"
                query_record.save()
                yield True , query_record
                return
            log.info("[chatgpt]: model={} query={}", model, new_query)

            async for final, reply in self.get_stream_full_response_for_one_question(user, model, new_query,
                                                                                     functions_definition,query_record):
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
                    query_record.complication_count = num_tokens_from_string(full_response)+query_record.complication_count
                    common.log.logger.info("Current query_record.complication_count={}".format(query_record.complication_count))
                    # query_record.set_cost()
                    # query_record.save()
                    # User.update(available_balance=User.available_balance - query_record.cost).where(
                    #     User.id == user.id).execute()
                    removeStopMessages(user.user_id)
                else:
                    query_record.reply= reply
                yield final, query_record


        except openai.error.RateLimitError as e:
            # rate limit exception
            log.warn(e)
            if retry_count < 1:
                query_record.reply = "[CHATGPT] Connection broken, 第{}次重试，等待{}秒".format(retry_count + 1, 5)
                query_record.save()
                yield False, query_record
                time.sleep(5)
                log.warn("[CHATGPT] RateLimit exceed, 第{}次重试".format(retry_count + 1))
                yield True, self.reply_text_stream(context, retry_count + 1)
            else:
                query_record.reply = "提问太快啦，请休息一下再问我吧"
                query_record.save()
                yield True, query_record
        except openai.error.APIConnectionError as e:
            log.warn(e)
            log.warn("[CHATGPT] APIConnection failed")
            query_record.reply = "我连接不到网络，请稍后重试"
            query_record.save()
            yield True, query_record
        except openai.error.Timeout as e:
            log.warn(e)
            log.warn("[CHATGPT] Timeout")
            query_record.reply = "我没有收到消息，请稍后重试"
            query_record.save()
            yield True, query_record
        except ChunkedEncodingError as e:
            log.warn(e)
            if retry_count < 1:
                wait_time = (retry_count + 1) * 5
                query_record.reply = "[CHATGPT] Connection broken, 第{}次重试，等待{}秒".format(retry_count + 1, wait_time)
                query_record.save()
                yield False, query_record
                log.warn("[CHATGPT] Connection broken, 第{}次重试，等待{}秒".format(retry_count + 1, wait_time))
                time.sleep(wait_time)
                yield True, self.reply_text_stream(context, retry_count + 1)
            else:
                query_record.reply = "我连接不到网络，请稍后重试"
                query_record.save()
                yield True, query_record
        except Exception as e:
            # unknown exception
            log.error(traceback.format_exc())
            Session.clear_session_by_user(user_session_id)
            query_record.reply = "请再问我一次吧"
            query_record.save()
            yield True, query_record

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

    def get_non_stream_full_response_for_one_question(self, model, new_query, functions_definition, query_record):
        is_stream = False
        response = self.get_GPT_answer(model, new_query, is_stream, functions_definition, query_record)
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
                response = self.get_GPT_function_call_answer(model, new_query, function_call, is_stream,
                                                             functions_definition, query_record)
            else:
                return response

    async def get_stream_full_response_for_one_question(self, user, model, new_query, functions_definition,
                                                        query_record):
        is_stream = True
        res = self.get_GPT_answer(model, new_query, is_stream, functions_definition, query_record)
        full_response = ""

        function_call = {
            "name": "",
            "arguments": "",
        }
        count = 0

        is_function_call = True

        while is_function_call:
            # log.info("count time: {}".format(count))
            # log.info("response No. {}: {}".format(count, res))
            count = count + 1
            chunk_count = 0
            for chunk in res:
                log.debug("query No. {}, chunk No.{}, {}".format(count, chunk_count, chunk))
                chunk_count = chunk_count + 1
                if "function_call" in chunk['choices'][0]['delta']:
                    function_call_flag = True
                    if "name" in chunk['choices'][0]['delta']["function_call"]:
                        function_call["name"] += chunk['choices'][0]['delta']["function_call"]["name"]
                    if "arguments" in chunk['choices'][0]['delta']["function_call"]:
                        function_call["arguments"] += chunk['choices'][0]['delta']["function_call"]["arguments"]
                    break
                if chunk.choices[0].finish_reason == "function_call":
                    if function_call_flag:
                        # log.info("function call={}", function_call)

                        res = self.get_GPT_function_call_answer(model, new_query, function_call, is_stream,
                                                                functions_definition, query_record)
                        function_call = {
                            "name": "",
                            "arguments": "",
                        }
                    break
                # if not chunk.get("content", None):
                #     continue]

                is_function_call = False

                if chunk["choices"][0]["finish_reason"] == "length":
                    full_response = full_response + " (The answer is too long to load, please try to separate " \
                                                    "your question or use the model supported more tokens.)"
                    yield True, full_response
                    return
                if chunk["choices"][0]["finish_reason"] == "content_filter":
                    yield True, full_response
                    return
                if chunk["choices"][0]["finish_reason"] == "stop":
                    # break
                    yield True, full_response
                    return
                chunk_message = chunk['choices'][0]['delta'].get("content")
                # log.info("chunk_message = {}".format(chunk_message))
                if chunk_message:
                    full_response += chunk_message
                    yield False, full_response
                if inStopMessages(user.user_id):
                    # break
                    yield True, full_response
                    return

            if count >= ChatGPTModel.STREAM_LOOP_BREAK_OUT_LIMIT:
                full_response = full_response + " (Your question maybe very complex, please ask separately.)"
                yield True, full_response
                return

    def get_GPT_answer(self, model, new_query, is_stream, functions_definition, query_record=None):
        openai_params = {
            'model': model,
            'messages': new_query,
            'temperature': model_conf(const.OPEN_AI).get("temperature", 0.8),
            'frequency_penalty': model_conf(const.OPEN_AI).get("frequency_penalty", 0.0),
            'presence_penalty': model_conf(const.OPEN_AI).get("presence_penalty", 1.0),
            'stream': is_stream,
            'timeout': 5,
        }

        if functions_definition is not None:
            openai_params['functions'] = functions_definition

        res = openai.ChatCompletion.create(**openai_params)
        query_record.set_query_trail(new_query)
        if is_stream:
            query_record.prompt_count = num_tokens_from_messages(new_query, model) + num_tokens_from_string(
                str(functions_definition)) + query_record.prompt_count
        else:
            query_record.prompt_count = res['usage']['prompt_tokens'] + query_record.prompt_count
            query_record.complication_count = res['usage']['completion_tokens'] + query_record.complication_count
        return res

    def get_GPT_function_call_answer(self, model, new_query, function_call, is_stream, functions_definition,
                                     query_record=None):
        new_query.append({
            "role": "assistant", "content": None, "function_call": function_call
        })

        function_name = function_call["name"]

        if is_stream:
            query_record.complication_count = num_tokens_from_string(
                function_name) + query_record.complication_count
            query_record.complication_count = num_tokens_from_string(function_call["arguments"]) + query_record.complication_count
            common.log.logger.info("Current query_record.complication_count={}".format(query_record.complication_count))

        if function_name == "python":
            content = "不允许执行定义函数之外的代码"
        else:
            parameters = json.loads(function_call["arguments"])
            # call function
            content = detect_function_and_call(function_name, parameters, functions_definition)
        # log.info("content={}", content)

        new_query.append({
            "role": "function", "name": function_name, "content": content
        })

        res = openai.ChatCompletion.create(
            model=model,
            functions=functions_definition,
            messages=new_query,

            temperature=model_conf(const.OPEN_AI).get("temperature", 0.8),
            frequency_penalty=model_conf(const.OPEN_AI).get("frequency_penalty", 0.0),
            presence_penalty=model_conf(const.OPEN_AI).get("presence_penalty", 1.0),
            stream=is_stream,
            timeout=5,
        )
        query_record.set_query_trail(new_query)
        if is_stream:
            query_record.prompt_count = num_tokens_from_messages(new_query, model) + num_tokens_from_string(
                str(functions_definition)) + query_record.prompt_count
        else:
            query_record.prompt_count = res['usage']['prompt_tokens'] + query_record.prompt_count
            query_record.complication_count = res['usage']['completion_tokens'] + query_record.complication_count
        return res

    # return openai.ChatCompletion.create(
    #         model=model,
    #         functions=functions_definition,
    #         messages=new_query,
    #
    #         temperature=model_conf(const.OPEN_AI).get("temperature", 0.8),
    #         frequency_penalty=model_conf(const.OPEN_AI).get("frequency_penalty", 0.0),
    #         presence_penalty=model_conf(const.OPEN_AI).get("presence_penalty", 1.0),
    #         stream=is_stream,
    #         timeout=5,
    #     )

    def menuList(self, arg):
        return [PreTrainDcoumnet(), QueryDcoumnet(), DocumentList(),
                CnblogsQueryDcoumnet(), CnblogsPreTrainDocument(),
                WxQueryDocument(), WxPreTrainDocument(), ClearMemory()]
