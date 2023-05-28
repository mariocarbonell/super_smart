from src.bdai.domain.model.Execution import Execution
from src.bdai.infrastructure.storage.LoggingService import log_error
from src.bdai.infrastructure.storage.mongo.MongoUtils import get_mongo_client


class MongoExecutionsService:

    def __init__(self, origin: str):
        self.origin = origin
        self.collection = get_mongo_client()['executions']['executions']

    def exists(self, execution_id: str, origin: str) -> bool:
        try:
            return len(list(self.collection.find({'id': execution_id, 'origin': origin}))) > 0
        except Exception as e:
            log_error()

    def create(self, execution: Execution):
        try:
            if self.exists(execution_id=execution.id, origin=self.origin):
                raise Exception('Execution already exists on MongoDB')
            else:
                obj = execution.to_dict()
                obj['origin'] = self.origin
                self.collection.insert_one(obj)
        except Exception as e:
            log_error()

    def update(self, execution: Execution):
        try:
            if self.exists(execution_id=execution.id, origin=self.origin):
                self.collection.update_one({'id': execution.id, 'origin': self.origin}, {'$set': execution.to_dict()})
            else:
                raise Exception('Execution not exists on MongoDB')
        except Exception as e:
            log_error()
