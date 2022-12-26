#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Utils import cleanString, ErrorClass
import decimal
from Constants import *
from Mssql import Mssql
from Utils import *
from texttable import Texttable
import readline

class Search (Mssql):#Mssql
	'''
	Search class 
	'''
	#CONSTANTS
	REQ_GET_COLUMNS_IN_TABLES = """
	SELECT co.name AS column_name,
		ta.name AS table_name,
		SCHEMA_NAME(schema_id) AS schema_name
	FROM sys.tables AS ta
		INNER JOIN sys.all_columns co ON ta.OBJECT_ID = co.OBJECT_ID
	WHERE co.name LIKE '{0}';
	""" #{0}: pattern
	REQ_GET_COLUMNS_IN_VIEWS = """
	SELECT co.name AS column_name,
		ta.name AS table_name,
		SCHEMA_NAME(schema_id) AS schema_name
	FROM sys.all_views AS ta
		INNER JOIN sys.all_columns co ON ta.OBJECT_ID = co.OBJECT_ID
	WHERE co.name LIKE '{0}';
	"""#{0}: pattern
	REQ_GET_VALUE_IN_COLUMN = """SELECT TOP 1 {0} FROM {2}.{1} WHERE {0} is not null AND {0} not like '';"""#{0} Column name, {1} table name, {2} schema name, 
	DEFAULT_VALUE_EMPTY_COLUMN = "(Empty Column)"
	DEFAULT_VALUE_UNKNOWN = "(Unknown)"
	EXEMPLE_VALUE_LEN_MAX = 40
	RIGHT_SPACE_SIZE = 40
	TRUNCATED_MESSAGE_EXEMPLE = '(Truncated...)'
	EXCLUDED_DATABASES = ['model', 'master', 'msdb', 'tempdb']
	REQ_GET_DATABASES_NAMES = """SELECT name FROM master..sysdatabases"""
	REQ_GET_TABLES_FOR_A_DB_NAME = """SELECT name, id FROM {0}..sysobjects WHERE xtype = 'U'"""#{0} Database name
	REQ_GET_COLUMNS = """SELECT syscolumns.name, systypes.name FROM {0}..syscolumns JOIN {0}..systypes ON syscolumns.xtype=systypes.xtype WHERE syscolumns.id={1}"""#{0} Database name, {1} table id
	REQ_GET_PATH_LOCAL_FILES = """SELECT name,  physical_name FROM sys.master_files"""
	REQ_GET_INSTANCE_INFORMATION = """
	SELECT SERVERPROPERTY('ComputerNamePhysicalNetBIOS') as NetBios, 
	SERVERPROPERTY('Edition') as Edition, 
	SERVERPROPERTY('InstanceDefaultDataPath') as InstanceDefaultDataPath, 
	SERVERPROPERTY('InstanceDefaultLogPath') as InstanceDefaultLogPath,
	SERVERPROPERTY('MachineName') as Host, SERVERPROPERTY('InstanceName') as Instance, 
	SERVERPROPERTY('ProductLevel') as ProductLevel, 
	SERVERPROPERTY('ProductVersion') as ProductVersion, 
	SERVERPROPERTY('SqlCharSetName') as SqlCharSetName, 
	Case SERVERPROPERTY('IsClustered') when 1 then 'CLUSTERED' else 'STANDALONE' end  as ServerType,
	Case SERVERPROPERTY('IsIntegratedSecurityOnly') when 1 then 'WINDOWS_AUTHENT_ONLY' else 'WINDOWS_AUTHENT_AND_SQL_SERVER_AUTH' end  as ServerType, 
	@@VERSION as VersionNumber"""
	REQ_GET_ADVANCED_OPTIONS = "EXEC  master.dbo.sp_configure "
	
	def __init__ (self, args=None):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		self._lastDBname = None #Use when moving to another db and we would like to come back to last one after

	def __searchPatternInColumnNamesOfTables__(self, pattern):
		'''
		Search the pattern in column names of all tables
		'''
		
		logging.debug("Searching the pattern '{0}' in all column names of all tables accessible to the current user".format(pattern))
		data = self.executeRequest(self.REQ_GET_COLUMNS_IN_TABLES.format(pattern), ld=['column_name', 'table_name', 'schema_name'], noResult=False)
		if isinstance(data,Exception):
			logging.error("Impossible to search the pattern '{0}' in column names of tables: '{1}'".format(pattern,data))
		return data
		
	def __searchPatternInColumnNamesOfViews__(self, pattern):
		'''
		Search the pattern in column names of all views
		'''
		
		logging.debug("Searching the pattern '{0}' in all column names of all views accessible to the current user".format(pattern))
		data = self.executeRequest(self.REQ_GET_COLUMNS_IN_VIEWS.format(pattern), ld=['column_name', 'table_name', 'schema_name'], noResult=False)
		if isinstance(data,Exception):
			logging.error("Impossible to search the pattern '{0}' in column names of views: '{1}'".format(pattern, data))
		return data
		
	def __getAnExampleOfValueForAColumn__(self, column_name, table_name, schema_name):
		'''
		Return an exemple of data for a column
		'''
		logging.info("Get an example of data for the column '{0}' stored in the table '{1}' of the schema '{2}'".format(column_name, table_name, schema_name))
		data = self.executeRequest(self.REQ_GET_VALUE_IN_COLUMN.format(column_name, table_name, schema_name), ld=[column_name], noResult=False)
		if isinstance(data,Exception):
			logging.warning("Impossible to get a value in the column '{0}' of the table '{1}' stored in the schema '{2}': '{3}".format(column_name, table_name, schema_name, data))
		return data
		
	def searchInColumnNames (self, pattern, noShowEmptyColumns=False):
		'''
		Search the pattern in column names of all views and tables
		'''
		resultsToTable = []
		columns = [[]]
		logging.info("Searching the pattern '{0}' in column names of all views and tables which are accessible to the current user".format(pattern))
		data1 = self.__searchPatternInColumnNamesOfTables__(pattern)
		if isinstance(data1,Exception): 
			pass
		else : 
			columns = data1
		data2 = self.__searchPatternInColumnNamesOfViews__(pattern)
		if isinstance(data2,Exception): 
			pass
		else :
			columns += data2
		#Creating the table and searching an example value for each column
		colNb = len(columns)
		if colNb>0 : pbar,currentColNum = self.getStandardBarStarted(colNb), 0
		resultsToTable.append(['column_name','table_name','schema_name','example'])
		for e in columns:
			if colNb>0 : currentColNum += 1
			if colNb>0 : pbar.update(currentColNum)
			showThisColumn = True
			anExample = self.__getAnExampleOfValueForAColumn__(e['column_name'],e['table_name'],e['schema_name'])
			if isinstance(anExample,Exception): 
				anExample=self.DEFAULT_VALUE_UNKNOWN
			elif anExample==[] or anExample==[{}]:
				if noShowEmptyColumns == False: showThisColumn = True
				else :                          showThisColumn = False
				anExample=self.DEFAULT_VALUE_EMPTY_COLUMN
			else :
				anExample = repr(anExample[0][e['column_name']])
				if len(anExample)>2 :
					if anExample[0:2]=="u'" and anExample[-1] == "'":   anExample = anExample [2:-1]
					if anExample[0]=="'" and anExample[-1] == "'":      anExample = anExample [1:-1]
				if len(anExample)>self.EXEMPLE_VALUE_LEN_MAX:
					anExample = anExample[:self.EXEMPLE_VALUE_LEN_MAX]+' '+self.TRUNCATED_MESSAGE_EXEMPLE
			if showThisColumn == True:
				resultsToTable.append([e['column_name'],e['table_name'],e['schema_name'],anExample])
		if colNb>0 : pbar.finish()
		table = Texttable(max_width=getScreenSize()[0])
		table.set_deco(Texttable.HEADER)
		table.add_rows(resultsToTable)
		return table.draw()
		
		
		
	def isEmptyTable (self, table):
		"""
		String table
		"""
		if table.count('\n') <= 1 :
			return True
		else : 
			return False
			
	def getDatabaseNames(self):
		'''
		Returns database names in a list
		Returns Exception if an error
		'''
		dbNames = []
		data = self.executeRequest(self.REQ_GET_DATABASES_NAMES, ld=['name'], noResult=False)
		if isinstance(data,Exception):
			logging.error("Impossible to get database names: '{0}'".format(data))
			return data
		for aDB in data:
			dbNames.append(aDB['name'])
		logging.debug("Database found: {0}".format(dbNames))
		return dbNames
		
	def printDatabases(self):
		'''
		print databases names
		Returns True if printed or False if an error
		'''
		dbNames = self.getDatabaseNames()
		if isinstance(dbNames,Exception) == False:
			print("# Database names:")
			for aDb in dbNames:
				print("\t- {0}".format(aDb))
			return True
		else:
			logging.error("Impossible to print dtabase names")
			return False
		
		
	def getAllTables(self, minusDB=EXCLUDED_DATABASES):
		'''
		Return all tables for each database minus databases in minusDB
		return None if an error
		'''
		tables = {}
		allDatabases = self.getDatabaseNames()
		if isinstance(allDatabases,Exception):
			logging.error("Impossible to get tables without database names")
			return None
		for aDBToExcl in minusDB:
			allDatabases.remove(aDBToExcl)
		logging.info("Tables in following databases are excluded: {0}".format(minusDB))
		for aDBname in allDatabases:
			tables[aDBname]=[]
			logging.info("Getting tables for {0} database...".format(aDBname))
			data = self.executeRequest(self.REQ_GET_TABLES_FOR_A_DB_NAME.format(aDBname), ld=['name','id'], noResult=False)
			if isinstance(data,Exception):
				logging.warning("Impossible to get tables for database {0}: '{1}'".format(aDBname,data))
			else:
				for aTableInfo in data:
					tables[aDBname].append(aTableInfo)
		return tables
		
	def getAllTablesAndColumns(self,minusDB=EXCLUDED_DATABASES):
		'''
		Return all tables & columns for each database minus databases in minusDB
		'''
		columns={}
		tables = self.getAllTables(minusDB=minusDB)
		for aDBName in tables:
			for aTableName in tables[aDBName]:
				data = self.executeRequest(self.REQ_GET_COLUMNS.format(aDBName,aTableName['id']), ld=['name','type'], noResult=False)
				if isinstance(data,Exception):
					logging.warning("Impossible to get columns of table {0}.{1}: '{2}'".format(aDBname,aTableName['name'],data))
				else:
					columns[aTableName['id']]=[]
					for aColumn in data:
						columns[aTableName['id']].append(aColumn)
		return tables, columns
		
	def saveSchema(self, pathToOutFile, minusDB=EXCLUDED_DATABASES):
		"""
		Save all tables in output file
		"""
		tables, columns = self.getAllTablesAndColumns(minusDB=minusDB)
		logging.info("Saving results in {0}:".format(pathToOutFile))
		f = open(pathToOutFile,"w")
		for aDBName in tables:
			f.write("Database {0}:\n".format(repr(aDBName)))
			for aTableName in tables[aDBName]:
				f.write("\t- {0}\n".format(aTableName['name']))
				for aColumn in columns[aTableName['id']]:
					f.write("\t\t- {0} ({1})\n".format(aColumn['name'], aColumn['type']))
		f.close()
		
	def saveTables(self, pathToOutFile, minusDB=EXCLUDED_DATABASES):
		"""
		Save all tables in output file
		"""
		tables = self.getAllTables(minusDB=minusDB)
		logging.info("Saving results in {0}:".format(pathToOutFile))
		f = open(pathToOutFile,"w")
		for aDBName in tables:
			f.write("Database {0}:\n".format(repr(aDBName)))
			for aTableName in tables[aDBName]:
				f.write("\t- {0}\n".format(aTableName['name']))
		f.close()
		
	def startInteractiveSQLShell(self):
		"""
		Start an interactive SQL shell (limited)
		Return True when finished
		"""
		print("Ctrl-D to close the SQL shell. Use ENTER twice for committing a request")
		while True:
			theLine = None
			allLines = ""
			#print("SQL> ", end='')
			while theLine != "":
				try:
					theLine = input("SQL> ")
				except EOFError:
					print("\nSQL shell closed")
					return True
				allLines += theLine
			if allLines != "":
				results = self.executeRequest(allLines, ld=[], noResult=False, autoLD=True)
				if isinstance(results,Exception):
					print(results)
				elif results==[]:
					print("Executed successfully but no result")
				else:
					resultsToTable = [tuple(results[0].keys())]
					for aLine in results:
						resultsToTable.append(tuple(aLine.values()))
					table = Texttable(max_width=getScreenSize()[0])
					table.set_deco(Texttable.HEADER)
					table.add_rows(resultsToTable)
					print(table.draw())
					
	def moveToMasterDBIfRequired(self):
		'''
		Returns True if OK
		Returns Exception if error
		'''
		self._lastDBname = self.getDBName()
		if isinstance(self._lastDBname,Exception):
			return self._lastDBname
		if self._lastDBname == "master":
			logging.info("Currently on master database, nothing to do")
		else:
			return self.useThisDB('master')
			
	def comeBackToLastDBIfRequired(self):
		'''
		Returns True if OK
		Returns Exception if error
		Returns None if critical bug in code
		'''
		if self._lastDBname == "master":
			logging.info("Last database was on master, nothing to do")
			return True
		elif self._lastDBname == None:
			logging.critical("Bug in code with comeBackToLastDBIfRequired()")
			return None
		else:
			return self.useThisDB(self._lastDBname)
		
	
	def getLocationDataFilesLogFiles(self):
		'''
		Get Location of Data Files and Log Files in SQL Server
		Returns exception if an error
		REQUIREMENT: Has to be executed on MASTER database
		'''
		data = self.executeRequest(self.REQ_GET_PATH_LOCAL_FILES, ld=['name','physical_name'], noResult=False)
		if isinstance(data,Exception):
			logging.warning("Impossible to get Data Files and Log Files: '{0}'".format(data))
			return data
		else:
			return data
	
	def printRemoteDatabaseConfig(self):
		'''
		print remote DB configuration
		'''
		self.moveToMasterDBIfRequired()
		data = self.getLocationDataFilesLogFiles()
		if isinstance(data,Exception) == False:
			print("# Location of Data Files and Log Files in SQL Server")
			for e in data:
				print("\t- {0}: {1}".format(e['name'], e['physical_name']))
		self.comeBackToLastDBIfRequired()
		
	def getInstanceInformation(self):
		'''
		Get SQL Server Instance information
		Returns exception if an error
		REQUIREMENT: Has to be executed on MASTER database
		'''
		data = self.executeRequest(self.REQ_GET_INSTANCE_INFORMATION, noResult=False, autoLD=True,)
		if isinstance(data,Exception):
			logging.warning("Impossible to get SQL Server Instance information: '{0}'".format(data))
			return data
		else:
			return data
			
	def printInstanceInformation(self):
		'''
		print remote DB configuration
		'''
		self.moveToMasterDBIfRequired()
		data = self.getInstanceInformation()
		if isinstance(data,Exception) == False:
			print("# SQL Server Instance information")
			for aK in data[0]:
				print("\t- {0}: {1}".format(aK, data[0][aK]))
		self.comeBackToLastDBIfRequired()
		
	def getAdvancedConfig(self):
		'''
		Get Advanced Options
		Returns exception if an error
		'''
		data = self.executeRequest(request=self.REQ_GET_ADVANCED_OPTIONS, ld=[], noResult=False, autoLD=True)
		if isinstance(data,Exception):
			logging.warning("Impossible to get SQL Server Instance information: '{0}'".format(data))
			return data
		else:
			return data
	
	def printAdvancedConfig(self):
		'''
		print Advanced Options
		'''
		data = self.getAdvancedConfig()
		if isinstance(data,Exception) == False:
			print("# SQL Server Advanced Options")
			resultsToTable = []
			columns = []
			for aK in data[0]:
				columns.append(aK)
			resultsToTable.append(tuple(columns))
			for aE in data:
				aLine = []
				for aK in aE:
					aLine.append(aE[aK])
				resultsToTable.append(tuple(aLine))
			table = Texttable(max_width=getScreenSize()[0])
			table.set_deco(Texttable.HEADER)
			table.add_rows(resultsToTable)
			print(table.draw())
			
	def printAllUsers(self):
		'''
		print All users
		Returns True if ok othwerwise returns False (an error)
		'''
		allUsernames = self.getUsernamesViaSyslogins()
		if isinstance(allUsernames,Exception):
			logging.error("Impossible to print users")
			return False
		else:
			print("# connection accounts (sys.syslogins):")
			for aUser in allUsernames:
				print("\t- {0}".format(aUser))
			return True
			
	def getDisableUsers(self):
		'''
		Get all disable users
		Returns list otherwise returns exception
		'''
		allUserNames = []
		REQ_GET_DISABLE_ACCOUNTS = """SELECT name FROM master.sys.server_principals WHERE is_disabled = 1"""
		data = self.executeRequest(request=REQ_GET_DISABLE_ACCOUNTS, ld=[], noResult=False, autoLD=True)
		if isinstance(data,Exception):
			logging.warning("Impossible to get disable users: '{0}'".format(data))
			return data
		else:
			for aUser in data:
				allUserNames.append(aUser['name'])
			return allUserNames
			
	def printDisableUsers(self):
		'''
		Print all disable users
		Returns True if ok othwerwise returns False (an error)
		'''
		allUsernames = self.getDisableUsers()
		if isinstance(allUsernames,Exception):
			logging.error("Impossible to print disable users")
			return False
		else:
			print("# disable connection accounts:")
			for aUser in allUsernames:
				print("\t- {0}".format(aUser))
			return True
			
	def getAccountsPwdPolicyNotSet(self):
		'''
		Returns accounts as list when password policy does not apply on it
		Returns list otherwise returns exception
		'''
		allUserNames = []
		REQ_GET_ACC_PWD_POLICY_NOT_SET = """SELECT name FROM master.sys.sql_logins WHERE is_policy_checked = 0"""
		data = self.executeRequest(request=REQ_GET_ACC_PWD_POLICY_NOT_SET, ld=[], noResult=False, autoLD=True)
		if isinstance(data,Exception):
			logging.warning("Impossible to get list of users when password policy does not apply on it: '{0}'".format(data))
			return data
		else:
			for aUser in data:
				allUserNames.append(aUser['name'])
			return allUserNames
			
	def printAccountsPwdPolicyNotSet(self):
		'''
		Print all accounts when password policy does not apply on it
		Returns True if ok othwerwise returns False (an error)
		'''
		allUsernames = self.getAccountsPwdPolicyNotSet()
		if isinstance(allUsernames,Exception):
			logging.error("Impossible to print accounts when pwd policy does not apply on account")
			return False
		else:
			print("# accounts when password policy does not apply on it:")
			for aUser in allUsernames:
				print("\t- {0}".format(aUser))
			return True
			
	def getAccountsNoExpiration(self):
		'''
		Returns accounts with no expiration pwd
		Returns list otherwise returns exception
		'''
		allUserNames = []
		REQ_GET_ACC_NO_EXPIRATION = """SELECT name FROM master.sys.sql_logins WHERE is_expiration_checked = 0"""
		data = self.executeRequest(request=REQ_GET_ACC_NO_EXPIRATION, ld=[], noResult=False, autoLD=True)
		if isinstance(data,Exception):
			logging.warning("Impossible to get list of accounts with no expiration pwd: '{0}'".format(data))
			return data
		else:
			for aUser in data:
				allUserNames.append(aUser['name'])
			return allUserNames
		
	def printAccountsNoExpiration(self):
		'''
		Print all accounts with no expiration pwd
		Returns True if ok othwerwise returns False (an error)
		'''
		allUsernames = self.getAccountsNoExpiration()
		if isinstance(allUsernames,Exception):
			logging.error("Impossible to print list of accounts with no expiration pwd")
			return False
		else:
			print("# accounts with no expiration password:")
			for aUser in allUsernames:
				print("\t- {0}".format(aUser))
			return True
		
	def getSysadminAccounts(self):
		'''
		Returns Sysadmin Accounts
		Returns list otherwise returns exception
		'''
		allUserNames = []
		REQ_GET_SYSADMIN_ACCOUNTS = """SELECT name FROM master.sys.syslogins WHERE sysadmin = 1"""
		data = self.executeRequest(request=REQ_GET_SYSADMIN_ACCOUNTS, ld=[], noResult=False, autoLD=True)
		if isinstance(data,Exception):
			logging.warning("Impossible to get list of sysadmin accounts: '{0}'".format(data))
			return data
		else:
			for aUser in data:
				allUserNames.append(aUser['name'])
			return allUserNames
		
	def printSysadminAccounts(self):
		'''
		Print all Sysadmin Accounts
		Returns True if ok othwerwise returns False (an error)
		'''
		allUsernames = self.getSysadminAccounts()
		if isinstance(allUsernames,Exception):
			logging.error("Impossible to print sysadmin accounts")
			return False
		else:
			print("# sysadmin accounts:")
			for aUser in allUsernames:
				print("\t- {0}".format(aUser))
			return True
			
	def printSysloginsInfo(self):
		'''
		Print syslogins information
		Returns True if ok othwerwise returns False (an error)
		'''
		data = self.getSysloginsInformation()
		if isinstance(data,Exception):
			logging.error("Impossible to print syslogins information")
			return False
		else:
			print("# Syslogins information")
			columns = ['name','loginname', 'updatedate','language','denylogin','hasaccess','isntname','isntgroup','sysadmin','securityadmin','serveradmin','setupadmin','processadmin','diskadmin','dbcreator','bulkadmin']
			resultsToTable = []
			resultsToTable.append(tuple(columns))
			for aE in data:
				aLine = []
				for aK in columns:
					aLine.append(aE[aK])
				resultsToTable.append(tuple(aLine))
			table = Texttable(max_width=getScreenSize()[0])
			table.set_deco(Texttable.HEADER)
			table.add_rows(resultsToTable)
			print(table.draw())
			
	def getStoredProceduresAccessible(self):
		'''
		Get all stored procedures
		Returns list otherwise returns exception
		'''
		storedProcs = []
		REQ_ALL_STORED_PROCEDURES = """SELECT sysobjects.name FROM sysobjects, sysprotects WHERE sysprotects.uid = 0 and xtype in ('x','p') and sysobjects.id = sysprotects.id ORDER BY sysobjects.name"""
		data = self.executeRequest(request=REQ_ALL_STORED_PROCEDURES, ld=[], noResult=False, autoLD=True)
		if isinstance(data,Exception):
			logging.warning("Impossible to get stored procedures: '{0}'".format(data))
			return data
		else:
			for aInfo in data:
				storedProcs.append(aInfo['name'])
		return storedProcs
		
	def printStoredProcedures(self):
		'''
		Print Stored Procedures
		Returns True if ok othwerwise returns False (an error)
		'''
		data = self.getStoredProceduresAccessible()
		if isinstance(data,Exception):
			logging.error("Impossible to print stored procedures")
			return False
		else:
			lenData = len(data)
			print("# All Stored procedures:")
			columns = ['name','name','name','name',]
			pos = 0
			resultsToTable = []
			resultsToTable.append(tuple(columns))
			for aE in data:
				aLine = []
				for i in range(4):
					if pos>= lenData:
						aLine.append('')
					else:
						aLine.append(data[pos])
					pos += 1
				resultsToTable.append(tuple(aLine))
			table = Texttable(max_width=getScreenSize()[0])
			table.set_deco(Texttable.HEADER)
			table.add_rows(resultsToTable)
			print(table.draw())
		
