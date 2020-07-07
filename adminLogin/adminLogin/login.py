from django.http import HttpResponse
import requests
import json
from django.views.decorators.csrf import csrf_exempt
import time
from django.core import signing
import hashlib
from django.core.cache import cache

HEADER = {'typ': 'JWP', 'alg': 'default'}
TIME_OUT = 30 * 60  # 30min


def encrypt(obj):
    """encrypt"""
    value = signing.dumps(obj)
    value = signing.b64_encode(value.encode()).decode()
    return value


def decrypt(src):
    """decrypt"""
    src = signing.b64_decode(src.encode()).decode()
    raw = signing.loads(src)
    return raw


def create_token(username):
    """create token"""
    # 1. encrypt header
    header = encrypt(HEADER)
    # 2. encrypt Payload
    payload = {"username": username, "iat": time.time()}
    payload = encrypt(payload)
    # 3. create signature
    md5 = hashlib.md5()
    md5.update(("%s.%s" % (header, payload)).encode())
    signature = md5.hexdigest()
    token = "%s.%s.%s" % (header, payload, signature)
    # store in cache
    cache.set(username, token, TIME_OUT)
    return token


def get_payload(token):
    payload = str(token).split('.')[1]
    payload = decrypt(payload)
    return payload


# get username with token
def get_username(token):
    payload = get_payload(token)
    return payload['username']
    pass


def check_token(token):
    try:
        username = get_username(token)
        last_token = cache.get(username)
        if last_token:
            return last_token == token
        return False
    except:
        return False

@csrf_exempt
def loginFit(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        # get username and password
        name = request_dict.get('username')
        psd = request_dict.get('password')

        r = requests.post(
            'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
        access_token = r.json()['access_token']
        datas = json.dumps({"env": "emss1-7y7xp", "query": "db.collection(\"administratorInfo\").get()"})
        r = requests.post('https://api.weixin.qq.com/tcb/databasequery?access_token=' + access_token, data=datas)
        result = r.json()['data']
        # compare the username and password
        status = '0'
        for res in result:
            admin = json.loads(res)
            if name == admin['username'] and psd == admin['password']:
                status = '1'
                break
        token = ''
        if status == '1':
            # create token
            token = create_token(name)
        data = {'status': status, 'token': token}
        login_info = json.dumps(data)
        return HttpResponse(login_info, content_type='application/json')


def hello(request):
    return HttpResponse("Hello world ! ")

@csrf_exempt
def changePassword(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        if check_token(my_token):
            # token is correct
            username = request_dict.get('username')
            if username != get_username(my_token):
                # username doesn't fit with the token
                status = '-1'
                return HttpResponse(json.dumps({"status": status}), content_type="application/json")
            oldpsd = request_dict.get('oldpassword')
            newpsd = request_dict.get('newpassword')
            r = requests.post(
                'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
            access_token = r.json()['access_token']
            datas = json.dumps({"env": "emss1-7y7xp", "query": "db.collection(\"administratorInfo\").get()"})
            r = requests.post('https://api.weixin.qq.com/tcb/databasequery?access_token=' + access_token, data=datas)
            result = r.json()['data']
            status = '-1'
            for res in result:
                admin = json.loads(res)
                # find the record with the same usename and password
                if username == admin['username'] and oldpsd == admin['password']:
                    status = '1'
                    id= admin['_id']
                    break
            if status == '-1':
                return HttpResponse(json.dumps({"status": status}), content_type="application/json")
            else:
                # change the password
                query = "db.collection(\"administratorInfo\").where({ _id: \"" + id + "\"}).update({data: { password: \"" + newpsd + "\"}})"
                datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                r = requests.post('https://api.weixin.qq.com/tcb/databaseupdate?access_token=' + access_token,
                                  data=datas)
                result = r.json()['errcode']
                return HttpResponse(json.dumps({'status': status, 'errcode': result}),
                                    content_type="application/json")
        else:
            status = '0'
            return HttpResponse(json.dumps({"status": status}), content_type="application/json")


@csrf_exempt
def getHealthData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        if check_token(my_token):
            r = requests.post(
                'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
            access_token = r.json()['access_token']

            datacountpost = json.dumps({"env": "emss1-7y7xp", "query": "db.collection(\"HealthData\").count()"})
            countr = requests.post('https://api.weixin.qq.com/tcb/databasecount?access_token=' + access_token, data=datacountpost)
            datacount = countr.json()['count']

            getquery = "db.collection(\"HealthData\").limit(" + str(datacount) + ").get()"

            datas = json.dumps({"env": "emss1-7y7xp", "query": getquery})
            r = requests.post('https://api.weixin.qq.com/tcb/databasequery?access_token=' + access_token, data=datas)
            result = r.json()['data']
            status = '1'
            return HttpResponse(json.dumps(result),content_type="application/json")
        else:
            status = '0'
            return HttpResponse(json.dumps({"status": status}), content_type="application/json")


@csrf_exempt 
def addHealthData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        addquery = request_dict.get('addquery')
        my_token = request_dict.get('token')
    
        if(check_token(my_token)):
            r = requests.post(
                'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
            access_token = r.json()['access_token']
            datas = json.dumps({"env": "emss1-7y7xp", "query": addquery})
            r = requests.post('https://api.weixin.qq.com/tcb/databaseadd?access_token=' + access_token, data=datas)
            result = r.json()['errcode']
            status = '1'

            return HttpResponse(json.dumps({"status": '1', "errcode": result}),content_type="application/json")
        else:
            status = '0'
            return HttpResponse(json.dumps({"status": status}), content_type="application/json")

@csrf_exempt 
def deleteHealthData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        deletequery = request_dict.get('deletequery')
        my_token = request_dict.get('token')

        if (check_token(my_token)):
            r = requests.post(
                'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
            access_token = r.json()['access_token']
            datas = json.dumps({"env": "emss1-7y7xp", "query": deletequery})
            r = requests.post('https://api.weixin.qq.com/tcb/databasedelete?access_token=' + access_token, data=datas)
            result = r.json()['errcode']
            status = '1'

            return HttpResponse(json.dumps({"status": '1', "errcode": result}),content_type="application/json")
        else:
            status = '0'
            return HttpResponse(json.dumps({"status": status}), content_type="application/json")


@csrf_exempt 
def editHealthData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        editquery = request_dict.get('editquery')
        my_token = request_dict.get('token')

        if (check_token(my_token)):
            r = requests.post(
                'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
            access_token = r.json()['access_token']
            datas = json.dumps({"env": "emss1-7y7xp", "query": editquery})
            r = requests.post('https://api.weixin.qq.com/tcb/databaseupdate?access_token=' + access_token, data=datas)
            result = r.json()['errcode']
            status = '1'

            return HttpResponse(json.dumps({"status": '1', "errcode": result}),content_type="application/json")
        else:
            status = '0'
            return HttpResponse(json.dumps({"status": status}), content_type="application/json")

