import subprocess

from django.http import QueryDict
from django.shortcuts import render, HttpResponse
from pydub import AudioSegment
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os
import difflib
from django.views.decorators.csrf import csrf_exempt
import base64
import hashlib
import hmac
import json
import os
import time
from django.core import serializers
import requests
from app01 import models
import datetime as dt

lfasr_host = 'http://raasr.xfyun.cn/api'
# 请求的接口名
api_prepare = '/prepare'
api_upload = '/upload'
api_merge = '/merge'
api_get_progress = '/getProgress'
api_get_result = '/getResult'
# 文件分片大小10M
file_piece_sice = 10485760

# ——————————————————转写可配置参数————————————————
# 参数可在官网界面（https://doc.xfyun.cn/rest_api/%E8%AF%AD%E9%9F%B3%E8%BD%AC%E5%86%99.html）查看，根据需求可自行在gene_params方法里添加修改
# 转写类型
lfasr_type = 0
# 是否开启分词
has_participle = 'false'
has_seperate = 'true'
# 多候选词个数
max_alternatives = 0
# 子用户标识
suid = ''

# Create your views here.
# 将重点片段处理并得到文字

# 听力页面
uploadTime = []

# local development
# save_path = r'C:\Users\24482\Desktop\vue\origin'
# save_path_short = r'C:\Users\24482\Desktop\vue'
# file_name = '\listening.mp3'

# on the server
save_path = '/data/myproject/dajngo4/audioSegment/origin'
save_path_short = '/data/myproject/dajngo4/audioSegment'
file_name = 'listening.mp3'



@csrf_exempt
def tp(request):
    arr = request.POST.getlist('recordingTime[]')
    timeInDB = ','.join(arr)
    models.timePoints.objects.create(timePoints=timeInDB)
    return HttpResponse("upload success")





