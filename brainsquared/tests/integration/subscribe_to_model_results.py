import json
from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

host = "rabbitmq.cloudbrain.rocks"
username = "cloudbrain"
pwd = "cloudbrain"

user = "brainsquared"
device = "openbci"
metric = "classification"
routing_key = "%s:%s:%s" % (user, device, metric)

sub = PikaSubscriber(host, username, pwd)
sub.connect()
sub.subscribe(routing_key)

def _print_message(ch, method, properties, body):
  print body


while 1:
  try:
    (a,c,b) = sub.get_one_message(routing_key)
    if b:
      print json.loads(b)
  except KeyboardInterrupt:
    sub.disconnect()

