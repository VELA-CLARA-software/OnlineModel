import run_parameter_controller as RunParameterController
import post_processing_controller as PostProcessingController

class UnifiedController():
        
        def __init__(self, m_RunParameterController, m_PostProcessingController):
            self.rpc = m_RunParameterController
            self.ppc = m_PostProcessingController
            self.rpc.enable_run_button()
            self.rpc.view.runButton.clicked.connect(self.run_rpc_process)
            
    
        def run_rpc_process(self):
            self.rpc.disable_run_button()
            self.rpc.run_thread(self.rpc.app_sequence)
            self.rpc.thread.start()