def runSearchModule(args):
	'''
	Run the Search module
	'''
	if checkOptionsGivenByTheUser(args,["column-names","pwd-column-names","no-show-empty-columns","test-module","schema-dump", "table-dump",'sql-shell','get-config'],checkAccount=True) == False : 
		return EXIT_MISS_ARGUMENT
	search = Search(args)
	search.connect(printErrorAsDebug=False, stopIfError=True)
	if args['get-config'] == True:
		args['print'].title("Getting database configuration")
		search.printInstanceInformation()
		search.printRemoteDatabaseConfig()
		search.printDatabases()
		search.printAllUsers()
		search.printDisableUsers()
		search.printSysadminAccounts()
		search.printSysloginsInfo()
		search.printAccountsNoExpiration()
		search.printAccountsPwdPolicyNotSet()
		search.printAdvancedConfig()
		search.printStoredProcedures()
	if args['column-names'] != None:
		args['print'].title("Searching the pattern '{0}' in column names of all views and tables accessible to the current user (each database accessible by current user shoud be tested manually)".format(args['column-names']))
		table= search.searchInColumnNames(args['column-names'],noShowEmptyColumns=args['no-show-empty-columns'])
		if search.isEmptyTable(table) == True :
			args['print'].badNews("No result found")
		else :
			args['print'].goodNews(table)
	if args['pwd-column-names'] != None:
		args['print'].title("Searching password patterns in column names of all views and tables accessible to the current user (each database accessible by current user shoud be tested manually)")
		for aPwdPattern in PATTERNS_COLUMNS_WITH_PWDS:
			aResult = search.searchInColumnNames (aPwdPattern, noShowEmptyColumns=args['no-show-empty-columns'])
			if search.isEmptyTable(aResult) == True :
				args['print'].badNews("No result found for the pattern '{0}'".format(aPwdPattern))
			else :
				args['print'].goodNews("Result(s) found for the pattern '{0}':".format(aPwdPattern))
				args['print'].goodNews(aResult)
	if args['schema-dump'] != None:
		outFile = args['schema-dump']
		args['print'].title("Extracting schema and saving in {0}".format(outFile))
		args['print'].goodNews("Keep calm and wait... Can take minutes!".format(outFile))
		search.saveSchema(pathToOutFile=args['schema-dump'])
		args['print'].goodNews("Results saved in {0}:".format(args['table-dump']))
	if args['table-dump'] != None:
		outFile = args['table-dump']
		args['print'].title("Extracting table and saving in {0}".format(outFile))
		search.saveTables(pathToOutFile=args['table-dump'])
		args['print'].goodNews("Results saved in {0}:".format(args['table-dump']))
	if args['sql-shell'] == True:
		args['print'].title("Starting an interactive SQL shell")
		search.startInteractiveSQLShell()
	search.closeConnection()

