# encoding:utf-8
import traceback

from expiring_dict import ExpiringDict

from common import const
from common import log
from common.functions import num_tokens_from_messages, num_tokens_from_string, get_max_token
from config import model_conf

if model_conf(const.OPEN_AI).get('expires_in_seconds'):
    user_session = ExpiringDict(model_conf(const.OPEN_AI).get('expires_in_seconds'))
    # logging.info("Set dict expire time "+model_conf(const.OPEN_AI).get('expires_in_seconds'))
else:
    user_session = ExpiringDict(3600)

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
