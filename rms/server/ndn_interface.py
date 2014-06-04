#!/usr/bin/env python
#encoding: utf-8
import sys
import pyndn

from common.settings import log

class rmsServerInterface(pyndn.Closure):
	def __init__(self, name):
		self.handle = pyndn.NDN()
		self.name = pyndn.Name(name)

	# this is so we don't have to do signing each time someone requests data
	# if we will be serving content multiple times
	def prepareContent(self, content, name, key):
		# create a new data packet
		co = pyndn.ContentObject()

		# since they want us to use versions and segments append those to our name
		co.name = name.appendVersion().appendSegment(0)

		# place the content
		co.content = content

		si = co.signedInfo

		# key used to sign data (required by ndnx)
		si.publisherPublicKeyDigest = key.publicKeyID

		# how to obtain the key (required by ndn); here we attach the
		# key to the data (not too secure), we could also provide name
		# of the key under which it is stored in DER format
		si.keyLocator = pyndn.KeyLocator(key)

		# data type (not needed, since DATA is the default)
		si.type = pyndn.CONTENT_DATA

		# number of the last segment (0 - i.e. this is the only
		# segment)
		si.finalBlockID = pyndn.Name.num2seg(0)

		# signing the packet
		co.sign(key)

		return co

	def handleRequest(self, interest):
		raise NotImplementedError

	# Called when we receive interest
	# once data is sent signal ndn_run() to exit
	def upcall(self, kind, info):
		if kind != pyndn.UPCALL_INTEREST:
			return pyndn.RESULT_OK

		content = self.handleRequest(info.Interest)
		if content == None:
			return pyndn.RESULT_OK

		self.handle.put(content) # send the prepared data
		# self.handle.setRunTimeout(0) # finish run() by changing its timeout to 0

		return pyndn.RESULT_INTEREST_CONSUMED

	def start(self):
		log.info("listening on %s"% self.name)
		# register our name, so upcall is called when interest arrives
		self.handle.setInterestFilter(self.name, self)

		# enter ndn loop (upcalls won't be called without it, get
		# doesn't require it as well)
		# -1 means wait forever
		self.handle.run(-1)
