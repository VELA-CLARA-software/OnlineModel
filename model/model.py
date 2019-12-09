from paramiko import *
import os
import sys
import stat
import numpy as np
from copy import deepcopy

sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'data'))
from data import data


class Model(object):
    output_directory = 'C:/Users/ujo48515/Documents/'
    width = 1000
    height = 600
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
        self.generator_params = ['number_of_particles', 'dist_x', 'dist_y', 'dist_z', 'sig_x', 'sig_y', 'sig_z']

    def ssh_to_server(self):
        try:
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            self.client.connect(self.hostname, username=self.username, password=self.password)

        except AuthenticationException:
            print('Wrong username or password')
            return

    def create_subdirectory(self):
        self.data.runParameterDict['directory_line_edit'] = self.data.runParameterDict['directory_line_edit'] + '/' if not self.data.runParameterDict['directory_line_edit'].endswith('/') else self.data.runParameterDict['directory_line_edit']
        self.check_if_directory_exists()

    def check_if_directory_exists(self):
        sftp = self.client.open_sftp()
        for files in sftp.listdir():
            if files == self.data.runParameterDict['directory_line_edit']:
                for runfiles in sftp.listdir(files):
                    if runfiles == 'run' + str(self.data.runParameterDict['astra_run_number_line_edit']):
                        self.path_exists = True
                        print('Top level directory {} with Run  {} already exists'.format(
                            self.data.runParameterDict['directory_line_edit'],
                            str(self.data.runParameterDict['astra_run_number_line_edit'])))
                        return
                    else:
                        continue
        self.path_exists = False
        sftp.close()
        print('Top level directory to be created at {}'.format(self.data.runParameterDict['directory_line_edit']))
        self.client.exec_command('mkdir ' + self.data.runParameterDict['directory_line_edit'])
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
        if self.data.scanDict['parameter_scan']:
            try:
                current_scan_value = float(self.data.scanDict['parameter_scan_from_value'])
                scan_end = float(self.data.scanDict['parameter_scan_to_value'])
                scan_step_size = float(self.data.scanDict['parameter_scan_step_size'])
            except ValueError:
                print("Enter a numerical value to conduct a scan")
            while current_scan_value <= scan_end:
                # path_command = 'cd ' + self.data.data_values['directory_line_edit'] + '; '
                # path_command = path_command + self.pathscript + 'script/./run_2BA1 '
                for key, value in self.data.latticeDict.items():
                    par = self.data.scanDict['parameter']# + '_line_edit'
                    if key == par:
                        if self.strip_text_before(key, ':') in self.generator_params:
                            self.modify_framework(scan=True, type=self.strip_text_before(key, ':'),
                                                  modify=current_scan_value,
                                                  generator_param=self.strip_text_after(key, ':'))
                        elif not self.strip_text_before(key, ':') in self.generator_params:
                            if self.data.runParameterDict[self.strip_text_before(key, ':')]['type'] == 'cavity':
                                self.modify_framework(scan=True, type=self.strip_text_before(key, ':'),
                                                      modify=current_scan_value,
                                                      cavity_params=self.strip_text_after(key, ':'))
                            else:
                                self.modify_framework(scan=True, type=self.strip_text_before(key, ':'),
                                                      modify=current_scan_value)
                        # path_command += str(current_scan_value) + ' '
                        subdir = par + '-' + str(current_scan_value)
                        current_scan_value += scan_step_size
                        self.data.Framework.setSubDirectory(subdir)
                        self.data.Framework.track(startfile='generator', endfile='S02')
                    else:
                        continue

                        # path_command = path_command + str(value) + ' '
                #path_command = self.path_command_ensemble('script/run_2BA1 ', self.data.data_values)
                #self.path_run_command(path_command, self.data.data_values['directory_line_edit'])
                # print 'Running with command: ' + path_command
                # path_command = self.path_command_ensemble()
                # stdin, stdout, stderr = self.client.exec_command(path_command)
                # print(stderr.readlines())
                '''
                  ASTRA RUN NUMBER NO LONGER INCLUDED, NEEDS TO BE ADDED IMPLICITLY HERE
                '''
                #if int(self.data.data_values['astra_run_number_line_edit']) < 100:
                #    self.data.data_values['astra_run_number_line_edit'] = '00' + str(
                #        int(self.data.data_values['astra_run_number_line_edit']) + 1)
                #else:
                #    self.data.data_values['astra_run_number_line_edit'] = str(
                #        int(self.data.data_values['astra_run_number_line_edit']) + 1)

                # print 'Running with command: ' + path_command
                # path_command = '' + self.pathscript+'script/./run_2BA1 '
        else:
            self.modify_framework(scan=False)
        self.data.Framework.setSubDirectory(self.data.parameterDict['simulation']['directory'])
        self.data.Framework.track(startfile="generator", endfile='BA1_dipole')

    ##### Find Starting Filename based on z-position ####
    def find_starting_lattice(self, z):
        lattices = self.data.Framework.latticeObjects.values()
        for l in lattices:
            for e in l.elements:
                    if e.position_end[2] <= z:
                        return l
        return 'generator'

    def modify_framework(self, scan=False, type=None, modify=None, cavity_params=None, generator_param=None):
        for key, value in self.data.latticeDict.items():
            if self.data.latticeDict[key]['type'] == 'quadrupole':
                self.data.Framework.modifyElement(key, 'k1l', value['k1l'])
            elif self.data.latticeDict[key]['type'] == 'cavity':
                self.data.Framework.modifyElement(key, 'field_amplitude', 1e6*value['field_amplitude'])
                self.data.Framework.modifyElement(key, 'phase', value['phase'])
            elif self.data.latticeDict[key]['type'] == 'solenoid':
                tempcav = self.data.latticeDict[key]['cavity']
                # print(self.data.runParameterDict[tempcav]['sub_elements'][key])
                self.data.Framework.modifyElement(key, 'field_amplitude', value['field_amplitude'])
            # elif self.data.runParameterDict[self.strip_text_before(key, ':')]['type'] == 'generator':
            #     self.data.Framework.modifyElement(key,key,value)
        self.data.Framework.generator.number_of_particles = int(self.data.generatorDict['number_of_particles']['value'])
        self.data.Framework.generator.charge = 1e-9*float(self.data.generatorDict['charge']['value'])
        print(float(self.data.generatorDict['sig_clock']['value']))
        print(float(self.data.generatorDict['sig_clock']['value']) / (2354.82))
        self.data.Framework.generator.sig_clock = float(self.data.generatorDict['sig_clock']['value']) / (2354.82)
        # self.data.Framework.generator.dist_x = self.data.generatorDict['dist_x']['value']
        # self.data.Framework.generator.dist_y = self.data.generatorDict['dist_y']['value']
        # self.data.Framework.generator.dist_z = self.data.generatorDict['dist_z']['value']
        self.data.Framework.generator.sig_x = self.data.generatorDict['spot_size']
        self.data.Framework.generator.sig_y = self.data.generatorDict['spot_size']
        # self.data.Framework.generator.sig_z = self.data.runParameterDict['sig_z']['value']
        if scan==True and type is not None:
            for key, value in self.data.latticeDict.items():
                if type == 'quadrupole':
                    self.data.Framework.modifyElement(key, 'k1l', modify)
                elif type == 'cavity':
                    if cavity_params == "AMP":
                        self.data.Framework.modifyElement(key, 1e6*'field_amplitude', modify)
                    elif cavity_params == "PHASE":
                        self.data.Framework.modifyElement(key, 'phase', modify)
                elif type == 'solenoid':
                    tempcav = self.data.latticeDict[key]['cavity']
                    # print(self.data.runParameterDict[tempcav]['sub_elements'][key])
                    self.data.Framework.modifyElement(key, 'field_amplitude', modify)
                # elif self.data.runParameterDict[self.strip_text_before(key, ':')]['type'] == 'generator':
                #     self.data.Framework.modifyElement(key,key,value)
        elif scan==True and generator_param in self.generator_params:
            if generator_param == 'number_of_particles':
                self.data.Framework.generator.number_of_particles = modify
            elif generator_param == 'dist_x':
                self.data.Framework.generator.dist_x = modify
            elif generator_param == 'dist_y':
                self.data.Framework.generator.dist_y = modify
            elif generator_param == 'dist_z':
                self.data.Framework.generator.dist_z = modify
            elif generator_param == 'sig_x':
                self.data.Framework.generator.sig_x = modify
            elif generator_param == 'sig_y':
                self.data.Framework.generator.sig_y = modify
            elif generator_param == 'sig_z':
                self.data.Framework.generator.sig_z = modify

    def strip_text_before(self, string, condition):
        sep = condition
        rest = string.split(sep, 1)[0]
        return rest

    def strip_text_after(self, string, condition):
        sep = condition
        rest = string.split(sep, 1)[1]
        return rest

    def path_command_ensemble(self, script, dictionary):
        path_command = self.pathscript + script
        for key, value in dictionary.iteritems():
            if key != 'directory_line_edit':
                path_command = path_command + str(value) + ' '
            else:
                continue
        return path_command

    def path_run_command(self, command, initial_path):
        path_command_exp = 'cd ' + str(initial_path) + ' && '
        path_command_exp += str(command) + ';'
        print('Running with command {}'.format(path_command_exp))
        stdin, stdout, stderr = self.client.exec_command(path_command_exp)
        print(stderr.readlines())

    def run_script_post(self):
        dictionary = deepcopy(self.data.runParameterDict_post)
        del(dictionary['directory_post_combo_box_3'])
        del(dictionary['directory_post_combo_box_4'])
        del (dictionary['directory_post_line_edit'])
        path_command = 'cd ' + self.data.runParameterDict_post['directory_post_line_edit'] + ' ;'
        path_command += self.path_command_ensemble('script/post_pro  ', dictionary)
        try:
            self.path_run_command(path_command, self.data.runParameterDict_post['directory_post_line_edit'])
        except OSError:
            print('Post-processing script failed')

    def run_script_summary(self):
        list_runs = self.get_runs_directories(self.data.data_summary_plot_parameters['directory_summary_line_edit'])
        list_runs = sorted([int(l_runs.replace('run', '')) for l_runs in list_runs if l_runs.startswith('run') and l_runs.find('_') == -1])
        path_command = 'cp ' + self.pathscript + 'tails_script/* ' + str(remote_path)+';'
        path_command += './make_tails ' + str(np.amin(list_runs)) + ' ' + str(np.amax(list_runs)) + ';'
        path_command += 'cd tls_'+str(np.amin(list_runs)) + '_' + str(np.amax(list_runs)) + ';'
        path_command += './fit 0.1 0.1 0.3 15 20 0.1;'
        try:
            self.path_run_command(path_command, self.data.data_summary_plot_parameters['directory_summary_line_edit'])
        except OSError:
            print('Summary Plot Post-Processing script failed')

    def conversion_routine(self, file_to_import):
        sftp = self.client.open_sftp()
        directory = self.data.runParameterDict_post['directory_post_line_edit']
        run1 = self.data.runParameterDict_post['directory_post_combo_box']
        run2 = self.data.runParameterDict_post['directory_post_combo_box_2']
        sftp.chdir(directory + '/plots/run_' + str(run1) + '_' + str(run2) + '/eps/')
        path_sftp = sftp.getcwd()
        for fil in sftp.listdir():
            if str(fil).find(file_to_import) != -1:
                try:
                    sftp.stat(str(fil).replace('eps', 'png'))
                    print('file {} has already been converted to png'.format(path_sftp + '/' + str(fil)))
                except IOError:
                    if str(fil).endswith('2BA1.eps'):
                        command = self.convert_eps2png(str(fil))
                        self.path_run_command(command, path_sftp)
                        print('file {} has been converted to {}'.format(path_sftp + '/' + str(fil),
                                                                        path_sftp + '/' + str(fil).replace('.eps', '.png')))
                fil = str(fil).replace('eps', 'png')
                sftp.get(path_sftp + '/' + fil, self.output_directory + fil)
                return file_to_import
            else:
                continue
        sftp.close()

    def convert_eps2png(self, epsfile):
        path = deepcopy(epsfile)
        path = path.replace('.eps', '.png')
        return 'convert -density 600 ' + epsfile + ' -rotate 90 -resize ' + str(self.width) + \
               'x'+str(self.height) + ' ' + path
