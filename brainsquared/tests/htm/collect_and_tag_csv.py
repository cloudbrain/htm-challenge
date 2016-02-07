"""
Collect training data and write them to a CSV.
"""
import argparse
import csv
import logging
import json
import sys
import time
import threading

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
_CSV_FILE = "data/training-data-%(tag)s-%(channel)s.csv"
_SUPPORTED_DEVICES = get_supported_devices()

_TIME_OFFSET = 2000  # 2s
_RECORDING_TIME = 10000  # 10s



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
                      default=True,
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
    self.start_time = int(time.time() * 1000)
    self.tag = tag
    self.convert_to_nupic = convert_to_nupic
    self.channels = channels
    self.row_counter = 0
    self.csv_writers = {
      channel: csv.writer(open(_CSV_FILE % {"tag": tag, 
                                            "channel": channel}, "wb"))
      for channel in self.channels}

    headers = ["x", "y", "label"]
    flags = ["", "", "C"]
    types = ["int", "float", "int"]
    # first rows of the file
    for channel in self.channels:
      csv_writer = self.csv_writers[channel]
      csv_writer.writerow(headers)
      if self.convert_to_nupic:
        csv_writer.writerow(types)
        csv_writer.writerow(flags)


  def write_csv_files(self, ch, method, properties, body):

    buffer = json.loads(body)
    for data in buffer:
      _LOGGER.debug(data)
      _LOGGER.debug("poorSignalLevel")

      now = int(time.time() * 1000)
      if now > _TIME_OFFSET:

        for channel_name in self.channels:
          writer = self.csv_writers[channel_name]
          row = []

          if "timestamp" not in data.keys():
            row.append(self.row_counter)
          else:
            row.append(int(data["timestamp"]))

          row.append(float(data[channel_name]))
          row.append(int(self.tag))
          writer.writerow(row)
          _LOGGER.info("Wrote row: %s" % row)

        self.row_counter += 1

      if now > _RECORDING_TIME + self.start_time:
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
  sub.subscribe(routing_key, csv_writer.write_csv_files)
