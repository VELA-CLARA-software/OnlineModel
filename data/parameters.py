from copy import deepcopy
from collections import OrderedDict
from . import lattices
from .elements.generator import generator
from .elements.quadrupole import quadrupole
from .elements.cavity import cavity
from .elements.field_coefficients import field_coefficients
from .elements.magnetic_lengths import magnetic_lengths
from .elements.simulation import simulation

def findDiff( d1, d2, path=""):
    """Compare two dictionaries and print the differences."""
    for k in d1:
        if (k not in d2):
            print ('findDiff:', path, ":")
            print ('findDiff:', k + " as key not in d2", "\n")
        else:
            if type(d1[k]) is dict:
                if path == "":
                    path = k
                else:
                    path = path + "->" + k
                findDiff(d1[k],d2[k], path)
            else:
                if d1[k] != d2[k]:
                    print('findDiff:', path+":"+k,':',d1[k],'=!=',d2[k])


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
            datacopy.update({k: deepcopy(v, memo)})
        return datacopy

    def get_data(self, Framework):
        # NEW FORMAT
        self.quad_values = quadrupole(Framework)
        self.rf_values = cavity(Framework)
        self.generator = generator(Framework)

        self.simulation_parameters = simulation()
        self.update_mag_field_coefficients()

    def initialise_data(self):
        gun = lattices.lattices[0]
        linac1 = lattices.lattices[1]
        self[gun]['bsol_tracking'] = {'value': True, 'type': 'simulation'}
        self[gun]['h_min'] = {'value': 0.0001, 'type': 'simulation'}
        self[gun]['h_max'] = {'value': 0.0001, 'type': 'simulation'}
        self[linac1]['zwake'] = {'value': True, 'type': 'simulation'}
        self[linac1]['trwake'] = {'value': True, 'type': 'simulation'}

        for latt in lattices.lattices:
            for key, value in self.quad_values.items():
                if latt == key[:len(latt)]:
                    self[latt][key] = OrderedDict()
                    for k,v in value.items():
                        self[latt][key][k] = v

            for key, value in self.simulation_parameters.items():
                self[latt][key] = OrderedDict()
                for k,v in value.items():
                    self[latt][key][k] = v

        for key, value in self.rf_values.items():
            if 'LRG' in key:
                self[gun].update({key: value})
            if 'L01' in key:
                self[linac1].update({key: value})

        for key, value in self.generator.items():
            self['generator'].update({key: value})


    def update_mag_field_coefficients(self):
        """Update magnet field coefficients in the relevant dictionaries."""

        for key in field_coefficients.keys():
            for k,v in field_coefficients[key].items():
                getattr(self, key)[k].update({'field_integral_coefficients': v})
        for key in magnetic_lengths.keys():
            for k,v in magnetic_lengths[key].items():
                getattr(self, key)[k].update({'magnetic_length': v})

class screenDict(OrderedDict):

    def __init__(self, Framework):
        self.Framework = Framework

        self.screen_values = OrderedDict()
        self.update_screen_values()

        self.update()

    def __deepcopy__(self, memo):
        """Copy only key-value pairs."""
        datacopy = type(self)()
        for k, v in self.items():
            datacopy.update({k: deepcopy(v, memo)})
        return datacopy

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
