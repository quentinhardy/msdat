#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, argparse
from sys import exit,stdout
from Constants import *

from Output import Output
from Utils import cleanString, ErrorClass, databaseHasBeenGiven
from Mssql import Mssql
from PasswordGuesser import PasswordGuesser, runPasswordGuesserModule, getHostsFromFile
from Passwordstealer import Passwordstealer, runPasswordStealerModule
from Xpcmdshell import Xpcmdshell
from BulkOpen import BulkOpen, runBulkOpenModule
from XpDirectory import XpDirectory,runXpDirectoryModule
from SMBAuthenticationCapture import SMBAuthenticationCapture, runSMBAuthenticationCaptureModule
from OleAutomation import OleAutomation, runOleAutomationModule
from MssqlInfo import MssqlInfo, runMssqlInfoModule
from Xpcmdshell import Xpcmdshell, runXpCmdShellModule
from TrustworthyPE import TrustworthyPE, runTrustworthyPEModule
from Search import Search, runSearchModule
from Jobs import Jobs, runJobsModule
from UsernameLikePassword import UsernameLikePassword,runUsernameLikePassword

from Cleaner import runCleaner

#PYTHON_ARGCOMPLETE_OK
try:
	import argcomplete
	ARGCOMPLETE_AVAILABLE = True
except ImportError:
	ARGCOMPLETE_AVAILABLE = False
#PYTHON_COLORLOG_OK
try:
	from colorlog import ColoredFormatter
	COLORLOG_AVAILABLE = True
except ImportError:
	COLORLOG_AVAILABLE = False

def configureLogging(args):
	'''
	Configure le logging
	'''	
	logformatNoColor = "%(asctime)s %(levelname)-3s -: %(message)s"
	logformatColor   = "%(bg_black)s%(asctime)s%(reset)s %(log_color)s%(levelname)-3s%(reset)s %(bold_black)s-:%(reset)s %(log_color)s%(message)s%(reset)s"#%(bold_black)s%(name)s:%(reset)s
	datefmt = "%H:%M:%S"
	#Set log level
	if args['verbose']==0: level=logging.WARNING
	elif args['verbose']==1: level=logging.INFO
	elif args['verbose']>=2: level=logging.DEBUG
	#Define color for logs
	if args['no-color'] == False and COLORLOG_AVAILABLE==True:
		formatter = ColoredFormatter(logformatColor, datefmt=datefmt,log_colors={'CRITICAL': 'bold_red', 'ERROR': 'red', 'WARNING': 'yellow'})
	else : 
		formatter = logging.Formatter(logformatNoColor, datefmt=datefmt)
	stream = logging.StreamHandler()
	stream.setFormatter(formatter)
	root = logging.getLogger()
	root.setLevel(level)
	root.addHandler(stream)
	
def runAllModulesOnEachHost(args):
	'''
	Run all modules (for each host)
	'''
	if args['hostlist'] != None:
		hosts = getHostsFromFile(args['hostlist'])
		for aHost in hosts:
			args['host'], args['port'] = aHost[0], aHost[1]
			args['user'], args['password'] = None, None
			runAllModules(args)
	else:
		runAllModules(args)
	
