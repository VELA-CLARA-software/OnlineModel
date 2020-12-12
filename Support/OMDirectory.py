import sys
import os
import numpy as np
sys.path.append('../../')
import glob
from munch import Munch
from controller.database_controller import DatabaseController
from data.data import Data as OMData
from SimulationFramework.Framework import Framework, frameworkDirectory
import SimulationFramework.Modules.Beams as rbf
import SimulationFramework.Modules.Twiss as rtf
try:
    import SimulationFramework.Modules.plotting as groupplot
    use_matplotlib = True
except ImportError:
    use_matplotlib = False

class OM_Beams():

    def __repr__(self):
        return repr(self.screens)

    def __init__(self, database='SimulationDatabase.db', runs=None, dbc=None):
        self.directory, database = os.path.split(os.path.abspath(database))
        if not dbc:
            self.dbc = DatabaseController(os.path.join(directory,database), verbose=False)
        else:
            self.dbc = dbc
        if not runs:
            self.runs = list(self.dbc.get_all_run_ids())
        else:
            self.runs = runs
        self.data = OMData(self.directory, settings_directory=os.path.relpath(__file__+'/../../'))
        self.screenpositions = self.data.screenDict
        self.allscreens = []
        for l, f in self.screenpositions.items():
            for k, v in f.items():
                n = k
                p = v['position']
                self.allscreens.append([n, p, l])
        self.allscreens = sortedscreennames = sorted(self.allscreens, key=lambda x: float(x[1]))
        self.screens = [s[0] for s in self.allscreens]

    def get_directory(self, selectedscreen):
        screens, positions, lattices = list(zip(*self.allscreens))
        screen_idx = screens.index(selectedscreen[0])
        lattice = lattices[screen_idx]
        return os.path.abspath(os.path.join(self.directory, self.prefixes[lattice],selectedscreen[0] + '.hdf5'))

    def get_beams(self, id):
        self.prefixes = self.dbc.find_run_id_for_each_lattice(id)
        beams = rbf.beamGroup()
        for s in self.allscreens:
            beams.add(self.get_directory(s))
        return beams

class OM_Twiss():

    def __repr__(self):
        return repr(self.twiss)

    def __init__(self, database='SimulationDatabase.db', runs=None, dbc=None):
        self.directory, database = os.path.split(database)
        if not dbc:
            self.dbc = DatabaseController(self.directory+'/'+database, verbose=False)
        else:
            self.dbc = dbc
        if not runs:
            self.runs = list(self.dbc.get_all_run_ids())
        else:
            self.runs = runs

    def addTwissDirectory(self, directory):
        '''
            Read the data files in a directory and add a plotItem to the relevant curves

            Keyword arguments:
            directory -- dictionary containing directory definitions:
                [
                    {'directory': <dir location>,           'sections': [<list of lattice sections>]},
                    {'directory': <another dir location>,   'sections': 'All'},
                    ...
                ]
                The directories are scanned for ASTRA or Elegant twiss files and imported as one set.
                The data is then sorted in z. No analysis is done for duplicate entries.
            name -- dictionary key name (default: last directory name)
        '''
        ''' load the data files into the twiss dictionary '''
        if not isinstance(directory, (list, tuple)):
            directory = [directory]
        ''' loads the first (and only?) param in the list of directories '''
        twiss = self.loadDataFile( reset=True, **(directory[0]))
        ''' loads any other directories '''
        for d in directory[1:]:
            twiss = self.loadDataFile(reset=False, twiss=twiss, **d)
        self.twiss = twiss
        return self.twiss

    def loadDataFile(self, directory, sections=None, reset=True, twiss=None):
        ''' loads ASTRA and Elegant data files from a directory and returns a twiss object'''
        if sections is None or (isinstance(sections, str) and sections.lower() == 'all'):
            astrafiles = sorted(glob.glob(directory+"/*Xemit.*"))
            elegantfiles = sorted(glob.glob(directory+"/*.flr"))
            gptfiles = sorted(glob.glob(directory+"/*emit.gdf"))
        else:
            astrafiles = []
            elegantfiles = []
            gptfiles = []
            for s in sections:
                astrafiles += sorted(glob.glob(directory+"/"+s+"*Xemit.*"))
                elegantfiles += sorted(glob.glob(directory+"/"+s+"*.flr"))
                gptfiles += sorted(glob.glob(directory+"/"+s+"*emit.gdf"))
        if twiss is None: # If it doesn't exist need to instantiate a twiss obkject
            twiss = rtf.twiss()
        ### ASTRA ###
        twiss.read_astra_twiss_files(astrafiles, reset=reset)
        ### ELEGANT ###
        reset = False if len(astrafiles) > 0 else reset # if we have alreay found some ASTRA files, we need to set this to false to append new data, otherwise check input value
        ''' reset=False stops the previously loaded data from being overwritten'''
        twiss.read_elegant_twiss_files(elegantfiles, reset=reset)
        ### GPT ###
        reset = False if len(astrafiles) > 0 or len(elegantfiles) > 0 else reset # if we have alreay found some ASTRA/Elegant files, we need to set this to false to append new data, otherwise check input value
        ''' reset=False stops the previously loaded data from being overwritten'''
        twiss.read_GPT_twiss_files(gptfiles, reset=reset)
        return twiss

    def loadTwiss(self, id):
        prefixes = self.dbc.find_run_id_for_each_lattice(id)
        twissList = []
        for s, d in prefixes.items():
            twissList.append({'directory': os.path.abspath(self.directory+'/'+d), 'sections': [s]})
        twiss = self.addTwissDirectory(twissList)
        return twiss

