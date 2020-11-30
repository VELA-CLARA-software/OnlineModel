import os, sys
import glob

sys.path.append(os.path.abspath(__file__+'/../../../OnlineModel/'))
sys.path.append(os.path.abspath(__file__+'/../../../SimFrame/'))
import SimulationFramework.Modules.Twiss as rtf

class twissData(object):

    def __init__(self, directory, name):
        super(twissData, self).__init__()
        self.directory = directory
        self.name = name

    def run_script(self):
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
        directory = self.directory
        name = self.name
        if not isinstance(directory, (list, tuple)):
            directory = [directory]
        ''' loads the first (and only?) param in the list of directories '''
        twiss = self.loadDataFile(directory[0], reset=True)
        ''' loads any other directories '''
        for d in directory[1:]:
            twiss = self.loadDataFile(d, reset=False, twiss=twiss)
        ''' assignes a reference name if none is given '''
        return twiss

    def loadDataFile(self, directory, sections=None, reset=True, twiss=None):
        ''' loads ASTRA and Elegant data files from a directory and returns a twiss object'''
        if sections is None or (isinstance(sections, str) and sections.lower() == 'all'):
            astrafiles = sorted(glob.glob(directory+"/*Xemit.*"))
            elegantfiles = sorted(glob.glob(directory+"/*.flr"))
        else:
            astrafiles = []
            elegantfiles = []
            for s in sections:
                astrafiles += sorted(glob.glob(directory+"/"+s+"*Xemit.*"))
                elegantfiles += sorted(glob.glob(directory+"/"+s+"*.flr"))
        if twiss is None: # If it doesn't exist need to instantiate a twiss obkject
            twiss = rtf.twiss()
        twiss.read_astra_emit_files(astrafiles, reset=reset)
        reset = False if len(astrafiles) > 0 else reset # if we have alreay found some ASTRA files, we need to set this to false to append new data, otherwise check input value
        ''' reset=False stops the previously loaded data from being overwritten'''
        twiss.read_elegant_twiss_files(elegantfiles, reset=reset)
        return twiss
