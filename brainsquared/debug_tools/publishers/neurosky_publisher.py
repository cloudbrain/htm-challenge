import time
from consider import Consider
from brainsquared.publishers.PikaPublisher import PikaPublisher


def get_tag(p, attention_threshold):
  if p.attention > attention_threshold:
    tag = 1
  else:
    tag = 0
  return tag


def get_raw_eeg(p):
  timestamp = int(time.time() * 1000)
  raw_eeg_record = {"timestamp": timestamp, "channel_0": None}
  return  raw_eeg_record


if __name__ == "__main__":
  attention_threshold = 70
  
  host = "localhost"
  username = "guest"
  pwd = "guest"
  
  user = "brainsquared"
  device = "neurosky"
  metric = "eeg"
  routing_key = "%s:%s:%s" % (user, device, metric)
  
  buffer_size = 128
  data_buffer = []
  
  pub = PikaPublisher(host, username, pwd)
  pub.connect()
  pub.register(routing_key)
  
  con = Consider()
  
  print "Ready to publish data to '%s' on queue '%s'" % (host, str(routing_key))
  print "Waiting for BCI headset signal ..."
  for p in con.packet_generator():
    if p.poor_signal == 0:
      
      tag = get_tag(p, attention_threshold)
      raw_eeg = get_raw_eeg(p)
      
      if len(data_buffer) > buffer_size:
        pub.publish(routing_key, data_buffer)
        data_buffer = []
      else:
        data_buffer.append(raw_eeg)
    else:
      print "no signal yet"
  

