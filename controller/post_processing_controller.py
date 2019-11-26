from PyQt4.QtCore import *
from PyQt4.QtGui import *
from copy import copy, deepcopy
import os
import shutil
import sys
import numpy as np


class GenericThread(QThread):
    signal = pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        QThread.__init__(self)
        self._stopped = False
        self.existent = 'existent file'
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def stop(self):
        self._stopped = True

    def run(self):
        self.signal.emit()
        if not self._stopped:
            self.object = self.function(*self.args, **self.kwargs)


class PostProcessingController(QObject):

    def __init__(self, app, view, model):
        super(PostProcessingController, self).__init__()
        self.my_name = 'PostProcessingController'
        self.app = app
        self.model = model
        self.view = view
        self.model.data.initialise_data()
        self.model.data.initialise_data_post()
        self.post_proc_run = False
        self.populate_plot_combo_box()

    # def run_thread(self, func):
    #    self.thread = GenericThread(func)
    #    self.thread.finished.connect(self.enable_run_postproc_button)

    def disable_run_postproc_button(self):
        self.view.runButton_post.setEnabled(False)
        return

    def enable_run_postproc_button(self):
        self.view.runButton_post.setEnabled(True)
        return

    def widgets_in_layout(self, layout):
        widget_list = []
        for children in layout.children():
            widget_list.append(children)
        return widget_list

    def populate_plot_combo_box(self):
        widget_list = self.widgets_in_layout(self.view.horizontalLayoutWidget)
        for widget in widget_list:
            if isinstance(widget, QComboBox) and str(widget.objectName()).endswith('box') or \
                    str(widget.objectName()).endswith('box_2'):
                parameters = [str(int(i)) for i in np.arange(101, 130)]
            elif isinstance(widget, QComboBox) and str(widget.objectName()).endswith('box_3') or \
                    str(widget.objectName()).endswith('box_4'):
                parameters = [keys for keys, values in self.model.data.data_plot_parameters.items()]
            else:
                continue
            for par in parameters:
                widget.addItem(par)

    def fill_in_run_combo_boxes(self, widget):
        parameters = self.model.get_runs_directories(self.model.data.data_values_post['directory_post_line_edit'])

        for par in parameters:
            widget.addItem(par)

    def check_if_directory_exists_post(self):
        run1 = self.model.data.data_values_post['directory_post_combo_box']
        run2 = self.model.data.data_values_post['directory_post_combo_box_2']
        sftp = self.model.client.open_sftp()

        try:
            sftp.stat(self.model.data.data_values_post['directory_post_line_edit'] + 'plots')
            sftp.chdir(self.model.data.data_values_post['directory_post_line_edit'] + 'plots')
            sftp.stat('run_' + str(run1) + '_' + str(run2))
            self.post_proc_run = True
        except Exception as e:
            self.post_proc_run = False

    def collect_post_proc_parameters(self):
        self.disable_run_postproc_button()
        self.collect_post_proc_directory()
        self.collect_plots_combo_boxes()
        return

    def collect_post_proc_directory(self):
        for widget in self.widgets_in_layout(self.view.formLayoutWidget_2):
            if isinstance(widget, QLineEdit) and str(widget.objectName()) == 'directory_post_line_edit':
                if str(widget.text()) == '':
                    self.model.data.data_values_post.update(
                        {str(widget.objectName()): self.model.data.data_values['directory_line_edit']})
                else:
                    text_box = str(widget.text())
                    if not text_box.endswith('/'):
                        text_box += '/'
                    self.model.data.data_values_post.update({str(widget.objectName()): text_box})
            else:
                continue

    def collect_plots_combo_boxes(self):
        """ To be implemented: Extension to update combo boxes from the server (runs existent in the directory) """
        for widget in self.widgets_in_layout(self.view.horizontalLayoutWidget):
            if isinstance(widget, QComboBox):
                if not (str(widget.objectName()).endswith('box_3') or str(widget.objectName()).endswith('box_4')):
                    self.model.data.data_values_post.update({str(widget.objectName()): str(widget.currentText())})
                else:
                    if str(widget.currentText()).rfind('(x)') != -1:
                        l_axis = '_x_'
                    elif str(widget.currentText()).rfind('(y)') != -1:
                        l_axis = '_y_'
                    elif str(widget.currentText()).rfind('(z)') != -1 and str(widget.currentText()).rfind('emit') != -1:
                        l_axis = '_z_'
                    else:
                        l_axis = '_'
                    file_name = self.model.data.data_plot_parameters[str(widget.currentText())]
                    file_name += '_' + self.model.data.data_values_post['directory_post_combo_box']
                    file_name += '_' + self.model.data.data_values_post['directory_post_combo_box_2'] + l_axis + '2BA1'
                    self.model.data.data_values_post.update({str(widget.objectName()): file_name})
            else:
                continue

    def retrieve_plots(self):
        self.disable_run_postproc_button()
        widget_list = self.widgets_in_layout(self.view.gridLayoutWidget)
        for view, scene, key in zip([self.view.graphics_post_graphics_view_2, self.view.graphics_post_graphics_view_1],
                                    [self.view.graphics_post_scene_2, self.view.graphics_post_scene_1],
                                    ['directory_post_combo_box_3', 'directory_post_combo_box_4']):
            file_to_import = self.model.data.data_values_post[key]
            img_gui = self.model.conversion_routine(file_to_import)
            if not img_gui.endswith('.png'):
                img_gui += '.png'

            self.show_image(img_gui, view, scene)

    def app_sequence_post(self):
        self.disable_run_postproc_button()
        self.model.ssh_to_server()
        self.collect_post_proc_parameters()
        self.check_if_directory_exists_post()
        if not self.post_proc_run:
            self.model.run_script_post()
        else:
            print(' ++++++++++ results of comparison are already available  +++++++++++++')
        self.retrieve_plots()
        return

    def show_image(self, filename, view, scene):
        scene.clear()
        pixmap = QPixmap(self.model.output_directory + filename)
        pixmap_scaled = pixmap.scaled(0.75 * self.model.width, 0.6 * self.model.height, Qt.KeepAspectRatio)
        scene.addPixmap(pixmap_scaled)
        view.setScene(scene)
