#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Mssql import Mssql
from Utils import ErrorClass, checkOptionsGivenByTheUser
from Constants import *

class XpDirectory (Mssql):
	'''
	To get a shell
	'''
	#CONSTANTES
	OUTPUT_FORMAT_XP_DIRTREE = "{0} ({1})\n"
	REQ_XP_DIRTREE = "EXEC master..xp_dirtree '{0}',1,1;" #{0}=>Folder
	REQ_XP_FILEEXIST = "EXEC MASTER.DBO.XP_FILEEXIST '{0}';"#{0}=>File or folder
	REQ_XP_FIXEDDRIVES = "EXEC master.sys.xp_fixeddrives"
	REQ_XP_AVAILABLEMEDIA = "EXEC master.sys.xp_availablemedia"
	REQ_XP_SUBDIRS = "EXEC master.sys.xp_subdirs'{0}';" #{0}=>Folder
	REQ_XP_CREATE_SUBDIR = "EXEC master.sys.xp_create_subdir '{0}'"#{0}=>Folder
	OUTPUT_DRIVES = "{0} ({1})"
	OUTPUT_MEDIA = "{0} (lowFree={1}), mediaType={2}"
	
	def __init__(self, args):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		#self.output = args['print']
		
	def listFilesViaXpDirtree (self, path):
		'''
		List files and folders remotely
		'''
		logging.info("Listing files stroed in '{0}' via xp_dirtree...".format(path))
		data = self.executeRequest(self.REQ_XP_DIRTREE.format(path),ld=['subdirectory','depth','file'])
		logging.debug("Raw data returned by the database: '{0}'".format(data))
		if isinstance(data,Exception):
			logging.debug("Impossible to list files stored in '{0}': {1}".format(path, data))
			return data
		else: 
			output = ""
			for l in data: 
				if int(l['file'])==0 : keyword = "Folder"
				else : keyword = "File"
				output += self.OUTPUT_FORMAT_XP_DIRTREE.format(l['subdirectory'],keyword)
			data = output
		return data
		
	def isFileExistViaXpFileexist (self, path):
		'''
		Return true if the file exist thanks to XP_FILEEXIST. Otherwise, return False.
		If error, return Error
		'''
		logging.info("Test if the file '{0}' exists via xp_fileexist...".format(path))
		data = self.executeRequest(self.REQ_XP_FILEEXIST.format(path),ld=['File Exists','File is a Directory','Parent Directory Exists'])
		if isinstance(data,Exception):
			logging.debug("Impossible to determine if the file '{0}' exists: {1}".format(path, data))
			return data
		else: 
			output = ""
			if int(data[0]['File is a Directory'])==1 : 
				logging.debug("It is a folder")
				output = "The folder {0} exists ".format(path)
			elif int(data[0]['File Exists'])==1 : 
				logging.debug("It is a file")
				output = "The file {0} exists ".format(path)
			else : 
				logging.debug("It is not a file and not a folder")
				output = "The file/folder {0} doesn't exist or feature not eanbled".format(path)
			data = output
		return data
		
	def listDrivesViaXpFixedDrives (self):
		'''
		List all drives via XP_FIXEDDRIVES
		'''
		logging.info("Listing drives via xp_fixeddrives...")
		data = self.executeRequest(self.REQ_XP_FIXEDDRIVES,ld=['drive','MB free'])
		if isinstance(data,Exception):
			logging.debug("Impossible to list drives: {0}".format(data))
			return data
		elif data == []:
			logging.debug("Impossible to list drives: empty result")
			return ErrorClass("Impossible to list drives: empty result")
		else: 
			output = ""
			for l in data: output += self.OUTPUT_DRIVES.format(l['drive'],l['MB free'])
			data = output
		return data
		

	def listDrivesViaXpAvailableMedia (self):
		'''
		List all drives via xp_availablemedia
		'''
		logging.info("Listing media via xp_availablemedia...")
		data = self.executeRequest(self.REQ_XP_AVAILABLEMEDIA,ld=['name','low free','high free','media type'])
		if isinstance(data,Exception):
			logging.debug("Impossible to list media: {0}".format(data))
			return data
		else: 
			output = ""
			for l in data: output += self.OUTPUT_MEDIA.format(l['name'],l['low free'],l['high free'],l['media type'])
			data = output
		return data
		
	def listDirectoriesViaXpSubdirs (self,path):
		'''
		List directories thanks to REQ_XP_SUBDIRS
		'''
		logging.info("Listing directories via xp_fixeddrives...")
		data = self.executeRequest(self.REQ_XP_SUBDIRS.format(path),ld=['subdirectory'])
		if isinstance(data,Exception):
			logging.debug("Impossible to list directories: {0}".format(data))
			return data
		else:
			output = ""
			for l in data: output += l['subdirectory']+'\n'
			data = output
		return data
		
	def createSubDiViaXpCreateSubdir (self,path):
		'''
		Create a folder thanks to XP_CREATE_SUBDIR
		Return True if created or exist
		otherwise, return erro
		'''
		logging.info("Creating the folder {0}".format(path))
		data = self.executeRequest(self.REQ_XP_CREATE_SUBDIR.format(path),noResult=True)
		if isinstance(data,Exception):
			logging.debug("Impossible to create the folder {0}: {1}".format(path, data))
			return data
		else: return True
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("Can you list files with xp_dirtree ?")
		status = self.listFilesViaXpDirtree(DEFAULT_FOLDER)
		if isinstance(status,Exception): 
			self.args['print'].badNews("KO")
		elif status=='':
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you list directories with xp_subdirs ?")
		status = self.listDirectoriesViaXpSubdirs(DEFAULT_FOLDER)
		if isinstance(status,Exception):
			if "xp_subdirs could not access" in str(status):
				self.args['print'].goodNews("OK")
			else:
				self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you list drives with xp_subdirs ?")
		status = self.listDrivesViaXpFixedDrives()
		if isinstance(status,Exception):
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you list medias with xp_availablemedia ?")
		status = self.listDrivesViaXpAvailableMedia()
		if isinstance(status,Exception):
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you check if a file exist thanks to xp_fileexist ?")
		status = self.isFileExistViaXpFileexist(DEFAULT_FOLDER)
		if isinstance(status,Exception):
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you create a folder with xp_createsubdir ?")
		status = self.createSubDiViaXpCreateSubdir(DEFAULT_FOLDER)
		if isinstance(status,Exception):
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		
		
