import json
import pika

from brainsquared.publishers.PublisherInterface import PublisherInterface



class PikaPublisher(PublisherInterface):
  """
  Publisher implementation for RabbitMQ via the Pika client
  """


  def __init__(self, rabbitmq_address, user, password):
    super(PikaPublisher, self).__init__(rabbitmq_address)
    self.user = user
    self.password = password
    self.connection = None
    self.channels = {}


  def connect(self):
    credentials = pika.PlainCredentials(self.user, self.password)

    self.connection = pika.BlockingConnection(pika.ConnectionParameters(
      host=self.host, credentials=credentials))


  def disconnect(self):
    for (routing_key, channel) in self.channels.items():
      if channel:
        channel.close()
    self.connection.close()


  def register(self, routing_key):
    channel = self.connection.channel()
    channel.exchange_declare(exchange=routing_key,
                             type='direct')
    self.channels[routing_key] = channel


  def publish(self, routing_key, data):
    self.channels[routing_key].basic_publish(exchange=routing_key,
                                             routing_key=routing_key,
                                             body=json.dumps(data),
                                             properties=pika.BasicProperties(
                                               delivery_mode=2,
                                               # makes the message persistent
                                             ))


if __name__ == "__main__":
  
  host = "rabbitmq.cloudbrain.rocks"
  username = "cloudbrain"
  pwd = "cloudbrain"
  
  user = "test"
  device = "openbci"
  metric = "mu"
  routing_key = "%s:%s:%s" % (user, device, metric)
  
  pub = PikaPublisher(host, username, pwd)
  pub.connect()
  pub.register(routing_key)
  
  while 1:
    try:
      pub.publish(routing_key, {"timestamp": 0, "value": 0})
    except KeyboardInterrupt:
      pub.disconnect()