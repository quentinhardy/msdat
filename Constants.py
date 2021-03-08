# -*- coding: utf-8 -*-
import string

DESCRIPTION = ""\
'''

               _   _  __  __   _  ___ 
              | \_/ |/ _||  \ / \|_ _|
              | \_/ |\_ \| o ) o || | 
              |_| |_||__/|__/|_n_||_| 
                        
------------------------------------------------------
 _   _  __            __           _           ___ 
| \_/ |/ _|         |  \         / \         |_ _|
| \_/ |\_ \         | o )         o |         | | 
|_| |_||__/icrosoft |__/atabase |_n_|ttacking |_|ool 
                        
-------------------------------------------------------

By Quentin Hardy (quentin.hardy@protonmail.com or quentin.hardy@bt.com)
'''
CURRENT_VERSION = "Version 2.1 - 2020/03/08"
DEFAULT_TIME_SLEEP = 0
DEFAULT_LOGIN_TIMEOUT = 5
DEFAULT_CHARSET = 'UTF-8'
DEFAULT_SID_MAX_SIZE = 2
MAX_HELP_POSITION=60
DEFAULT_ACCOUNT_FILE = "accounts.txt"
DEFAULT_DATABASE_NAME = "master"
SCAN_PORT_NUMBER_THREAD = 1
DEFAULT_DATABASE_PORT = 1433
EXIT_MISS_ARGUMENT = 104
ALL_IS_OK=0
TIMEOUT_VALUE = 5
PASSWORD_FOLDER = "temp"
PASSWORD_EXTENSION_FILE = ".msdat.save"
SHOW_SQL_REQUESTS_IN_VERBOSE_MODE = False
DEFAULT_SYS_CMD = "whoami" #Default windows command used to test if we can execute system commands (in xpcmdshell)
DEFAULT_SHARE_NAME = "SHARE" #Default share name for the SMB authentication capture
DEFAULT_FILENAME = "test.txt"  #Use to read or write files
DEFAULT_SYS_CMD_OLE = "cmd.exe /c dir" #Default windows command used to test if we can execute system commands (in OLEautomation)
ERROR_PROCEDURE_BLOCKED = "SQL Server blocked access to"
BULKOPEN_METHOD_IN_BULKOPEN = 'bulkinsert'
OPENROWSET_METHOD_IN_BULKOPEN = 'openrowset'
DEFAULT_FOLDER = 'C:\\' #Used in XpDirectory
DEFAULT_SQL_REQUEST = "select @@ServerName" #Used for remote connection from database
MAX_RETRY_CONNECTION_SCANPORTS = 6
#Trustworthy PE module
DEFAULT_SP_NAME = "IMDATELOHJOSUUSOOJAHMSAT"
#JOB
SLEEP_TIME_BEFORE_TO_GET_STATUS = 2 #seconds
#PasswordStealer
NB_SERVER_USER_ID_MAX = 400
#SEARCH module
PATTERNS_COLUMNS_WITH_PWDS = [
	'%motdepasse%',
	'%motdepasses%',
	'%mot_de_passe%',
	'%mot_de_passes%',
	'%mdp%',
	'%mdps%',
	'%pwd%',
	'%pwds%',
	'%passswd%',
	'%passswds%',
	"%password%",
	"%passwords%",
	"%contraseña%",
	"%contraseñas%",
	"%clave%",
	"%claves%",
	"%chiave%",
	"%пароль%",
	"%wachtwoord%",
	"%Passwort%",
	"%hasło%",
	"%senha%",
	]

