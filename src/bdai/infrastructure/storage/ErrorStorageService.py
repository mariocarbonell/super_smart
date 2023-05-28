import os

from src.bdai.infrastructure.storage.LoggingService import log_error
from utils import get_root_path, get_data_path
from src.bdai.domain.model.ScrapingError import ScrapingError


class ErrorStorageService:
    def __init__(self, execution_id: str, origin: int) -> None:
        self.file_path = os.sep.join([get_data_path(), 'errors', f'{execution_id}_{origin}.json'])
        self.error_list = []

    def save(self, error: ScrapingError) -> None:
        self.error_list.append(error)
        try :
            with open(self.file_path, 'w') as f:
                f.write(ScrapingError.schema().dumps(self.error_list, many=True))
        except Exception as e:
            log_error(error.to_json())

    def load(self) -> list[ScrapingError]:
        try:
            with open(self.file_path, 'r') as f:
                text = f.read()
                return ScrapingError.schema().loads(text, many=True)
        except FileNotFoundError:
            return []