@csrf_exempt
def listenRecord(request):

    class Ws_Param(object):
        # 初始化
        def __init__(self, APPID, APIKey, APISecret, AudioFile):
            self.APPID = APPID
            self.APIKey = APIKey
            self.APISecret = APISecret
            self.AudioFile = AudioFile

            # 公共参数(common)
            self.CommonArgs = {"app_id": self.APPID}
            # 业务参数(business)，更多个性化参数可在官网查看
            self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1,
                                 "vad_eos": 10000}

        # 生成url
        def create_url(self):
            url = 'wss://ws-api.xfyun.cn/v2/iat'
            # 生成RFC1123格式的时间戳
            now = datetime.now()
            date = format_date_time(mktime(now.timetuple()))

            # 拼接字符串
            signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
            signature_origin += "date: " + date + "\n"
            signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
            # 进行hmac-sha256进行加密
            signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                     digestmod=hashlib.sha256).digest()
            signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

            authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
                self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
            # 将请求的鉴权参数组合为字典
            v = {
                "authorization": authorization,
                "date": date,
                "host": "ws-api.xfyun.cn"
            }
            # 拼接鉴权参数，生成url
            url = url + '?' + urlencode(v)
            # print("date: ",date)
            # print("v: ",v)
            # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
            # print('websocket url :', url)
            return url

    # 收到websocket消息的处理
    def on_message(ws, message):
        try:
            code = json.loads(message)["code"]
            sid = json.loads(message)["sid"]
            if code != 0:
                errMsg = json.loads(message)["message"]
                print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

            else:
                data = json.loads(message)["data"]["result"]["ws"]
                print('isinstance list', isinstance(data, list))
                wordsInSentence = []
                for segment in data:
                    for word in segment["cw"]:
                        wordsInSentence.append(word["w"])
                resultOneSentence = "".join(wordsInSentence)
                print('resultOneSentence\n', resultOneSentence)
                # add new adjustment to control the accuracy
                if (resultOneSentence != '.' and resultOneSentence != '。'):
                    listSentence.append(resultOneSentence)

                print("sid:%s call success!,data is:%s" % (sid, json.dumps(data, ensure_ascii=False)))


        except Exception as e:
            print("receive msg,but parse exception:", e)

    # 收到websocket错误的处理
    def on_error(ws, error):
        print("### error:", error)

    # 收到websocket关闭的处理
    def on_close(ws, a, b):
        print("### closed ###")

    # 收到websocket连接建立的处理
    def on_open(ws):
        def run(*args):
            frameSize = 8000  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

            with open(wsParam.AudioFile, "rb") as fp:
                while True:
                    buf = fp.read(frameSize)
                    # 文件结束
                    if not buf:
                        status = STATUS_LAST_FRAME
                    # 第一帧处理
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    if status == STATUS_FIRST_FRAME:

                        d = {"common": wsParam.CommonArgs,
                             "business": wsParam.BusinessArgs,
                             "data": {"status": 0, "format": "audio/L16;rate=16000",
                                      "audio": str(base64.b64encode(buf), 'utf-8'),
                                      "encoding": "raw"}}
                        d = json.dumps(d)
                        ws.send(d)
                        status = STATUS_CONTINUE_FRAME
                    # 中间帧处理
                    elif status == STATUS_CONTINUE_FRAME:
                        d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                      "audio": str(base64.b64encode(buf), 'utf-8'),
                                      "encoding": "raw"}}
                        ws.send(json.dumps(d))
                    # 最后一帧处理
                    elif status == STATUS_LAST_FRAME:
                        d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                      "audio": str(base64.b64encode(buf), 'utf-8'),
                                      "encoding": "raw"}}
                        ws.send(json.dumps(d))
                        time.sleep(1)
                        break
                    # 模拟音频采样间隔
                    time.sleep(intervel)
            ws.close()

        thread.start_new_thread(run, ())

    class SliceIdGenerator:
        """slice id生成器"""

        def __init__(self):
            self.__ch = 'aaaaaaaaa`'

        def getNextSliceId(self):
            ch = self.__ch
            j = len(ch) - 1
            while j >= 0:
                cj = ch[j]
                if cj != 'z':
                    ch = ch[:j] + chr(ord(cj) + 1) + ch[j + 1:]
                    break
                else:
                    ch = ch[:j] + 'a' + ch[j + 1:]
                    j = j - 1
            self.__ch = ch
            return self.__ch

    class RequestApi(object):
        def __init__(self, appid, secret_key, upload_file_path):
            self.appid = appid
            self.secret_key = secret_key
            self.upload_file_path = upload_file_path

        # 根据不同的apiname生成不同的参数,本示例中未使用全部参数您可在官网(https://doc.xfyun.cn/rest_api/%E8%AF%AD%E9%9F%B3%E8%BD%AC%E5%86%99.html)查看后选择适合业务场景的进行更换
        def gene_params(self, apiname, taskid=None, slice_id=None):
            appid = self.appid
            secret_key = self.secret_key
            upload_file_path = self.upload_file_path
            ts = str(int(time.time()))
            m2 = hashlib.md5()
            m2.update((appid + ts).encode('utf-8'))
            md5 = m2.hexdigest()
            md5 = bytes(md5, encoding='utf-8')
            # 以secret_key为key, 上面的md5为msg， 使用hashlib.sha1加密结果为signa
            signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
            signa = base64.b64encode(signa)
            signa = str(signa, 'utf-8')
            file_len = os.path.getsize(upload_file_path)
            file_name = os.path.basename(upload_file_path)
            param_dict = {}

            if apiname == api_prepare:
                # slice_num是指分片数量，如果您使用的音频都是较短音频也可以不分片，直接将slice_num指定为1即可
                slice_num = int(file_len / file_piece_sice) + (0 if (file_len % file_piece_sice == 0) else 1)
                param_dict['app_id'] = appid
                param_dict['signa'] = signa
                param_dict['ts'] = ts
                param_dict['file_len'] = str(file_len)
                param_dict['file_name'] = file_name
                param_dict['slice_num'] = str(slice_num)
            elif apiname == api_upload:
                param_dict['app_id'] = appid
                param_dict['signa'] = signa
                param_dict['ts'] = ts
                param_dict['task_id'] = taskid
                param_dict['slice_id'] = slice_id
            elif apiname == api_merge:
                param_dict['app_id'] = appid
                param_dict['signa'] = signa
                param_dict['ts'] = ts
                param_dict['task_id'] = taskid
                param_dict['file_name'] = file_name
            elif apiname == api_get_progress or apiname == api_get_result:
                param_dict['app_id'] = appid
                param_dict['signa'] = signa
                param_dict['ts'] = ts
                param_dict['task_id'] = taskid
            return param_dict

        # 请求和结果解析，结果中各个字段的含义可参考：https://doc.xfyun.cn/rest_api/%E8%AF%AD%E9%9F%B3%E8%BD%AC%E5%86%99.html
        def gene_request(self, apiname, data, files=None, headers=None):
            response = requests.post(lfasr_host + apiname, data=data, files=files, headers=headers)
            result = json.loads(response.text)
            print()
            if result["ok"] == 0:
                print("{} success:".format(apiname) + str(result))
                if apiname == '/getResult':
                    print('dict ==', isinstance(result, dict))
                    print('object ==', isinstance(result, object))
                    data = result
                    parsed_data = json.loads(data["data"])
                    # extract all the onebest values
                    onebest_values = [item["onebest"] for item in parsed_data]
                    resultOneSentence = "".join(onebest_values)
                    audioTxt[0] = resultOneSentence
                    print('resultOneSentence\n', resultOneSentence)
                return result
            else:
                print("{} error:".format(apiname) + str(result))
                exit(0)
                return result

        # 预处理
        def prepare_request(self):
            return self.gene_request(apiname=api_prepare,
                                     data=self.gene_params(api_prepare))

        # 上传
        def upload_request(self, taskid, upload_file_path):
            file_object = open(upload_file_path, 'rb')
            try:
                index = 1
                sig = SliceIdGenerator()
                while True:
                    content = file_object.read(file_piece_sice)
                    if not content or len(content) == 0:
                        break
                    files = {
                        "filename": self.gene_params(api_upload).get("slice_id"),
                        "content": content
                    }
                    response = self.gene_request(api_upload,
                                                 data=self.gene_params(api_upload, taskid=taskid,
                                                                       slice_id=sig.getNextSliceId()),
                                                 files=files)
                    if response.get('ok') != 0:
                        # 上传分片失败
                        print('upload slice fail, response: ' + str(response))
                        return False
                    print('upload slice ' + str(index) + ' success')
                    index += 1
            finally:
                'file index:' + str(file_object.tell())
                file_object.close()
            return True

        # 合并
        def merge_request(self, taskid):
            return self.gene_request(api_merge, data=self.gene_params(api_merge, taskid=taskid))

        # 获取进度
        def get_progress_request(self, taskid):
            return self.gene_request(api_get_progress, data=self.gene_params(api_get_progress, taskid=taskid))

        # 获取结果
        def get_result_request(self, taskid):
            return self.gene_request(api_get_result, data=self.gene_params(api_get_result, taskid=taskid))

        def all_api_request(self):
            # 1. 预处理
            pre_result = self.prepare_request()
            taskid = pre_result["data"]
            # 2 . 分片上传
            self.upload_request(taskid=taskid, upload_file_path=self.upload_file_path)
            # 3 . 文件合并
            self.merge_request(taskid=taskid)
            # 4 . 获取任务进度
            while True:
                # 每隔20秒获取一次任务进度
                progress = self.get_progress_request(taskid)
                progress_dic = progress
                if progress_dic['err_no'] != 0 and progress_dic['err_no'] != 26605:
                    print('task error: ' + progress_dic['failed'])
                    return
                else:
                    data = progress_dic['data']
                    task_status = json.loads(data)
                    if task_status['status'] == 9:
                        print('task ' + taskid + ' finished')
                        break
                    print('The task ' + taskid + ' is in processing, task status: ' + str(data))

                # 每次获取进度间隔20S
                time.sleep(20)
            # 5 . 获取结果
            self.get_result_request(taskid=taskid)

    def find_closest_match2(text, pattern):
        match_start = text.find(pattern)
        if match_start == -1:
            return ''
        match_end = match_start + len(pattern)
        # 扩展匹配范围到完整单词
        while match_start > 0 and text[match_start - 1] != ' ':
            match_start -= 1
        while match_end < len(text) and text[match_end] != ' ':
            match_end += 1
        return text[match_start:match_end]

    def find_most_similar(text, target):
        max_similarity = 0
        most_similar = ""
        for i in range(len(text) - len(target) + 1):
            substr = text[i:i + len(target)]
            similarity = difflib.SequenceMatcher(None, substr, target).ratio()
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = substr
        #  还有比对全部句子
        res = find_closest_match2(text, most_similar)
        return res

    print('upload_audio', request.FILES['audiofile'])
    audio_file = request.FILES['audiofile']
    # linux
    with open(f'{save_path}/{file_name}', 'wb') as destination:
        for chunk in audio_file.chunks():
            destination.write(chunk)

     # windows
     # with open(f'{save_path}\\{file_name}', 'wb') as destination:
    audio = AudioSegment.from_file(
        save_path+"/"+file_name,
        "mp3")
    # Define the start and end times for each segment in milliseconds

    # get the segments from the front end
    # two for each pair
    arr = models.timePoints.objects.last().timePoints
    timeInDB = arr.split(',')
    print(timeInDB)
    timeInDB = list(map(float, timeInDB))
    for i in timeInDB:
        print('i',i,type(i))

    segments = [(timeInDB[i], timeInDB[i + 1]) for i in range(0, len(timeInDB), 2)]

    uploadTime = segments
    print('timePoints = ', uploadTime)
    for i, segment_pair in enumerate(segments):
        start_time = int(segment_pair[0])  # 起始时间
        end_time = int(segment_pair[1])  # 结束时间
        segmented_audio = audio[start_time:end_time]
        segmented_audio.export(
            save_path_short+"/segment-{}.mp3".format(
                i), format="mp3")

    folder_path = save_path_short
    # 获取文件夹中所有文件的名称
    file_names = os.listdir(folder_path)
    # 构造文件的绝对路径
    file_paths = [os.path.join(folder_path, file_name) for file_name in file_names if file_name.endswith('.mp3')]
    print(file_paths)

    number = 0
    for eachFilePath in file_paths:
        input_file = eachFilePath
        outputFIle = save_path_short+ '/short' + format(
            number) + ".pcm"
        print('eachFilePath', eachFilePath, outputFIle)
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_file, "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "8000", outputFIle])
        number = number + 1
    print('finish the task of segment and transfer')
    # 小短音频开始上传  分割
    STATUS_FIRST_FRAME = 0  # 第一帧的标识
    STATUS_CONTINUE_FRAME = 1  # 中间帧标识
    STATUS_LAST_FRAME = 2  # 最后一帧的标识

    print('MMMMMMMEEEEE',request.method)
    if request.method == 'POST':
        nowTime = dt.datetime.now().strftime('%F')
        models.allMandD.objects.create(nameOfRadio="test", date=nowTime, timePoints=timeInDB)
    #     return HttpResponse('success POST')
    # if request.method == 'GET':
        tp = models.allMandD.objects.last()
        print("from databases",tp)
        timeback = tp

        # for tpp in tp:
        #     timeback.append(tpp.timePoints)

        print("111111111111111", timeback.timePoints)
        audioTxt = [""]

        api = RequestApi(appid="5d7e830d",
                         secret_key="84a6873c3f5b7cc198ab943a710303de",
                         upload_file_path=save_path+"/listening.mp3")
        api.all_api_request()
