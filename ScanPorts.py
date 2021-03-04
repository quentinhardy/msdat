#!/usr/bin/python
# -*- coding: utf-8 -*

#from BulkOpen import BulkOpen
import threading, _thread, logging, queue, os
from texttable import Texttable
from Utils import getStandardBarStarted
from Mssql import Mssql
from Constants import *

class ScanPorts ():
	'''
	Allow the user to scan ports with threads
	'''
	def __init__(self,args):
		'''
		Constructor
		'''
		self.args = args

	class scanAPort(threading.Thread):
		'''
		'''
		#Constants
		ERROR_CONNECTION_IMPOSSIBLE = "No connection could be made"
		ERROR_CONNECTION_CLOSED = "An existing connection was forcibly closed"
		ERROR_LOGIN_FAILED = "Login failed for user"
		ERROR_MUST_RETRY = "Attempt to initiate a new Adaptive Server operation with results pending"

		def __init__(self, scannerObject, ip, portStatusQueue, pbar, nb, portsQueue, queueLock): 
			'''
			'''
			threading.Thread.__init__(self)
			self.ip = ip
			self.portStatusQueue = portStatusQueue
			self.pbar = pbar
			self.nb = nb
			self.portsQueue = portsQueue
			self.queueLock = queueLock
			self.scannerObject = scannerObject
			
		def waitSomeSecs(self, minimum=3, maximum=5):
			'''
			'''
			import random, time
			t = random.randrange(minimum, maximum)
			logging.debug ("Waiting {0} secs".format(t))
			time.sleep(t)
		
		def run(self):
			'''
			'''
			protocol, status, info = None, None, None
			while True:
				if self.portsQueue.empty(): _thread.exit()
				try :
					port = self.portsQueue.get(block=False)
				except Exception as e:
					_thread.exit()
				logging.debug("Scanning {0}:{1} ... (response in max 60 secs)".format(self.ip, port))
				response = ""
				self.waitSomeSecs()
				response = self.scannerObject.remoteConnectionWithOpenrowset (self.ip, port, login="", password="", database="", sqlRequest="")
				if isinstance(response,Exception):
					logging.debug('Error returned: {0}'.format(response))
					if self.ERROR_MUST_RETRY in str(response):
						nbRetry = 1
						while self.ERROR_MUST_RETRY in str(response):
							logging.debug('Error. Retry to connect number {0}'.format(nbRetry))
							self.waitSomeSecs(minimum=nbRetry*2, maximum=nbRetry*3)
							response = self.scannerObject.remoteConnectionWithOpenrowset (self.ip, port, login="", password="", database="", sqlRequest="")
							nbRetry += 1
							if nbRetry >= MAX_RETRY_CONNECTION_SCANPORTS : break
					if self.ERROR_CONNECTION_IMPOSSIBLE in str(response): protocol, status, info = 'tcp','close',self.ERROR_CONNECTION_IMPOSSIBLE
					elif self.ERROR_CONNECTION_CLOSED in str(response): protocol, status, info = 'tcp','open',self.ERROR_CONNECTION_CLOSED
					elif self.ERROR_LOGIN_FAILED in str(response): protocol, status, info = 'tcp','open',self.ERROR_LOGIN_FAILED
					else: protocol, status, info = 'tcp','unknown',None
				else:
					logging.debug('No error')
					protocol, status, info = 'tcp','open', "MSSQL"
				self.queueLock.acquire()
				if protocol != None : self.portStatusQueue.put([port,protocol,status,info])
				nb = self.nb.get(block=False) + 1
				self.nb.put(nb)
				self.pbar.update(nb)
				self.queueLock.release()
				self.portsQueue.task_done()

	def scanTcpPorts(self,scannerObject=None,ip=None,ports=[],nbThread=2):
		'''
		Scan tcp port of the ip system
		'''
		pbar,nb = getStandardBarStarted(len(ports)),queue.Queue(1)
		threads, portStatusQueue, portsQueue = [], queue.Queue(), queue.Queue()
		queueLock = threading.Lock()
		nb.put(0)
		for aPort in ports : portsQueue.put(aPort)
		logging.info ("Multithread scan is starting....")
		for i in range(nbThread):
			thread = ScanPorts.scanAPort(scannerObject,ip,portStatusQueue,pbar,nb,portsQueue,queueLock)
			threads += [thread]
			thread.start()
		portsQueue.join()
		pbar.finish()
		logging.info ("Scan is finish")
		portStatus = [item for item in portStatusQueue.queue]
		return sorted(portStatus, key=lambda x: int(x[0]))

	def printScanPortResults(self,results):
		'''
		resultats is a list of list
		print resultat of scan port
		'''
		cleanList = []
		results.insert(0,["PORT","PROTOCOL","STATE",'ERROR'])
		table = Texttable(max_width=120)
		table.set_deco(Texttable.HEADER)
		if self.args['verbose']<2 :
			for l in results:
				if l[2]!='close': cleanList.append(l)
			results = cleanList
		table.add_rows(results)
		self.args['print'].goodNews("Scan report for {0}:\n{1}".format(self.args['scan-ports'][0],table.draw()))

