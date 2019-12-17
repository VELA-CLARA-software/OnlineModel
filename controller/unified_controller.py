import run_parameter_controller as RunParameterController
import post_processing_controller as PostProcessingController

class UnifiedController():

        def __init__(self, m_RunParameterController, m_DynamicPlotController):#, m_PostProcessingController):
            self.rpc = m_RunParameterController
            self.dpc = m_DynamicPlotController
            #self.ppc = m_PostProcessingController
            #self.rpc.enable_run_button()
            self.rpc.view.actionImport_YAML.triggered.connect(self.rpc.import_parameter_values_from_yaml_file)
            self.rpc.view.actionExport_YAML.triggered.connect(self.rpc.export_parameter_values_to_yaml_file)
            self.rpc.view.actionRead_from_EPICS.triggered.connect(self.rpc.read_from_epics)
            self.rpc.view.actionAuto_load_Settings.toggled.connect(self.rpc.connect_auto_load_settings)
            #self.rpc.view.runButton.clicked.connect(self.rpc.run_astra)
            #self.rpc.view.runButton.clicked.connect(self.run_rpc_process)
            #self.ppc.view.runButton_post.clicked.connect(self.run_ppc_process)


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
