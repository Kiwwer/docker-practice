from concurrent import futures
import logging

import grpc
import service.server.servicer_pb2 as servicer_pb2
import service.server.servicer_pb2_grpc as servicer_pb2_grpc

import os
import sys
import timeit

import pickle
import json
import xmltodict
import dicttoxml
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToDict
import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter
import yaml
import msgpack

# Serializable by everything (almost) without any custom encoders (which are, IMHO, against the spirit of this task)
testSlug = {'integer': 71615141, 'floating': 7161.5141, 'array': [7, 1, 6, 1, 5, 1, 4, 1],
            'boolean': True, 'string': "71615141", 'dictionary': {'7': 1, '6': 1, '5': 1, '4': 1}}

overrideNumber = 0
typeCnt = 7


def TestSerDeserTime(typeId, testObject, iterationsCount):
    serializeTimeSum = 0
    deserializeTimeSum = 0
    for i in range(iterationsCount):
        startTime = timeit.default_timer()
        fileName = FuncDict[typeId][0](testObject)
        serializeTimeSum += timeit.default_timer() - startTime
        startTime = timeit.default_timer()
        obj = FuncDict[typeId][1](fileName)
        deserializeTimeSum += timeit.default_timer() - startTime
    serializeTime = serializeTimeSum / iterationsCount
    deserializeTime = deserializeTimeSum / iterationsCount
    return serializeTime, deserializeTime

def SerNative(obj):
    fileName = 'ser.dmp'
    pickle.dump(obj, open(fileName, "wb+"), protocol=pickle.HIGHEST_PROTOCOL)
    return fileName
    
def DeserNative(fileName):
    return pickle.load(open(fileName, "rb"))
    
def SerXML(obj):
    s = dicttoxml.dicttoxml(obj, attr_type=False)
    fileName = 'ser.dmp'
    with open(fileName, 'wb+') as file:
        file.write(s)
    return fileName
    
def DeserXML(fileName):
    with open(fileName, 'rb') as file:
        s = file.read()
    return xmltodict.parse(s)
    
def SerJSON(obj):
    fileName = 'ser.dmp'
    json.dump(obj, open(fileName, "w"))
    return fileName
    
def DeserJSON(fileName):
    return json.load(open(fileName, "r"))
    
def SerGPB(obj):
# costyl.exe
    ss = Struct()
    tS = dict(obj)
    tS['d1'] = [k for k, v in tS['dictionary'].items()]
    tS['d2'] = [v for k, v in tS['dictionary'].items()]
    tS['dictionary'] = 0
    ss.update(tS)
    s = ss.SerializeToString()
    fileName = 'ser.dmp'
    with open(fileName, 'wb+') as fi:
        fi.write(s)
    return fileName
    
def DeserGPB(fileName):
# uncostyl.exe
    with open(fileName, 'rb') as fi:
        s = fi.read()
    ss = Struct()
    ss.MergeFromString(s)
    tS = MessageToDict(ss)
    tS['dictionary'] = {}
    for i in range(len(tS['d1'])):
        tS['dictionary'][tS['d1'][i]] = tS['d2'][i]
    del tS['d1']
    del tS['d2']
    return tS
    
def SerAA(obj):
    schema = avro.schema.parse(open("service/server/ser.avsc", "rb").read())
    fileName = "ser.dmp"
    writer = DataFileWriter(open(fileName, "wb+"), DatumWriter(), schema)
    writer.append(obj)
    writer.close()
    return fileName
    
def DeserAA(fileName):
    reader = DataFileReader(open(fileName, "rb"), DatumReader())
    for ser in reader:
        obj = ser
    reader.close()
    return obj
    
def SerYAML(obj):
    fileName = 'ser.dmp'
    yaml.dump(obj, open(fileName, "w"))
    return fileName
    
def DeserYAML(fileName):
    return yaml.load(open(fileName, "r"))

def SerMP(obj):
    fileName = 'ser.dmp'
    with open(fileName, "wb+") as fi:
        fi.write(msgpack.packb(testSlug))
    return fileName
    
def DeserMP(fileName):
    with open(fileName, "rb") as fi:
        ss = fi.read()
    return msgpack.unpackb(ss)


FuncDict = [[SerNative, DeserNative],
	    [SerXML, DeserXML],
	    [SerJSON, DeserJSON],
	    [SerGPB, DeserGPB],
	    [SerAA, DeserAA],
	    [SerYAML, DeserYAML],
	    [SerMP, DeserMP]]
	    


class Servicer(servicer_pb2_grpc.ServicerServicer):

    def GetSerializationTime(self, request, context):
        typeId = request.typeId
        if (typeId <= -1 or typeId >= typeCnt):
            typeId = overrideNumber
        testObject = dict(testSlug)
        iterationsCount = int(os.environ.get('ITER_COUNT', '1012'))
        serializeTime, deserializeTime = TestSerDeserTime(typeId, testObject, iterationsCount)
        objSize = sys.getsizeof(testObject)
        return servicer_pb2.SerializationResponse(typeId=typeId, objSize=objSize, serializeTime=serializeTime, deserializeTime=deserializeTime)


def serve():
    port = os.environ.get('SERVICE_PORT', '8080')
    overrideNumber = int(port) - 8081
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    servicer_pb2_grpc.add_ServicerServicer_to_server(Servicer(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
