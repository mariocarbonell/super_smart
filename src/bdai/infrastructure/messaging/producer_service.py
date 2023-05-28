import paho.mqtt.client as paho
import json
from datetime import datetime

status = 0


def on_connect():
    global status
    status = 1


client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv311)
client.on_connect = on_connect
client.username_pw_set("[cloudamqp_user]", "[cloudamqp_password]")
client.connect("[cloudamqp_url]", 1883)


def produce_exception(text: str, origin: str) -> None:
    obj = {'origin': origin, 'command': 'exception', 'moment': datetime.now().isoformat(), 'traceback': text}
    client.publish("commands-dashboard", payload=json.dumps(obj), qos=1)


def produce_product(product_id: str, version: str, origin: str) -> None:
    obj = {'origin': origin, 'command': 'product', 'moment': datetime.now().isoformat(), 'id': product_id,
           'version': version}
    client.publish("commands-dashboard", payload=json.dumps(obj), qos=1)


def produce_begin(origin: str, version: str) -> None:
    obj = {'origin': origin, 'command': 'begin', 'moment': datetime.now().isoformat(), 'version': version}
    client.publish("commands-dashboard", payload=json.dumps(obj), qos=1)


def produce_end(origin: str, version: str) -> None:
    obj = {'origin': origin, 'command': 'end', 'moment': datetime.now().isoformat(), 'version': version}
    client.publish("commands-dashboard", payload=json.dumps(obj), qos=1)


def produce_abort_scraping() -> None:
    obj = {'command': 'abort_scraping', 'moment': datetime.now().isoformat()}
    client.publish("commands-dashboard", payload=json.dumps(obj), qos=1)


def produce_change_mode(mode: int, service: str = None) -> None:
    # if status:
    obj = {'command': 'change_mode', 'mode': mode, 'moment': datetime.now().isoformat()}
    if service:
        obj['service'] = service
    client.publish("commands-dashboard", payload=json.dumps(obj), qos=1)
