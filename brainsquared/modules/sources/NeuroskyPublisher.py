# -*- coding: utf-8 -*-

"""
Copyright Puzzlebox Productions, LLC (2016)

Ported from Puzzlebox Synapse
Publisher code imported from Puzzlebox.Synapse.Cloudbrain.Publisher
http://puzzlebox.io

This code is released under the Affero GNU Pulic License (AGPL) version 3
For more information please refer to https://www.gnu.org/licenses/agpl.html

Author: Steve Castellotti <sc@puzzlebox.io>
"""

__changelog__ = """
Last Update: 2016.02.12
"""

DEBUG = 1


import time
from brainsquared.publishers.PikaPublisher import PikaPublisher


try:
	import Puzzlebox.Synapse.Configuration as configuration
except:

	class Configuration():
		
		def __init__(self):
		
			# Ported from Puzzlebox.Synapse.Configuration
			
			self.DEBUG = 1
			
			self.ENABLE_QT = False
			self.ENABLE_PYSIDE = False
			
			self.RABBITMQ_HOST = 'localhost'
			self.RABBITMQ_USERNAME = 'guest'
			self.RABBITMQ_PASSWORD = 'guest'
			self.PUBLISHER_USERNAME = 'brainsquared'
			self.PUBLISHER_DEVICE = 'neurosky'
			self.PUBLISHER_METRIC = 'mindwave'
			
			#THINKGEAR_DEVICE_SERIAL_PORT = '/dev/tty.MindWaveMobile-DevA'
			#THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA = False
	
	
	configuration = Configuration()


if configuration.ENABLE_QT:
	if configuration.ENABLE_PYSIDE:
		try:
			import PySide
			from PySide import QtCore
			Thread = PySide.QtCore.QThread
		except Exception, e:
			print "ERROR: Exception importing PySide:",
			print e
			configuration.ENABLE_PYSIDE = False
		else:
			print "INFO: [Synapse:Cloudbrain:Publisher] Using PySide module"
	
	if not configuration.ENABLE_PYSIDE:
		try:
			print "INFO: [Synapse:Cloudbrain:Publisher] Using PyQt4 module"
			from PyQt4 import QtCore
		except:
			configuration.ENABLE_QT = False


if not configuration.ENABLE_QT:
	import threading
	Thread = threading.Thread


#####################################################################
# Classes
#####################################################################

class puzzlebox_synapse_cloudbrain_publisher(Thread):

	def __init__(self, log, \
		          rabbitmq_host=configuration.RABBITMQ_HOST,
		          rabbitmq_username=configuration.RABBITMQ_USERNAME,
		          rabbitmq_password=configuration.RABBITMQ_PASSWORD,
		          publisher_username=configuration.PUBLISHER_USERNAME,
		          publisher_device=configuration.PUBLISHER_DEVICE,
		          publisher_metric=configuration.PUBLISHER_METRIC,
		          displayPacketCSV=False,
		          DEBUG=DEBUG, \
		          parent=None):
		
		try:
			QtCore.QThread.__init__(self, parent)
		except:
			Thread.__init__ (self)
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent = parent


		self.keep_running = True
		self.packet_queue = []
		self.displayPacketCSV = displayPacketCSV


		self.attention_threshold = 70

		self.data = {
			'poorSignalLevel': 200, 'attention': 0, 'meditation': 0, 'delta': 0,
			'theta': 0, 'lowAlpha': 0, 'highAlpha': 0, 'lowBeta': 0, 'highBeta': 0,
			'lowGamma': 0, 'highGamma': 0, 'label': 0
		}

		self.rabbitmq_host = rabbitmq_host
		self.rabbitmq_username = rabbitmq_username
		self.rabbitmq_password = rabbitmq_password

		self.publisher_username = publisher_username
		self.publisher_device = publisher_device
		self.publisher_metric = publisher_metric

		# Send data efficiently in one packet
		self.buffer_size = 10
		self.data_buffer = []
		self.routing_key = "%s:%s:%s" % (self.publisher_username, self.publisher_device, self.publisher_metric)
		self.pub = PikaPublisher(self.rabbitmq_host, self.rabbitmq_username, self.rabbitmq_password)
		self.pub.connect()
		self.pub.register(self.routing_key)

		# Also send each metric individually in cloudbrain format
		self.metrics = ['timestamp', 'eeg', 'poorSignalLevel', 'attention', \
		                'meditation', 'delta', 'theta', 'lowAlpha', 'highAlpha', \
		                'lowBeta', 'highBeta', 'lowGamma', 'highGamma']
		self.publishers = {}
		self.routing_keys = {}
		for metric in self.metrics:
			self.routing_keys[metric] = "%s:neurosky:%s" % (self.publisher_username, metric)
			self.publishers[metric] = PikaPublisher(
			                             self.rabbitmq_host,
			                             self.rabbitmq_username,
			                             self.rabbitmq_password)

			self.publishers[metric].connect()
			self.publishers[metric].register(self.routing_keys[metric])

		# Send FFT
		self.fft_routing_key = "%s:%s:%s" % (self.publisher_username, self.publisher_device, "fft")
		self.fft_pub = PikaPublisher(self.rabbitmq_host, self.rabbitmq_username, self.rabbitmq_password)
		self.fft_pub.connect()
		self.fft_pub.register(self.fft_routing_key)

		# Final setup
		#self.configureEEG()
		displayCSVHeader()


	##################################################################
	
	def appendPacket(self, packet):
		
		self.packet_queue.append(packet)
	
	
	##################################################################
	
	def processPacketCloudbrain(self, packet):
		
		if 'rawEeg' in packet.keys():

			# packet['channel_0'] = packet.pop('rawEeg')
			#packet['eeg'] = packet.pop('rawEeg')
			packet['eeg'] = packet['rawEeg']

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
			
			if self.displayPacketCSV:
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


##################################################################

	def run(self):
		
		while self.keep_running:
		
			while self.packet_queue != []:
				
				packet = self.packet_queue.pop(0)
				
				self.processPacketCloudbrain(packet)
			
			
			time.sleep(0.002)
	
	
	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		self.keep_running = False
		
		if callThreadQuit:
			if configuration.ENABLE_QT:
				Thread.quit(self)
			else:
				self.join()


##################################################################
# Functions
##################################################################

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