#         audioTxt[0] = "  Listen to part of a lecture in a marketing class. Now it's not uncommon to see a celebrity advertising a product, right? A popular basketball player endorsing shoes, a beautiful actress selling shampoo. Marketers use the appeal of that person to sell their products. Another tactic is to use art in advertising. This is called art infusion. The idea of art infusion is that when a piece of arts associated with a product, sum of its qualities or prestige spills over onto the product and actually changes how consumers evaluate it. We've long assumed this to be the case, but it was never studied systematically until recently. When two university researchers designed some experiments to test the phenomenon. But before I describe those studies, let's talk about how we're defining art because of course the question of what art really is has been debated by philosophers for centuries. But this isn't a philosophy class for our purposes, art is what the consumer says it is to define art for their experiments. The researchers conducted some screenings where they asked people to evaluate whether they considered an image to be art or not. In general, they found that people considered images representing what we might call expression for its own sake, work without any additional function to be art. But they were also more likely to read an images art if they thought creating it involved skill. If they couldn't do it, for example, sofor their first experiment, the researchers uh first look to see how the public would respond to paintings versus photos. So they ask 20 people to rate two images with similar content side by side. 1, a painting of an outdoor cafe by a famous artist Vincent van Gogh. andThe other a photograph of an outdoor cafe. And they found that the famous painting was much more likely to be viewed as art than the photograph. So then each image, the painting and the photograph was printed on the lid of a black velvet box so that the the two boxes were identical, except for the image. And then the researchers introduced the product silverware. The researchers showed the set of silverware to customers at a restaurant. The silverware was the same each time, but half the customer saw it presented in the box with the painting and the other half saw it in the box with the photograph. The image on the lid was visible before the box was opened. Then the customers were asked to give a general rating of the product. Did they like it or not? And also to rated in terms of its perceived status or prestige and the results showed that the silverware was consistently rated higher on both counts when it was presented in the box with the painting. soThis first experiment supported the art infusion effect. Something about that painting status as art seemed to positively affect the silver wears ratings. But what's especially helpful about this experiment is that it was conducted in a crowded restaurant, not in a lab. So it basically reproduced the same level of distraction that consumers experience when evaluating actual products in the marketplace. That degree of realism says a lot about the accuracy of these results in my opinion. Okay. Then the researchers wanted to find out the content of a painting mattered. Or was it just enough that it was a work of art? soThey conducted a second experiment using three images, too famous paintings and one photograph pre experiment screenings identified the paintings as art and the photograph as non art. ohThe screenings also identified the content of the paintings as either positive or negative. One painting had positive content, buildings overlooking a canal, and one had negative content, burning buildings on the banks of a river. The photograph had similar content to the positive art image to replicate the first study. Each of these three images was placed on an identical bottle of hand soap, and each soap was then rated by participants. wellAs with the silverware, the product with the non art image was the lowest rated. But more interesting is the fact that the soap with the negative content image, the painting of the fire was rated just as high as the one with the positive canal scene. This suggests that the art infusion effect is content independent that is regardless of what the subject of that art actually is, product ratings are positively affected by association with an art image. "
#         audioTxt[0] = \
# "  Listen to part of a lecture in a marketing class. Now it's not uncommon to see a celebrity advertising a product, right? A popular basketball player endorsing shoes, a beautiful actress selling shampoo. Marketers use the appeal of that person to sell their products. Another tactic is to use art in advertising. This is called art infusion. The idea of art infusion is that when a piece of arts associated with a product, sum of its qualities or prestige spills over onto the product and actually changes how consumers evaluate it. We've long assumed this to be the case, but it was never studied systematically until recently. When two university researchers designed some experiments to test the phenomenon. But before I describe those studies, let's talk about how we're defining art because of course the question of what art really is has been debated by philosophers for centuries. But this isn't a philosophy class for our purposes, art is what the consumer says it is to define art for their experiments. The researchers conducted some screenings where they asked people to evaluate whether they considered an image to be art or not. In general, they found that people considered images representing what we might call expression for its own sake, work without any additional function to be art. But they were also more likely to raid in images art if they thought creating it involved skill. If they couldn't do it, for example, sofor their first experiment, the researchers first looked to see how the public would respond to paintings versus photos. So they asked 20 people to rate two images with similar content side by side. 1, a painting of an outdoor cafe by a famous artist Vincent van Gogh. andThe other a photograph of an outdoor cafe. And they found that the famous painting was much more likely to be viewed as art than the photograph. So then each image, the painting and the photograph was printed on the lid of a black velvet box so that the the two boxes were identical, except for the image. And then the researchers introduced the product silverware. The researchers showed the set of silverware to customers at a restaurant. The silverware was the same each time, but half the customer saw it presented in the box with the painting and the other half saw it in the box with the photograph. The image on the lid was visible before the box was opened. Then the customers were asked to give a general rating of the product. Did they like it or not? And also to read it in terms of its perceived status or prestige and the results showed that the silverware was consistently rated higher on both counts when it was presented in the box with the painting. soThis first experiment supported the art infusion effect. Something about that painting status as art seemed to positively affect the silver wears ratings. But what's especially helpful about this experiment is that it was conducted in a crowded restaurant, not in a lab. So it basically reproduced the same level of distraction that consumers experience when evaluating actual products in the marketplace. That degree of realism says a lot about the accuracy of these results in my opinion. Okay. Then the researchers wanted to find out the content of a painting mattered. Or was it just enough that it was a work of art? soThey conducted a second experiment using three images, too famous paintings and one photograph pre experiment screenings identified the paintings as art and the photograph as non art. ohThe screenings also identified the content of the paintings as either positive or negative. One painting had positive content, buildings overlooking a canal, and one had negative content, burning buildings on the banks of a river. The photograph had similar content to the positive art image to replicate the first study. Each of these three images was placed on an identical bottle of hand soap, and each soap was then rated by participants. wellAs with the silverware, the product with the non art image was the lowest rated. But more interesting is the fact that the soap with the negative content image, the painting of the fire was rated just as high as the one with a positive canal seen. This suggests that the art infusion effect is content independent that is regardless of what the subject of that art actually is, product ratings are positively affected by association with an art image. "
#         # print('aaa', audioTxt)
        listSentence = []



        # 获取文件夹中所有文件的名称
        file_names = os.listdir(folder_path)
        print('folder_path', file_names)
        # 构造文件的绝对路径
        file_paths = [os.path.join(folder_path, file_name) for file_name in file_names if file_name.endswith('.pcm')]


        print('file_paths', file_paths)
        for eachFilePath in file_paths:
            wsParam = Ws_Param(APPID='5d7e830d', APISecret='NGRjOGQxM2YwNDk5NmJlNjY2MmVlOGI1',
                               APIKey='3eab84c8f7558107f128fd4afb4fea35',
                               AudioFile=eachFilePath)
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()
            ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            print('Key words dictSentence', listSentence)
        # temporary use
        # listSentence = ["really appreciate you taking the time to talk to me, professor, ",
        #                 'got from my assistant said you have some questions, something', 'wellkind of when I talk to your assistant,',
        #                 "ohYes, that's right. soYou're writing about an astronomer.", 'course and our assignments to write a biographical feature']

        mostSimilar = []
        countInMostSimilar = 0
        print('listSentence', listSentence)
        for i in listSentence:
            most_similar = find_most_similar(audioTxt[0], i)
            print('|origin|', i, '|deal the similarity|', most_similar)
            if (most_similar != ''):
                mostSimilar.append(most_similar)
                countInMostSimilar = countInMostSimilar + 1
            else:
                print('we lose the ', countInMostSimilar)
                countInMostSimilar = countInMostSimilar + 1

        print('ffffffmostSimilar = ', mostSimilar)
        print('ffffffTIME = ', request.POST.getlist('recordingTime[]'))
        print('ffffffmethod = ', request.method)

        # # deal with the string similarity
        # # listSentence includes the keywords

        # # if we do not have listen the audio before

        detailsThisTime = {
            "name": "audio.mp3",
            "keywords": listSentence
        }
        print('detailsThisTime = ', detailsThisTime)

        print('listSentence======', listSentence)
        print( "timePoints222222",timeInDB)
        json_data = json.dumps(timeInDB)
        return render(request, "listenRecord.html",
                      {
                          'keywords': mostSimilar,
                          'timePoint': uploadTime,
                          "details": mostSimilar,
                          "audioTxt": audioTxt[0],
                          "timePoints": json_data
                      })
        # return HttpResponse('success GET')

