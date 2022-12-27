#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Utils import cleanString, ErrorClass
import pymssql, decimal
from Constants import *
from progressbar import *

class Mssql ():
	'''
	MS SQL class 
	'''
	
	#CONSTANTES
	ERROR_ACCOUNT_IS_DISABLED = "Reason: The account is disabled"
	ERROR_ACCOUNT_INVALID = "Login failed for user "
	ERROR_UNTRUSTED_DOMAIN = "The login is from an untrusted domain and cannot be used with Windows authentication." #Credentials are not valid
	ERROR_UNABLE_TO_CONNECT = "Unable to connect:"
	MS2019_BANNER = "Microsoft SQL Server 2019"
	MS2017_BANNER = "Microsoft SQL Server 2017"
	MS2016_BANNER = "Microsoft SQL Server 2016"
	MS2014_BANNER = "Microsoft SQL Server 2014"
	MS2012_BANNER = "Microsoft SQL Server 2012"
	MS2008_BANNER = "Microsoft SQL Server 2008"
	MS2005_BANNER = "Microsoft SQL Server 2005" #<------------------------------------ CHECK this value: perhaps FALSE
	MS2000_BANNER = "Microsoft SQL Server 2000" #<------------------------------------ CHECK this value: perhaps FALSE
	POST_TABLE_NAME = "MSAT_TABLE_" #Post table name created in the tool
	REQ_USE_THIS_DB = "USE {0}" #{0} database
	REQ_GET_DB_NAME = "SELECT DB_NAME() AS databasename"
	REQ_EXEC_SP_FOR_PE = "EXEC {0}" #{0} proc name
	REQ_DEL_PROC = "DROP PROCEDURE {0}" #{0} proc name

	def __init__ (self, args=None, loginTimeout=DEFAULT_LOGIN_TIMEOUT, charset=DEFAULT_CHARSET):
		'''
		Constructor
		'''
		self.host = args['host']
		self.user = args['user']
		self.password = args['password']
		self.database = args['database']
		self.port = args['port']
		self.loginTimeout = args['loginTimeout']
		self.charset = args['charset']
		self.domain = args['domain']
		self.args = args
		if ('connection' in self.args) == False : self.args['connection'] = None
		if ('cursor' in self.args) == False : self.args['cursor'] = None
		self.autocommit = True
		self.completeVersion = None

	def connect(self, printErrorAsDebug=False, stopIfError=False):
		'''
		Connect to the database
		Create a connection object and a cursor
		Return True if Ok, otherwise, return 
		'''
		logging.debug("Connecting to the '{0}':'{4}' database server, on the '{1}' database with the '{2}':'{3}' account...".format(self.host, self.database, self.user, self.password, self.port))
		if self.domain == None : 
			logging.debug("Domain name NOT specified. Consequently, windows authentication NOT enabled: SQL server Authentication eanbled ONLY !");
			userString = self.user
		else :
			logging.debug("Domain name specified. Consequently, SQL server Authentication DISABLED and windows authentication ENABLED !");
			userString = '{0}\\{1}'.format(self.domain, self.user)
		try :
			self.args['connection'] = pymssql.connect(host=self.host, user=userString, password=self.password, database=self.database, port=self.port, charset=self.charset, login_timeout = DEFAULT_LOGIN_TIMEOUT)
			self.args['connection'].autocommit(self.autocommit)
		except Exception as e :
			logging.debug("Connection not established : '{0}'".format(repr(e)))
			if self.ERROR_ACCOUNT_IS_DISABLED in str(e):
				errorMsg = "The '{0}' account is disabled".format(self.user)
				if printErrorAsDebug == False : logging.error(errorMsg)
				else: logging.debug(errorMsg)
				return ErrorClass(errorMsg)
			elif self.ERROR_ACCOUNT_INVALID in str(e) or self.ERROR_UNTRUSTED_DOMAIN in str(e):
				if self.domain == None :
					errorMsg = "The '{0}' account is invalid. A domain name could be used to enable the Windows Authentication".format(self.user)
				else:
					errorMsg = "The '{0}' account is invalid. The domain name could be removed to enable SQL server Authentication".format(self.user)
				if printErrorAsDebug == False : logging.error(errorMsg)
				else: logging.debug(errorMsg)
				return ErrorClass(errorMsg)
			else:
				if self.ERROR_UNABLE_TO_CONNECT in str(e) or printErrorAsDebug == False : 
					logging.error("Connection error: {0}".format(e))
					return -1
				else: logging.debug("Connection error: {0}".format(e))
			return ErrorClass(e)
		else :
			logging.debug("Connection established. Creating the cursor...")
			try: 
				self.args['cursor'] = self.args['connection'].cursor()
				logging.debug("Cursor created")
				return True
			except Exception as e:
				return ErrorClass(e)
				
	def update (self, host, user, password, database='master', port=1433):
		'''
		Update host user password database and port
		'''
		self.host = host
		self.user = user
		self.password = password
		self.database = database
		self.port = port
		self.args['connection'] = None
		self.args['cursor'] = None
	
	def closeConnection (self):
		'''
		close the connection
		return True if Ok, otherwise return ErrorClass()
		'''
		logging.debug("Closing the connection to the {0} database server...".format(self.host))
		if self.args['connection'] != None :
			try: self.args['connection'].close()
			except Exception as e: return ErrorClass(e)
			else:   
				logging.debug("Connection closed")
				return True
		else:
			errorMsg = "A connection has not been established to the {0} database server".format(self.host) 
			logging.error(errorMsg)
			return ErrorClass(errorMsg)

	def executeRequest (self, request, ld=[], noResult=False, autoLD=False):
		'''
		Execute request
		ld: list containing all name of columns
		Return a list of dico named by column. 
		Example:  
			request = "SELECT name FROM master..syslogins"
			ld = ['version']
			return : [{'version': u'Microsoft SQL Server 2008 (RTM) ...\n'}]
		Otherwise, return ErrorClass
		'''
		logging.debug("Executing the following request: {0}...".format(repr(request)))
		if self.args['cursor'] != None:
			try: 
				self.args['cursor'].execute(request)
			except Exception as e: return ErrorClass(e)
			else:
				if noResult==True : return []
				try:
					results = self.args['cursor'].fetchall()
				except Exception as e: return ErrorClass(e)
				if ld==[]:
					if autoLD == True:
						ld = [item[0] for item in self.args['cursor'].description]
					else:
						return results
				values = []
				for line in results:
					dico = {}
					for i in range(len(line)): 
						dico[ld[i]] = line[i]
					values.append(dico)
				return values
		else :
			errorMsg = "A cursor has not been created to the {0} database server".format(self) 
			logging.error(errorMsg)
			return ErrorClass(errorMsg) 

	def getCompleteVersion (self):
		'''
		return complete version
		'''
		logging.debug("Getting the database version installed on the {0} server".format(self.host))
		if self.completeVersion == None :
			data = self.executeRequest("SELECT @@version",['version'])
			if isinstance(data,Exception): return data
			elif len(data) == 1 :
				version = cleanString(data[0]['version'])
				logging.debug("The version is : {0}".format(version))
				return version
			else : return ""
		else : self.completeVersion 
		
	def __loadCompleteVersionIfNeed__(self):
		'''
		Load the complete version value if it is not None
		Return True if loaded. Else return False
		'''
		if self.completeVersion == None : 
				self.completeVersion = self.getCompleteVersion()
				return True
		else : 
			return False
		
	def isThe2019Version (self):
		'''
		Return True if version 2019, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2019_BANNER in self.completeVersion : return True
		else: return False
		
	def isThe2017Version (self):
		'''
		Return True if version 2017, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2017_BANNER in self.completeVersion : return True
		else: return False
		
	def isThe2016Version (self):
		'''
		Return True if version 2016, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2016_BANNER in self.completeVersion : return True
		else: return False
		
	def isThe2014Version (self):
		'''
		Return True if version 2014, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2014_BANNER in self.completeVersion : return True
		else: return False

	def isThe2012Version (self):
		'''
		Return True if version 2012, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2012_BANNER in self.completeVersion : return True
		else: return False

	def isThe2008Version (self):
		'''
		Return True if version 2008, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2008_BANNER in self.completeVersion : return True
		else: return False
		
	def isThe2005Version (self):
		'''
		Return True if version 2005, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2005_BANNER in self.completeVersion : return True
		else: return False
		
	def isThe2000Version (self):
		'''
		Return True if version 2000, else return False
		'''
		self.__loadCompleteVersionIfNeed__()
		if self.MS2000_BANNER in self.completeVersion : return True
		else: return False
		
	def getStandardBarStarted(self, maxvalue):
		"""Standard status bar"""
		return ProgressBar(widgets=['', Percentage(), ' ', Bar(),' ', ETA(), ' ',''], maxval=maxvalue).start()
		
	def useThisDB(self, name):
		'''
		Returns True if OK
		Returns Exception if error
		'''
		logging.info("Moving to the database {0}".format(name))
		data = self.executeRequest(self.REQ_USE_THIS_DB.format(name), noResult=True)
		if isinstance(data,Exception):
			logging.warning("Impossible to move to the database {0}".format(name))
			return data
		else:
			logging.debug("We are in the database {0}".format(name)) 
			return True
			
	def __isCurrentUser__(self, roleName):
		'''
		Returns True if current user has roleName
		Otherwise return False
		If error, return Exception
		'''
		REQ = "SELECT is_srvrolemember('{0}') as role".format(roleName)
		logging.info("Checking if the current user is {0}".format(roleName))
		data = self.executeRequest(REQ,ld=['role'])
		if isinstance(data,Exception): 
			logging.warning("Impossible to known if the user has {0} role: {1}".format(roleName, data))
			return data
		else:
			for e in data: 
				if e['role']==0:
					logging.debug("The current user is not {0}".format(roleName))
					return False
				elif e['role']==1:
					logging.debug("The current user is {0}".format(roleName))
					return True
				else:
					msg = "Impossible to known if the user has {0} because the result is not 1 or 0. The result is '{1}'".format(roleName, e['issysadmin'])
					logging.warning(msg)
					return ErrorClass(msg)
			msg = "Impossible to known if the user has {0} because the result is empty"
			logging.warning(msg)
			return ErrorClass(msg)

	def isCurrentUserSysadmin(self):
		'''
		Returns True if current user is SYSADMIN
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('sysadmin')
		
	def isCurrentUserServeradmin(self):
		'''
		Returns True if current user is serveradmin
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('serveradmin')
		
	def isCurrentUserDbcreator(self):
		'''
		Returns True if current user is dbcreator
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('dbcreator')
		
	def isCurrentUserSetupadmin(self):
		'''
		Returns True if current user is setupadmin
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('setupadmin')
		
	def isCurrentUserBulkadmin(self):
		'''
		Returns True if current user is bulkadmin
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('bulkadmin')
	
	def isCurrentUserSecurityadmin(self):
		'''
		Returns True if current user is securityadmin
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('securityadmin')
	
	def isCurrentUserDiskadmin(self):
		'''
		Returns True if current user is diskadmin
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('diskadmin')

	def isCurrentUserPublic(self):
		'''
		Returns True if current user is public
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('public')
		
	def isCurrentUserProcessadmin(self):
		'''
		Returns True if current user is processadmin
		Otherwise return False
		If error, return Exception
		'''
		return self.__isCurrentUser__('processadmin')

	def getCurrentUser(self):
		'''
		Returns the current user name
		If error, returns Exception
		'''
		logging.info("Getting the current username")
		data = self.executeRequest(self.REQ_GET_CURRENT_USER,ld=['username'])
		if isinstance(data,Exception): 
			logging.warning("Impossible to know the current username: {0}".format(data))
			return data
		else:
			for e in data:
				username = e['username'].replace("{0}\\".format(self.domain),'')
				logging.debug("The current user is {0}".format(username)) 
				return username
			msg = "Impossible to know the current username because the result is empty"
			logging.warning(msg)
			return ErrorClass(msg)

	def execSP(self, spName):
		'''
		Execute the stored proc named spName
		Returns True
		Returns Exception if error
		'''
		logging.info("Executing the {0} stored procedure".format(spName))
		data = self.executeRequest(self.REQ_EXEC_SP_FOR_PE.format(spName), noResult=True)
		if isinstance(data,Exception):  
			logging.warning("Impossible to execute the stored procedure '{1}': {0}".format(data, spName))
			return data
		else:
			logging.debug("The stored procedure named {0} has been executed".format(spName))
			return True

	def deleteSP(self, spName):
		'''
		Delete the stored proc named spName
		Returns True
		Returns Exception if error
		'''
		logging.info("Deleting the stored procedure named {0}".format(spName))
		data = self.executeRequest(self.REQ_DEL_PROC.format(spName), noResult=True)
		if isinstance(data,Exception):
			logging.debug("Impossible to delete the stored procedure '{1}': {0}".format(data, spName))
			return data
		else:
			logging.debug("The stored procedure named {0} has been removed".format(spName))
			return True

	def getDBName (self):
		'''
		returns the current database name
		Returns Exception if error
		'''
		logging.info("Getting the current database name")
		data = self.executeRequest(self.REQ_GET_DB_NAME, ld=['databasename'])
		if isinstance(data,Exception):
			logging.warning("Impossible to get the current database name: {0}".format(data))
			return data
		else:
			for e in data:
				logging.debug("The database name is {0}".format(e['databasename']))
				return e['databasename']
			msg = "Impossible to get the current database name because the result is empty"
			logging.warning(msg)
			return ErrorClass(msg)
			
	def getUsernamesViaSyslogins(self):
		'''
		Get all usernames from the syslogins table
		Returns list of usernames of no problem. Otherwise returns an exception
		'''
		QUERY = "SELECT name FROM master..syslogins"
		logging.info('Get all usernames from the syslogins table...')
		response = self.executeRequest(request=QUERY,ld=['username'])
		if isinstance(response,Exception) :
			logging.info('Error with the SQL request {0}: {1}'.format(QUERY,str(response)))
			return response
		else:
			allUsernames = []
			if response == []: 
				pass
			else:
				for e in response : 
					allUsernames.append(e['username']) 
			return allUsernames
			
	def getSysloginsInformation(self):
		'''
		Get information from sys.syslogins
		Returns list of dict or expection if an error
		'''
		QUERY = "SELECT * FROM master..syslogins"
		logging.info('Get info from syslogins table...')
		response = self.executeRequest(request=QUERY,ld=[], noResult=False, autoLD=True)
		if isinstance(response,Exception) :
			logging.info('Error with the SQL request {0}: {1}'.format(QUERY,str(response)))
			return response
		else:
			return response