class OMDirectory(frameworkDirectory):

    def __init__(self, id, database='SimulationDatabase.db', twiss=True, beams=False, verbose=False):
        directory, database = os.path.split(os.path.abspath(database))
        self.id = id
        self.dbc = DatabaseController(directory+'/'+database, verbose=False)
        self.runs = list(self.dbc.get_all_run_ids())
        self.prefixes = self.dbc.find_run_id_for_each_lattice(id)
        subdirectory = os.path.abspath(directory+'/'+list(self.prefixes.items())[-1][-1])
        settingsfile = os.path.join(os.path.relpath(subdirectory),'settings.def')
        changesfile = os.path.join(os.path.relpath(subdirectory),'changes.yaml')
        self.framework = Framework(os.path.relpath(subdirectory), clean=False, verbose=verbose)
        self.framework.loadSettings(settingsfile)
        if os.path.exists(changesfile):
            self.framework.load_changes_file(changesfile)
        self.screens = None
        if twiss:
            twiss = OM_Twiss(database=os.path.join(directory,database), dbc=self.dbc, runs=self.runs)
            self.twiss = twiss.loadTwiss(id)
        else:
            self.twiss = None
        if beams:
            self.OMbeams = OM_Beams(database=os.path.join(directory,database), dbc=self.dbc, runs=self.runs)
            self.screens = self.OMbeams.screens
            self.beams = self.OMbeams.get_beams(id)
        else:
            self.beams = None

    def save_summary_files(self):
        twiss = False if self.twiss is None else True
        beams = False if self.beams is None else True
        save_summary_files(self.id, twiss=twiss, beams=beams, omd=self)

def load_directory(id, database='SimulationDatabase.db', twiss=True, beams=True, **kwargs):
    fw = OMDirectory(id, database=database, twiss=twiss, beams=beams, verbose=True, **kwargs)
    return fw

def get_runs(database='SimulationDatabase.db'):
    directory, database = os.path.split(os.path.abspath(database))
    dbc = DatabaseController(directory+'/'+database, verbose=False)
    return list(dbc.get_all_run_ids())

def save_summary_files(id, database='SimulationDatabase.db', twiss=True, beams=True, omd=None):
    directory, database = os.path.split(os.path.abspath(database))
    if not omd:
        omd = OMDirectory(id, os.path.join(directory, database), twiss=twiss, beams=beams)
    if twiss:
        omd.twiss.save_HDF5_twiss_file(os.path.join(omd.framework.subdirectory,'Twiss_Summary.hdf5'))
    if beams:
        omd.OMbeams.prefixes = omd.OMbeams.dbc.find_run_id_for_each_lattice(id)
        beams = []
        for s in omd.OMbeams.allscreens:
            beams.append(os.path.abspath(omd.OMbeams.get_directory(s)))
        rbf.hdf5.write_HDF5_summary_file(os.path.join(omd.framework.subdirectory,'Beam_Summary.hdf5'), beams, clean=True)