def startListening(request):
    # audioTxt ="But this isn't a philosophy class for our purposes, art is what the consumer says it is to define art for their experiments. The researchers conducted some screenings where they asked people to evaluate whether they considered an image to be art or not. In general, they found that people considered images representing what we might call expression for its own sake, work without any additional function to be art. But they were also more likely to read an images art if they thought creating it involved skill. If they couldn't do it, for example, sofor their first experiment, the researchers uh first look to see how the public would respond to paintings versus photos. So they ask 20 people to rate two images with similar content side by side. 1, a painting of an outdoor cafe by a famous artist Vincent van Gogh. andThe other a photograph of an outdoor cafe. And they found that the famous painting was much more likely to be viewed as art than the photograph. So then each image, the painting and the photograph was printed on the lid of a black velvet box so that the the two boxes were identical, except for the image. And then the researchers introduced the product silverware. The researchers showed the set of silverware to customers at a restaurant. The silverware was the same each time, but half the customer saw it presented in the box with the painting and the other half saw it in the box with the photograph. The image on the lid was visible before the box was opened. Then the customers were asked to give a general rating of the product. Did they like it or not? And also to rated in terms of its perceived status or prestige and the results showed that the silverware was consistently rated higher on both counts when it was presented in the box with the painting. soThis first experiment supported the art infusion effect. Something about that painting status as art seemed to positively affect the silver wears ratings. But what's especially helpful about this experiment is that it was conducted in a crowded restaurant, not in a lab. So it basically reproduced the same level of distraction that consumers experience when evaluating actual products in the marketplace. That degree of realism says a lot about the accuracy of these results in my opinion. Okay. Then the researchers wanted to find out the content of a painting mattered. Or was it just enough that it was a work of art? soThey conducted a second experiment using three images, too famous paintings and one photograph pre experiment screenings identified the paintings as art and the photograph as non art. ohThe screenings also identified the content of the paintings as either positive or negative. One painting had positive content, buildings overlooking a canal, and one had negative content, burning buildings on the banks of a river. The photograph had similar content to the positive art image to replicate the first study. Each of these three images was placed on an identical bottle of hand soap, and each soap was then rated by participants. wellAs with the silverware, the product with the non art image was the lowest rated. But more interesting is the fact that the soap with the negative content image, the painting of the fire was rated just as high as the one with a positive canal scene. This suggests that the art infusion effect is content independent that is regardless of what the subject of that art actually is, product ratings are positively affected by association with an art image."

    return render(request, "startListening.html", {})


