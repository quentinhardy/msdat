#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket, struct, logging, re
from itertools import izip_longest
from Utils import checkOptionsGivenByTheUser
from Constants import *

class MssqlInfo:
	'''
	To get info about a remote MSSQL database without authentication
	'''
	
	VERSIONS = {#SOURCE: http://sqlserverbuilds.blogspot.fr/
		"SQL Server 2014": ['12.0.2'],
		"SQL Server 2012 (no SP)": ['11.0.2'],
		"SQL Server 2012 SP1": ["11.0.3","11.1.3"],
		"SQL Server 2012 SP2": ["11.0.5","11.2.5"],
		"SQL Server 2008 R2 (no SP)": ['10.50.1'],
		"SQL Server 2008 R2 SP1": ['10.50.2','10.51.2'],
		"SQL Server 2008 R2 SP2": ['10.50.4','10.52.4'],
		"SQL Server 2008 R2 SP3": ['10.50.6','10.53.6'],
		"SQL Server 2008 (no SP)": ['10.0.16'],
		"SQL Server 2008 SP1": ['10.0.2','10.1.2'],
		"SQL Server 2008 SP2": ['10.0.4','10.2.4'],
		"SQL Server 2008 SP3": ['10.0.5','10.3.5'],
		"SQL Server 2008 SP4": ['10.0.6','10.4.6'],
		"SQL Server 2005 (no SP)": ['9.0.1'],
		"SQL Server 2005 SP1": ['9.0.2'],
		"SQL Server 2005 SP2": ['9.0.3'],
		"SQL Server 2005 SP3": ['9.0.4'],
		"SQL Server 2005 SP4": ['9.0.5'],
		"SQL Server 2000 (no SP)": ['8.0.1'],
		"SQL Server 2000 SP1": ['8.0.3'],
		"SQL Server 2000 SP2": ['8.0.5'],
		"SQL Server 2000 SP3": ['8.0.7'],
		"SQL Server 2000 SP4": ['8.0.2'],
		"SQL Server 7.0 (no SP)": ['7.0.62'],
		"SQL Server 7.0 SP1": ['7.0.69'],
		"SQL Server 7.0 SP2": ['7.0.8'],
		"SQL Server 7.0 SP3": ['7.0.9'],
		"SQL Server 7.0 SP4": ['7.0.1']
		}

	def __init__(self, args):
		'''
		Constructor
		'''
		self.args = args
		self.host = args['host']
		self.port = args['port']
		self.sqlServerBrowserPort = 1434
		self.UDP_TIMEOUT_RCPT = 5

	def __getRemoteVersionThroughTDSResponse__(self):
		'''
		Get the remote database version using the tds response 
		containing the version (port tcp/1433 by default)
		Return a list : [product Name, version String, version list] (example: ['SQL Server 2008 SP4', '10.0.6.64', (10, 0, 6, 64)])
		Otherwise, return ['','', ()]
		'''
		packet = [0x12, 0x01, 0x00, 0x29, 0x00, 0x00, 0x01, 0x00, 
		0x00, 0x00, 0x15, 0x00, 0x06, 0x01, 0x00, 0x1b, 
		0x00, 0x01, 0x02, 0x00, 0x1c, 0x00, 0x01, 0x03, 
		0x00, 0x1d, 0x00, 0x04, 0xff, 0x09, 0x00, 0x05, 
		0x77, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
		0x00]
		productVersionString, productName, productVersion= "", "", []
		toSend = ''.join([struct.pack('B', val) for val in packet])
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		logging.info("The mssql-info script is sending a TCP packet to the database server to get the remote database version (without authentication)")
		logging.debug("writing {0} bytes ".format(len(toSend)))
		try : s.connect((self.host, self.port))
		except Exception as e:
			logging.critical("Impossible to establish a TCP connection to {0}:{1}".format(self.host,self.port))
			return {'productName':productName, 'version:':productVersionString, 'versionNumber':productVersion}
		s.sendall(toSend)
		data = s.recv(500)
		lenData = len(data)
		if lenData >= 5 :#There is data
			values = struct.unpack('BB', data[0:2])
			if values[0] == 4 and values[1] == 1: #it is a response and ack==success
				length = struct.unpack('>H', data[2:4])[0]
				if length == lenData : 
					mssqlRawData = data[8:] #type + status + length + Channel + packet# + window 
					logging.debug("The following packet received should be used to get the remote database server version: '{0}'".format(repr(mssqlRawData)))
					tds_version=struct.unpack('BBBB', mssqlRawData[0:4])
					debVersion = mssqlRawData.rfind('ff'.decode('hex'))
					productVersionBase = list(struct.unpack('BBBBBB',mssqlRawData[debVersion+1:debVersion+7]))
					productVersion.append(productVersionBase[0])
					productVersion.append(productVersionBase[1])
					productVersion.append(productVersionBase[2]*256+productVersionBase[3])
					productVersion.append(productVersionBase[4]*256+productVersionBase[5])
					productVersionString = '.'.join(str(val) for val in productVersion)
					logging.debug("The remote database version is {0}".format(productVersionString))
					#search the version string
					productName = self.__getProductNameFromVersion__ (productVersionString)
					if productName != "":
						logging.info("The remote database server is {0} ({1})".format(productName, productVersionString))
						return {'ProductName':productName, 'Version':productVersionString, 'VersionNumber':productVersion}
					else :
						logging.debug("The version {0} is not in the version knowledge base, can't give you the product name and service pack".format(productVersionString))
				else :
					logging.debug("The packet received has not a good length, can't continue to get the version!")
			else:
				logging.debug("The packet format received is unknows, can't continue to get the version!")
		else:
			logging.debug("The packet received is too short, can't continue to get the version!")
		logging.warning("The remote database server version can't be known")
		return {'productName':productName, 'version:':productVersionString, 'versionNumber':productVersion}
	
	def __getProductNameFromVersion__ (self,productVersionString):
		'''
		Returns "" if the product name associated to the version is unknown
		Otherwise returns the product name
		'''
		productName = ""
		for aVersionString, versions  in self.VERSIONS.iteritems():
			for aVersion in versions : 
				pattern = re.compile(aVersion)
				if pattern.match(productVersionString) != None: 
					productName = aVersionString
					logging.info("The product name associated to the version {0} is {1}".format(productVersionString, productName))
					return productName
		logging.info("The product name associated to the version {0} is unknown".format(productVersionString))
		return productName
	
	def __getRemoteVersionThroughSQLServerBrowser__(self):
		'''
		Get the remote database version using the SQL Server Browser
		Send a UDP to the SQL database server. Database responds with the exact version.
		Return dict. Example: {'': '', 'ServerName': 'WIN-E3DZ2TMI307', 'tcp': '1433', 'IsClustered': 'No', 'Version': '10.0.1600.22', 'InstanceName': 'SQLEXPRESS'}
		Return {} if port not opened
		'''
		dataDict = {}
		sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		logging.info("The mssql-info script is sending a UDP packet to the SQL Server Browser to get the remote database version (without authentication)")
		sock.settimeout(self.UDP_TIMEOUT_RCPT)
		sock.sendto(struct.pack('B', 0x03), (self.host,self.sqlServerBrowserPort))
		try : data = sock.recv(1024)
		except socket.timeout:
			logging.info("The UDP port {0} is not opened on the server {1}".format(self.sqlServerBrowserPort, self.host))
			return dataDict
		else:
			logging.debug("Data received: '{0}'".format(data))
			logging.debug("Consequently, SQL Server Browser is eanbled :)".format(data))
			dataSplit = data[3:].split(';')
			dataDict = dict(izip_longest(*[iter(dataSplit)] * 2, fillvalue=""))
			dataDict = dict((k, v) for k, v in dataDict.iteritems() if v != '')
			dataDict['ProductName'] = self.__getProductNameFromVersion__(dataDict['Version'])
			logging.debug("The product name of the version '{0}' retrieved through SQL Server Browser is '{1}'".format(dataDict['Version'],dataDict['ProductName']))
			return dataDict
		
	def getRemoteDatabaseVersion (self):
		'''
		Get remote database version using:
		- tds protocol to get the version number
		- SQL Server Browser to get the exact version
		Best info in SQL Server Browser
		'''
		information = None
		tempInfo = self.__getRemoteVersionThroughSQLServerBrowser__()
		if tempInfo == {}:
			information = self.__getRemoteVersionThroughTDSResponse__()
			logging.info("SQL Server Browser is not enabled on the remote database server")
			information['retrievedThroughSQLServerBrowser'] = False
		else :
			information = tempInfo
			logging.info("SQL Server Browser is enabled on the remote database server")
			information['retrievedThroughSQLServerBrowser'] = True
		logging.info("Information about the remote database retrieved without authentication: '{0}'".format(tempInfo))
		return information
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].title("Is SQL Server Browser enabled ?")
		info = self.getRemoteDatabaseVersion()
		if info['retrievedThroughSQLServerBrowser'] == True :
			self.args['print'].goodNews("OK")
		else :
			self.args['print'].badNews("KO")
			
	def returnPrintableStringFromDict(self,aDictionary):
		'''
		'''
		string = ""
		for e,v in aDictionary.items(): string += '   -> {0}: {1}\n'.format(e,v)
		return string
			
		
		
