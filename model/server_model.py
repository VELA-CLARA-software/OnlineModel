import database.database_controller as dbc
import data.lattices as lattices
from model.local_model import Model as local_model
from model.local_model import convert_data_types, create_yaml_dictionary

sys.path.append(os.path.abspath(__file__+'/../../../SimFrame/'))
import SimulationFramework.Framework as Fw

class Model(local_model):
    """Model object for the server model."""

    def __init__(self, directoryname, data, dbcontroller, runno=1):
        self.data = data
        self.directoryname = directoryname
        sddsindex = runno % 20
        self.data.Framework = Fw.Framework(directory='.', clean=False, verbose=False, sddsindex=sddsindex)
        # print('self.Framework.master_lattice_location = ', self.Framework.master_lattice_location)
        # self.Framework.defineElegantCommand(location=[self.Framework.master_lattice_location+'Codes/elegant'])
        # os.environ['RPN_DEFNS'] = self.Framework.master_lattice_location+'Codes/defns.rpn'
        self.data.Framework.loadSettings(lattices.lattice_definition)
        self.lattices = lattices.lattices
        self.dbcontroller = dbcontroller
