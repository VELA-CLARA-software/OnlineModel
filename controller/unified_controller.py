import run_parameter_controller as RunParameterController
import post_processing_controller as PostProcessingController

class UnifiedController():
        
        def __init__(self, m_RunParameterController, m_PostProcessingController):
            self.rpc = m_RunParameterController
            self.ppc = m_PostProcessingController
            self.rpc.enable_run_button()
            self.rpc.view.actionImport_YAML.triggered.connect(self.rpc.import_parameter_values_from_yaml_file)
            self.rpc.view.actionExport_YAML.triggered.connect(self.rpc.export_parameter_values_to_yaml_file)

