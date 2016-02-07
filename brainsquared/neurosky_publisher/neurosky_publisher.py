# -*- coding: utf-8 -*-

# Copyright Puzzlebox Productions, LLC (2010-2016)
#
# Ported from Puzzlebox Synapse
# ThinkGear code imported from Puzzlebox.Synapse.ThinkGear.Server
# http://puzzlebox.io
#
# This code is released under the GNU Pulic License (GPL) version 3
# For more information please refer to http://www.gnu.org/copyleft/gpl.html
#
# Author: Steve Castellotti <sc@puzzlebox.io>
#
# Example call:
# python2.7 neurosky_publisher.py \
#   --server_host=rabbitmq.cloudbrain.rocks \
#   --server_username=cloudbrain \
#   --server_password=cloudbrain \
#   --publisher_user=brainsquared publisher_device=neurosky \
#   --publisher_metric=eeg \
#   --device=/dev/tty.MindWaveMobile-DevA


__changelog__ = """
Last Update: 2016.02.02
"""

import sys, signal, time
from brainsquared.publishers.PikaPublisher import PikaPublisher
#from PySide import QtCore, QtGui, QtNetwork
import threading
#import Puzzlebox.Synapse.ThinkGear.Protocol as thinkgear_protocol
import protocol_thinkgear as thinkgear_protocol


DEBUG = 1

#serial_device = None
#protocol = None
#log = None

THINKGEAR_DEVICE_SERIAL_PORT = '/dev/tty.MindWaveMobile-DevA'
THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA = False

CLOUDBRAIN_HOST = 'localhost'
#CLOUDBRAIN_HOST = 'rabbitmq.cloudbrain.rocks'

CLOUDBRAIN_USERNAME = 'guest'
#CLOUDBRAIN_USERNAME = 'cloudbrain'

CLOUDBRAIN_PASSWORD = 'guest'
#CLOUDBRAIN_PASSWORD = 'cloudbrain'

PUBLISHER_USERNAME = 'brainsquared'
PUBLISHER_DEVICE = 'neurosky'
PUBLISHER_METRIC = 'eeg'

