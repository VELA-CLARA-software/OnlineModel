import datetime
import requests
import math
import re
import numpy
from .. import lattices
from .DBURT_parser import DBURT_Parser

class constants():

    speed_of_light = 299792458.0

class DBURT_to_data(object):

    def __init__(self, parameterDict, quad_values, rf_values):
        self.lattices = lattices.lattices
        self.parameterDict = parameterDict
        self.quad_values = quad_values
        self.rf_values = rf_values
        self.parser = DBURT_Parser()

    def get_pv_alias(self, dict, name, param=None, rf_type=None):
        """Return the PV alias for a given dictionary entry.

        :param dict: element dictionary
        :type dict: dictionary
        :param name: element name
        :type name: str
        :param param: element parameter, defaults to None
        :type param: str, optional
        :param rf_type: type of RF cavity, defaults to None
        :type rf_type: str, optional
        """
        if dict[name]['type'] == 'quadrupole':
            dict[name].update({"pv_suffix_alias": "SETI"})
            return "SETI"
        elif dict[name]['type'] == 'solenoid':
            dict[name].update({"pv_suffix_alias": "SETI"})
            return "SETI"
        elif dict[name]['type'] == "cavity" and rf_type is not None:
            if param == "phase":
                dict[name].update({"pv_phase_alias": "vm:dsp:sp_ph:phase"})
                return "vm:dsp:sp_ph:phase"
            elif param == "field_amplitude":
                dict[name].update({"pv_field_amplitude_alias": "ad1:ch6:power_remote_s.POWER"})
                return "ad1:ch6:power_remote_s.POWER"
        elif dict[name]['type'] == "generator" and param is not None:
            if param == "charge":
                dict[name].update({"pv_root_alias": "CLA-S01-DIA-WCM-01"})
                dict[name].update({"pv_suffix_alias": "Q"})
                return "Q"
        else:
            dict[name].update({"pv_suffix_alias": "SETI"})

    def read_values_from_archiver(self, pv_name, time_from=None, time_to=None):
        """Extract values from the archiver for a given PV.

        :param pv_name: PV name to get values for
        :type pv_name: str
        :param time_from: start of time period to average values over, defaults to None
        :type time_from: float, optional
        :param time_to: end of time period to average values over, defaults to None
        :type time_to: float, optional
        :return: value extracted from the archiver
        :rtype: float
        """
        # NOTE: time_from and time_to must be in ISO 1806 format!!
        # see http://claraserv2.dl.ac.uk/cssi_wiki/doku.php/archiver:pulling_data?s[]=archiver
        if time_from is None:
            time_from = datetime.datetime.now().isoformat() + "Z"
        if time_to is None:
            time_to = datetime.datetime.now().isoformat() + "Z"
        url = "http://claraserv2.dl.ac.uk:17668/retrieval/data/getData.json?pv=" + pv_name + "&from=" + time_from + "&to=" + time_to
        # print(url)
        r = requests.get(url)
        data = r.json()
        value = numpy.mean(data[0]['data'][0]['val'])
        # print(value)
        return value

    def get_energy_gain(self, time_from=None, time_to=None):
        """Return the calculated energy gain for an RF structure based on timstamps in the archiver.

        :param time_from: start of time period to average values over, defaults to None
        :type time_from: float, optional
        :param time_to: end of time period to average values over, defaults to None
        :type time_to: float, optional
        :return: total_energy_gain
        :rtype: float
        """
        for l in self.lattices:
            for key, value in self.parameterDict[l].items():
                if value['type'] == 'cavity':
                    cavity_length = value['length']
                    pv_amp_alias = value['pv_root_alias'] + ":" + value['pv_field_amplitude_alias']
                    pv_phase_alias = value['pv_root_alias'] + ":" + value['pv_phase_alias']
                    forward_power = self.read_values_from_archiver(pv_amp_alias, time_from, time_to) * 1.e6
                    phase = 0 # self.read_values_from_archiver(pv_phase_alias, time_from, time_to)
                    if value['controller_name'] == "GUN10":
                        pulse_length = 2.5
                        gun_energy_gain = self.get_energy_from_rf(forward_power, phase, pulse_length) / cavity_length
                        value.update({'energy_gain': float(gun_energy_gain)})
                        value['field_amplitude'] = float(gun_energy_gain)
                    elif value['controller_name'] == "L01":
                        pulse_length = 0.75
                        l01_energy_gain = self.get_energy_from_rf(forward_power, phase, pulse_length) / cavity_length
                        value.update({'energy_gain': float(l01_energy_gain)})
                        value['field_amplitude'] = float(l01_energy_gain)
                    value['phase'] = phase
                    value['pulse_length'] = pulse_length
        total_energy_gain = gun_energy_gain + l01_energy_gain
        return total_energy_gain

    def generate_magnet_name(self, name):
        """Return fully formed magnet name based on the framework element name.

        :param name: Framework element name
        :type name: str
        :return: tuple of (lattice name, magnet PV name)
        :rtype: tuple of strings
        """
        name_number = re.compile(r'(?P<name>[a-zA-Z]+)(?P<number>\d+)')
        name_nonumber = re.compile(r'(?P<name>[a-zA-Z]+)')
        split = name.split('-')
        if split[0] == 'INJ':
            lattice = 'EBT-INJ'
        elif split[0] == 'BA1':
            lattice = 'EBT-BA1'
        else:
            lattice = 'CLA-' + split[0]
        match = name_number.search(split[1])
        if match:
            name, number = match.group('name'), match.group('number').zfill(2)
            if 'QUAD' in name:
                return lattice, lattice + '-MAG-QUAD-' + number
            elif 'SOL' in name:
                return lattice, lattice + '-MAG-SOL-' + number
        if split[0] == 'LRG':
            match = name_nonumber.search(split[1])
            if match and match.group('name'):
                name = match.group('name')
                lattice = 'CLA-LRG1'
                if 'SOL' == name:
                    return 'Gun', lattice + '-MAG-SOL-01'
                elif 'BSOL' == name:
                    return 'Gun', lattice + '-MAG-BSOL-01'
        return None, None

    def read_values_from_DBURT(self, dburt):
        """Extrtact values from a DBURT file and update the dictionaries.

        :param dburt: DBURT dictionary
        :type dburt: dictionary
        :return: magnet data
        :rtype: dictionary
        """
        data = self.parser.parse_DBURT(dburt)
        magnetdata = {}
        speed_of_light = constants.speed_of_light / 1e6
        for key, mag in data['magnets'].items():
            mag['lattice'], mag['fullname'] = self.generate_magnet_name(mag['name'])
            if mag['lattice'] == 'CLA-L01':
                mag['lattice'] = 'Linac'
            if mag['lattice'] == 'Linac' or mag['lattice'] == 'Gun':
                self.total_energy_gain = 5
            else:
                self.total_energy_gain = 35
            if mag['fullname'] in self.quad_values:
                value = self.quad_values[mag['fullname']]
            elif mag['fullname'] in self.rf_values:
                value = self.rf_values[mag['fullname']]
            else:
                value = {'type': None}
            mag['value'] = value

            if value['type'] == 'quadrupole':
                quad_pv_alias = key + ":" + value['pv_suffix_alias']
                current = float(mag['setI'])
                coeffs = numpy.append(value['field_integral_coefficients'][:-1],
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = speed_of_light * int_strength / self.total_energy_gain
                # self.update_widgets_with_values("lattice:" + key + ":k1l", effect / value['magnetic_length'])
                value['k1l'] = effect / value['magnetic_length']
            elif value['type'] == 'solenoid':
                sol_pv_alias = key + ":" + value['pv_suffix_alias']
                current = float(mag['setI'])
                sign = numpy.copysign(1, current)
                coeffs = numpy.append(value['field_integral_coefficients'][-4:-1] * int(sign),
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = int_strength / value['magnetic_length']
                value['field_amplitude'] = float(effect / value['magnetic_length'])
            magnetdata[mag['name']] = mag
        return magnetdata

    def read_values_from_epics(self, dict, time_from=None, time_to=None):
        """Extract values from an EPICS PV and update the dictionary.

        :param dict: dictionary to be updated
        :type dict: dictionary
        :param time_from: start of time period to average values over, defaults to None
        :type time_from: float, optional
        :param time_to: end of time period to average values over, defaults to None
        :type time_to: float, optional
        """
        self.total_energy_gain = self.get_energy_gain(time_from, time_to)
        speed_of_light = constants.speed_of_light / 1e6
        for key, value in dict.items():
            if value['type'] == 'quadrupole':
                quad_pv_alias = key + ":" + value['pv_suffix_alias']
                current = self.read_values_from_archiver(quad_pv_alias, time_from, time_to)
                coeffs = numpy.append(value['field_integral_coefficients'][:-1],
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = speed_of_light * int_strength / self.total_energy_gain
                value['k1l'] = effect / value['magnetic_length']
            elif value['type'] == 'solenoid':
                sol_pv_alias = key + ":" + value['pv_suffix_alias']
                current = self.read_values_from_archiver(sol_pv_alias, time_from, time_to)
                sign = numpy.copysign(1, current)
                coeffs = numpy.append(value['field_integral_coefficients'][-4:-1] * int(sign),
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = int_strength / value['magnetic_length']
                value['field_amplitude'] = float(effect / value['magnetic_length'])
            elif value['type'] == 'generator':
                if key == 'charge':
                    charge_pv_alias = value['pv_root_alias'] + ":" + value['pv_suffix_alias']
                    charge = self.read_values_from_archiver(charge_pv_alias, time_from, time_to)
                    value['value'] = charge * 1e-3

    def get_energy_from_rf(self, klystron_power, phase, pulse_length):
        """Return the estimated energy gain from an RF cavity for the given RF parameters.

        :param klystron_power: RF cavity forward power
        :type klystron_power: float
        :param phase: RF cavity phase
        :type phase: float
        :param pulse_length: RF cavity pulse length
        :type pulse_length: float
        :return: energy gain in RF cavity
        :rtype: float
        """
        bestcase = 0.407615 + 1.94185 * (((1 - math.exp((-1.54427 * 1e6 * pulse_length * 1e6))) * (
                    0.0331869 + 6.05422 * 1e-7 * klystron_power)) * numpy.cos(phase)) ** 0.5
        worstcase = 0.377 + 1.81689 * (((1 - math.exp((-1.54427 * 1e6 * pulse_length * 1e6))) * (
                    0.0331869 + 6.05422 * 1e-7 * klystron_power)) * numpy.cos(phase)) ** 0.5
        return numpy.mean([bestcase, worstcase])
