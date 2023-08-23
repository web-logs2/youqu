import azure.cognitiveservices.speech as speechsdk
import config
from common import const
from config import model_conf
import os
os.environ['AZURE_C_SHARED_LOG_LEVEL'] = 'LOG_INFO'

class AZURE:

    def __init__(self):
        config.load_config()
        self.speech_key = model_conf(const.AZURE).get('api_key')
        self.service_region = model_conf(const.AZURE).get('region')
        self.style = model_conf(const.AZURE).get('style')
        self.styledegree = model_conf(const.AZURE).get('styledegree')
        self.xml_lang = model_conf(const.AZURE).get('xml_lang')
        self.voice_name = model_conf(const.AZURE).get('voice_name')
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.service_region)
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    def synthesize_speech(self, text, style='chat', voice_name='zh-CN-XiaoxiaoNeural'):
        # 创建一个合成器实例

        # 设置语音合成参数
        ssml_string = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
                   xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{self.xml_lang}">
                <voice name="{self.voice_name}">
                    <mstts:express-as style="{self.style}" styledegree="{self.styledegree}">
                        <mstts:prosody rate="5.00%" rate-as="48kHz">
                            {text}
                        </mstts:prosody>
                    </mstts:express-as>
                </voice>
            </speak>'''

        # 执行语音合成并获取合成后的音频流
        speech_synthesis_result = self.speech_synthesizer.speak_ssml_async(ssml_string).get()

        # 保存音频流为 WAV 格式文件
        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = "{}_{}_{}.wav".format("output", text[:10], timestamp)
        # with open(filename, "wb") as f:
        #     f.write(speech_synthesis_result.audio_data)
        return speech_synthesis_result


# - Affectionate：感情风格，温柔感人；
# - Angry：愤怒风格，语气激烈，适合表达愤怒、不满等情感；
# - Assistant：助手风格，语调亲切、自然，适合交互式场景；
# - Calm：冷静风格，语调平稳、沉着，适合表达冷静、理智的情感；
# - Chat：闲聊风格，语气轻松、随意，适合互动式场景；
# - Cheerful：欢快风格，语调轻松愉快，适合表达开心的内容；
# - CustomerService：客服风格，语调专业、礼貌，适合客服场景；
# - Disgruntled：不满风格，语气不满、不悦，适合表达不满情感；
# - Fearful：恐惧风格，语气紧张、恐惧，适合表达害怕、紧张等情感；
# - Friendly：友好风格，语调亲切自然，适合传递亲密友好的情感；
# - Gentle：柔和风格，语调轻柔、温和，适合表达柔和、婉约的情感；
# - Lyrical：抒情风格，语气抒情、感性，适合表达抒情、感性的内容；
# - Newscast：新闻播报风格，语调正式、严肃，适合新闻播报场合；
# - Poetry-Reading：诗歌朗读风格，语调悠扬、诗意盎然，适合朗读诗歌；
# - Sad：悲伤风格，语调低沉哀怨，适合表达悲伤和忧郁的情感；
# - Serious：严肃风格，语调严谨庄重，适合表达严肃的内容，如新闻报道、公告等。


def loopTest():
    # Get text from the console and synthesize to the default speaker.
    print("Enter some text that you want to speak >")
    text = input()
    azure = AZURE()
    speech_synthesis_result = azure.synthesize_speech(text)

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")


def menuList(self, arg):
    return []
