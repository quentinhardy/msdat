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
	
	def __init__ (self, args=None):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		
	
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
				if noShowEmptyColumns == False:	showThisColumn = True
				else : 							showThisColumn = False
				anExample=self.DEFAULT_VALUE_EMPTY_COLUMN
			else :
				anExample = repr(anExample[0][e['column_name']])
				if len(anExample)>2 :
					if anExample[0:2]=="u'" and anExample[-1] == "'":	anExample = anExample [2:-1]
					if anExample[0]=="'" and anExample[-1] == "'":		anExample = anExample [1:-1]
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
		Returns None if an error
		'''
		dbNames = []
		data = self.executeRequest(self.REQ_GET_DATABASES_NAMES, ld=['name'], noResult=False)
		if isinstance(data,Exception):
			logging.error("Impossible to get database names: '{0}'".format(data))
			return None
		for aDB in data:
			dbNames.append(aDB['name'])
		logging.debug("Database found: {0}".format(dbNames))
		return dbNames
		
	def getAllTables(self, minusDB=EXCLUDED_DATABASES):
		'''
		Return all tables for each database minus databases in minusDB
		'''
		tables = {}
		allDatabases = self.getDatabaseNames()
		if allDatabases == None:
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
			
		
def runSearchModule(args):
	'''
	Run the Search module
	'''
	if checkOptionsGivenByTheUser(args,["column-names","pwd-column-names","no-show-empty-columns","test-module","schema-dump", "table-dump",'sql-shell'],checkAccount=True) == False : 
		return EXIT_MISS_ARGUMENT
	search = Search(args)
	search.connect(printErrorAsDebug=False, stopIfError=True)
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

