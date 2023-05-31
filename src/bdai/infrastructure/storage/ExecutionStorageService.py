import os

from src.bdai.infrastructure.storage.mongo.MongoExecutionsService import MongoExecutionsService
from utils import get_data_path
from src.bdai.domain.model.Execution import Execution


class ExecutionStorageService:
    """Clase que gestiona la persistencia de los registros de ejecuciones en todos los medios definidos"""

    def __init__(self, origin: str) -> None:
        self.origin = origin
        self.file_path = os.sep.join([get_data_path(), f'{origin}.json'])
        self.database_service = MongoExecutionsService(origin=origin)

    def insert(self, execution: Execution) -> None:
        """
        Metodo que almacena una ejecucion en todos los metodos definidos

        * Base de datos MongoDB
        * fichero en DataLake

        :param execution:
        """
        executions = self.load()
        executions.append(execution)
        self.database_service.create(execution=execution)
        with open(self.file_path, 'w+') as f:
            f.write(Execution.schema().dumps(executions, many=True))

    def update(self, execution: Execution) -> None:
        """
        Metodo que actualiza y finaliza una ejecucion en todos los metodos definidos

        * Base de datos MongoDB
        * fichero en DataLake

        :param execution:
        """
        executions = self.load()
        if executions:
            executions = executions[:-1]
        executions.append(execution)
        self.database_service.update(execution=execution)
        with open(self.file_path, 'w+') as f:
            f.write(Execution.schema().dumps(executions, many=True))

    def load(self) -> list[Execution]:
        try:
            with open(self.file_path, 'r+') as f:
                text = f.read()
                return Execution.schema().loads(text, many=True)
        except FileNotFoundError:
            return []
