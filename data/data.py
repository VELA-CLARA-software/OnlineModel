import collections
import os, sys, time
import re
import numpy as np
import ruamel.yaml as yaml
sys.path.append(os.path.abspath(__file__+'/../../../'))
import SimFrame.SimulationFramework.Framework as Fw
import SimFrame.SimulationFramework.Modules.constants
import requests, json, datetime, math, numpy
import data.lattices as lattices
from copy import copy, deepcopy

from .DBURT.data import DBURT_to_data
from .parameters import parameterDict
from .parameters import screenDict

class Data(object):
    """Data object to hold all of the parameters and interface to the SimFrame framework."""

    def __getitem__(self, key):
        return getattr(self, key)

    def __init__(self, initialise=True):
        super(Data, self).__init__()
        """Initialise the Data object:
              - Create required dictionaries
              - Initialise the SimFrame framework object
              - Extract element data from the framework
              - Initialise dictionaries with the specified values
        """
        self.lattices = lattices.lattices

        if initialise: # When we are deep copying we don't need to do this, so don't...
            self.Framework = Fw.Framework(directory='.', clean=False, verbose=False, delete_output_files=False)
            self.Framework.loadSettings(lattices.lattice_definition)
            self.parameterDict = parameterDict()
            self.generatorDict = self.parameterDict['generator']
            self.runsDict = self.parameterDict['runs']
            self.scanDict = self.parameterDict['scan']
            self.screenDict = screenDict(self.Framework)

            self.get_data()
            self.initialise_data()

            self.DBURT_data = DBURT_to_data(self.parameterDict, self.quad_values, self.rf_values)


    def __deepcopy__(self, memo):
        """Only copy required objects."""
        start = time.time()
        datacopy = type(self)(initialise=False)
        start = time.time()
        datacopy.Framework = deepcopy(self.Framework, memo)
        datacopy.parameterDict = deepcopy(self.parameterDict, memo)
        datacopy.generatorDict = datacopy.parameterDict['generator']
        datacopy.runsDict = datacopy.parameterDict['runs']
        return datacopy

    def get_data(self):
        """Initialise element dictionaries and prepare them for the framework values."""
        self.scan_parameter = collections.OrderedDict()
        self.parameterDict.get_data(self.Framework)

    def initialise_data(self):
        """Initialise the element dictionaries and keys with data from the framework."""
        self.parameterDict.initialise_data()
        self.quad_values = self.parameterDict.quad_values
        self.rf_values = self.parameterDict.rf_values

    def initialise_scan(self, id):
        """Initialise the scan dictionary with relevant parameters."""
        self.scanDict[str(id)] = {}
        [self.scanDict[str(id)].update({key: None}) for key in ['scan', 'parameter', 'scan_from_value', 'scan_to_value', 'scan_step_size']]

    def initialise_scan_parameters(self):
        """Update the scan_parameter dictionary with relevant parameters."""
        [self.scan_parameter.update({key: value}) for key, value in zip(scan_keys, scan_v)]
