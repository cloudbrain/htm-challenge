# -*- coding: utf-8 -*-
import json
import logging
import argparse

from collections import defaultdict
from sockjs.tornado.conn import SockJSConnection
from sockjs.tornado import SockJSRouter
from tornado.ioloop import IOLoop

from brainsquared.websocket_server.TornadoSubscriber import TornadoSubscriber

_SERVER_PORT = 31415
_RABBITMQ_ADDRESS = "localhost"
_RABBITMQ_LOGIN = "guest"
_RABBITMQ_PWD = "guest"

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

recursivedict = lambda: defaultdict(recursivedict)
rabbimq_address = _RABBITMQ_ADDRESS
rabbimq_user = _RABBITMQ_LOGIN
rabbimq_pwd = _RABBITMQ_PWD



def get_args_parser():
  parser = argparse.ArgumentParser()

  parser.add_argument('-s', '--server',
                      default=_RABBITMQ_ADDRESS,
                      help="The address of the RabbitMQ server you are "
                           "sending data to.")
  parser.add_argument('-u', '--user',
                      default=_RABBITMQ_LOGIN,
                      help="The login to authenticate with the RabbitMQ "
                           "instance you are sending data to.\n")
  parser.add_argument('-p', '--pwd',
                      default=_RABBITMQ_PWD,
                      help="The password to authenticate with the RabbitMQ "
                           "instance you are sending data to.\n")
  return parser



def get_opts():
  parser = get_args_parser()
  opts = parser.parse_args()
  return opts



class WebsocketConnection(SockJSConnection):
  clients = set()


  def __init__(self, session):
    super(self.__class__, self).__init__(session)
    self.subscribers = recursivedict()


  def send_probe_factory(self, device_id, device_name, metric):

    def send_probe(body):
      _LOGGER.debug("GOT: " + body)
      buffer_content = json.loads(body)

      for record in buffer_content:
        record["device_id"] = device_id
        record["device_name"] = device_name
        record["metric"] = metric
        self.send(json.dumps(record))


    return send_probe


  def on_open(self, info):
    _LOGGER.info("Got a new connection...")
    self.clients.add(self)


  def on_message(self, message):
    """
    This will receive instructions from the client to change the
    stream. After the connection is established we expect to receive a JSON
    with deviceName, deviceId, metric; then we subscribe to RabbitMQ and
    start streaming the data.
    
    NOTE: it's not possible to open multiple connections from the same client.
          so in case we need to stream different devices/metrics/etc. at the
          same time, we need to use a solution that is like the multiplexing
          in the sockjs-tornado examples folder.

    """
    _LOGGER.info("Got a new message: " + message)

    msg_dict = json.loads(message)
    if msg_dict['type'] == 'subscription':
      self.handle_channel_subscription(msg_dict)
    elif msg_dict['type'] == 'unsubscription':
      self.handle_channel_unsubscription(msg_dict)


  def handle_channel_subscription(self, stream_configuration):
    device_name = stream_configuration['deviceName']
    device_id = stream_configuration['deviceId']
    metric = stream_configuration['metric']

    if not self.metric_exists(device_id, device_name, metric):
      self.subscribers[device_id][device_name][metric] = TornadoSubscriber(
          callback=self.send_probe_factory(device_id, device_name, metric),
          device_name=device_name,
          device_id=device_id,
          rmq_address=rabbimq_address,
          rmq_user=rabbimq_user,
          rmq_pwd=rabbimq_pwd,
          metric_name=metric)

      self.subscribers[device_id][device_name][metric].connect()


  def handle_channel_unsubscription(self, unsubscription_msg):
    device_name = unsubscription_msg['deviceName']
    device_id = unsubscription_msg['deviceId']
    metric = unsubscription_msg['metric']

    _LOGGER.info("Unsubscription received for device_id: %s, "
                 "device_name: %s, metric: %s"
                 % (device_id, device_name, metric))
    if self.metric_exists(device_id, device_name, metric):
      self.subscribers[device_id][device_name][metric].disconnect()


  def on_close(self):
    _LOGGER.info("Disconnecting client...")
    for device_id in self.subscribers:
      for device_name in self.subscribers[device_id]:
        for metric in self.subscribers[device_id][device_name]:
          subscriber = self.subscribers[device_id][device_name][metric]
          if subscriber is not None:
            _LOGGER.info("Disconnecting subscriber for device_id: "
                         "%s, device_name: %s, metric: %s"
                         % (device_id, device_name, metric))
            subscriber.disconnect()

    self.subscribers = {}
    self.clients.remove(self)
    _LOGGER.info("Client disconnection complete!")


  def send_heartbeat(self):
    self.broadcast(self.clients, 'message')


  def metric_exists(self, device_id, device_name, metric):
    return (self.subscribers.has_key(device_id)
            and self.subscribers[device_id].has_key(device_name)
            and self.subscribers[device_id][device_name].has_key(metric))



if __name__ == "__main__":
  # 0. Toggle RabbitMQ options 
  opts = get_opts()
  rabbimq_address = opts.server
  rabbimq_user = opts.user
  rabbimq_pwd = opts.pwd

  # 1. Create chat router
  WebsocketRouter = SockJSRouter(WebsocketConnection, '/websocket')
  _LOGGER.info("Websocket server running at http://localhost:%s" %
               _SERVER_PORT)

  # 4. Start IOLoop
  IOLoop.instance().start()
