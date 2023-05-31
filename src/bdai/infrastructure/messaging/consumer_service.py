import paho.mqtt.client as paho
import json

from src.bdai.domain.service.ExecutionService import ExecutionService
from src.bdai.infrastructure.messaging.producer_service import produce_change_mode
from src.bdai.infrastructure.storage.LoggingService import log_info


def active_consumer() -> None:
    """
    funcion que se subscribe al topic y ejecuta los comandos recibidos
    """
    def on_message(client, userdata, msg):
        """
        funcion que se ejecuta cuando se recibe un comando

        :param client:
        :param userdata:
        :param msg:
        """
        message = json.loads(msg.payload)
        log_info('onmessage: ' + message['command'])
        execution_service: ExecutionService = ExecutionService()
        if message['command'] == 'start_service':
            execution_service.execute(service=message['service'])
        elif message['command'] == 'start_all':
            execution_service.execute()
        elif message['command'] == 'abort':
            execution_service.abort = True

    client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv311)
    client.username_pw_set("[cloudamqp_user]", "[cloudamqp_password]")
    client.connect("[cloudamqp_url]", 1883)
    client.subscribe("commands-scraping", qos=1)
    client.on_message = on_message
    log_info('begin - consumer')
    produce_change_mode(mode=3)
    client.loop_forever()
