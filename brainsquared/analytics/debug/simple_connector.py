from __future__ import print_function

from cloudbrain.subscribers.PikaSubscriber import PikaSubscriber
from cloudbrain.settings import RABBITMQ_ADDRESS
import threading

import csv
import json
import time

device_id = "brainsquared"
device_name = "openbci"
metric = 'tag'

host = RABBITMQ_ADDRESS
buffer_size = 100

fname = 'test_{}.csv'.format(int(time.time()))
fieldnames = ['timestamp',
              'channel_0', 'channel_1', 'channel_2', 'channel_3',
              'channel_4', 'channel_5', 'channel_6', 'channel_7',
              'tag']

tag_subscriber = PikaSubscriber('module1', 'brainsquared', host, 'tag')
tag_subscriber.connect()

eeg_subscriber = PikaSubscriber(device_name, device_id, host, 'eeg')
eeg_subscriber.connect()

f_out = open(fname, 'w')
writer = csv.DictWriter(f_out, fieldnames=fieldnames)
writer.writeheader()

tag = "baseline"


def consume_tag(connection,deliver,properties,msg_s):
    global tag

    msg = json.loads(msg_s)
    tag = msg['value']

    print(msg)

def consume_eeg(connection,deliver,properties,msg_s):
    global tag
    print(tag)
    tag_copy = tag
    msg = json.loads(msg_s)
    for row in msg:
        row['tag'] = tag_copy
        writer.writerow(row)


    f_out.flush()
    # pass

t1 = threading.Thread(target=tag_subscriber.consume_messages, args=(consume_tag,))
t2 = threading.Thread(target=eeg_subscriber.consume_messages, args=(consume_eeg,))

t1.start()
t2.start()


