# -*- coding: utf-8 -*-

"""
Copyright Puzzlebox Productions, LLC (2010-2016)

Ported from Puzzlebox Synapse
ThinkGear code imported from Puzzlebox.Synapse.ThinkGear.Server
http://puzzlebox.io

This code is released under the GNU Pulic License (GPL) version 3
For more information please refer to http://www.gnu.org/copyleft/gpl.html

Author: Steve Castellotti <sc@puzzlebox.io>
"""

__changelog__ = """
Last Update: 2016.02.02
"""

import sys, signal
from brainsquared.publishers.PikaPublisher import PikaPublisher
import threading
from brainsquared.modules.sources import NeuroskyConnector

DEBUG = 1

THINKGEAR_DEVICE_SERIAL_PORT = '/dev/tty.MindWaveMobile-DevA'
THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA = False

RABBITMQ_HOST = 'localhost'
RABBITMQ_USERNAME = 'guest'
RABBITMQ_PASSWORD = 'guest'
PUBLISHER_USERNAME = 'brainsquared'
PUBLISHER_DEVICE = 'neurosky'
PUBLISHER_METRIC = 'mindwave'



def displayCSVHeader():
  print "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
    'timestamp',
    'eeg',
    'poorSignalLevel',
    'attention',
    'meditation',
    'delta',
    'theta',
    'lowAlpha',
    'highAlpha',
    'lowBeta',
    'highBeta',
    'lowGamma',
    'highGamma',
    'label',
  )



def displayCSV(packet):
  print "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
    packet['timestamp'],
    packet['eeg'],
    packet['poorSignalLevel'],
    packet['attention'],
    packet['meditation'],
    packet['delta'],
    packet['theta'],
    packet['lowAlpha'],
    packet['highAlpha'],
    packet['lowBeta'],
    packet['highBeta'],
    packet['lowGamma'],
    packet['highGamma'],
    packet['label'],
  )



