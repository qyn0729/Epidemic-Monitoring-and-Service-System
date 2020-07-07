from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from . import login
import pandas as pd
import datetime
import requests

@csrf_exempt
def updateEpidemic_Area(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            # token is correct
            status = '1'
            try:
                # get data
                r = requests.get('https://lab.isaaclin.cn/nCoV/api/area')
                a = json.dumps(r.json()['results'], ensure_ascii=False)
                results = r.json()['results']
                data = []
                for item in results:
                    if item['countryEnglishName'] != None:
                        data.append([item['countryEnglishName'], item['provinceEnglishName'], item['currentConfirmedCount'], item['confirmedCount'], item['deadCount'], item['curedCount']])
            except:
                status = '-1'

            if status == '1':
                r = requests.post(
                    'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
                access_token = r.json()['access_token']
                cur_time = datetime.datetime.now().strftime('%G-%m-%d')

                # search
                query = "db.collection(\"Epidemic_Area2\").where({ date: \"" + cur_time + "\"}).get()"
                datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                r = requests.post('https://api.weixin.qq.com/tcb/databasequery?access_token=' + access_token,
                                  data=datas)
                find = len(r.json()['data'])

                if find == 0:
                    # add new record
                    query = "db.collection(\"Epidemic_Area2\").add({data: { date: \"" + cur_time + "\", results: " + str(
                        a) + "}})"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databaseadd?access_token=' + access_token,
                                      data=datas)
                    result = r.json()['errcode']

                    # find the earliest record
                    query = "db.collection(\"Epidemic_Area2\").limit(1).get()"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databasequery?access_token=' + access_token,
                                      data=datas)
                    result = r.json()['data']
                    _id = json.loads("".join(result))['_id']
                    # delete the earliest record
                    query = "db.collection(\"Epidemic_Area2\").doc(\"" + str(_id) + "\").remove()"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databasedelete?access_token=' + access_token,
                                      data=datas)
                    return HttpResponse(json.dumps({'status': status, 'errcode': result, 'data': data}),
                                    content_type="application/json")
                else:
                    # update the record
                    query = "db.collection(\"Epidemic_Area2\").where({ date: \"" + cur_time + "\"}).update({data: { date: \"" + cur_time + "\", results: " + str(
                        a) + "}})"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databaseupdate?access_token=' + access_token,
                                      data=datas)
                    result = r.json()['errcode']
                    return HttpResponse(json.dumps({'status': status, 'errcode': result, 'data': data}),
                                        content_type="application/json")
            else:
                json_data = {'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            status = '0'
            json_data = {'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')

@csrf_exempt
def updateEpidemic_US(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            status = '1'
            cur_time = datetime.datetime.now() + datetime.timedelta(days=-1)
            yes_time = cur_time + datetime.timedelta(days=-1)
            cur_file_name = cur_time.strftime('%m-%d-%G.csv')
            yes_file_name = yes_time.strftime('%m-%d-%G.csv')
            status = '1'
            data = []
            # get data
            try:
                data = pd.read_csv(
                    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + cur_file_name)
                available_time = cur_time.strftime('%m-%d-%G')
            except:
                status = '-1'
            if status == '-1':
                try:
                    data = pd.read_csv(
                    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + yes_file_name)
                    status = '1'
                    available_time = yes_time.strftime('%m-%d-%G')
                except:
                    status = '-1'

            if status == '1':
                json_data = data.to_json(orient="records")
                ab = json.loads(json_data)
                data = []
                for item in ab:
                    data.append([item['Province_State'], item['Lat'], item['Long_'], item['Confirmed'], item['Deaths'], item['Recovered'], item['Active']])
                a = str(ab).replace('None', 'null')

                r = requests.post(
                    'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx000d5f14535c4623&secret=8f5fc6e7f1fe4a112ecd2ca595f7823c')
                access_token = r.json()['access_token']

                # search
                query = "db.collection(\"Epidemic_US\").where({ date: \"" + available_time + "\"}).get()"
                datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                r = requests.post('https://api.weixin.qq.com/tcb/databasequery?access_token=' + access_token,
                                  data=datas)
                find = len(r.json()['data'])

                if find == 0:
                    # add new record
                    query = "db.collection(\"Epidemic_US\").add({data: { date: \"" + available_time + "\", results: " + str(
                        a) + "}})"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databaseadd?access_token=' + access_token, data=datas)
                    result = r.json()['errcode']
                    # find the earliest record
                    query = "db.collection(\"Epidemic_US\").limit(1).get()"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databasequery?access_token=' + access_token,
                                      data=datas)
                    result = r.json()['data']
                    _id = json.loads("".join(result))['_id']
                    # delete the earlist record
                    query = "db.collection(\"Epidemic_US\").doc(\"" + str(_id) + "\").remove()"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databasedelete?access_token=' + access_token,
                                      data=datas)
                else:
                    # update the record
                    query = "db.collection(\"Epidemic_US\").where({ date: \"" + available_time + "\"}).update({data: { date: \"" + available_time + "\", results: " + str(
                        a) + "}})"
                    datas = json.dumps({"env": "emss1-7y7xp", "query": query})
                    r = requests.post('https://api.weixin.qq.com/tcb/databaseupdate?access_token=' + access_token,
                                      data=datas)
                    result = r.json()['errcode']
                return HttpResponse(json.dumps({'status': status, 'errcode': result, 'data': data}), content_type="application/json")
            else:
                json_data = {'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            status = '0'
            json_data = {'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')

@csrf_exempt
def getDXYConfirmedData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            status = '1'
            try:
                # get data
                r = requests.get('https://lab.isaaclin.cn/nCoV/api/area')
                results = r.json()['results']

                data = []
                for item in results:
                    if item['countryEnglishName'] != None:
                        data.append([item['countryEnglishName'], item['provinceEnglishName'], item['currentConfirmedCount'], item['confirmedCount']])
                json_data = {'data': data, 'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
            except:
                status = '-1'
                data = []
                json_data = {'data': data, 'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            data = []
            json_data = {'data': data, 'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')

@csrf_exempt
def getDXYDeathData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            status = '1'
            try:
                # get data
                r = requests.get('https://lab.isaaclin.cn/nCoV/api/area')
                results = r.json()['results']

                data = []
                for item in results:
                    if item['countryEnglishName'] != None:
                        data.append([item['countryEnglishName'], item['provinceEnglishName'], item['deadCount']])
                json_data = {'data': data, 'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
            except:
                status = '-1'
                data = []
                json_data = {'data': data, 'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            data = []
            json_data = {'data': data, 'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')

@csrf_exempt
def getDXYCuredData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            status = '1'
            try:
                # get data
                r = requests.get('https://lab.isaaclin.cn/nCoV/api/area')
                results = r.json()['results']

                data = []
                for item in results:
                    if item['countryEnglishName'] != None:
                        data.append([item['countryEnglishName'], item['provinceEnglishName'], item['curedCount']])
                json_data = {'data': data, 'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
            except:
                status = '-1'
                data = []
                json_data = {'data': data, 'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            data = []
            json_data = {'data': data, 'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')

@csrf_exempt
def getJHUConfirmedData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            cur_time = datetime.datetime.now() + datetime.timedelta(days=-1)
            yes_time = cur_time + datetime.timedelta(days=-1)
            cur_file_name = cur_time.strftime('%m-%d-%G.csv')
            yes_file_name = yes_time.strftime('%m-%d-%G.csv')
            data = []
            # get global data
            status = '1'
            try:
                datas = pd.read_csv(
                    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/" + cur_file_name)
            except:
                status = '-1'
            if status == '-1':
                try:
                    datas = pd.read_csv(
                        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/" + yes_file_name)
                    status = '1'
                except:
                    status = '-1'

            if status == '1':
                json_data = datas.to_json(orient="records")
                ab = json.loads(json_data)
                for item in ab:
                    if item['Country_Region'] != 'US':
                        data.append([item['Country_Region'], item['Province_State'], item['Active'], item['Confirmed']])
                # get us data
                try:
                    datas = pd.read_csv(
                        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + cur_file_name)
                except:
                    status = '-1'
                if status == '-1':
                    try:
                        datas = pd.read_csv(
                            "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + yes_file_name)
                        status = '1'
                    except:
                        status = '-1'

                if status == '1':
                    json_data = datas.to_json(orient="records")
                    ab = json.loads(json_data)

                    for item in ab:
                        data.append([item['Country_Region'], item['Province_State'], item['Active'], item['Confirmed']])
                    json_data = {'data': data, 'status': status}
                    return HttpResponse(json.dumps(json_data), content_type='application/json')
                else:
                    json_data = {'status': status}
                    return HttpResponse(json.dumps(json_data), content_type='application/json')
            else:
                json_data = {'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            data = []
            json_data = {'data': data, 'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')

@csrf_exempt
def getJHUDeathData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            cur_time = datetime.datetime.now() + datetime.timedelta(days=-1)
            yes_time = cur_time + datetime.timedelta(days=-1)
            cur_file_name = cur_time.strftime('%m-%d-%G.csv')
            yes_file_name = yes_time.strftime('%m-%d-%G.csv')
            data = []
            # get global data
            status = '1'
            try:
                datas = pd.read_csv(
                    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/" + cur_file_name)
            except:
                status = '-1'
            if status == '-1':
                try:
                    datas = pd.read_csv(
                        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/" + yes_file_name)
                    status = '1'
                except:
                    status = '-1'

            if status == '1':
                json_data = datas.to_json(orient="records")
                ab = json.loads(json_data)
                for item in ab:
                    if item['Country_Region'] != 'US':
                        data.append([item['Country_Region'], item['Province_State'], item['Deaths']])
                # get us data
                try:
                    datas = pd.read_csv(
                        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + cur_file_name)
                except:
                    status = '-1'
                if status == '-1':
                    try:
                        datas = pd.read_csv(
                            "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + yes_file_name)
                        status = '1'
                    except:
                        status = '-1'

                if status == '1':
                    json_data = datas.to_json(orient="records")
                    ab = json.loads(json_data)

                    for item in ab:
                        data.append([item['Country_Region'], item['Province_State'], item['Deaths']])
                    json_data = {'data': data, 'status': status}
                    return HttpResponse(json.dumps(json_data), content_type='application/json')
                else:
                    json_data = {'status': status}
                    return HttpResponse(json.dumps(json_data), content_type='application/json')
            else:
                json_data = {'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            data = []
            json_data = {'data': data, 'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')

@csrf_exempt
def getJHUCuredData(request):
    print("connected")
    if request.method == 'POST':
        request_data = request.body
        request_dict = json.loads(request_data.decode('utf-8'))
        my_token = request_dict.get('token')
        status = '0'
        if login.check_token(my_token):
            cur_time = datetime.datetime.now() + datetime.timedelta(days=-1)
            yes_time = cur_time + datetime.timedelta(days=-1)
            cur_file_name = cur_time.strftime('%m-%d-%G.csv')
            yes_file_name = yes_time.strftime('%m-%d-%G.csv')
            data = []
            # get global data
            status = '1'
            try:
                datas = pd.read_csv(
                    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/" + cur_file_name)
            except:
                status = '-1'
            if status == '-1':
                try:
                    datas = pd.read_csv(
                        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/" + yes_file_name)
                    status = '1'
                except:
                    status = '-1'

            if status == '1':
                json_data = datas.to_json(orient="records")
                ab = json.loads(json_data)
                for item in ab:
                    if item['Country_Region'] != 'US':
                        data.append([item['Country_Region'], item['Province_State'], item['Recovered']])
                # get us data
                try:
                    datas = pd.read_csv(
                        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + cur_file_name)
                except:
                    status = '-1'
                if status == '-1':
                    try:
                        datas = pd.read_csv(
                            "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/" + yes_file_name)
                        status = '1'
                    except:
                        status = '-1'

                if status == '1':
                    json_data = datas.to_json(orient="records")
                    ab = json.loads(json_data)

                    for item in ab:
                        data.append([item['Country_Region'], item['Province_State'], item['Recovered']])
                    json_data = {'data': data, 'status': status}
                    return HttpResponse(json.dumps(json_data), content_type='application/json')
                else:
                    json_data = {'status': status}
                    return HttpResponse(json.dumps(json_data), content_type='application/json')
            else:
                json_data = {'status': status}
                return HttpResponse(json.dumps(json_data), content_type='application/json')
        else:
            data = []
            json_data = {'data': data, 'status': status}
            return HttpResponse(json.dumps(json_data), content_type='application/json')



