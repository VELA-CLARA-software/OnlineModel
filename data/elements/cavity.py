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
