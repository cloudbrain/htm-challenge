from brainsquared.subscribers.PikaSubscriber import PikaSubscriber

import json



def _print_message(ch, method, properties, body):
  # print ch, method, properties, body
  buffer = json.loads(body)
  for data in buffer:
    print data



if __name__ == "__main__":
  # host = "rabbitmq.cloudbrain.rocks"
  # username = "cloudbrain"
  # pwd = "cloudbrain"

  host = "localhost"
  username = "guest"
  pwd = "guest"

  user = "brainsquared"
  device = "wildcard"
  metric = "classification"
  routing_key = "%s:%s:%s" % (user, device, metric)

  sub = PikaSubscriber(host, username, pwd)
  sub.connect()
  sub.register(routing_key)

  msg = sub.get_one_message(routing_key)
  print "[DEBUG] de-queued one message: %s" % str(msg)

  print "[DEBUG] Consuming messages from queue '%s' at '%s'" % (routing_key,
                                                                host)
  while 1:
    try:
      sub.subscribe(routing_key, _print_message)
    except KeyboardInterrupt:
      sub.disconnect()