#class neurosky_publisher(QtCore.QThread):
class neurosky_publisher(threading.Thread):
	
	def __init__(self, log, \
		          #server_interface=SERVER_INTERFACE, \
		          #server_port=SERVER_PORT, \
		          #device_model=None, \
		          device_address=THINKGEAR_DEVICE_SERIAL_PORT, \
		          emulate_headset_data=THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA, \
		          server_host=CLOUDBRAIN_HOST, \
		          server_username=CLOUDBRAIN_USERNAME, \
		          server_password=CLOUDBRAIN_PASSWORD, \
		          publisher_user=PUBLISHER_USERNAME, \
		          publisher_device=PUBLISHER_DEVICE, \
		          publisher_metric=PUBLISHER_METRIC, \
		          DEBUG=DEBUG, \
		          parent=None):
		
		#QtCore.QThread.__init__(self,parent)
		threading.Thread.__init__ (self,parent)
		
		self.log = log
		self.DEBUG = DEBUG
		self.parent = parent
		
		self.device_address = device_address
		self.emulate_headset_data = emulate_headset_data
		
		self.attention_threshold = 70
		
		
		self.data = {}
		self.data['poorSignalLevel'] = 200
		self.data['attention'] = 0
		self.data['meditation'] = 0
		self.data['delta'] = 0
		self.data['theta'] = 0
		self.data['lowAlpha'] = 0
		self.data['highAlpha'] = 0
		self.data['lowBeta'] = 0
		self.data['highBeta'] = 0
		self.data['lowGamma'] = 0
		self.data['highGamma'] = 0
		self.data['label'] = 0
		
		self.host = server_host
		self.username = server_username
		self.pwd = server_password

		self.user = publisher_user
		self.device = publisher_device
		self.metric = publisher_metric
		
		self.routing_key = "%s:%s:%s" % (self.user, self.device, self.metric)

		#self.buffer_size = 128
		self.buffer_size = 10
		self.data_buffer = []

		self.pub = PikaPublisher(self.host, self.username, self.pwd)
		self.pub.connect()
		self.pub.register(self.routing_key)
		
		self.configureEEG()
		
		self.displayCSVHeader()
		
		
	##################################################################
	
	def setPacketCount(self, value):
		
		if self.parent != None:
			self.parent.setPacketCount(value)
	
	
	##################################################################
	
	def setBadPackets(self, value):
		
		if self.parent != None:
			self.parent.setBadPackets(value)
	
	
	##################################################################
	
	def incrementPacketCount(self):
		
		if self.parent != None:
			self.parent.incrementPacketCount()
	
	
	##################################################################
	
	def incrementBadPackets(self):
		
		if self.parent != None:
			self.parent.incrementBadPackets()
	
	
	##################################################################
	
	def resetSessionStartTime(self):
		
		if self.parent != None:
			self.parent.resetSessionStartTime()
	
	
	##################################################################
	
	def configureEEG(self):
		
		if not self.emulate_headset_data:
			
			self.serial_device = \
				thinkgear_protocol.SerialDevice( \
					self.log, \
					device_address=self.device_address, \
					#DEBUG=self.DEBUG, \
					DEBUG=0, \
					parent=self)
			
			self.serial_device.start()
		
		else:
			self.serial_device = None
		
		
		self.protocol = \
			thinkgear_protocol.puzzlebox_synapse_protocol_thinkgear( \
				self.log, \
				self.serial_device, \
				device_model='NeuroSky MindWave', \
				#DEBUG=self.DEBUG, \
				DEBUG=0, \
				parent=self)
		
		#self.plugin_session = self.parent.plugin_session # for Jigsaw compatability
		
		self.protocol.start()


	##################################################################
	
	def processPacketThinkGear(self, packet):
		
		if self.DEBUG > 2:
			print packet

		if ('rawEeg' in packet.keys()):
			
			#packet['channel_0'] = packet.pop('rawEeg')
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
				self.displayCSV(packet)
			
			if len(self.data_buffer) > self.buffer_size:
				self.pub.publish(self.routing_key, self.data_buffer)
				if self.DEBUG > 1:
					print self.data_buffer
				self.data_buffer = []
				if self.DEBUG > 1:
					print "Publishing:",
					print self.routing_key
			else:
				self.data_buffer.append(packet)
		
		else:
			
			if ('poorSignalLevel' in packet.keys()):
				self.data['poorSignalLevel'] = packet['poorSignalLevel']
			
			if ('eegPower' in packet.keys()):
				self.data['delta'] = packet['eegPower']['delta']
				self.data['theta'] = packet['eegPower']['theta']
				self.data['lowAlpha'] = packet['eegPower']['lowAlpha']
				self.data['highAlpha'] = packet['eegPower']['highAlpha']
				self.data['lowBeta'] = packet['eegPower']['lowBeta']
				self.data['highBeta'] = packet['eegPower']['highBeta']
				self.data['lowGamma'] = packet['eegPower']['lowGamma']
				self.data['highGamma'] = packet['eegPower']['highGamma']
			
			if ('eSense' in packet.keys()):
				if ('attention' in packet['eSense'].keys()):
					self.data['attention'] = packet['eSense']['attention']
					
					if (self.data['attention'] >= self.attention_threshold):
						self.data['label'] = 1
					else:
						self.data['label'] = 0
					
				if ('meditation' in packet['eSense'].keys()):
					self.data['meditation'] = packet['eSense']['meditation']
	
	
	##################################################################

	def displayCSV(self, packet):
		
		print "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % ( \
			packet['timestamp'], \
			packet['eeg'], \
			packet['poorSignalLevel'], \
			packet['attention'], \
			packet['meditation'], \
			packet['delta'], \
			packet['theta'], \
			packet['lowAlpha'], \
			packet['highAlpha'], \
			packet['lowBeta'], \
			packet['highBeta'], \
			packet['lowGamma'], \
			packet['highGamma'], \
			packet['label'], \
		)
	
	
	##################################################################
	
	def displayCSVHeader(self):
		
		print "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % ( \
			'timestamp', \
			'eeg', \
			'poorSignalLevel', \
			'attention', \
			'meditation', \
			'delta', \
			'theta', \
			'lowAlpha', \
			'highAlpha', \
			'lowBeta', \
			'highBeta', \
			'lowGamma', \
			'highGamma', \
			'label', \
		)
	
	
	##################################################################
	
	def resetDevice(self):
		
		if self.serial_device != None:
			self.serial_device.exitThread()
		
		if self.protocol != None:
			self.protocol.exitThread()
		
		self.configureEEG()


	##################################################################
	
	def exitThread(self, callThreadQuit=True):
		
		if (self.emulate_headset_data):
			try:
				self.emulationTimer.stop()
			except Exception, e:
				if self.DEBUG:
					print "ERROR: Exception when stopping emulation timer:",
					print e
		
		# Calling exitThread() on protocol first seems to occassionally 
		# create the following error:
		# RuntimeError: Internal C++ object (PySide.QtNetwork.QTcpSocket) already deleted.
		# Segmentation fault
		# ...when program is closed without pressing "Stop" button for EEG
		#if self.protocol != None:
			#self.protocol.exitThread()
		
		# Call disconnect block in protocol first due to above error
		self.protocol.disconnectHardware()
		
		if self.serial_device != None:
			self.serial_device.exitThread()
		
		if self.protocol != None:
			self.protocol.exitThread()
		
		self.socket.close()
		
		if callThreadQuit:
			if self.DEBUG:
				self.join()
			self.join()
			#QtCore.QThread.quit(self)
		
		if self.parent == None:
			sys.exit()


