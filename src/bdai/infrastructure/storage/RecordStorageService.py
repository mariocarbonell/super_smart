import json
import os
from datetime import datetime

from src.bdai.infrastructure.storage.LoggingService import log_console, log_error
from src.bdai.infrastructure.storage.mongo.MongoProductsService import MongoProductsService
from utils import get_data_path
from src.bdai.domain.model.Product import Product


class RecordStorageService:
    def __init__(self, execution_id: str, origin: str):
        self.file_path = os.sep.join([get_data_path(), 'records', f'{execution_id}_{origin}.json'])
        self.product_list: list[Product] = []
        self.saved_products_id = []
        self.origin = origin
        self.database_service = MongoProductsService(origin=origin)
        self.indexed_products = self.load_master()

    def save(self, product: Product) -> None:

        try:
            if product.id not in self.saved_products_id:
                self.saved_products_id.append(product.id)
                self.product_list.append(product)
                self.database_service.save_product(product=product)
                try:
                    with open(self.file_path, 'w') as f:
                        f.write(Product.schema().dumps(self.product_list, many=True))
                except Exception as e:
                    log_error("error_open_records_file")
                    raise e
                product_master = self.find(product.id)
                if not product_master:
                    self.indexed_products[product.id] = product
                log_console(
                    f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - {self.origin} - {len(self.saved_products_id)}',
                    first=len(self.saved_products_id) == 0)
        except Exception:
            log_error()

    def find(self, id: str):
        try:
            if id in self.indexed_products:
                return self.indexed_products[id]
        except Exception as e:
            log_error()
        return None

    def load_master(self):
        print(f'master_{self.origin}.json')
        with open(os.sep.join([get_data_path(), 'records', f'master_{self.origin}.json']), 'r') as f:
            records = json.loads(f.read())

        products = {k: Product.from_dict(records[k]) for k in records}
        return products

    def is_stored(self, id: str) -> bool:
        return id in self.saved_products_id