@csrf_exempt
def histortyRecord(request):
    print('request.method when historyRecord', request.method)
    if request.method == 'POST':
        detailsInDB = request.POST.getlist('detailsOnce')
        nameInDB = request.POST.getlist('nameOfAudio')
        keyWord = request.POST.getlist('detailsWord')
        nowTime = dt.datetime.now().strftime('%F')

        print('keyWord', keyWord)
        a = 0
        for obj in detailsInDB:
            print("obj", obj)
            print("keyWord[a]", keyWord[a])
            models.allMistakesNew.objects.create(nameOfRadio=nameInDB[0], date=nowTime, details=obj, keyword=keyWord[a])
            a = a + 1
        confirmData = models.allMistakesNew.objects.all()
        # print(confirmData)
        for x in confirmData:
            print(x)
        confirmData = serializers.serialize("json", confirmData)
        print("666", confirmData)
        confirmData = json.loads(confirmData)
        fields = [item['fields'] for item in confirmData]
        print(fields)
        print(confirmData)
        return render(request, "histortyRecord.html", {'confirmData': fields})
    if request.method == 'GET':
        confirmData = models.allMistakesNew.objects.all()
        # print(confirmData)
        for x in confirmData:
            print(x)
        confirmData = serializers.serialize("json", confirmData)
        print("666", confirmData)
        confirmData = json.loads(confirmData)
        fields = [item['fields'] for item in confirmData]
        print(fields)
        print(confirmData)
        return render(request, "histortyRecord.html", {'confirmData': fields})


