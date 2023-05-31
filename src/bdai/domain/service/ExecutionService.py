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
    """
    Esta clase gestiona las ejecuciones
    """

    def __init__(self):
        self.abort = False

    def __init_logging(self, origin: str, execution_id: str) -> None:
        """
        Esta funcion inicializa el logging para que cada fichero de log solo contenga las trazas de un origen de datos
        y una version.

        :param str origin:
        :param str execution_id:
        """
        file_path = os.sep.join([get_data_path(), 'logs', f'{execution_id}_{origin}.log'])
        logging.getLogger().handlers.clear()
        logging.basicConfig(level=logging.INFO, filename=file_path, filemode='a',
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%y-%m-%d %H:%M:%S')

    def execute(self, service: str = None) -> None:
        """
        Este metodo inicia los servicios de scraping

        :param str service:
        """
        try:
            log_info('execute - begin')
            # se define el id de la version
            execution_id = datetime.now().strftime('%Y%m%d%H')
            path = os.sep.join([get_src_path(), 'infrastructure', 'scraping', 'services'])
            # por cada fichero .py del directorio, se carga de forma dinámica y se ejecuta
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

                self.__execute_service(execution_id=execution_id, execution_storage_service=execution_storage_service,
                                       records_storage_service=record_storage_service,
                                       error_storage_service=error_storage_service,
                                       scraping_service=scraping_service)
            log_info('execute - end')
        except AbortScrapingException as ase:
            produce_abort_scraping()
        except Exception as e:
            produce_exception(origin='general', text=traceback.format_exc())
            log_error()

    def __execute_service(self, execution_id: str, execution_storage_service: ExecutionStorageService,
                          records_storage_service: RecordStorageService,
                          error_storage_service: ErrorStorageService,
                          scraping_service: ScrapingInterface) -> None:
        """
        Ejecuta un servicio de scraping, es decir, el scraping de un origen de datos

        :param execution_id:
        :param execution_storage_service:
        :param records_storage_service:
        :param error_storage_service:
        :param scraping_service:
        """
        origin = scraping_service.get_origin()
        try:
            log_info(f'create execution - {origin} - begin')

            execution = Execution(id=execution_id)
            execution.begin()
            produce_begin(origin=origin, version=execution_id)

            def on_product(product: Product) -> None:
                """
                Callback que se ejecuta desde el servicio de scraping, cuando se ha obtenido un producto

                :param product:
                """
                product.version = execution_id
                product.version_date = datetime.strptime(execution_id, '%Y%m%d%H').strftime('%y-%m-%d %H:%M:%S')
                product.origin = origin
                product.scrape_datetime = datetime.now()
                produce_product(product_id=product.id, version=product.version, origin=origin)
                self.__must_abort()

            def on_error(error: ScrapingError) -> None:
                """
                Callback que se ejecuta desde el servicio de scraping cuando se ha producido un error de scraping,
                es decir, cuando se espera un elemento HTML pero no existe

                :param error:
                """
                self.__must_abort()

            def find_product(id: str) -> Product:
                """
                Callback que permite al servicio de scraping buscar productos en la base de datos

                :param id:
                :return:
                """
                return records_storage_service.find(id=id)

            try:
                scraping_service.scrape(on_product_callback=on_product, on_error_callback=on_error,
                                        find_product=find_product, is_saved=records_storage_service.is_stored)
            except Exception:
                log_error()

            execution.end()
            execution.num_products = len(records_storage_service.product_list)
            execution.num_errors = len(error_storage_service.error_list)
            produce_end(origin=origin, version=execution_id)
            log_info(f'create execution - {origin} - end')
        except AbortScrapingException as ase:
            raise ase
        except Exception as e:
            produce_exception(origin=origin, text=traceback.format_exc())
            log_error()

    def __must_abort(self):
        """
        Metodo que valida si se debe abortar el proceso de scraping
        """
        if self.abort:
            raise AbortScrapingException()
