import pika
from cloudbrain.subscribers.SubscriberInterface import SubscriberInterface
from cloudbrain.utils.metadata_info import get_metrics_names
from cloudbrain.settings import RABBITMQ_ADDRESS



class PikaSubscriber(SubscriberInterface):
  def __init__(self, rabbitmq_address, user, password):
    super(PikaSubscriber, self).__init__(rabbitmq_address)
    self.user = user
    self.password = password
    self.connection = None
    self.channels = {}


  def connect(self):
    credentials = pika.PlainCredentials(self.user, self.password)
    self.connection = pika.BlockingConnection(pika.ConnectionParameters(
      host=self.host, credentials=credentials))


  def subscribe(self, routing_key):
    channel = self.connection.channel()
    channel.exchange_declare(exchange=routing_key,
                             type='direct')

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=routing_key,
                       queue=queue_name,
                       routing_key=routing_key)

    self.channels[routing_key] = [channel, queue_name]


  def disconnect(self):
    for (routing_key, channel) in self.channels.items():
      channel[0].stop_consuming()
    self.connection.close()


  def consume_messages(self, routing_key, callback):
    
    channel = self.channels[routing_key][0]
    queue_name =  self.channels[routing_key][1]

    channel.basic_consume(callback,
                          queue=queue_name,
                          exclusive=True,
                          no_ack=True)

    channel.start_consuming()



  def get_one_message(self, routing_key):
    # for method, properties, body in self.channel.consume(self.queue_name, 
    #                                                      exclusive=True, 
    #                                                      no_ack=True):
    #   return body
    
    channel = self.channels[routing_key][0]
    queue_name =  self.channels[routing_key][1]
    meth_frame, header_frame, body = channel.basic_get(queue_name)
    return (meth_frame, header_frame, body)



def _print_message(ch, method, properties, body):
  #print ch, method, properties, body
  print body



if __name__ == "__main__":

  host = "localhost"
  username = "guest"
  pwd = "guest"

  user = "test"
  device = "muse"
  metric = "eeg"
  routing_key = "%s:%s:%s" % (user, device, metric)

  sub = PikaSubscriber(host, username, pwd)
  sub.connect()
  sub.subscribe(routing_key)

  print sub.get_one_message(routing_key)

  while 1:
    try:
      sub.consume_messages(routing_key, _print_message)
    except KeyboardInterrupt:
      sub.disconnect()