def runXpDirectoryModule(args):
	'''
	Run the XpDirectory module
	'''
	if checkOptionsGivenByTheUser(args,['list-files','list-dir','list-fixed-drives','list-available-media','file-exists','create-dir'],checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	xpDirectory = XpDirectory(args)
	xpDirectory.connect()
	if args["test-module"] == True: xpDirectory.testAll()
	if args["list-files"] != None:
		args['print'].title("Try to list files stored in {0}".format(args["list-files"][0]))
		data= xpDirectory.listFilesViaXpDirtree(args["list-files"][0])
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to list files stored in {0}: {1}".format(args["list-files"][0],data))
		else:
			args['print'].goodNews("Files stored in {0}:\n{1}".format(args["list-files"][0],data))
	if args["list-dir"] != None:
		args['print'].title("Try to list directories stored in {0}".format(args["list-dir"][0]))
		data= xpDirectory.listDirectoriesViaXpSubdirs(args["list-dir"][0])
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to list files stored in {0}: {1}".format(args["list-dir"][0],data))
		else:
			args['print'].goodNews("Files stored in {0}:\n{1}".format(args["list-dir"][0],data))
	if args["list-fixed-drives"] == True:
		args['print'].title("Try to list drives with xp_subdirs")
		data= xpDirectory.listDrivesViaXpFixedDrives()
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to list drives with xp_subdirs: {1}".format(data))
		else:
			args['print'].goodNews("Drives:\n{0}".format(data))
	if args["list-available-media"] == True:
		args['print'].title("Try to list medias with xp_availablemedia")
		data= xpDirectory.listDrivesViaXpAvailableMedia()
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to list drives with xp_availablemedia: {1}".format(data))
		else:
			args['print'].goodNews("Medias:\n{0}".format(data))
	if args["file-exists"] != None:
		args['print'].title("Try to check if the file {0} exists".format(args["file-exists"][0]))
		data= xpDirectory.isFileExistViaXpFileexist(args["file-exists"][0])
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to know if the file {0} exists: {1}".format(args["file-exists"][0],data))
		else:
			args['print'].goodNews("{1}".format(args["file-exists"][0],data))
	if args["create-dir"] != None:
		args['print'].title("Try to create the folder {0}".format(args["create-dir"][0]))
		data= xpDirectory.createSubDiViaXpCreateSubdir(args["create-dir"][0])
		if isinstance(data,Exception):
			args['print'].badNews("Impossible to create the folder {0}: {1}".format(args["create-dir"][0],data))
		else:
			args['print'].goodNews("The folder {0} has been created".format(args["create-dir"][0]))
	xpDirectory.closeConnection()





