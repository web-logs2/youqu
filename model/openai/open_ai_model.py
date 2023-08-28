# encoding:utf-8

import time

import openai

from common import const
from common import log
from config import model_conf
from model.model import Model
from model.openai.chat_session import Session

user_session = dict()


# OpenAI对话模型API (可用)
class OpenAIModel(Model):
    def __init__(self):
        openai.api_key = model_conf(const.OPEN_AI).get('api_key')

    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            log.info("[OPEN_AI] query={}".format(query))
            from_user_id = context['from_user_id']
            if query == '#清除记忆':
                Session.clear_session(from_user_id)
                return '记忆已清除'

            new_query = Session.build_session_query(query, from_user_id)
            log.debug("[OPEN_AI] session query={}".format(new_query))
            reply_content = self.reply_text(new_query, from_user_id, 0)
            log.debug("[OPEN_AI] new_query={}, user={}, reply_cont={}".format(new_query, from_user_id, reply_content))
            if reply_content and query:
                Session.save_session(query, reply_content, from_user_id)
            return reply_content
        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def _process_reply_stream(
            self,
            query: str,
            reply: dict,
            user_id: str
    ) -> str:
        full_response = ""
        for response in reply:
            if response.get("choices") is None or len(response["choices"]) == 0:
                raise Exception("OpenAI API returned no choices")
            if response["choices"][0].get("finish_details") is not None:
                break
            if response["choices"][0].get("text") is None:
                raise Exception("OpenAI API returned no text")
            if response["choices"][0]["text"] == "<|endoftext|>":
                break
            yield response["choices"][0]["text"]
            full_response += response["choices"][0]["text"]
        if query and full_response:
            Session.save_session(query, full_response, user_id)

    def create_img(self, context, retry_count=0):
        try:
            query = context['msg']
            log.info("[OPEN_AI] image_query={}".format(query))
            response = openai.Image.create(
                prompt=query,  # 图片描述
                n=1,  # 每次生成图片的数量
                size="1024x1024",  # 图片大小,可选有 256x256, 512x512, 1024x1024
                response_format="b64_json"
            )
            # image_url = response['data'][0]['url']
            image_base64 = response['data'][0]['b64_json']
            log.debug("[OPEN_AI] image={}".format(image_base64))
            return image_base64
        except openai.error.RateLimitError as e:
            log.warn(e)
            if retry_count < 1:
                time.sleep(5)
                log.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.reply_text(query, retry_count + 1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            log.exception(e)
            return None