def runAllModules(args):
	'''
	Run all modules
	'''
	connectionInformation, validDatabaseList = {}, []
	#A)REMOTE VERSION
	###########mssqlInfo = MssqlInfo(args)
	###########mssqlInfo.testAll()
	if databaseHasBeenGiven(args):
		validDatabaseList = [args['database']]
	#B)ACCOUNT MANAGEMENT
	if args['user'] == None and args['password'] == None:
		for database in validDatabaseList:
			args['print'].title("Searching valid accounts on the {0} database".format(database))
			args['database'] = database
			passwordGuesser = PasswordGuesser(args, usernamesFile=args['usernames-file'], passwordsFile=args['passwords-file'], accountsFile=args['accounts-file'])
			status = passwordGuesser.searchValideAccounts()
			if status == False: #Connection error during scan (perhaps host is unavailable now)
				logging.error("Host is probably unavailable. Stopping for this host!")
				return
			validAccountsList = passwordGuesser.valideAccounts
			if validAccountsList == {}:
				args['print'].badNews("No found a valid account on {0}:{1}/{2}.".format(args['host'], args['port'], args['database']))
				return
			else :
				args['print'].goodNews("Accounts found on {0}:{1}/{2}: {3}. All modules will be started with this (these) account(s)".format(args['host'], args['port'], args['database'],validAccountsList))
				for aLogin, aPassword in validAccountsList.items(): 
					if connectionInformation.has_key(database) == False: connectionInformation[database] = [[aLogin,aPassword]]
					else : connectionInformation[database].append([aLogin,aPassword])
	else :
		validAccountsList = {args['user']:args['password']}
		for database in validDatabaseList:
			for aLogin, aPassword in validAccountsList.items():
				if connectionInformation.has_key(database) == False: connectionInformation[database] = [[aLogin,aPassword]]
				else : connectionInformation[database].append([aLogin,aPassword])
	#C)ALL OTHERS MODULES
	for aDatabase in connectionInformation.keys():
		for loginAndPass in connectionInformation[aDatabase]:
			args['database'] , args['user'], args['password'] = aDatabase, loginAndPass[0],loginAndPass[1]
			args['print'].title("Testing the '{0}' database with the account {1}/{2}".format(database,args['user'], args['password']))
			#C.0)Trustworthy module (Privilege escalation)
			trustworthyPE = TrustworthyPE(args)
			status = trustworthyPE.connect()
			if isinstance(status,Exception):
				args['print'].badNews("Impossible to connect to the remote database: {0}".format(str(status).replace('\n','')))
				break
			trustworthyPE.testAll()
			#C.1)Passwordstealer
			passwordstealer = Passwordstealer(args)
			passwordstealer.testAll()
			#C.2)xpcmdshell
			xpcmdshell = Xpcmdshell(args)
			xpcmdshell.testAll()
			#C.3)Jobs
			jobs = Jobs(args)
			jobs.testAll()
			#C.4) SMBAUthenticationCapture
			smbAuthenticationCapture = SMBAuthenticationCapture(args,localIp="127.0.0.1", shareName=DEFAULT_SHARE_NAME)
			smbAuthenticationCapture.testAll()
			#C.5) OLEAutomation
			oleAutomation = OleAutomation(args)
			oleAutomation.testAll()
			#C.6) BulkOpen
			bulkOpen = BulkOpen(args)
			bulkOpen.testAll()
			#C.7) XpDirectory
			PPxpdirectory = XpDirectory(args)
			PPxpdirectory.testAll()
			bulkOpen.closeConnection()
	
	#usernamelikepassword
	args['run'] = True
	runUsernameLikePassword(args)
		
