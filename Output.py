#!/usr/bin/python
# -*- coding: utf-8 -*-

#PYTHON_TERMCOLOR_OK
from __future__ import print_function
try:
	from termcolor import colored
	TERMCOLOR_AVAILABLE = True
except ImportError:
	TERMCOLOR_AVAILABLE = False

class Output ():
	'''
	All output except log used this object
	'''
	def __init__(self, args):
		'''
		CONSTRUCTOR
		'''
		self.args = args
		self.noColor = args['no-color']
		self.titlePos = 0
		self.subTitlePos = 0

	def title (self, m):
		'''
		print a title
		'''
		self.titlePos += 1
		self.subTitlePos = 0
		formatMesg = '\n\n[{0}] {1}: {2}'.format(self.titlePos,'({0}:{1})'.format(self.args['host'],self.args['port']),m)
		if self.noColor == True or TERMCOLOR_AVAILABLE == False: print(formatMesg)
		else : print(colored(formatMesg, 'white',attrs=['bold']))

	def subtitle (self, m):
		'''
		print a subtitle
		'''
		self.subTitlePos += 1
		formatMesg = '[{0}.{1}] {2}'.format(self.titlePos, self.subTitlePos, m)
		if self.noColor == True  or TERMCOLOR_AVAILABLE == False: print(formatMesg)
		else : print(colored(formatMesg, 'white',attrs=['bold'])) 

	def badNews (self, m):
		'''
		print a stop message
		'''
		formatMesg = '[-] {0}'.format(m)
		if self.noColor == True  or TERMCOLOR_AVAILABLE == False: print(formatMesg)
		else : print(colored(formatMesg, 'red',attrs=['bold'])) 

	def goodNews(self,m):
		'''
		print good news
		'''
		formatMesg = '[+] {0}'.format(m)
		if self.noColor == True  or TERMCOLOR_AVAILABLE == False: print(formatMesg)
		else : print(colored(formatMesg, 'green',attrs=['bold'])) 

	def unknownNews(self,m):
		'''
		print unknow news
		'''
		formatMesg = '[+] {0}'.format(m)
		if self.noColor == True  or TERMCOLOR_AVAILABLE == False: print(formatMesg)
		else : print(colored(formatMesg, 'yellow',attrs=['bold'])) 

	def printOSCmdOutput(self,m):
		'''
		print the output of a OS command
		'''
		print(m)
