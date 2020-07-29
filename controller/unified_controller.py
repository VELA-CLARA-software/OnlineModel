import sys, os
sys.path.append(os.path.abspath(__file__+'/../../'))
import controller.run_parameter_controller as RunParameterController


class UnifiedController():

        def __init__(self, m_RunParameterController, m_DynamicPlotController):
            self.rpc = m_RunParameterController
            self.dpc = m_DynamicPlotController
            #self.rpc.enable_run_button()
            self.rpc.view.actionImport_YAML.triggered.connect(self.rpc.import_parameter_values_from_yaml_file)
            self.rpc.view.actionExport_YAML.triggered.connect(self.rpc.export_parameter_values_to_yaml_file)
            self.rpc.view.actionRead_from_EPICS.triggered.connect(self.rpc.read_from_epics)
            self.rpc.view.actionAuto_load_Settings.toggled.connect(self.rpc.connect_auto_load_settings)
            #self.rpc.view.runButton.clicked.connect(self.rpc.run_astra)
            #self.rpc.view.runButton.clicked.connect(self.run_rpc_process)
            self.rpc.add_plot_signal.connect(self.dpc.add_twiss_plot)
            self.rpc.remove_plot_signal.connect(self.dpc.remove_twiss_plot)
            self.dpc.plotcolor.connect(self.rpc.setrunplotcolor)

        def run_rpc_process(self):
            self.rpc.disable_run_button()
            self.rpc.run_thread(self.rpc.app_sequence)
            self.rpc.thread.start()

