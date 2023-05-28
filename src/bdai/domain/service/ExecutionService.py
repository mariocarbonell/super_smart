import logging
import time
import traceback

from src.bdai.infrastructure.messaging.AbortScrapingException import AbortScrapingException
from src.bdai.infrastructure.messaging.producer_service import produce_abort_scraping, produce_exception, \
    produce_product, produce_begin, produce_end
from src.bdai.infrastructure.storage.LoggingService import log_info, log_error
from utils import get_src_path, get_root_path, get_data_path
from src.bdai.domain.model.Execution import Execution
from src.bdai.domain.model.Product import Product
from src.bdai.domain.model.ScrapingError import ScrapingError
from datetime import datetime

import os

from src.bdai.infrastructure.scraping.ScrapingInterface import ScrapingInterface
from src.bdai.infrastructure.storage.ErrorStorageService import ErrorStorageService
from src.bdai.infrastructure.storage.ExecutionStorageService import ExecutionStorageService
from src.bdai.infrastructure.storage.RecordStorageService import RecordStorageService


class ExecutionService:

    def __init__(self):
        self.abort = False

    def __init_logging(self, origin: str, execution_id: str) -> None:
        file_path = os.sep.join([get_data_path(), 'logs', f'{execution_id}_{origin}.log'])
        logging.getLogger().handlers.clear()
        logging.basicConfig(level=logging.INFO, filename=file_path, filemode='a',
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%y-%m-%d %H:%M:%S')

    def execute(self, service: str = None):
        try:
            log_info('execute - begin')
            execution_id = datetime.now().strftime('%Y%m%d%H')
            path = os.sep.join([get_src_path(), 'infrastructure', 'scraping', 'services'])
            for entry in os.scandir(path):
                if not entry.is_file():
                    continue

                class_name = entry.name[:-3]
                if service and service not in class_name.lower():
                    continue

                string = f'from src.bdai.infrastructure.scraping.services.{class_name} import {class_name}'
                exec(string)
                scraping_service: class_name = locals()[class_name]()
                origin = scraping_service.get_origin()
                self.__init_logging(execution_id=execution_id, origin=origin)
                execution_storage_service: ExecutionStorageService = ExecutionStorageService(origin=origin)
                record_storage_service: RecordStorageService = RecordStorageService(execution_id=execution_id,
                                                                                    origin=origin)
                error_storage_service: ErrorStorageService = ErrorStorageService(execution_id=execution_id,
                                                                                 origin=origin)

                self.__create_execution(execution_id=execution_id, execution_storage_service=execution_storage_service,
                                        records_storage_service=record_storage_service,
                                        error_storage_service=error_storage_service,
                                        scraping_service=scraping_service)
            log_info('execute - end')
        except AbortScrapingException as ase:
            produce_abort_scraping()
        except Exception as e:
            produce_exception(origin='general', text=traceback.format_exc())
            log_error()

    def __create_execution(self, execution_id: str, execution_storage_service: ExecutionStorageService,
                           records_storage_service: RecordStorageService,
                           error_storage_service: ErrorStorageService,
                           scraping_service: ScrapingInterface) -> None:
        origin = scraping_service.get_origin()
        try:
            log_info(f'create execution - {origin} - begin')

            execution = Execution(id=execution_id)
            execution.begin()
            # execution_storage_service.insert(execution)
            produce_begin(origin=origin, version=execution_id)

            def on_product(product: Product) -> None:
                product.version = execution_id
                product.version_date = datetime.strptime(execution_id, '%Y%m%d%H').strftime('%y-%m-%d %H:%M:%S')
                product.origin = origin
                product.scrape_datetime = datetime.now()
                # records_storage_service.save(product)
                produce_product(product_id=product.id, version=product.version, origin=origin)
                self.__must_abort()

            def on_error(error: ScrapingError) -> None:
                # error_storage_service.save(error)
                self.__must_abort()

            def find_product(id: str) -> Product:
                return records_storage_service.find(id=id)

            try:
                scraping_service.scrape(on_product_callback=on_product, on_error_callback=on_error,
                                        find_product=find_product, is_saved=records_storage_service.is_stored)
            except Exception:
                log_error()

            execution.end()
            execution.num_products = len(records_storage_service.product_list)
            execution.num_errors = len(error_storage_service.error_list)
            # execution_storage_service.update(execution)
            produce_end(origin=origin, version=execution_id)
            log_info(f'create execution - {origin} - end')
        except AbortScrapingException as ase:
            raise ase
        except Exception as e:
            produce_exception(origin=origin, text=traceback.format_exc())
            log_error()

    def __must_abort(self):
        if self.abort:
            raise AbortScrapingException()
