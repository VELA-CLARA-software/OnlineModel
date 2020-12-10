from copy import deepcopy
from collections import OrderedDict
from . import lattices
from .elements.generator import generator
from .elements.quadrupole import quadrupole
from .elements.cavity import cavity

class parameterDict(OrderedDict):

    def __init__(self):
        for l in lattices.lattices:
            self.update({l: OrderedDict()})
        self['scan'] = OrderedDict()
        self['generator'] = OrderedDict()
        self['runs'] = OrderedDict()

    def __deepcopy__(self, memo):
        """Copy only key-value pairs."""
        datacopy = type(self)()
        for k, v in self.items():
            print(k)
            datacopy.update({k: deepcopy(v, memo)})
        print('finished!')
        return datacopy

    def get_data(self, Framework):
        # NEW FORMAT
        self.quad_values = quadrupole(Framework)
        self.rf_values = cavity(Framework)
        self.generator = generator(Framework)

        # self.tracking_code = OrderedDict()
        self.simulation_parameters = {'tracking_code': 'elegant', 'csr': True, 'csr_bins': 200, 'lsc': True, 'lsc_bins': 200}

    def initialise_data(self):
        self['Gun']['h_min'] = {'value': 0.0001, 'type': 'simulation'}
        self['Gun']['h_max'] = {'value': 0.0001, 'type': 'simulation'}

        for l in lattices.lattices:
            for key, value in self.quad_values.items():
                if l == key[:len(l)]:
                    self[l].update({key: value})

            for key, value in self.simulation_parameters.items():
                self[l][key] = OrderedDict()
                self[l][key]['value'] = value
                self[l][key]['type'] = 'simulation'

        for key, value in self.rf_values.items():
            if 'LRG' in key:
                self[lattices.lattices[0]].update({key: value})
            if 'L01' in key:
                self[lattices.lattices[1]].update({key: value})

        for key, value in self.generator.items():
            self['generator'].update({key: value})

        self['Linac']['zwake'] = {'value': True, 'type': 'simulation'}
        self['Linac']['trwake'] = {'value': True, 'type': 'simulation'}

        self[lattices.lattices[0]]['bsol_tracking'] = {'value': True, 'type': 'simulation'}

class screenDict(OrderedDict):

    def __init__(self, Framework):
        self.Framework = Framework

        self.screen_values = OrderedDict()
        self.update_screen_values()

        self.update()


    def update_screen_values(self):
        for screen in self.Framework.getElementType(['screen', 'watch_point', 'monitor', 'beam_arrival_monitor', 'marker']):
            name = screen['objectname'].replace('-W','')
            type = screen['objecttype']
            position = float(screen.middle[2])
            self.screen_values.update({name: {'type': type, 'position': position}})

    def update(self):
        for l in lattices.lattices:
            dic = OrderedDict()
            for key, value in self.screen_values.items():
                if l == key[:len(l)]:
                    dic.update({key: value})
                elif l == 'Gun' and 'CLA-S01' == key[:len('CLA-S01')]:
                    dic.update({key: value})
                elif l == 'Linac' and 'CLA-L01' == key[:len('CLA-L01')]:
                    dic.update({key: value})
            self[l] = dic
        self['generator'] = {'Laser': {'type': 'screen', 'position': 0.0}}
