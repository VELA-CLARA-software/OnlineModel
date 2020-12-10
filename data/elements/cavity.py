from .element import element

class cavity(element):

    rf_parameters = {
    'type':                     {'key': 'objecttype'},
    'phase':                    {'key': 'phase'},
    'pv_root_alias':            {'key': 'PV'},
    'controller_name':          {'key': 'Controller_Name'},
    'field_amplitude':          {'key': 'field_amplitude'},
    'pv_field_amplitude_alias': {'value': "ad1:ch6:power_remote_s.POWER"},
    'pv_phase_alias':           {'value': "vm:dsp:sp_ph:phase"},
    }

    solenoid_parameters = {
    'type':                     {'value': 'solenoid'},
    'pv_suffix_alias':          {'value': 'SETI'},
    'field_amplitude':          {'key': 'field_amplitude'},
    'cavity':                   {'key': 'objectname'},
    }

    def __init__(self, framework):
        super().__init__(framework)
        self.Framework_key = 'generator'

        for cavity in self.Framework.getElementType('cavity'):
            self.Framework_key = cavity['objectname']
            self.parameters = self.rf_parameters
            self.update_element(key=cavity['objectname'])
            self.get_element_length(self.Framework_key)

            for key, value in cavity['sub_elements'].items():
                if value['type'] == "solenoid":
                    self.parameters = self.solenoid_parameters
                    self.update_element(key=key)

    def get_element_length(self, key):
        """Get the length of a given element and update the dictionary."""
        length = self.Framework.getElement(key)['position_end'][2] - self.Framework.getElement(key)['position_start'][2]
        self[key].update({'length': length})


        # for cavity in self.Framework.getElementType('cavity'):
        #     self.rf_values.update({cavity['objectname']: collections.OrderedDict()})
        #     self.rf_values[cavity['objectname']].update({'type': cavity['objecttype']})
        #     self.rf_values[cavity['objectname']].update({'phase': cavity['phase']})
        #     self.rf_values[cavity['objectname']].update({'pv_root_alias': cavity['PV']})
        #     self.rf_values[cavity['objectname']].update({'controller_name': cavity['Controller_Name']})
        #     self.get_element_length(self.rf_values, cavity['objectname'])
        #     self.rf_values[cavity['objectname']].update({'field_amplitude': cavity['field_amplitude']})
        #     self.rf_values[cavity['objectname']].update({'pv_field_amplitude_alias': "ad1:ch6:power_remote_s.POWER"})
        #     self.rf_values[cavity['objectname']].update({'pv_phase_alias': "vm:dsp:sp_ph:phase"})
        #     for key, value in cavity['sub_elements'].items():
        #         if value['type'] == "solenoid":
        #             self.rf_values.update({key: collections.OrderedDict()})
        #             self.rf_values[key].update({'type': 'solenoid'})
        #             self.rf_values[key].update({'cavity': cavity['objectname']})
        #             self.rf_values[key].update({'field_amplitude': value['field_amplitude']})
        #             self.rf_values[key].update({'pv_suffix_alias': "SETI"})
