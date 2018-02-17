#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, os
from Mssql import Mssql
from Utils import cleanString, ErrorClass, getStandardBarStarted, checkOptionsGivenByTheUser
from time import sleep
from Constants import *

class PasswordGuesser:
	'''
	To do a dictionary attack on MS SQL account remotly
	'''
	def __init__(self, args, accountsFile, usernamesFile, passwordsFile, separator='/'):
		'''
		Constructor
		'''
		self.args=args
		self.valideAccounts = {}
		self.credSeparator = separator
		self.accountsFile = accountsFile
		self.usernamesFile = usernamesFile
		self.passwordsFile = passwordsFile
		if self.accountsFile == '' or self.accountsFile == None :  self.accounts = []
		elif self.usernamesFile != None and self.passwordsFile != None:
			self.accounts = []
			users = self.__getUsernames__()
			pwds = self.__getPasswords__()
			for aUser in users:
				for aPwd in pwds:
					self.accounts.append([aUser,aPwd])
		else :  self.accounts = self.__getAccounts__()
		
	def __getUsernames__(self):
		'''
		Returns  list containing usernames
		'''
		usernames = []
		logging.info('Loading usernames stored in the {0} file...'.format(self.usernamesFile))
		f = open(self.usernamesFile)
		for l in f:
			l = cleanString(l)
			usernames.append(l)
		f.close()
		logging.debug("Usernames loaded")
		return usernames

	def __getPasswords__(self):
		'''
		Returns  list containing usernames
		'''
		passwords = []
		logging.info('Loading usernames stored in the {0} file...'.format(self.passwordsFile))
		f = open(self.passwordsFile)
		for l in f:
			l = cleanString(l)
			passwords.append(l)
		f.close()
		logging.debug("Passwords loaded")
		return passwords

	def __getAccounts__(self):
		'''
		return list containing accounts
		'''
		accounts = []
		logging.info('Loading accounts stored in the {0} file...'.format(self.accountsFile))
		f = open(self.accountsFile)
		for l in f:
			lsplit = cleanString(l).split(self.credSeparator)
			if isinstance(lsplit,list):
				if len(lsplit) == 2 : 
					accounts.append([lsplit[0],lsplit[1]])
				elif len(lsplit) > 2 : 
					tempPasswd = ""
					for i in range(len(lsplit)): 
						if i != 0 : tempPasswd += lsplit[i]
					accounts.append([lsplit[0],tempPasswd])
				else : logging.warning("The account '{0}' not contains '{1}' or it contains more than one '{1}'. This account will not be tested".format(lsplit[0],self.credSeparator))
		f.close()
		logging.debug("Accounts loaded")
		return sorted(accounts, key=lambda x: x[0])

	def searchValideAccounts(self):
		'''
		Search valid accounts
		Return True if no connection error.
		Return False if a connection error
		'''
		userChoice = 1 
		logging.info("Searching valid accounts on '{0}':'{1}'/'{2}'".format(self.args['host'], self.args['port'], self.args['database']))
		pbar, nb = getStandardBarStarted(len(self.accounts)), 0
		for anAccount in self.accounts :
			currentUser, currentPassword = anAccount[0], anAccount[1]
			nb += 1
			pbar.update(nb)
			logging.debug("Try to connect with {0}".format('/'.join(anAccount)))
			status = self.__saveThisLoginInFileIfNotExist__(anAccount[0])
			if self.args['force-retry'] == False and status == False and userChoice ==1: 
				userChoice = self.__askToTheUserIfNeedToContinue__(anAccount[0])
			if userChoice == 0 : 
				logging.info("The attack is aborded because you choose to stop (s/S)")
				break
			self.args['user'], self.args['password'] = currentUser, currentPassword
			mssql = Mssql(args=self.args)
			status = mssql.connect(printErrorAsDebug = True)
			if status == -1:
				logging.error("Connection error. Abording!")
				return False
			elif status == True:
				mssql.closeConnection()
				self.valideAccounts[currentUser] = currentPassword
				logging.info("Valid credential: '{0}'/'{1}' on ('{2}':'{3}'/'{4}')  ".format(currentUser, currentPassword, self.args['host'], self.args['port'], self.args['database']))
			else: logging.info("Unvalid credential: '{0}'/'{1}' on ('{2}':'{3}'/'{4}')  ".format(currentUser, currentPassword, self.args['host'], self.args['port'], self.args['database']))
			sleep(self.args['timeSleep'])
		pbar.finish()
		return True
		
	def __saveThisLoginInFileIfNotExist__(self,login):
		''' 
		Save this login in the trace file to known if this login has already been tested
		If the login is in the file , return False. Otherwise return True
		'''
		if ('loginTraceFile' in self.args) == False:
			self.args['loginTraceFile'] = "{4}/{0}-{1}-{2}{3}".format(self.args['host'],self.args['port'],self.args['database'],PASSWORD_EXTENSION_FILE, PASSWORD_FOLDER)
			if os.path.isfile(self.args['loginTraceFile']) == False:
				if os.path.isdir(PASSWORD_FOLDER) == False:
					os.mkdir(PASSWORD_FOLDER)
				f=open(self.args['loginTraceFile'],'w')
				f.close()
				logging.info("The {0} file has been created".format(self.args['loginTraceFile']))
		f=open(self.args['loginTraceFile'],'r')
		for l in f:
			aLoginInFile = l.replace('\n','').replace('\r','').replace('\t','')
			if login == aLoginInFile :
				f.close() 
				return False
		f.close()
		f=open(self.args['loginTraceFile'],'a')
		f.write('{0}\n'.format(login))
		f.close()
		return True
		
	def __askToTheUserIfNeedToContinue__(self,login):
		'''
		Ask to the user if the module need to continue
		return:
		- 0 : stop (no)
		- 1 : continue and ask again (yes)
		- 2 : continue without ask (yes) 
		'''
		def askToContinue ():
			rep = raw_input("The login {0} has already been tested at least once. What do you want to do:\n- stop (s/S)\n- continue and ask every time (a/A)\n- continue without to ask (c/C)\n".format(login))
			if rep == 's' or rep == 'S' : return 0
			elif rep == 'a' or rep == 'A' : return 1
			elif rep == 'c' or rep == 'C' : return 2
			else : return -1
		rep = askToContinue()
		while (rep==-1):
			rep = askToContinue()
		return rep
		

