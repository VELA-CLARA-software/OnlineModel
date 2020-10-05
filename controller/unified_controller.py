import sys, os
sys.path.append(os.path.abspath(__file__+'/../../'))
import controller.run_parameter_controller as RunParameterController
# import controller.post_processing_controller as PostProcessingController

class UnifiedController():

        def __init__(self, m_RunParameterController, m_DynamicPlotController, m_DatabaseController):#, m_PostProcessingController):
            self.rpc = m_RunParameterController
            self.dpc = m_DynamicPlotController
            self.dbc = m_DatabaseController

            self.rpc.view.actionImport_YAML.triggered.connect(self.rpc.import_parameter_values_from_yaml_file)
            self.rpc.view.actionExport_YAML.triggered.connect(self.rpc.export_parameter_values_to_yaml_file)
            self.rpc.view.actionRead_from_EPICS.triggered.connect(self.rpc.read_from_epics)
            self.rpc.view.actionRead_from_DBURT.triggered.connect(self.rpc.read_from_DBURT)

            self.rpc.view.actionChange_DB.triggered.connect(self.rpc.change_database)
            # self.rpc.view.actionAuto_load_Settings.toggled.connect(self.rpc.connect_auto_load_settings)

            # Connects signal from the run controller to add a plot to the plot controller
            self.rpc.add_plot_signal.connect(self.dpc.add_twiss_plot)
            # Connects signal from the run controller to remove a plot to the plot controller
            self.rpc.remove_plot_signal.connect(self.dpc.remove_twiss_plot)
            # Returns a color from the plot controller to the run controller
            self.dpc.plotcolor.connect(self.rpc.setrunplotcolor)
            # Connects a signal from the run controller to the database controller to delete an entry from the database
            self.rpc.delete_run_id_signal.connect(self.dbc.delete_run_id_from_database)
            # Connects a signal from the run controller to the database controller to change the active database file
            self.rpc.change_database_signal.connect(self.change_database)
            # Connects a signal from clicking on a run_id to the plotting controller
            self.rpc.run_id_clicked_signal.connect(self.dpc.curveClicked)

        def change_database(self, database):
            self.dbc.change_database(database)
            self.rpc.database_changed()

        def run_rpc_process(self):
            self.rpc.disable_run_button()
            self.rpc.run_thread(self.rpc.app_sequence)
            self.rpc.thread.start()

        # def run_ppc_process(self):
            # self.ppc.disable_run_postproc_button()
            # self.ppc.app_sequence_post()
            # self.ppc.enable_run_postproc_button()
            # #self.ppc.run_thread(self.ppc.app_sequence_post)
            # #self.ppc.thread.start()
