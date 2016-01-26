import csv
import time

from brainsquared.publishers.PikaPublisher import PikaPublisher

buffer_size = 128
csvFile = "data/motor_data.csv"

host = "localhost"
username = "guest"
pwd = "guest"

user = "brainsquared"
device = "openbci"
metric = "eeg"
routing_key = "%s:%s:%s" % (user, device, metric)

pub = PikaPublisher(host, username, pwd)
pub.connect()
pub.register(routing_key)

f = open(csvFile, "rb")
csvReader = csv.reader(f)
headers = csvReader.next()[:-1] # No tag 

data_buffer = []
rewindCounter = 0
print "[DEBUG] Publishing data to '%s' on queue '%s'" % (host, str(routing_key))
while 1:
  time.sleep(0.0001)
  try:
    row = csvReader.next()
    if len(data_buffer) < buffer_size:
      data_buffer.append(dict(zip(headers, row[:-1])))
    else:
      pub.publish(routing_key, data_buffer)
      print data_buffer
      data_buffer = []        

  except StopIteration:
    print "End of CSV file. Rewinding. Iteration %s." % rewindCounter
    f.close()
    f = open(csvFile, "rb")
    csvReader = csv.reader(f)
    headers = csvReader.next()[:-1] # no tag
    rewindCounter += 1
