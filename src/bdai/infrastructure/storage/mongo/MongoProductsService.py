import logging
import traceback
from datetime import datetime

from src.bdai.infrastructure.storage.LoggingService import log_error
from src.bdai.infrastructure.storage.mongo.MongoUtils import get_mongo_client
from utils import get_root_path
from src.bdai.domain.model.Product import Product
import os

from pymongo import MongoClient
from pymongo.server_api import ServerApi


class MongoProductsService:
    def __init__(self, origin: str):
        self.origin = origin
        self.collection = get_mongo_client()['products']['products']

    def __generate_id(self, product: Product):
        now = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f'{product.id}-{now}'

    def save_product(self, product: Product):
        try:
            print(product.version)
            self.collection.update_one({'id': product.id, 'origin': product.origin}, {
                '$setOnInsert': {'_id': self.__generate_id(product), 'id': product.id, 'origin': product.origin},
                '$push': {'versions': product.to_dict()}}, upsert=True)
        except Exception as e:
            log_error()

    def find_product(self, product_id: str) -> Product or None:
        try:
            cursor = self.collection.aggregate([
                {'$unwind': '$versions'},
                {'$match': {'id': product_id, 'origin': self.origin}},
                {'$sort': {'versions.version': -1}},
                {'$group': {'_id': '$_id', 'producto': {'$push': '$versions'}}},
                {'$project': {'versions': '$producto'}},
            ])
            if cursor.alive:
                next_val = cursor.next()
                return Product.from_dict(next_val['versions'][0])
            else:
                return None
        except Exception as e:
            log_error()
