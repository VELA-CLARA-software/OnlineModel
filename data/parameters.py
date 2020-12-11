from copy import deepcopy
from collections import OrderedDict
from . import lattices
from .elements.generator import generator
from .elements.quadrupole import quadrupole
from .elements.cavity import cavity
from .elements.field_coefficients import field_coefficients
from .elements.magnetic_lengths import magnetic_lengths
from .elements.simulation import simulation
from .elements.gun import gun
from .elements.linac import linac

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
        """Get GUI dictionary key/values."""
        self.quad_values = quadrupole(Framework)
        self.rf_values = cavity(Framework)
        self.generator = generator(Framework)
        self.simulation_parameters = simulation()
        self.gun_parameters = gun()
        self.linac1_parameters = linac()

    def initialise_data(self):
        """Update dictionary with required GUI key/value pairs and default values."""
        self.update_gun()
        self.update_linac1()
        self.update_quads()
        self.update_simulations()
        self.update_generator()
        self.update_mag_field_coefficients()

    def update_gun(self):
        """Update gun parameters in dictionary."""
        gun_lattice = lattices.lattices[0]
        for key, value in self.gun_parameters.items():
            self[gun_lattice][key] = OrderedDict()
            for k,v in value.items():
                self[gun_lattice][key][k] = v
        for key, value in self.rf_values.items():
            if 'LRG' in key:
                self[gun_lattice].update({key: value})

    def update_linac1(self):
        """Update linac1 parameters in dictionary."""
        linac1_lattice = lattices.lattices[1]
        for key, value in self.linac1_parameters.items():
            self[linac1_lattice][key] = OrderedDict()
            for k,v in value.items():
                self[linac1_lattice][key][k] = v
        for key, value in self.rf_values.items():
            if 'L01' in key:
                self[linac1_lattice].update({key: value})

    def update_quads(self):
        """Update quadrupole parameters in dictionary."""
        for latt in lattices.lattices:
            for key, value in self.quad_values.items():
                if latt == key[:len(latt)]:
                    self[latt][key] = OrderedDict()
                    for k,v in value.items():
                        self[latt][key][k] = v

    def update_simulations(self):
        """Update simulation parameters in dictionary."""
        for latt in lattices.lattices:
            for key, value in self.simulation_parameters.items():
                self[latt][key] = OrderedDict()
                for k,v in value.items():
                    self[latt][key][k] = v

    def update_generator(self):
        """Update generator parameters in dictionary."""
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
        """Extract screen positions from the Framework."""
        for screen in self.Framework.getElementType(['screen', 'watch_point', 'monitor', 'beam_arrival_monitor', 'marker']):
            name = screen['objectname'].replace('-W','')
            type = screen['objecttype']
            position = float(screen.middle[2])
            self.screen_values.update({name: {'type': type, 'position': position}})

    def update(self):
        """Update dictionary with key/value pairs and add on laser screen."""
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