def main():
	#Parse Args
	parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)
	#1- Parent parsers
	parser.add_argument('--version', action='version', version=CURRENT_VERSION)
	#1.0- Parent parser: optional
	PPoptional = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPoptional._optionals.title = "optional arguments"
	PPoptional.add_argument('-v', dest='verbose', action='count', default=0, help='enable verbosity (-vv for more)')
	PPoptional.add_argument('--sleep', dest='timeSleep', required=False, type=float, default=DEFAULT_TIME_SLEEP, help='time sleep between each test or request (default: %(default)s)')
	PPoptional.add_argument('--login-timeout', dest='loginTimeout', required=False, type=float, default=DEFAULT_LOGIN_TIMEOUT, help='login timeout (default: %(default)s)')
	PPoptional.add_argument('--charset', dest='charset', required=False, type=str, default=DEFAULT_CHARSET, help='character set with which to connect to the database (default: %(default)s)')
	PPoptional.add_argument('--accounts-file',dest='accounts-file',required=False,metavar="FILE",default=DEFAULT_ACCOUNT_FILE,help='file containing credentials to test (default: %(default)s)')
	PPoptional.add_argument('--usernames-file',dest='usernames-file',required=False,metavar="FILE",default=None,help='file containing usernames to test (default: %(default)s)')
	PPoptional.add_argument('--passwords-file',dest='passwords-file',required=False,metavar="FILE",default=None,help='file containing passwords to test (default: %(default)s)')
	#1.1- Parent parser: connection options
	PPconnection = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPconnection._optionals.title = "connection options"
	PPconnection.add_argument('-s', dest='host', required=False, help='host server')
	PPconnection.add_argument('-p', dest='port', required=False, default=DEFAULT_DATABASE_PORT, type=int, help='port (default: %(default)s)')
	PPconnection.add_argument('-U', dest='user', required=False, help='MS-SQL username')
	PPconnection.add_argument('-P', dest='password', required=False, default=None, help='MS-SQL password')
	PPconnection.add_argument('-d', dest='database', required=False, type=str, default=DEFAULT_DATABASE_NAME, help='MS-SQL database (default: %(default)s)')
	PPconnection.add_argument('-D', dest='domain', required=False, type=str, default=None, help='Enable windows authentication and define the domain to use. Disable SQL server authentication')
	#1.2- Parent parser: output options
	PPoutput = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPoutput._optionals.title = "output configurations"
	PPoutput.add_argument('--no-color', dest='no-color', required=False, action='store_true', help='no color for output')
	#PPoutput.add_argument('--output-file',dest='outputFile',default=None,required=False,help='save results in this file')
	#1.3- Parent parser: Password Guesser
	PPpassguesser = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPpassguesser._optionals.title = "password guesser options"
	PPpassguesser.add_argument('--force-retry',dest='force-retry',action='store_true',help='allow to test multiple passwords for a user without ask you')
	PPpassguesser.add_argument('-l', dest='hostlist', required=False, help='filename which contains hosts (one ip on each line: "ip:port" or "ip" only)')
	PPpassguesser.add_argument('--search',dest='search',action='store_true',help='search valid credentials')
	#1.3- Parent parser: MssqlInfo
	PPmssqlinfo = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPmssqlinfo._optionals.title = "mssql info options"
	PPmssqlinfo.add_argument('--get-max-info',dest='get-max-info',required=False,action='store_true',default=False,help='get info about the remote database without authentication')
	#1.4- Parent parser: PasswordStealer
	PPpassstealer = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPpassstealer._optionals.title = "password stealer options"
	PPpassstealer.add_argument('--dump',dest='dump',required=False,action='store_true',default=False,help='get hashed passsword')
	PPpassstealer.add_argument('--save-to-file',dest='save-to-file',metavar="FILE",required=False,help='file to save hashed passsword')
	PPpassstealer.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	#1.5- Parent parser: xpcmdshell
	PPxpcmdshell = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPxpcmdshell._optionals.title = "xpcmdshell options"
	PPxpcmdshell.add_argument('--shell',dest='shell',required=False, action='store_true',default=False,help='get a shell')
	PPxpcmdshell.add_argument('--enable-xpcmdshell',dest='enable-xpcmdshell',required=False, action='store_true',help='enable xpcmdshell')
	PPxpcmdshell.add_argument('--disable-xpcmdshell',dest='disable-xpcmdshell',required=False, action='store_true',help='disable xpcmdshell')
	PPxpcmdshell.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	#1.6- Parent parser: jobs
	PPjobs = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPjobs._optionals.title = "jobs options"
	PPjobs.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	PPjobs.add_argument('--exec',dest='exec',required=False, type=str, help='execute this system command (no stdout/stderr output)')
	PPjobs.add_argument('--reverse-shell',dest='reverse-shell', required=False, nargs=2, metavar=('ip','port'), help='get a reverse interactive shell (with powershell)')
	PPjobs.add_argument('--type',dest='type',required=False, type=str, default='CMDEXEC', choices=['CMDEXEC', 'POWERSHELL'], help='execution type (default: %(default)s)')
	PPjobs.add_argument('--sp-name',dest='sp-name',required=False, type=str, default=DEFAULT_SP_NAME, help='set the stored proc name (default: %(default)s)')
	PPjobs.add_argument('--sleep-status',dest='sleep-status',required=False, type=int, default=SLEEP_TIME_BEFORE_TO_GET_STATUS, help='set the sleep time before to get the job status (default: %(default)s)')
	#1.7- Parent parser: SMBAuthenticationCapture
	PPSMBAuthenticationCapture = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPSMBAuthenticationCapture._optionals.title = "SMB Authentication Capture options"
	PPSMBAuthenticationCapture.add_argument('--share-name',dest='share-name',default=DEFAULT_SHARE_NAME,required=False,nargs=1,metavar=('share'),help='define the share name (default: %(default)s)')
	PPSMBAuthenticationCapture.add_argument('--capture',dest='capture',default=None,required=False,nargs=1,metavar=('ip'),help='capture SMB authentication with xp_dirtree or xp_fileexist or xp_getfiledetails')
	PPSMBAuthenticationCapture.add_argument('--xp-dirtree-capture',dest='xp-dirtree-capture',default=None,required=False,nargs=1,metavar=('ip'), help='capture SMB authentication with xp_dirtree')
	PPSMBAuthenticationCapture.add_argument('--xp-fileexist-capture',dest='xp-fileexist-capture',default=None,required=False,nargs=1,metavar=('ip'), help='capture SMB authentication with xp_fileexist')
	PPSMBAuthenticationCapture.add_argument('--xp-getfiledetails-capture',dest='xp-getfiledetails-capture',default=None,required=False,nargs=1,metavar=('ip'), help='capture SMB authentication with xp_getfiledetails (MSSQL 2000)')
	PPSMBAuthenticationCapture.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	#1.8- Parent parser: OleAutomation
	PPoleautomation = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPoleautomation._optionals.title = "ole automation options"
	PPoleautomation.add_argument('--read-file',dest='read-file',default=None,required=False,nargs=1,metavar=('filename'),help='read a file')
	PPoleautomation.add_argument('--write-file',dest='write-file',default=None,required=False,nargs=2,metavar=('filename','datatowrite'),help='write a file')
	PPoleautomation.add_argument('--get-file',dest='get-file',default=None,required=False,nargs=2,metavar=('remotefilename','localfilename'),help='get a file')
	PPoleautomation.add_argument('--put-file',dest='put-file',default=None,required=False,nargs=2,metavar=('localfilename','remotefilename'),help='put a file')
	PPoleautomation.add_argument('--exec-sys-cmd',dest='exec-sys-cmd',default=None,required=False,nargs=1,metavar=('syscmd'),help='execute a system command')
	PPoleautomation.add_argument('--enable-ole-automation',dest='enable-ole-automation',required=False, action='store_true',help='enable OLE Automation')
	PPoleautomation.add_argument('--disable-ole-automation',dest='disable-ole-automation',required=False, action='store_true',help='disable OLE Automation')
	PPoleautomation.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	#1.9- Parent parser: Bulkopen
	PPbulkopen = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPbulkopen._optionals.title = "bulkopen options"
	PPbulkopen.add_argument('--read-file',dest='read-file',default=None,required=False,nargs=1,metavar=('filename'),help='read a file')
	PPbulkopen.add_argument('--get-file',dest='get-file',default=None,required=False,nargs=2,metavar=('remotefilename','localfilename'),help='get a file')
	PPbulkopen.add_argument('--method',dest='method',default=None,required=False,choices=[BULKOPEN_METHOD_IN_BULKOPEN,OPENROWSET_METHOD_IN_BULKOPEN],help='method to use to read files')
	PPbulkopen.add_argument('--enable-ad-hoc-distributed-queries',dest='enable-ad-hoc-distributed-queries',required=False, action='store_true',help='enable ad hoc distributed queries')
	PPbulkopen.add_argument('--disable-ad-hoc-distributed-queries',dest='disable-ad-hoc-distributed-queries',required=False, action='store_true',help='disable ad hoc distributed queries')
	PPbulkopen.add_argument('--search-credentials',dest='search-credentials',default=None,required=False,nargs=3,metavar=('ip','port','database'),help='dictionary attack on a remote database from the targeted database')
	PPbulkopen.add_argument('--request-rdb',dest='request-rdb',default=None,required=False,nargs=6,metavar=('ip','port','database','login','password','request'),help='request a remote database from the target')
	PPbulkopen.add_argument('--scan-ports',dest='scan-ports',default=None,required=False,nargs=2,metavar=('ip','ports'),help='scan tcp ports of a remote engine')
	PPbulkopen.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	#1.10- Parent parser: XpDirectory
	PPxpdirectory = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPxpdirectory._optionals.title = "xpdirectory  options"
	PPxpdirectory.add_argument('--list-files',dest='list-files',default=None,required=False,nargs=1,metavar=('path'),help='list files')
	PPxpdirectory.add_argument('--list-dir',dest='list-dir',default=None,required=False,nargs=1,metavar=('path'),help='list directories')
	PPxpdirectory.add_argument('--list-fixed-drives',dest='list-fixed-drives',required=False, action='store_true',help='list all drives with xp_fixeddrives')
	PPxpdirectory.add_argument('--list-available-media',dest='list-available-media',required=False, action='store_true',help='list all drives with xp_availablemedia')
	PPxpdirectory.add_argument('--file-exists',dest='file-exists',default=None,required=False,nargs=1,metavar=('filename'),help='know if a file exists')
	PPxpdirectory.add_argument('--create-dir',dest='create-dir',default=None,required=False,nargs=1,metavar=('filename'),help='create a directory')
	PPxpdirectory.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	#1.11- Parent parser: TrustworthyPE
	PPtrustworthype = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPtrustworthype._optionals.title = "trustworthyPE  options"
	PPtrustworthype.add_argument('--be-sysadmin',dest='be-sysadmin',required=False, action='store_true',help='become sysadmin')
	PPtrustworthype.add_argument('--drop-sysadmin',dest='drop-sysadmin',required=False, action='store_true',help='drop sysadmin to user given')
	PPtrustworthype.add_argument('--is-sysadmin',dest='is-sysadmin',required=False, action='store_true',help='know if current user is sysadmin')
	PPtrustworthype.add_argument('--sp-name',dest='sp-name',required=False, type=str, default=DEFAULT_SP_NAME, help='set the stored proc name (default: %(default)s)')
	PPtrustworthype.add_argument('--test-module',dest='test-module',required=False, action='store_true',help='check features usable in this module')
	#1.12- Parent parser: usernamelikepassword
	PPusernamelikepassword = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPusernamelikepassword._optionals.title = "usernamelikepassword commands"
	PPusernamelikepassword.add_argument('--run',dest='run',action='store_true',required=True,help='try to connect using each MSSQL username like the password')
	PPusernamelikepassword.add_argument('--force-retry',dest='force-retry',action='store_true',help='allow to test multiple passwords for a user without ask you')
	#1.13- Parent parser: Search
	PPsearch = argparse.ArgumentParser(add_help=False,formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=MAX_HELP_POSITION))
	PPsearch._optionals.title = "search commands"
	PPsearch.add_argument('--column-names',dest='column-names',default=None,required=False,metavar='sqlPattern',help='search a pattern in all collumns')
	PPsearch.add_argument('--pwd-column-names',dest='pwd-column-names',default=None,action='store_true',help='search password patterns in all collumns')
	PPsearch.add_argument('--no-show-empty-columns',dest='no-show-empty-columns',action='store_true',help="don't show columns if columns are empty")
	PPsearch.add_argument('--test-module',dest='test-module',action='store_true',help='test the module before use it')
	#2- main commands
	subparsers = parser.add_subparsers(help='\nChoose a main command')
	#2.a- Run all modules
	parser_all = subparsers.add_parser('all',parents=[PPoptional,PPconnection,PPoutput,PPpassguesser],help='to run all modules in order to know what it is possible to do')	
	parser_all.set_defaults(func=runAllModulesOnEachHost,auditType='all')
	#2.b- Run mssqlInfo modules
	parser_all = subparsers.add_parser('mssqlinfo',parents=[PPoptional,PPconnection,PPoutput,PPmssqlinfo],help='to get information without authentication')	
	parser_all.set_defaults(func=runMssqlInfoModule,auditType='mssqlinfo')
	#2.c- PasswordGuesser
	parser_passwordGuesser = subparsers.add_parser('passwordguesser',parents=[PPoptional,PPconnection,PPpassguesser,PPoutput],help='to know valid credentials')
	parser_passwordGuesser.set_defaults(func=runPasswordGuesserModule,auditType='passwordGuesser')
	#2.d- PasswordStealer
	parser_passwordStealer = subparsers.add_parser('passwordstealer',parents=[PPoptional,PPconnection,PPpassstealer,PPoutput],help='to get hashed passowrds')
	parser_passwordStealer.set_defaults(func=runPasswordStealerModule,auditType='passwordStealer')
	#2.e- Xpcmdshell
	parser_xpcmdshell = subparsers.add_parser('xpcmdshell',parents=[PPoptional,PPconnection,PPxpcmdshell,PPoutput],help='to get a shell')
	parser_xpcmdshell.set_defaults(func=runXpCmdShellModule, auditType='xpcmdshell')
	#2.f- Jobs
	parser_jobs = subparsers.add_parser('jobs',parents=[PPoptional,PPconnection,PPjobs,PPoutput],help='to execute system commands')
	parser_jobs.set_defaults(func=runJobsModule, auditType='jobs')
	#2.g- SMBAuthenticationCapture
	parser_xpcmdshell = subparsers.add_parser('smbauthcapture',parents=[PPoptional,PPconnection,PPSMBAuthenticationCapture,PPoutput],help='to capture a SMB authentication')
	parser_xpcmdshell.set_defaults(func=runSMBAuthenticationCaptureModule, auditType='smbauthenticationcapture')
	#2.h- OLEAutomation
	parser_xpcmdshell = subparsers.add_parser('oleautomation',parents=[PPoptional,PPconnection,PPoleautomation,PPoutput],help='to read/write file and execute system commands')
	parser_xpcmdshell.set_defaults(func=runOleAutomationModule, auditType='oleautomation')
	#2.i- Bulkopen
	parser_bulkopen = subparsers.add_parser('bulkopen',parents=[PPoptional,PPconnection,PPbulkopen,PPoutput],help='to read a file and scan ports')
	parser_bulkopen.set_defaults(func=runBulkOpenModule, auditType='bulkopen')
	#2.j- XpDirectory
	parser_xpdirectory = subparsers.add_parser('xpdirectory',parents=[PPoptional,PPconnection,PPxpdirectory,PPoutput],help='to list files/drives and to create directories')
	parser_xpdirectory.set_defaults(func=runXpDirectoryModule, auditType='xpdirectory')
	#2.k- TrustworthyPE
	parser_trustworthype = subparsers.add_parser('trustworthype',parents=[PPoptional,PPconnection,PPtrustworthype,PPoutput],help='to become sysadmin with the trustwothy database method')
	parser_trustworthype.set_defaults(func=runTrustworthyPEModule, auditType='trustworthype')
	#2.l- username like password
	parser_usernamelikepassword = subparsers.add_parser('userlikepwd',parents=[PPoptional,PPconnection,PPusernamelikepassword,PPoutput], help='to try each MSSQL username stored in the DB like the corresponding pwd')
	parser_usernamelikepassword.set_defaults(func=runUsernameLikePassword,auditType='usernamelikepassword')
	#2.m- Search
	parser_search = subparsers.add_parser('search',parents=[PPoptional,PPconnection,PPsearch,PPoutput],help='to search in column names')
	parser_search.set_defaults(func=runSearchModule, auditType='search')
	#2.n- clean
	parser_cleaner = subparsers.add_parser('cleaner',parents=[PPoptional,PPoutput], help='clean local traces')
	parser_cleaner.set_defaults(func=runCleaner,auditType='cleaner')
	#3- parse the args
	if ARGCOMPLETE_AVAILABLE == True : argcomplete.autocomplete(parser)
	args = dict(parser.parse_args()._get_kwargs())
	arguments = parser.parse_args()
	#4- Configure logging and output
	configureLogging(args)
	args['print'] = Output(args)
	#Start the good function
	#if args['auditType']!='clean' and ipHasBeenGiven(args) == False : return EXIT_MISS_ARGUMENT
	arguments.func(args)
	exit(ALL_IS_OK)


if __name__ == "__main__":
	main()
		
