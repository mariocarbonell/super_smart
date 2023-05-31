import os

from src.bdai.infrastructure.storage.LoggingService import log_error
from utils import get_root_path, get_data_path
from src.bdai.domain.model.ScrapingError import ScrapingError


class ErrorStorageService:
    """Clase que gestiona la persistencia en todos los medios definidos, de los errores de scraping"""

    def __init__(self, execution_id: str, origin: int) -> None:
        self.file_path = os.sep.join([get_data_path(), 'errors', f'{execution_id}_{origin}.json'])
        self.error_list = []

    def save(self, error: ScrapingError) -> None:
        """
        Metodo que gestiona el almacenamiento de un error de scraping en todos los medios definidos.

        * listado interno
        * fichero en DataLake

        :param error:
        """
        self.error_list.append(error)
        try :
            with open(self.file_path, 'w') as f:
                f.write(ScrapingError.schema().dumps(self.error_list, many=True))
        except Exception as e:
            log_error(error.to_json())

