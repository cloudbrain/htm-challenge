# -*- coding: utf-8 -*-

"""
Copyright Puzzlebox Productions, LLC (2010-2016)

Ported from Puzzlebox Synapse
ThinkGear code imported from Puzzlebox.Synapse.ThinkGear.Server
http://puzzlebox.io

This code is released under the GNU Lesser Public License (LGPL) version 3
For more information please refer to http://www.gnu.org/copyleft/lgpl.html

Author: Steve Castellotti <sc@puzzlebox.io>
"""

__changelog__ = """
Last Update: 2016.02.12
"""

import sys, signal
import threading
from brainsquared.publishers.PikaPublisher import PikaPublisher
from brainsquared.modules.sources import NeuroskyConnector
from brainsquared.modules.sources import NeuroskyPublisher

DEBUG = 1


THINKGEAR_DEVICE_SERIAL_PORT = '/dev/tty.MindWaveMobile-DevA'


RABBITMQ_HOST = 'localhost'
RABBITMQ_USERNAME = 'guest'
RABBITMQ_PASSWORD = 'guest'
PUBLISHER_USERNAME = 'brainsquared'
PUBLISHER_DEVICE = 'neurosky'
PUBLISHER_METRIC = 'mindwave'


class NeuroskySource(threading.Thread):
	def __init__(self, log,
					device_address=THINKGEAR_DEVICE_SERIAL_PORT,
					rabbitmq_host=RABBITMQ_HOST,
					rabbitmq_username=RABBITMQ_USERNAME,
					rabbitmq_password=RABBITMQ_PASSWORD,
					publisher_username=PUBLISHER_USERNAME,
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


		self.cloudbrain_publisher = \
			NeuroskyPublisher.puzzlebox_synapse_cloudbrain_publisher( \
				log, \
				rabbitmq_host=rabbitmq_host,
				rabbitmq_username=rabbitmq_username,
				rabbitmq_password=rabbitmq_password,
				publisher_username=publisher_username,
				publisher_device=publisher_device,
				publisher_metric=publisher_metric,
				displayPacketCSV=True,
				DEBUG=DEBUG, \
				parent=None)
		
		self.cloudbrain_publisher.start()

		# Final setup
		self.configureEEG()



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
		
		self.serial_device = \
			NeuroskyConnector.SerialDevice(
				self.log, \
				device_address=self.device_address, \
				#DEBUG=self.DEBUG, \
				DEBUG=0, \
				parent=self)
		
		self.serial_device.start()
		
		
		self.protocol = \
			NeuroskyConnector.puzzlebox_synapse_protocol_thinkgear( \
				self.log, \
				self.serial_device, \
				#device_model=self.device_model, \
				DEBUG=self.DEBUG, \
				parent=self)
		
		self.protocol.start()


	def processPacketThinkGear(self, packet):

		if self.DEBUG > 2:
			print packet
		
		if (packet != {}):
			self.cloudbrain_publisher.appendPacket(packet)


	def resetDevice(self):

		if self.serial_device is not None:
			self.serial_device.exitThread()

		if self.protocol is not None:
			self.protocol.exitThread()

		if self.cloudbrain_publisher != None:
			self.cloudbrain_publisher.exitThread()

		self.configureEEG()


	def exitThread(self, callThreadQuit=True):

		# Call disconnect block in protocol first due to above error
		self.protocol.disconnectHardware()

		if self.serial_device is not None:
			self.serial_device.exitThread()

		if self.protocol is not None:
			self.protocol.exitThread()

		if self.cloudbrain_publisher != None:
			self.cloudbrain_publisher.exitThread()

		if callThreadQuit:
			self.join()

		if self.parent is None:
			sys.exit()


if __name__ == "__main__":

	# Perform correct KeyboardInterrupt handling
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	log = None

	device_address = THINKGEAR_DEVICE_SERIAL_PORT
	rabbitmq_host = RABBITMQ_HOST
	rabbitmq_username = RABBITMQ_USERNAME
	rabbitmq_password = RABBITMQ_PASSWORD
	publisher_username = PUBLISHER_USERNAME
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
		rabbitmq_host=rabbitmq_host,
		rabbitmq_username=rabbitmq_username,
		rabbitmq_password=rabbitmq_password,
		publisher_username=publisher_username,
		publisher_device=publisher_device,
		publisher_metric=publisher_metric,
		DEBUG=DEBUG)

	publisher.start()
