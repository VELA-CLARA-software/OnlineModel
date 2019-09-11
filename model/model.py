from paramiko import *
import os
import sys
from copy import deepcopy
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'data'))
from data import data


class Model(object):

	def __init__(self):

		self.my_name = 'model'
		self.username = ''
		self.password = ''
		self.hostname = 'apclara1.dl.ac.uk'
		self.port = 22
		self.pathscript = '/opt/ControlRoomApps/OnlineModel/'
		self.path_exists = False
		self.data = data.Data()
		self.client = SSHClient()

	def ssh_to_server(self):
		try:
			self.client.set_missing_host_key_policy(AutoAddPolicy())
			self.client.connect(self.hostname, username=self.username, password=self.password)

		except AuthenticationException:
			print('Wrong username or password')
			return

	def create_subdirectory(self):
		path = self.data.data_values['directory_line_edit']
		if not path.endswith('/'):
			path = path + '/'
		self.check_if_directory_exists()
		#sftp = self.client.open_sftp()
		#sftp.chdir(path)
		#for files in sftp.listdir():
		#    if files == 'run'+str(astra_run_number):
		#        self.path_exists = True
		 #       break
		 #       return
		#    else:
		#        continue
		#sftp.close()
		if self.path_exists:
			return
		else:
			print('Top level directory to be created at {}'.format(path))
			command = ' mkdir ' + path
			self.client.exec_command(command)
			return

	def check_if_directory_exists(self):
		sftp = self.client.open_sftp()
		for files in sftp.listdir():
			if files == self.data.data_values['directory_line_edit']:
				sftp.chdir(self.data.data_values['directory_line_edit'])
				break
			else:
				continue

		for files in sftp.listdir():
			if files == 'run'+str(self.data.data_values['astra_run_number_line_edit']):
				self.path_exists = True
				break
				return
			else:
				continue

		self.path_exists = False
		sftp.close()
		return

	def close_connection(self):
		return self.client.close()

	def run_script(self):
		print('+++++++++++++++++ Start the script ++++++++++++++++++++++')
		#path_command = 'export PATH=$PATH:/opt/ASTRA:' + self.pathscript
		#self.client.exec_command(path_command)
		path_command = 'cd ' + self.data.data_values['directory_line_edit'] + '; '
		path_command = path_command + self.pathscript+'script/./run_2BA1 '
		try:
			current_scan_value = float(self.data.scan_values['from'])
			scan_end = float(self.data.scan_values['to'])
			scan_step_size = float(self.data.scan_values['step'])
		except ValueError:
			print "Enter a numerical value to conduct a scan"
		while current_scan_value <= scan_end:
			for key, value in self.data.data_values.iteritems():
				if str(key).replace('_line_edit','') == self.data.scan_values['parameter']:
					path_command = path_command + str(current_scan_value) + ' '
					current_scan_value += scan_step_size
				else:
					path_command = path_command + str(value) + ' '	
			print 'Running with command: ' + path_command
			path_command = '' + self.pathscript+'script/./run_2BA1 '
		#stdin, stdout, stderr = self.client.exec_command(path_command)
		#print(stderr.readlines())
		return
