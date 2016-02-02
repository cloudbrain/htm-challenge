"""
Script to collect EEG data and tag it.
"""
import threading
import csv
import json
import time
import os

from brainsquared.subscribers.PikaSubscriber import PikaSubscriber



def consume_tag(connection, deliver, properties, msg_s):
  global tag

  msg = json.loads(msg_s)
  tag = msg['value']

  print "Got tag: %s" % tag



def consume_eeg(connection, deliver, properties, msg_s):
  global tag
  tag_copy = tag
  msg = json.loads(msg_s)
  for row in msg:
    row['tag'] = tag_copy
    writer.writerow(row)
  f_out.flush()



if __name__ == "__main__":

  device_id = "brainsquared"
  device_name = "openbci"
  tag_routing_key = "%s:%s:%s" % (device_id, device_name, "tag")
  eeg_routing_key = "%s:%s:%s" % (device_id, device_name, "eeg")

  host = "localhost"
  username = "guest"
  pwd = "guest"

  buffer_size = 100
  data_dir = "data"

  fieldnames = ['timestamp',
                'channel_0', 'channel_1', 'channel_2', 'channel_3',
                'channel_4', 'channel_5', 'channel_6', 'channel_7',
                'tag']

  if not os.path.exists(data_dir):
    os.makedirs(data_dir)

  file_name = '{}/test_{}.csv'.format(data_dir, int(time.time()))

  tag_subscriber = PikaSubscriber(host, username, pwd)
  tag_subscriber.connect()
  tag_subscriber.register(tag_routing_key)

  eeg_subscriber = PikaSubscriber(host, username, pwd)
  eeg_subscriber.connect()
  eeg_subscriber.register(eeg_routing_key)

  f_out = open(file_name, 'w')
  writer = csv.DictWriter(f_out, fieldnames=fieldnames)
  writer.writeheader()

  tag = 0

  t1 = threading.Thread(target=tag_subscriber.subscribe,
                        args=(tag_routing_key, consume_tag,))
  t2 = threading.Thread(target=eeg_subscriber.subscribe,
                        args=(eeg_routing_key, consume_eeg,))

  t1.start()
  t2.start()