def getHostsFromFile(filename):
	'''
	Return a list of hosts : [['1.1.1.1',1433],['1.1.1.2',1433], etc]
	'''
	hosts, lines = [], None
	logging.debug("Trying to read hosts from {0}".format(filename))
	f = open(filename)
	lines = f.readlines()
	logging.info("Reading hosts from {0}".format(filename))
	for aHost in lines:
		aHostSplitted = cleanString(aHost).split(':')
		if len(aHostSplitted) == 1:
			hosts.append([aHostSplitted[0],1433])
		elif len(aHostSplitted) == 2:
			hosts.append([aHostSplitted[0],aHostSplitted[1]])
		else:
			logging.warning("Impossible to read this host: {0}".format(aHostSplitted))
	f.close()
	logging.debug("Hosts stored in {0}: {1}".format(filename, hosts))
	return hosts
	
def runPasswordGuesserModuleOnAHost(args):
	'''
	'''
	passwordGuesser = PasswordGuesser(args, usernamesFile=args['usernames-file'], passwordsFile=args['passwords-file'], accountsFile=args['accounts-file'], separator='/')
	passwordGuesser.searchValideAccounts()
	validAccountsList = passwordGuesser.valideAccounts
	if validAccountsList == {}:
		args['print'].badNews("No found a valid account on {0}:{1}/{2}".format(args['host'], args['port'], args['database']))
	else :
		args['print'].goodNews("Accounts found on {0}:{1}/{2}: {3}".format(args['host'], args['port'], args['database'],validAccountsList))
		
def runPasswordGuesserModule(args):
	'''
	Run the PasswordGuesser module
	'''
	if checkOptionsGivenByTheUser(args,["search"],checkAccount=False, allowHostsFile=True) == False : return EXIT_MISS_ARGUMENT
	if args['hostlist'] != None:
		hosts = getHostsFromFile(args['hostlist'])
		args['print'].title("Searching valid accounts on these targets: {0}".format(hosts))
		for aHost in hosts:
			args['host'], args['port'] = aHost[0], aHost[1]
			args['print'].subtitle("Searching valid accounts on the {0} server, port {1}".format(args['host'], args['port']))
			runPasswordGuesserModuleOnAHost(args)
	else:
		args['print'].title("Searching valid accounts on the {0} server, port {1}".format(args['host'], args['port']))
		runPasswordGuesserModuleOnAHost(args)
		
	
