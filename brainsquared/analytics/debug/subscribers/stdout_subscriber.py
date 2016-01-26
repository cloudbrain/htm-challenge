from brainsquared.subscribers.PikaSubscriber import PikaSubscriber



def _print_message(ch, method, properties, body):
  # print ch, method, properties, body
  print body



if __name__ == "__main__":
  host = "localhost"
  username = "cloudbrain"
  pwd = "cloudbrain"

  user = "brainsquared"
  device = "openbci"
  metric = "mu"
  routing_key = "%s:%s:%s" % (user, device, metric)

  sub = PikaSubscriber(host, username, pwd)
  sub.connect()
  sub.subscribe(routing_key)

  msg = sub.get_one_message(routing_key)
  print "[DEBUG] de-queued one message: %s" % str(msg)

  print "[DEBUG] Consuming messages from queue '%s' at '%s'" % (routing_key,
                                                                host)
  while 1:
    try:
      sub.consume_messages(routing_key, _print_message)
    except KeyboardInterrupt:
      sub.disconnect()
