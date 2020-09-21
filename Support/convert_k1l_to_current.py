import sys, os
from munch import Munch
import numpy as np
import ruamel.yaml as yaml
sys.path.append(os.path.abspath(__file__+'/../../'))
import controller.run_parameters_parser as yaml_parser
import data.lattices as lattices
import scipy.constants
import argparse

SPEED_OF_LIGHT = scipy.constants.c / 1e6  # in megametres/second, use with p in MeV/c

class magnet(Munch):

    def __init__(self, yaml, name):
        super(magnet, self).__init__(yaml)
        self.momentum = 35.5
        self.magType = 'QUAD'
        self.name = name
        self.magneticLength = self.magnetic_length
        self.fieldIntegralCoefficients = self.field_integral_coefficients

    @property
    def k(self):
        return 1000 * self.k1l / self.magneticLength

def getK(magnet, momentum=None):
    """Calculate the current to set in a magnet based on its K value (or bend angle)."""
    # What is the momentum in this section?
    k = magnet.k
    momentum = momentum if momentum is not None else magnet.momentum
    mag_type = str(magnet.magType)
    int_strength = None
    if mag_type == 'DIP':  # k represents deflection in degrees
        effect = np.radians(k) * 1000
    elif mag_type in ('QUAD', 'SEXT'):
        effect = magnet.k1l
    elif mag_type in ('HCOR', 'VCOR'):  # k represents deflection in mrad
        effect = k
    else:  # solenoids
        int_strength = k
    if int_strength is None:
        int_strength = effect * momentum / SPEED_OF_LIGHT
    coeffs = np.copy(magnet.fieldIntegralCoefficients[:-4] if mag_type in ('SOL', 'BSOL') else magnet.fieldIntegralCoefficients)
    # are we above or below residual field? Need to set coeffs accordingly to have a smooth transition through zero
    sign = np.copysign(1, int_strength - coeffs[-1])
    coeffs = np.append(coeffs[:-1] * sign, coeffs[-1])
    coeffs[-1] -= int_strength  # Need to find roots of polynomial, i.e. a1*x + a0 - y = 0
    roots = np.roots(coeffs)
    current = np.copysign(roots[-1].real, sign)  # last root is always x value (#TODO: can prove this?)
    return current

def load_yaml_file(filename, momentum=35.5):
    magnets = {}
    loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
    for l in lattices.lattices:
        for name, elem in loaded_parameter_dict[l].items():
            if 'type' in elem and elem['type'] == 'quadrupole':
                magnets[name] = magnet(elem, name)
    for name,m in magnets.items():
        print(name, getK(m,momentum))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add Sets.')
    parser.add_argument('filename', type=str)
    parser.add_argument('-p', '--momentum', default=35.5, type=float)
    args = parser.parse_args()

    load_yaml_file(args.filename, momentum=args.momentum)
