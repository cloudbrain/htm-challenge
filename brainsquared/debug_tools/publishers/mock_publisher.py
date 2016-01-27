import time
import random

from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.utils.metadata import get_num_channels



class MockPublisher(object):
  def __init__(self, user, device, metric):
    self.routing_key = "%s:%s:%s" % (user, device, metric)
    self.num_channels = get_num_channels(device, metric)
    self.pub = None


  def connect(self, host, username, pwd):
    self.pub = PikaPublisher(host, username, pwd)
    self.pub.connect()
    self.pub.register(self.routing_key)
    print "Connected to: {}".format(host)


  def publish(self, buffer_size):

    print "Publishing on queue: {}".format(self.routing_key)

    data = {"timestamp": int(time.time() * 1000)}
    for i in xrange(self.num_channels):
      data["channel_%s" % i] = random.random() * 10

    data_buffer = []
    while 1:
      time.sleep(0.0001)
      if len(data_buffer) < buffer_size:
        data_buffer.append(data)
      else:
        self.pub.publish(self.routing_key, data_buffer)
        print data_buffer
        data_buffer = []



if __name__ == "__main__":
  BUFFER_SIZE = 128

  HOST = "localhost"
  USERNAME = "guest"
  PWD = "guest"

  USER_ID = "brainsquared"
  DEVICE = "neurosky"
  METRIC = "eeg"

  mock_pub = MockPublisher(USER_ID, DEVICE, METRIC)
  mock_pub.connect(HOST, USERNAME, PWD)
  mock_pub.publish(BUFFER_SIZE)
