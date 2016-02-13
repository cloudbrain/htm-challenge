# -*- coding: utf-8 -*-

"""
Copyright Puzzlebox Productions, LLC (2016)

Ported from Puzzlebox Synapse
Publisher code imported from Puzzlebox.Synapse.Cloudbrain.Publisher
http://puzzlebox.io

This code is released under the GNU Lesser Public License (LGPL) version 3
For more information please refer to https://www.gnu.org/licenses/lgpl.html

Author: Steve Castellotti <sc@puzzlebox.io>
"""

__changelog__ = """
Last Update: 2016.02.13
"""

#####################################################################
# Imports
#####################################################################

import time
from brainsquared.publishers.PikaPublisher import PikaPublisher

try:
	import Puzzlebox.Synapse.Configuration as configuration
except:

	class Configuration():
		
		def __init__(self):
			
			self.DEBUG = 1
			
			self.ENABLE_QT = False
			self.ENABLE_PYSIDE = False
			
			self.RABBITMQ_HOST = 'localhost'
			self.RABBITMQ_USERNAME = 'guest'
			self.RABBITMQ_PASSWORD = 'guest'
			self.PUBLISHER_USERNAME = 'user_0'
			self.PUBLISHER_DEVICE = 'neurosky'
			self.PUBLISHER_METRIC = 'mindwave'
	
	
	configuration = Configuration()


if configuration.ENABLE_QT:
	if configuration.ENABLE_PYSIDE:
		try:
			import PySide
			from PySide import QtCore
			Thread = PySide.QtCore.QThread
		except Exception, e:
			if configuration.DEBUG:
				print "ERROR: Exception importing PySide:",
				print e
			configuration.ENABLE_PYSIDE = False
		else:
			if configuration.DEBUG:
				print "INFO: [Synapse:Cloudbrain:Publisher] Using PySide module"
	
	if not configuration.ENABLE_PYSIDE:
		try:
			if configuration.DEBUG:
				print "INFO: [Synapse:Cloudbrain:Publisher] Using PyQt4 module"
			from PyQt4 import QtCore
		except:
			configuration.ENABLE_QT = False


if not configuration.ENABLE_QT:
	import threading
	Thread = threading.Thread
	if configuration.DEBUG:
		print "INFO: [Synapse:Cloudbrain:Publisher] Using 'threading' module"


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
		          DEBUG=configuration.DEBUG, \
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


		self.rabbitmq_host = rabbitmq_host
		self.rabbitmq_username = rabbitmq_username
		self.rabbitmq_password = rabbitmq_password

		self.publisher_username = publisher_username
		self.publisher_device = publisher_device
		self.publisher_metric = publisher_metric

		self.buffer_sizes = {}
		self.data_buffers = {}

		# Send each metric individually in cloudbrain format
		self.metrics = ['eeg', 'poorSignalLevel', 'attention', 'meditation', \
		                'delta', 'theta', 'lowAlpha', 'highAlpha', \
		                'lowBeta', 'highBeta', 'lowGamma', 'highGamma']
		
		self.publishers = {}
		self.routing_keys = {}
		
		for metric in self.metrics:
			routing_key = "%s:%s:%s" % (self.publisher_username, \
			                            self.publisher_device, \
			                            metric)
			
			self.routing_keys[metric] = routing_key
			
			self.publishers[metric] = PikaPublisher(
			                             self.rabbitmq_host,
			                             self.rabbitmq_username,
			                             self.rabbitmq_password)
			
			self.publishers[metric].connect()
			self.publishers[metric].register(self.routing_keys[metric])
			
			
			self.data_buffers[metric] = []
			
			
			if metric == 'eeg':
				if (self.publisher_device == 'neurosky'):
					self.buffer_sizes[metric] = 128
				else:
					self.buffer_sizes[metric] = 10
			else:
				if (self.publisher_device == 'neurosky'):
					self.buffer_sizes[metric] = 1
				else:
					self.buffer_sizes[metric] = 1
		
		if self.DEBUG > 1:
			displayCSVHeader()


	##################################################################
	
	def appendPacket(self, packet):
		
		self.packet_queue.append(packet)
	
	
	##################################################################
	
	def processPacketCloudbrain(self, packet):
		
		if 'rawEeg' in packet.keys():
			
			metric_packet = {}
			metric_packet['timestamp'] = packet['timestamp']
			metric_packet['channel_0'] = packet['rawEeg']
			
			self.data_buffers['eeg'].append(metric_packet)
			
			if self.DEBUG > 2:
				print metric_packet
			
			#if self.displayPacketCSV:
				#if self.DEBUG > 1:
					#displayCSV(metric_packet)
			
			if len(self.data_buffers['eeg']) > self.buffer_sizes['eeg']:
				
				self.publishers['eeg'].publish( \
					self.routing_keys['eeg'], \
					self.data_buffers['eeg'])
				
				self.data_buffers['eeg'] = []
				
			else:
				self.data_buffers['eeg'].append(metric_packet)
		
		
		else:
			
			if 'poorSignalLevel' in packet.keys():
				
				metric_packet = {}
				metric_packet['timestamp'] = packet['timestamp']
				metric_packet['channel_0'] = packet['poorSignalLevel']
				
				self.publishers['poorSignalLevel'].publish(
					self.routing_keys['poorSignalLevel'],
					[metric_packet])
				
				if self.displayPacketCSV:
					if self.DEBUG > 1:
						displayCSV(metric_packet)
			
			
			if 'eegPower' in packet.keys():
				
				self.publishers['delta'].publish(
					self.routing_keys['delta'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['delta']
					}] )
				self.publishers['theta'].publish(
					self.routing_keys['theta'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['theta']
					}] )
				self.publishers['lowAlpha'].publish(
					self.routing_keys['lowAlpha'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['lowAlpha']
					}] )
				self.publishers['highAlpha'].publish(
					self.routing_keys['highAlpha'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['highAlpha']
					}] )
				self.publishers['lowBeta'].publish(
					self.routing_keys['lowBeta'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['lowBeta']
					}] )
				self.publishers['highBeta'].publish(
					self.routing_keys['highBeta'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['highBeta']
					}] )
				self.publishers['lowGamma'].publish(
					self.routing_keys['lowGamma'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['lowGamma']
					}] )
				self.publishers['highGamma'].publish(
					self.routing_keys['highGamma'], [{
						'timestamp': packet['timestamp'], \
						'channel_0': packet['eegPower']['highGamma']
					}] )
			
			
			if 'eSense' in packet.keys():
				
				if 'attention' in packet['eSense'].keys():
					
					self.publishers['attention'].publish(
						self.routing_keys['attention'], [{
							'timestamp': packet['timestamp'], \
							'channel_0': packet['eSense']['attention']
						}] )
				
				if 'meditation' in packet['eSense'].keys():
					
					self.publishers['meditation'].publish(
						self.routing_keys['meditation'], [{
							'timestamp': packet['timestamp'], \
							'channel_0': packet['eSense']['meditation']
						}] )


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
