from PyQt4.QtCore import *
from PyQt4.QtGui import *

class PostProcessingController(QObject):

    def __init__(self, app, view, model):
        super(PostProcessingController, self).__init__()
        self.my_name = 'PostProcessingController'
        self.app = app
        self.model = model
        self.view = view
        self.model.data.initialise_data()