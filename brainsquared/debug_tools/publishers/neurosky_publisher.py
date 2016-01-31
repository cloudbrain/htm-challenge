import time
from consider import Consider
from brainsquared.publishers.PikaPublisher import PikaPublisher


def get_attention(p):
  timestamp = int(time.time() * 1000)
  data = {"timestamp": timestamp, "channel_0": p.attention}
  return data


if __name__ == "__main__":
  attention_threshold = 70
  
  host = "localhost"
  username = "guest"
  pwd = "guest"
  
  user = "brainsquared"
  device = "neurosky"
  metric = "attention"
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
    print "==> Signal quality: {}".format(p.poor_signal)
    
    if p.poor_signal == 0:
      print "Got good signal!"
      data = get_attention(p)
      
      if len(data_buffer) > buffer_size:
        pub.publish(routing_key, data_buffer)
        print "--> Published {}".format(data_buffer)
        data_buffer = []
      else:
        data_buffer.append(data)
    else:
      print "no signal yet"
  

