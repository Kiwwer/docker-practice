from __future__ import print_function

import logging

import grpc
import service.server.servicer_pb2 as servicer_pb2
import service.server.servicer_pb2_grpc as servicer_pb2_grpc
import socket
import os
import sys
import math
from threading import Thread

idTypeDict = ["Native", "XML", "JSON", "GoogleProtoBuff", "Apache Avro", "YAML", "MessagePack", "all"]
typeIdDict = {"Native": 0, "XML": 1, "JSON": 2, "GoogleProtoBuff": 3, "Apache Avro": 4, "YAML": 5, "MessagePack": 6, "all": -1}
services = []
commands = {}
latest = [0, 0, 0, 0, 0, 0, 0]
typeCnt = 7

def GRPCQueryMTV(typeId):
    serviceAddr = services[typeId]
    with grpc.insecure_channel(serviceAddr) as channel:
        stub = servicer_pb2_grpc.ServicerStub(channel)
        response = stub.GetSerializationTime(servicer_pb2.Query(typeId=typeId))
    latest[typeId] = response
    return response

def RegisterServices():
    services.append(os.environ.get('SERVICE1_ADDR', 'localhost:8081'))
    services.append(os.environ.get('SERVICE2_ADDR', 'localhost:8082'))
    services.append(os.environ.get('SERVICE3_ADDR', 'localhost:8083'))
    services.append(os.environ.get('SERVICE4_ADDR', 'localhost:8084'))
    services.append(os.environ.get('SERVICE5_ADDR', 'localhost:8085'))
    services.append(os.environ.get('SERVICE6_ADDR', 'localhost:8086'))
    services.append(os.environ.get('SERVICE7_ADDR', 'localhost:8087'))

def FuncGetResult(typeName):
    if typeName in idTypeDict:
        typeId = typeIdDict[typeName]
        if typeId == -1:
            threads = []
            for i in range(typeCnt):
                threads.append(Thread(target=GRPCQueryMTV, args=[i]))
            for i in range(typeCnt):
                threads[i].start()
            for i in range(typeCnt):
                threads[i].join()
            reply = ''
            for i in range(typeCnt):
                result = latest[i]
                typeName = idTypeDict[result.typeId]
                objSize = result.objSize
                serializeTime = float(int(math.floor(100000 * (result.serializeTime)))) / 100
                deserializeTime = float(int(math.floor(100000 * (result.deserializeTime)))) / 100
                reply += f'RESPONSE: {typeName} - {objSize} bytes - {serializeTime} ms - {deserializeTime} ms\n'
            return reply
        else:
            result = GRPCQueryMTV(typeId)
            typeName = idTypeDict[result.typeId]
            objSize = result.objSize
            serializeTime = float(int(math.floor(100000 * (result.serializeTime)))) / 100
            deserializeTime = float(int(math.floor(100000 * (result.deserializeTime)))) / 100
            reply = f'RESPONSE: {typeName} - {objSize} bytes - {serializeTime} ms - {deserializeTime} ms\n'
            return reply
    return "RESPONSE: Invalid serialization method name. Please check documentation or try running: get_result all\n"
def UDPParser(message):
    cmd = message.split()
    if (len(cmd) < 2):
        return "RESPONSE: Invalid command, usage: get_result {Method Name} OR get_result all\n"
    if (cmd[0] == 'get_result'):
        return FuncGetResult(cmd[1])
    return "RESPONSE: Invalid command, usage: get_result {Method Name} OR get_result all\n"
        

def run():
    port = os.environ.get('SERVER_PORT', '2000')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', int(port)))
    RegisterServices()
    while True:
        message, address = server_socket.recvfrom(1024)
        message = message.decode('utf-8')
        reply = UDPParser(message)
        reply = reply.encode('utf-8')
        server_socket.sendto(reply, address)


if __name__ == '__main__':
    logging.basicConfig()
    run()
