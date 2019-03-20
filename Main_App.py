import sys,os
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))),'model'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))),'controller'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))),'view'))

from model import model

class App(object):
    def __init__(self):
        self.model = model.model()


    def main(self):
        self.model.data.data_values['directory'] ='/home/qfi29231/Bruno_results_1/'
        setattr(self.model,'username' ,'qfi29231')
        setattr(self.model, 'password', "qd'3xk.mr6&&")
        self.model.app_sequence()


if __name__ == '__main__':
    app = App()
    app.main()