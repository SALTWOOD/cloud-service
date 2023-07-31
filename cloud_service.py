# -*- coding: utf-8 -*-
import requests
import threading
import socket
import json
#import base64

def lookup(ip):

    URL = 'http://ip-api.com/batch'
    try:
        r = requests.post(URL,data=json.dumps([{"query":ip,"lang":"zh-CN"}]))
    except requests.RequestException as e:
        print(e)

    i = r.json()[0]
    print(i)
    if i["status"] == "success":
        return(i["country"],i["regionName"],i["city"])
    elif i["message"] == "reserved range":
        return("reserved range","reserved range","reserved range")
    else:
        raise Exception("IP lookup failed.")


def main(client,thread,addr):
    print(f"[Thread {thread}/INFO]第{thread}号线程启动处理程序...")
    try:
        header = client.recv(2048)
        print(header.decode())
        head = header[0:header.find(b"\r\n\r\n")].decode().split("\r\n")
        reqDict = {}
        url = head[0].split(" ")[1]
        if url == "/api/getUserInfo":
            for i in head[1:]:
                value = ":".join(i.split(":")[1:])
                key, value = (i.split(":")[0],value if value[0] == " " else value[1:])
                value = value if not value[0] == " " else value[1:]
                reqDict[key] = value
            try:
                secret = reqDict["Secret"]
                with open(f"./databases/{secret}.json") as f:
                    data = json.dumps(json.loads(f.read()))
                    client.send(f"HTTP/1.1 200 OK\r\nServer: Powered-by-SALTWOOD/cloud-service\r\n\r\n{data}".encode())
            except Exception as ex:
                print(f"[Thread {thread}/WARN]第{thread}号线程处理请求时出现错误:{ex}")
                client.send("HTTP/1.1 404\r\nServer: Powered-by-SALTWOOD/cloud-service\r\nEncode: UTF-8\r\n\r\n请求参数缺失！".encode("gbk"))
                client.close()
        elif url == "/getLocalFile":
            for i in head[1:]:
                value = ":".join(i.split(":")[1:])
                key, value = (i.split(":")[0],value if value[0] == " " else value[1:])
                value = value if not value[0] == " " else value[1:]
                reqDict[key] = value
            try:
                file = reqDict["Secret"]
                with open(file,"rb") as f:
                    data = f.read()
                    client.send(b"HTTP/1.1 200 OK\r\nServer: Powered-by-SALTWOOD/cloud-service\r\n\r\n" + data)
            except Exception as ex:
                print(f"[Thread {thread}/WARN]第{thread}号线程处理请求时出现错误:{ex}")
                client.send("HTTP/1.1 404\r\nServer: Powered-by-SALTWOOD/cloud-service\r\nEncode: UTF-8\r\n\r\n请求参数缺失！".encode("gbk"))
        elif url == "/getIP":
            for i in head[1:]:
                value = ":".join(i.split(":")[1:])
                key, value = (i.split(":")[0],value if value[0] == " " else value[1:])
                value = value if not value[0] == " " else value[1:]
                reqDict[key] = value
            reqDict = dict({"IP":addr[0]},**reqDict)
            #for i in head[1:]:
                #value = ":".join(i.split(":")[1:])
                #key, value = (i.split(":")[0],value if value[0] == " " else value[1:])
                #value = value if not value[0] == " " else value[1:]
                #reqDict[key] = value
            print(reqDict)
            try:
                ipAddr = lookup(reqDict["IP"])
                client.send("""HTTP/1.1 200 OK\r\nServer: Powered-by-SALTWOOD/cloud-service\r\nContent-Type: text/html\r\nEncode: UTF-8\r\n\r\n<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>IP属地查询</title>
</head>
<body>

<h1>IP属地</h1>
<p>{0}</p>

</body>
</html>""".format("/".join(ipAddr)).encode())
            except Exception as ex:
                print(f"[Thread {thread}/WARN]第{thread}号线程处理请求时出现错误:{ex}")
                client.send("HTTP/1.1 404\r\nServer: Powered-by-SALTWOOD/cloud-service\r\nEncode: UTF-8\r\n\r\n请求参数缺失！".encode())
                client.close()
    except Exception as ex:
        print(f"[Thread {thread}/ERROR]第{thread}号线程出现错误:{ex}")
    client.close()

bind = ("",80)
server = socket.socket()
server.bind(bind)
server.listen(16)

pool = []
count = 1

print(f"[Main/INFO]服务器正在监听<{bind[0] if not bind[0] == '' else '0.0.0.0'}:{bind[1]}>")

while 1:
    try:
        client,addr = server.accept()
        print(f"[Main/INFO]收到来自<{addr[0]}:{addr[1]}>的请求数据")
        thread = threading.Thread(target=main,args=(client,count,addr))
        count += 1
        pool.append(thread)
        thread.start()
    except KeyboardInterrupt:
        print("[Main/INFO]Ctrl + C已按下，正在关闭...")
        for i in range(len(pool)):
            print(f"[Main/INFO]正在关闭{i+1}号线程...")
            pool[i].join(500)
            print(f"[Main/INFO]{i+1}号线程已关闭")
        server.close()
        exit(0)
    except Exception as ex:
        print(f"[Main/ERROR]主线程出现错误:{ex}")