#def get_tag(p, attention_threshold):
	#if p.attention > attention_threshold:
		#tag = 1
	#else:
		#tag = 0
	#return tag


#def get_raw_eeg(p):
	#timestamp = int(time.time() * 1000000)
	#raw_eeg_record = {"timestamp": timestamp, "channel_0": 100}
	#return  raw_eeg_record


if __name__ == "__main__":
	
	# Perform correct KeyboardInterrupt handling
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	log = None

	#server_interface = configuration.THINKGEAR_SERVER_INTERFACE
	#server_port = configuration.THINKGEAR_SERVER_PORT
	#device_address = configuration.THINKGEAR_DEVICE_SERIAL_PORT
	device_address = THINKGEAR_DEVICE_SERIAL_PORT
	#device_id = configuration.THINKGEAR_DEVICE_ID
	server_host=CLOUDBRAIN_HOST
	server_username=CLOUDBRAIN_USERNAME
	server_password=CLOUDBRAIN_PASSWORD
	publisher_user=PUBLISHER_USERNAME
	publisher_device=PUBLISHER_DEVICE
	publisher_metric=PUBLISHER_METRIC

	for each in sys.argv:
		if each.startswith("--interface="):
			server_interface = each[ len("--interface="): ]
		if each.startswith("--port="):
			server_port = each[ len("--port="): ]
		if each.startswith("--device="):
			device_address = each[ len("--device="): ]
		if each.startswith("--debug="):
			DEBUG = int (each[ len("--debug="): ] )
		if each.startswith("--id="):
			device_id = int (each[ len("--id="): ] )
		if each.startswith("--server_host="):
			server_host = each[ len("--server_host="): ]
		if each.startswith("--server_username="):
			server_username = each[ len("--server_username="): ]
		if each.startswith("--server_password="):
			server_password = each[ len("--server_password="): ]
		if each.startswith("--publisher_user="):
			publisher_user = each[ len("--publisher_user="): ]
		if each.startswith("--publisher_device="):
			publisher_device = each[ len("--publisher_device="): ]
		if each.startswith("--publisher_metric="):
			publisher_metric = each[ len("--publisher_metric="): ]
	
	#app = QtCore.QCoreApplication(sys.argv)
	
	publisher = neurosky_publisher( \
				log, \
				#server_interface=server_interface, \
				#server_port=server_port, \
				#device_id, \
				device_address=device_address, \
				emulate_headset_data = THINKGEAR_ENABLE_SIMULATE_HEADSET_DATA, \
				server_host = server_host, \
				server_username = server_username, \
				server_password = server_password, \
				publisher_user = publisher_user, \
				publisher_device = publisher_device, \
				publisher_metric = publisher_metric, \
				DEBUG=DEBUG)

	publisher.start()
	
	#sys.exit(app.exec_())
	
