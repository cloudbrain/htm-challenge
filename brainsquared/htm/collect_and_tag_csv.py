"""
Collect training data and write them to a CSV.
"""
import argparse
import csv
import logging
import json
import sys

from brainsquared.subscribers.PikaSubscriber import PikaSubscriber
from brainsquared.utils.metadata import get_supported_devices

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

_RABBITMQ_ADDRESS = "localhost"
_RABBITMQ_LOGIN = "guest"
_RABBITMQ_PWD = "guest"
_USER = "brainsquared"
_DEVICE = "wildcard"
_METRIC = "motor_imagery"

_ROUTING_KEY = "%s:%s:%s"
_CSV_FILE = "data/training-data[%s].csv"
_SUPPORTED_DEVICES = get_supported_devices()

_ROW_OFFSET = 2000
_NUM_ROWS = 10000



def get_args_parser():
  parser = argparse.ArgumentParser()

  parser.add_argument('-s', '--server',
                      default=_RABBITMQ_ADDRESS,
                      help="The address of the RabbitMQ server you are "
                           "sending data to.")
  parser.add_argument('-l', '--login',
                      default=_RABBITMQ_LOGIN,
                      help="The login to authenticate with the RabbitMQ "
                           "instance you are sending data to.\n")
  parser.add_argument('-p', '--pwd',
                      default=_RABBITMQ_PWD,
                      help="The password to authenticate with the RabbitMQ "
                           "instance you are sending data to.\n")
  parser.add_argument('-u', '--user',
                      default=_USER,
                      help="The user ID.")
  parser.add_argument('-d', '--device',
                      default=_DEVICE,
                      help="The device type. Supported devices: %s"
                           % _SUPPORTED_DEVICES)
  parser.add_argument('-m', '--metric',
                      default=_METRIC,
                      help="The name of the metric.")

  parser.add_argument('-c', '--channels',
                      required=True,
                      help="List of channel names")

  parser.add_argument('-t', '--tag',
                      required=True,
                      help="The tag of the data that will be recorded.")
  
  parser.add_argument('-n', '--nupic',
                      default=False,
                      help="Make CSV compliant with the NuPIC format (add "
                           "two CSV headeres: types and flags).")

  return parser



def get_opts():
  parser = get_args_parser()
  opts = parser.parse_args()
  return opts



class CSVWriter(object):
  """Handles the logic to write, convert, and tag data"""
  
  def __init__(self, tag, channels, convert_to_nupic):
    self.tag = tag
    self.convert_to_nupic = convert_to_nupic
    self.out_file = _CSV_FILE % tag
    self.csv_writer = csv.writer(open(self.out_file, "wb"))
    self.channels = channels
    self.headers = []
    self.counter = 0

    # convert channel names to channel_X, except for the timestamp.
    self.headers.append("timestamp")
    if "timestamp" in self.channels:
      self.channels.pop("timestamp")
    for channel in self.channels:
      self.headers.append("channel_%s" % self.channels.index(channel))
    self.headers.append("label")

    # first rows of the file
    self.csv_writer.writerow(self.headers)

    if self.convert_to_nupic:
      types = ["int"]  # timestamp
      for _ in self.channels:
        types.append("float")  # channel values
      types.append("int")  # category
      self.csv_writer.writerow(types)
  
      flags = [""]  # timestamp
      for _ in self.channels:
        flags.append("")  # channel values
      flags.append("C")  # category
      self.csv_writer.writerow(flags)


  def write_csv(self, ch, method, properties, body):

    buffer = json.loads(body)
    for data in buffer:
      _LOGGER.debug(data)
      # print data["poorSignalLevel"]
      
      if self.counter > _ROW_OFFSET:
        row = []
        if "timestamp" not in data.keys():
          row.append(self.counter)
        else:
          row.append(data["timestamp"])

        for channel_name in self.channels:
          row.append(data[channel_name])
        row.append(self.tag)
        self.csv_writer.writerow(row)
        _LOGGER.info("Wrote row: %s" % row)

      self.counter += 1
      if self.counter == _NUM_ROWS:
        sys.exit(1)



if __name__ == "__main__":
  opts = get_opts()
  host = opts.server
  username = opts.login
  pwd = opts.pwd
  user = opts.user
  device = opts.device
  metric = opts.metric
  channels = json.loads(opts.channels)
  tag = int(opts.tag)
  convert_to_nupic = bool(opts.nupic) 
  routing_key = _ROUTING_KEY % (user, device, metric)

  sub = PikaSubscriber(host, username, pwd)
  sub.connect()
  sub.register(routing_key)

  _LOGGER.info("Consuming messages from queue '%s' at '%s'"
               % (routing_key, host))

  csv_writer = CSVWriter(tag, channels, convert_to_nupic)
  while 1:
    try:
      sub.subscribe(routing_key, csv_writer.write_csv)
    except KeyboardInterrupt:
      sub.disconnect()
