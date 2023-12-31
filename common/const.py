# channel

from decimal import Decimal

TERMINAL = "terminal"
WECHAT = "wechat"
WECHAT_MP = "wechat_mp"
WECHAT_MP_SERVICE = "wechat_mp_service"
QQ = "qq"
GMAIL = "gmail"
TELEGRAM = "telegram"
SLACK = "slack"
HTTP = "http"

# model
OPEN_AI = "openai"
CHATGPT = "chatgpt"
AZURE = "azure"

BAIDU = "baidu"
BING = "bing"

# db
MYSQL = "mysql"

MODEL_TEXT_ADA_001 = "text-ada-001"
MODEL_TEXT_BABBAGE_001 = "text-babbage-001"
MODEL_TEXT_BABBAGE = "text-babbage"
MODEL_TEXT_CURIE_001 = "text-curie-001"
MODEL_TEXT_DAVINCI_003 = "text-davinci-003"

MODEL_GPT_35_TURBO = "gpt-3.5-turbo"
MODEL_GPT_35_TURBO_0301 = "gpt-3.5-turbo-0301"
MODEL_GPT4_8K = "gpt-4"
MODEL_GPT4_32K = "gpt-4-32k"
MODEL_GPT4_0314 = "gpt-4-0314"
MODEL_GPT_35_turbo_16K = "gpt-3.5-turbo-16k"
USD_TO_CNY = 7.2
INITIAL_BALANCE = 5

cost_magnification = 1.5

MODEL_GPT_35_TURBO_COMPLETION_PRICE = Decimal(0.002 / 1000 * USD_TO_CNY * cost_magnification)
MODEL_GPT_35_TURBO_PROMPT_PRICE = Decimal(0.0015 / 1000 * USD_TO_CNY * cost_magnification)

MODEL_GPT_35_TURBO_16K_COMPLETION_PRICE = Decimal(0.004 / 1000 * USD_TO_CNY * cost_magnification)
MODEL_GPT_35_TURBO_16K_PROMPT_PRICE = Decimal(0.003 / 1000 * USD_TO_CNY * cost_magnification)

MODEL_GPT_4_COMPLETION_PRICE = Decimal(0.06 / 1000 * USD_TO_CNY * cost_magnification)
MODEL_GPT_4_PROMPT_PRICE = Decimal(0.03 / 1000 * USD_TO_CNY * cost_magnification)

BOT_SYSTEM_PROMPT = "你是一个人工智能音响，你回复的所有文字都会被转成语音，请尽量用汉语回答所有的问题。除非明确要求你说英语。"

EMAIL_SENDER = "no-reply@youqu.app"
EMAIL_SENDER_NAME = "YouQu"
EMAIL_TEMPLATE_RESET_PASSWORD = "d-a054f2d7236d4ee7be847308bbbfc5f0"
EMAIL_TEMPLATE_VERIFY_CODE = "d-92a43b8451ab467bb05a9c131a5960e1"

YU_ER_BU_ZU = "余额不足，请及时充值。"
YU_ER_BU_ZU_EN = "Insufficient balance, please recharge in time."

MIN_GAN_CI = "您的发言包含敏感词，请注意言行。"
MIN_GAN_CI_EN = "Your speech contains sensitive words, please pay attention to your words and deeds."

ZUIXIAO_CHONGZHI = "亲，最小充值金额0.01元"
ZUIDA_CHONGZHI = "土豪，最大充值金额10000元"
INVALID_INPUT = "无效输入"
