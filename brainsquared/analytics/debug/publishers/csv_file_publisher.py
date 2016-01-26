import csv
import time

from brainsquared.publishers.PikaPublisher import PikaPublisher

bufer_size = 10
# csvFile = "data/motor_data.csv"
csvFile = "data/mu_motor_data.csv"

host = "localhost"
username = "cloudbrain"
pwd = "cloudbrain"

user = "brainsquared"
device = "openbci"
# metric = "eeg"
metric = "mu"
routing_key = "%s:%s:%s" % (user, device, metric)

pub = PikaPublisher(host, username, pwd)
pub.connect()
pub.register(routing_key)

f = open(csvFile, "rb")
csvReader = csv.reader(f)
headers = csvReader.next()

data_buffer = []
rewindCounter = 0
print "[DEBUG] Publishing data to '%s' on queue '%s'" % (host, str(routing_key))
while 1:
  time.sleep(0.01)
  try:
    row = csvReader.next()
    if len(data_buffer) < bufer_size:
      data_buffer.append(dict(zip(headers, row)))
    else:
      try:
        pub.publish(routing_key, data_buffer)
      except KeyboardInterrupt:
        pub.disconnect()
      data_buffer = []
  except StopIteration:
    print "End of CSV file. Rewinding. Iteration %s." % rewindCounter
    f.close()
    f = open(csvFile, "rb")
    csvReader = csv.reader(f)
    headers = csvReader.next()
    rewindCounter += 1
