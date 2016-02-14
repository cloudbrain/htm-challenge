import json

from brainsquared.subscribers.PikaSubscriber import PikaSubscriber



def _print_message(ch, method, properties, body):
  buffer = json.loads(body)
  for data in buffer:
    print data



if __name__ == "__main__":
  host = "127.0.0.1"
  username = "guest"
  pwd = "guest"

  user = "brainsquared"
  device = "neurosky"
  metric = "attention"
  routing_key = "%s:%s:%s" % (user, device, metric)

  sub = PikaSubscriber(host, username, pwd)
  sub.connect()
  sub.register(routing_key)

  print "[DEBUG] Consuming messages from queue '%s' at '%s'" % (routing_key,
                                                                host)
  while 1:
    try:
      sub.subscribe(routing_key, _print_message)
    except KeyboardInterrupt:
      sub.disconnect()
