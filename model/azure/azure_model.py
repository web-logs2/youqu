import os
import time

import requests

from common import const
from common.log import logger
from config import model_conf

os.environ['AZURE_C_SHARED_LOG_LEVEL'] = 'LOG_INFO'

import azure.cognitiveservices.speech as speechsdk


class BinaryFileReaderCallback(speechsdk.audio.PullAudioInputStreamCallback):
    def __init__(self, filename: str):
        super().__init__()
        self._file_h = open(filename, "rb")

    def read(self, buffer: memoryview) -> int:
        print('trying to read {} frames'.format(buffer.nbytes))
        try:
            size = buffer.nbytes
            frames = self._file_h.read(size)

            buffer[:len(frames)] = frames
            print('read {} frames'.format(len(frames)))

            return len(frames)
        except Exception as ex:
            print('Exception in `read`: {}'.format(ex))
            raise

    def close(self) -> None:
        print('closing file')
        try:
            self._file_h.close()
        except Exception as ex:
            print('Exception in `close`: {}'.format(ex))
            raise


def compressed_stream_helper(compressed_format,
                             webm_file_path,
                             default_speech_auth):
    callback = BinaryFileReaderCallback(webm_file_path)
    stream = speechsdk.audio.PullAudioInputStream(stream_format=compressed_format, pull_stream_callback=callback)

    speech_config = speechsdk.SpeechConfig(**default_speech_auth)
    audio_config = speechsdk.audio.AudioConfig(stream=stream)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    done = False

    def stop_cb(evt):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
    speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

    speech_recognizer.stop_continuous_recognition()


def pull_audio_input_stream_compressed_webm(webm_file_path: str,
                                            default_speech_auth):
    # Create a compressed format
    compressed_format = speechsdk.audio.AudioStreamFormat(
        compressed_stream_format=speechsdk.AudioStreamContainerFormat.OGG_OPUS)
    compressed_stream_helper(compressed_format, webm_file_path, default_speech_auth)


class AZURE:
    def __init__(self):
        self.speech_key = model_conf(const.AZURE).get('api_key')
        self.service_region = model_conf(const.AZURE).get('region')
        self.style = model_conf(const.AZURE).get('style')
        self.styledegree = model_conf(const.AZURE).get('styledegree')
        self.xml_lang = model_conf(const.AZURE).get('xml_lang')
        self.voice_name = model_conf(const.AZURE).get('voice_name')

    def speech_recognize_through_api(self, file_name):

        url = f'https://{self.service_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken'

        # 获取访问令牌
        headers = {
            'Ocp-Apim-Subscription-Key': self.speech_key
        }
        response = requests.post(url, headers=headers)
        access_token = response.text

        # 使用访问令牌调用语音识别API
        speech_api_url = f'https://{self.service_region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={self.xml_lang}'

        with open(file_name, 'rb') as audio_file:
            audio_data = audio_file.read()

        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'audio/wav'
        }
        response = requests.post(speech_api_url, headers=headers, data=audio_data)
        if response.status_code != 200:
            logger.error("response status code: "+str(response.status_code))
            logger.error("response content: "+str(response.content))
            return ""
        result = response.json()
        logger.info("Recognized: {}".format(result['DisplayText']))
        return result['DisplayText']

    # def synthesize_speech(self, text, style='chat', voice_name='zh-CN-XiaoxiaoNeural'):
    #     # 创建一个合成器实例
    #
    #     # 设置语音合成参数
    #     ssml_string = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
    #                xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{self.xml_lang}">
    #             <voice name="{self.voice_name}">
    #                 <mstts:express-as style="{self.style}" styledegree="{self.styledegree}">
    #                     <mstts:prosody rate="5.00%" rate-as="48kHz">
    #                         {text}
    #                     </mstts:prosody>
    #                 </mstts:express-as>
    #             </voice>
    #         </speak>'''
    #
    #     # 执行语音合成并获取合成后的音频流
    #     speech_synthesis_result = self.speech_synthesizer.speak_ssml_async(ssml_string).get()
    #
    #     # 保存音频流为 WAV 格式文件
    #     # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    #     # filename = "{}_{}_{}.wav".format("output", text[:10], timestamp)
    #     # with open(filename, "wb") as f:
    #     #     f.write(speech_synthesis_result.audio_data)
    #     return speech_synthesis_result

    def speech_recognized(self, file_name):
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.service_region)
        audio_config = speechsdk.audio.AudioConfig(filename=file_name)
        # Creates a speech recognizer using a file as audio input, also specify the speech language

        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, language=self.xml_lang, audio_config=audio_config)

        # Starts speech recognition, and returns after a single utterance is recognized. The end of a
        # single utterance is determined by listening for silence at the end or until a maximum of 15
        # seconds of audio is processed. It returns the recognition text as result.
        # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
        # shot recognition like command or query.
        # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
        result = speech_recognizer.recognize_once()

        # Check the result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logger.info("Recognized: {}".format(result.text))
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            logger.info("No speech could be recognized: {}".format(result.no_match_details))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.info("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.info("Error details: {}".format(cancellation_details.error_details))
        return ""


azure = AZURE()


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
