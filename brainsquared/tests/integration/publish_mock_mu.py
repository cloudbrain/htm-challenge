import random
import time

from brainsquared.publishers.PikaPublisher import PikaPublisher

host = "rabbitmq.cloudbrain.rocks"
username = "cloudbrain"
pwd = "cloudbrain"

user = "brainsquared"
device = "openbci"
metric = "mu"
routing_key = "%s:%s:%s" % (user, device, metric)

pub = PikaPublisher(host, username, pwd)
pub.connect()
pub.register(routing_key)

mu_data = {"timestamp": random.random(), "value": random.random()}
while 1:
  try:
    pub.publish(routing_key, mu_data)
    time.sleep(0.1)
  except KeyboardInterrupt:
    pub.disconnect()