class NeuroskySource(threading.Thread):
  def __init__(self, log,
               device_address=THINKGEAR_DEVICE_SERIAL_PORT,
               emulate_headset_data=THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA,
               server_host=RABBITMQ_HOST,
               server_username=RABBITMQ_USERNAME,
               server_password=RABBITMQ_PASSWORD,
               publisher_user=PUBLISHER_USERNAME,
               publisher_device=PUBLISHER_DEVICE,
               publisher_metric=PUBLISHER_METRIC,
               DEBUG=DEBUG,
               parent=None):

    threading.Thread.__init__(self, parent)

    self.protocol = None
    self.serial_device = None

    self.log = log
    self.DEBUG = DEBUG
    self.parent = parent

    self.device_address = device_address
    self.emulate_headset_data = emulate_headset_data

    self.attention_threshold = 70

    self.data = {
      'poorSignalLevel': 200, 'attention': 0, 'meditation': 0, 'delta': 0,
      'theta': 0, 'lowAlpha': 0, 'highAlpha': 0, 'lowBeta': 0, 'highBeta': 0,
      'lowGamma': 0, 'highGamma': 0, 'label': 0
    }

    self.host = server_host
    self.username = server_username
    self.pwd = server_password

    self.user = publisher_user
    self.device = publisher_device
    self.metric = publisher_metric

    # Send data efficiently in one packet
    self.buffer_size = 10
    self.data_buffer = []
    self.routing_key = "%s:%s:%s" % (self.user, self.device, self.metric)
    self.pub = PikaPublisher(self.host, self.username, self.pwd)
    self.pub.connect()
    self.pub.register(self.routing_key)

    # Also send each metric individually in cloudbrain format
    self.metrics = ['timestamp', 'eeg', 'poorSignalLevel', 'attention',
                    'meditation', 'delta', 'theta', 'lowAlpha', 'highAlpha',
                    'lowBeta', 'highBeta', 'lowGamma', 'highGamma']
    self.publishers = {}
    self.routing_keys = {}
    for metric in self.metrics:
      self.routing_keys[metric] = "%s:neurosky:%s" % (self.user, metric)
      self.publishers[metric] = PikaPublisher(self.host,
                                              self.username,
                                              self.pwd)

      self.publishers[metric].connect()
      self.publishers[metric].register(self.routing_keys[metric])

    # Send FFT
    self.fft_routing_key = "%s:%s:%s" % (self.user, self.device, "fft")
    self.fft_pub = PikaPublisher(self.host, self.username, self.pwd)
    self.fft_pub.connect()
    self.fft_pub.register(self.fft_routing_key)

    # Final setup
    self.configureEEG()
    displayCSVHeader()


  def setPacketCount(self, value):

    if self.parent is not None:
      self.parent.setPacketCount(value)


  def setBadPackets(self, value):

    if self.parent is not None:
      self.parent.setBadPackets(value)


  def incrementPacketCount(self):

    if self.parent is not None:
      self.parent.incrementPacketCount()


  def incrementBadPackets(self):

    if self.parent is not None:
      self.parent.incrementBadPackets()


  def resetSessionStartTime(self):

    if self.parent is not None:
      self.parent.resetSessionStartTime()


  def configureEEG(self):

    if not self.emulate_headset_data:

      self.serial_device = NeuroskyConnector.SerialDevice(
          self.log,
          device_address=self.device_address,
          DEBUG=0,
          parent=self)

      self.serial_device.start()

    else:
      self.serial_device = None

    self.protocol = NeuroskyConnector.puzzlebox_synapse_protocol_thinkgear(
        self.log,
        self.serial_device,
        device_model='NeuroSky MindWave',
        DEBUG=0,
        parent=self)

    self.protocol.start()


  def processPacketThinkGear(self, packet):

    if self.DEBUG > 2:
      print packet

    if 'rawEeg' in packet.keys():

      # packet['channel_0'] = packet.pop('rawEeg')
      packet['eeg'] = packet.pop('rawEeg')

      packet['poorSignalLevel'] = self.data['poorSignalLevel']
      packet['attention'] = self.data['attention']
      packet['meditation'] = self.data['meditation']
      packet['delta'] = self.data['delta']
      packet['theta'] = self.data['theta']
      packet['lowAlpha'] = self.data['lowAlpha']
      packet['highAlpha'] = self.data['highAlpha']
      packet['lowBeta'] = self.data['lowBeta']
      packet['highBeta'] = self.data['highBeta']
      packet['lowGamma'] = self.data['lowGamma']
      packet['highGamma'] = self.data['highGamma']
      packet['label'] = self.data['label']

      if self.DEBUG > 1:
        print packet
      else:
        displayCSV(packet)

      if len(self.data_buffer) > self.buffer_size:
        # Publish efficiently in one packet
        #self.pub.publish(self.routing_key, self.data_buffer)

        # Also send each metric individually in cloudbrain format
        for metric in self.metrics:
          buffer_out = []
          for packet in self.data_buffer:
            metric_data = {
              "timestamp": packet["timestamp"],
              "channel_0": packet[metric]
            }
            buffer_out.append(metric_data)
          self.publishers[metric].publish(self.routing_keys[metric],
                                          buffer_out)

        # Also send fft
        buffer_out = []
        for packet in self.data_buffer:
          metric_data = {
            "timestamp": packet["timestamp"],
            "channel_0": packet['lowAlpha'],
            "channel_1": packet['highAlpha'],
            "channel_2": packet['lowBeta'],
            "channel_3": packet['highBeta'],
            "channel_4": packet['lowGamma'],
            "channel_5": packet['highGamma'],
            "channel_6": packet['delta'],
            "channel_7": self.data['theta'],
          }
          buffer_out.append(metric_data)
        self.fft_pub.publish(self.fft_routing_key, buffer_out)

        if self.DEBUG > 1:
          print self.data_buffer
        self.data_buffer = []
        if self.DEBUG > 1:
          print "Publishing:",
          print self.routing_key
      else:
        self.data_buffer.append(packet)

    else:

      if 'poorSignalLevel' in packet.keys():
        self.data['poorSignalLevel'] = packet['poorSignalLevel']

      if 'eegPower' in packet.keys():
        self.data['delta'] = packet['eegPower']['delta']
        self.data['theta'] = packet['eegPower']['theta']
        self.data['lowAlpha'] = packet['eegPower']['lowAlpha']
        self.data['highAlpha'] = packet['eegPower']['highAlpha']
        self.data['lowBeta'] = packet['eegPower']['lowBeta']
        self.data['highBeta'] = packet['eegPower']['highBeta']
        self.data['lowGamma'] = packet['eegPower']['lowGamma']
        self.data['highGamma'] = packet['eegPower']['highGamma']

      if 'eSense' in packet.keys():
        if 'attention' in packet['eSense'].keys():
          self.data['attention'] = packet['eSense']['attention']

          if self.data['attention'] >= self.attention_threshold:
            self.data['label'] = 1
          else:
            self.data['label'] = 0

        if 'meditation' in packet['eSense'].keys():
          self.data['meditation'] = packet['eSense']['meditation']


  def resetDevice(self):

    if self.serial_device is not None:
      self.serial_device.exitThread()

    if self.protocol is not None:
      self.protocol.exitThread()

    self.configureEEG()


  def exitThread(self, callThreadQuit=True):

    # Call disconnect block in protocol first due to above error
    self.protocol.disconnectHardware()

    if self.serial_device is not None:
      self.serial_device.exitThread()

    if self.protocol is not None:
      self.protocol.exitThread()

    if callThreadQuit:
      if self.DEBUG:
        self.join()
      self.join()

    if self.parent is None:
      sys.exit()



if __name__ == "__main__":

  # Perform correct KeyboardInterrupt handling
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  log = None

  device_address = THINKGEAR_DEVICE_SERIAL_PORT
  server_host = RABBITMQ_HOST
  server_username = RABBITMQ_USERNAME
  server_password = RABBITMQ_PASSWORD
  publisher_user = PUBLISHER_USERNAME
  publisher_device = PUBLISHER_DEVICE
  publisher_metric = PUBLISHER_METRIC

  for each in sys.argv:
    if each.startswith("--interface="):
      server_interface = each[len("--interface="):]
    if each.startswith("--port="):
      server_port = each[len("--port="):]
    if each.startswith("--device="):
      device_address = each[len("--device="):]
    if each.startswith("--debug="):
      DEBUG = int(each[len("--debug="):])
    if each.startswith("--id="):
      device_id = int(each[len("--id="):])
    if each.startswith("--server_host="):
      server_host = each[len("--server_host="):]
    if each.startswith("--server_username="):
      server_username = each[len("--server_username="):]
    if each.startswith("--server_password="):
      server_password = each[len("--server_password="):]
    if each.startswith("--publisher_user="):
      publisher_user = each[len("--publisher_user="):]
    if each.startswith("--publisher_device="):
      publisher_device = each[len("--publisher_device="):]
    if each.startswith("--publisher_metric="):
      publisher_metric = each[len("--publisher_metric="):]

  publisher = NeuroskySource(
      log,
      device_address=device_address,
      emulate_headset_data=THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA,
      server_host=server_host,
      server_username=server_username,
      server_password=server_password,
      publisher_user=publisher_user,
      publisher_device=publisher_device,
      publisher_metric=publisher_metric,
      DEBUG=DEBUG)

  publisher.start()
