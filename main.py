from src.bdai.domain.service.ExecutionService import ExecutionService
from src.bdai.infrastructure.messaging.consumer_service import active_consumer
from src.bdai.infrastructure.messaging.producer_service import produce_change_mode

from utils import get_data_path
import os

import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Execute scraping service')
    parser.add_argument('--service', type=str, nargs='?', default=None)
    parser.add_argument('--stream', type=bool, nargs='?', default=False)

    args = parser.parse_args()

    if not os.path.exists(get_data_path()):
        raise Exception('Data folder not found')

    if args.stream:
        active_consumer()
    else:
        if args.service:
            execution_service: ExecutionService = ExecutionService()
            produce_change_mode(mode=2, service=args.service)
            execution_service.execute(service=args.service)
        else:
            execution_service: ExecutionService = ExecutionService()
            produce_change_mode(mode=1)
            execution_service.execute()

