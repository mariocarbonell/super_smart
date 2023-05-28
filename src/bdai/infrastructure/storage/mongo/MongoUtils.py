import os

from pymongo import MongoClient
from pymongo.server_api import ServerApi

from utils import get_root_path

__global_mongo_client = None


def get_mongo_client():
    global __global_mongo_client
    if not __global_mongo_client:
        uri = "[mongodb_cloud_url]"
        __global_mongo_client = MongoClient(uri,
                                            tls=True,
                                            tlsCertificateKeyFile=os.sep.join(
                                                [get_root_path(), 'resources', "[mongodb_cloud_certificat_path]"]),
                                            server_api=ServerApi('1'))
    return __global_mongo_client


__global_logs_mongo_client = None


def get_logs_mongo_client():
    global __global_logs_mongo_client
    if __global_logs_mongo_client:
        print('get_logs_mongo_client', __global_logs_mongo_client is None)
        return __global_logs_mongo_client


def set_logs_mongo_client(client):
    global __global_logs_mongo_client
    __global_logs_mongo_client = client
    print(__global_logs_mongo_client is None)
