# coding: utf-8

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from chatbot import Chat, reflections, multiFunctionCall
import requests, os
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation
import urllib.parse
import subprocess
from threading import Timer

gbl_username="" 
gbl_pcname="" 
gbl_info=""

def timeout():
    global chat
    print("Anything you want to check with me ?")
    return "Anyting you want to check with me ?"

def issueIs(query, sessionID="general"):
    print("issueIs "+str(query))
    exec_stmt='exec sp_chatbot_ret'
    sqlcmd_loc='C:\Program Files\Microsoft SQL Server\100\Tools\Binn\sqlcmd'
    sqlcmd_out=subprocess.Popen([r'C:\Program Files\Microsoft SQL Server\100\Tools\Binn\sqlcmd', "-E", "-S", "127.0.0.1", "-d", "btnet", "-Q", exec_stmt], stdout=subprocess.PIPE)
    line_stdout=str(sqlcmd_out.stdout.readlines())
    tmp_stdout=line_stdout.split(",")
    line_total_cnt = len(tmp_stdout)
    line_cnt=0
    stdout=""
    while (line_cnt < line_total_cnt):
       crln_stdout=tmp_stdout[line_cnt].split("\\r\\n")
       actual_stdout=crln_stdout[0].split("b'")
       stdout=stdout+actual_stdout[1]+"<br />"
       line_cnt=line_cnt+1
    #stdout="a<br />b<br />"
    if query[-2] == '?':
        query = "Mr/Ms "+gbl_username+" "+query[:len(query)-2]
    try:
        return 'query:'+stdout
		#send the link to user to click
        #return '<a href="http://www.google.com">www.google.com</a>'
        #return '<a href="file://c:\\8\\joyhome-logo.png">c:\8\joyhome-logo.png</a><br/>'
        #return query
    except:
        pass
    return "Oh, You misspelled somewhere!"


def whoIs(query, sessionID="general"):
    if query[-2] == '?':
        query = query[:len(query)-2]
    try:
        response = requests.get('http://api.stackexchange.com/2.2/tags/' + query + '/wikis?site=stackoverflow')
        data = response.json()
        return data['items'][0]['excerpt']
    except:
        pass
    return "Oh, You misspelled somewhere!"


def results(query, sessionID="general"):
    query_list = query.split(' ')
    query_list = [x for x in query_list if x not in ['posted', 'questions', 'recently', 'recent', 'display', '', 'in', 'of', 'show']]
    # print(query_list)
    if len(query_list) == 1:
        # print('con 1')
        try:
            response = requests.get('https://api.stackexchange.com/2.2/questions?pagesize=5&order=desc&sort=activity&tagged=' + query_list[0] + '&site=stackoverflow')
            data = response.json()
            data_list = [str(i+1)+'. ' + data['items'][i]['title'] for i in range(5)]
            return '<br/>'.join(data_list)
        except:
            pass
    elif len(query_list) == 2 and 'unanswered' not in query_list:
        # print('con 2')
        query_list = sorted(query_list)
        n = query_list[0]
        tag = query_list[1]
        try:
            response = requests.get('https://api.stackexchange.com/2.2/questions?pagesize='+ n +'&order=desc&sort=activity&tagged=' + tag + '&site=stackoverflow')
            data = response.json()
            data_list = [str(i+1)+'. ' + data['items'][i]['title'] for i in range(int(n))]
            return '<br/>'.join(data_list)
        except:
            pass

    else:
        # print('con 3')
        query_list = [x for x in query_list if x not in ['which', 'where', 'whos', 'who\'s' 'is', 'are', 'answered', 'not', 'unanswered', 'for']]
        # print(query_list)
        if len(query_list) ==1:
            try:
                response = requests.get(
                    'https://api.stackexchange.com/2.2/questions/no-answers?pagesize=5&order=desc&sort=activity&tagged=' + query_list[0] + '&site=stackoverflow')
                data = response.json()
                data_list = [str(i+1)+'. ' + data['items'][i]['title'] for i in range(5)]
                return '<br/>'.join(data_list)
            except:
                pass
        elif len(query_list) == 2:
            query_list = sorted(query_list)
            n = query_list[0]
            tag = query_list[1]
            try:
                response = requests.get(
                    'https://api.stackexchange.com/2.2/questions/no-answers?pagesize='+ n +'&order=desc&sort=activity&tagged=' + tag + '&site=stackoverflow')
                data = response.json()
                data_list = [str(i+1)+'. ' + data['items'][i]['title'] for i in range(int(n))]

                return '<br/>'.join(data_list)
            except:
                pass
    return "Oh, You misspelled somewhere!"


#Display recent 3 python questions which are not answered
firstQuestion = "Hi, How may i help you?"


call = multiFunctionCall({"whoIs": whoIs,
                          "issueIs" : issueIs,
                              "results": results})

chat = Chat(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "chatbotTemplate",
                         "Example.template"
                         ),
            reflections, call=call)

def Home(request):
    global gbl_username, gbl_pcname, gbl_info
    print("request["+str(request)+"]")
    gbl_pcname=""
    gbl_username=""
    gbl_info=""
	
    # duration is in seconds
    #t = Timer(1 * 30, timeout)
    #t.start()

    # wait for time completion
    #t.join()

    try:
       para=str(request).split("?")
       if (len(para) <= 1):
          print("No parameter provided")
       else:
          para1=para[1].split("'")
          para2=para1[0].split("&")
          ws_cnt=0
          while (ws_cnt < len(para2)):
             if para2[ws_cnt].upper().find("PCNAME") == 0:
                gbl_pcname=para2[ws_cnt].split("=")[1]
             if para2[ws_cnt].upper().find("USERNAME") == 0:
                gbl_username=para2[ws_cnt].split("=")[1]
             if para2[ws_cnt].upper().find("INFO") == 0:
                gbl_info=urllib.parse.unquote(para2[ws_cnt].split("=")[1])
             ws_cnt=ws_cnt+1
    except:
       print("One of the parameter didn't pass in "+para)

    return render(request, "alpha/home.html", {'home': 'active', 'chat': 'chat'})


@csrf_exempt
def Post(request):
    global gbl_username, gbl_pcname, gbl_info
    print("Post func "+gbl_username+" "+gbl_pcname+" "+gbl_info)
    while len(chat.conversation["general"])<2:
        chat.conversation["general"].append('initiate')
    if request.method == "POST":
        query = request.POST.get('msgbox', None)
        response = chat.respond(query)
        chat.conversation["general"].append('<br/>'.join(['ME: '+query, 'BOT: '+response]))
        if query.lower() in ['bye', 'quit', 'bbye', 'seeya', 'goodbye']:
            chat_saved = chat.conversation["general"][2:]
            response = response + '<br/>' + '<h3>Chat Summary:</h3><br/>' + '<br/><br/>'.join(chat_saved)
            chat.conversation["general"] = []
            return JsonResponse({'response': response, 'query': query})
        #c = Conversation(query=query, response=response)
        return JsonResponse({'response': response, 'query': query})
    else:
        return HttpResponse('Request must be POST.')


'''
def Post(request):
    if request.method == "POST":
        msg = request.POST.get('msgbox', None)
        c = Chat(message=msg)
        if msg != '':
            c.save()
        return JsonResponse({'msg': msg, 'user': 'user'})
    else:
        return HttpResponse('Request must be POST.')'''