def aiAna(request):
    def get_rhymes(word):
        response = requests.get(f'https://api.datamuse.com/words?rel_rhy={word}')
        count = 0
        for word in json.loads(response.text):
            print(word)
            if count > 5:
                break
            if word['score'] > 10:
                count = count + 1
                rhyming_words.append(word['word'])
                models.AiWordsTrial.objects.create(linkWord=word['word'])
        print('once', rhyming_words)
        return rhyming_words

    # aiwords = models.allMistakesNew.objects.all().values('keyword')
    # rhyming_words = []
    # deduplication = {''}
    # for each in aiwords:
    #     if each['keyword'] in deduplication:
    #         continue
    #     else:
    #         deduplication.add(each['keyword'])
    #         get_rhymes(each['keyword'])

    returnwords = models.AiWordsTrial.objects.all()
    print('returnwords', returnwords)
    return render(request, "aiAna.html", {'similarWords': returnwords})


def getStart(request):
    print('hihi',request.GET)
    return render(request, 'getStart.html')


from django.http import JsonResponse

@csrf_exempt
def upload_audio(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        folder = request.POST.get('folder')
        # 在指定文件夹内创建文件
        with open(f'/data/myproject/dajngo4/audio_from_usr', 'wb') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)

        return JsonResponse({'message': '服务器：音频上传成功'})
    else:
        return JsonResponse({'message': '服务器：无效的请求'}, status=400)



