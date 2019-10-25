from paramiko import *
import os
import sys
import stat
from copy import deepcopy
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

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
        if not self.data.data_values['directory_line_edit'].endswith('/'):
            self.data.data_values['directory_line_edit'] = self.data.data_values['directory_line_edit'] + '/'
        self.check_if_directory_exists()

    def check_if_directory_exists(self):
        sftp = self.client.open_sftp()
        for files in sftp.listdir():
            if files == self.data.data_values['directory_line_edit']:
                for runfiles in sftp.listdir(files):
                    if runfiles == 'run' + str(self.data.data_values['astra_run_number_line_edit']):
                        self.path_exists = True
                        print('Top level directory {} with Run  {} already exists'.format(
                            self.data.data_values['directory_line_edit'],
                            str(self.data.data_values['astra_run_number_line_edit'])))
                        return
                    else:
                        continue
        self.path_exists = False
        sftp.close()
        print('Top level directory to be created at {}'.format(self.data.data_values['directory_line_edit']))
        self.client.exec_command('mkdir ' + self.data.data_values['directory_line_edit'])
        return

    def get_runs_directories(self, remote_path):
        sftp = self.client.open_sftp()
        list_runs = []
        for files, file_attr in zip(sftp.listdir(remote_path), sftp.listdir_attr(remote_path)):
            if stat.S_IFDIR(file_attr.st_mode) and files.startswith('run') and files.find('_') != -1:
                list_runs.append(files)
            else:
                continue
        sftp.close()
        return list_runs

    def close_connection(self):
        return self.client.close()

    def run_script(self):
        print('+++++++++++++++++ Start the script ++++++++++++++++++++++')

        if self.data.scan_parameter['parameter_scan_check_box']:
            try:
                current_scan_value = float(self.data.scan_values['from'])
                scan_end = float(self.data.scan_values['to'])
                scan_step_size = float(self.data.scan_values['step'])
            except ValueError:
                print "Enter a numerical value to conduct a scan"
            while current_scan_value <= scan_end:
                # path_command = 'cd ' + self.data.data_values['directory_line_edit'] + '; '
                # path_command = path_command + self.pathscript + 'script/./run_2BA1 '
                for key, value in self.data.data_values.iteritems():

                    par = self.data.scan_values['parameter'] + '_line_edit'

                    if key == par:
                        self.data.data_values[key] = current_scan_value
                        # path_command += str(current_scan_value) + ' '
                        current_scan_value += scan_step_size
                    else:
                        continue

                        # path_command = path_command + str(value) + ' '
                path_command = self.path_command_ensemble('script/run_2BA1 ', self.data.data_values)
                self.path_run_command(path_command, self.data.data_values['directory_line_edit'])
                # print 'Running with command: ' + path_command
                # path_command = self.path_command_ensemble()
                # stdin, stdout, stderr = self.client.exec_command(path_command)
                # print(stderr.readlines())
                if int(self.data.data_values['astra_run_number_line_edit']) < 100:
                    self.data.data_values['astra_run_number_line_edit'] = '00' + str(
                        int(self.data.data_values['astra_run_number_line_edit']) + 1)
                else:
                    self.data.data_values['astra_run_number_line_edit'] = str(
                        int(self.data.data_values['astra_run_number_line_edit']) + 1)

                # print 'Running with command: ' + path_command
                # path_command = '' + self.pathscript+'script/./run_2BA1 '
        else:
            path_command = self.path_command_ensemble('script/run_2BA1 ', self.data.data_values)
            # path_command = 'cd ' + self.data.data_values['directory_line_edit'] + '; '
            # path_command = path_command + self.pathscript + 'script/./run_2BA1 '
            # for key, value in self.data.data_values.iteritems():
            #     path_command = path_command + str(value) + ' '
            self.path_run_command(path_command, self.data.data_values['directory_line_edit'])
        # return

    def path_command_ensemble(self, script, dictionary):
        path_command = self.pathscript + script
        for key, value in dictionary.iteritems():
            path_command = path_command + str(value) + ' '
        return path_command

    def path_run_command(self, command, initial_path):
        path_command_exp = 'cd ' + initial_path + '; '
        path_command_exp += command
        print('Running with command {}'.format(path_command_exp))
        stdin, stdout, stderr = self.client.exec_command(path_command_exp)
        print(stderr.readlines())

    # def path_run_command_post(self, command, initial_path):
    #     path_command_exp = 'cd ' + self.data.data_values_post['directory_post_line_edit'] + '; '
    #     path_command_exp += command
    #     print('Running with command {}'.format(path_command_exp))
    #     stdin, stdout, stderr = self.client.exec_command(path_command_exp)
    #     print(stderr.readlines())

    def run_script_post(self): #To be implemented
        dictionary = deepcopy(self.data.data_values_post)
        del(dictionary['directory_post_combo_box_3'])
        del(dictionary['directory_post_combo_box_4'])
        del (dictionary['directory_post_line_edit'])
        path_command = self.path_command_ensemble('script/post_pro  ', dictionary)
        try:
            self.path_run_command(path_command, self.data.data_values_post['directory_post_line_edit'])
        except OSError:
            print('Post-processing script failed')


    def retrieve_plots(self): #To be implemented
        """migrate from jupyter-notebook, load pictures method of the class"""
        pass