def runMssqlInfoModule(args):
	'''
	'''
	if checkOptionsGivenByTheUser(args,["get-max-info"],checkAccount=False) == False : return EXIT_MISS_ARGUMENT
	if args['get-max-info'] == True:
		mssqlInfo = MssqlInfo(args)
		productName = mssqlInfo.__getRemoteVersionThroughTDSResponse__()
		args['print'].title("Try to get the remote database version thanks to the TDS protocol:")
		if ('Version' in productName) == True and ('ProductName' in productName) == True:
			args['print'].goodNews("The SQL server version of {0}:{1}: {2} i.e. {3}".format(args['host'],args['port'], productName['Version'],productName['ProductName']))
		else :
			args['print'].badNews("Impossible to get the remote database version thanks to the TDS protocol")
		args['print'].title("Try to get information about the remote database thanks to SQL browser Server:")
		info = mssqlInfo.__getRemoteVersionThroughSQLServerBrowser__()
		if info == {}:
			args['print'].badNews("SQL Server Browser is not enabled on the server {0}:{1}".format(args['host'], args['port']))
		else :
			args['print'].goodNews("SQL Server Browser is enabled on the server {0}:{1}:\n{2}".format(args['host'], args['port'], mssqlInfo.returnPrintableStringFromDict(info)))
			

		
		
		
		
		
	

