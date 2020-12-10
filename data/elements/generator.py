from .element import element

class generator(element):

    parameters = {
    # Space Charge On/Off
    'space_charge':                 {'value': 'True'},
    # Cathode On/Off
    'cathode':                      {'key': 'cathode'},
    # Number of particles
    'number_of_particles':          {'value': 4},
    # Charge Parameters
    'charge':                       {'key': 'charge'},
    'pv_root_alias':                {'value': 'CLA-S01-DIA-WCM-01'},
    'pv_suffix_alias':              {'value': 'Q'},
    # Laser parameters
    'transverse_distribution':      {'key': 'distribution_type_x'},
    'transverse_cutoff':            {'key': 'guassian_cutoff_x'},
    'longitudinal_distribution':    {'key': 'distribution_type_z'},
    'longitudinal_cutoff':          {'key': 'guassian_cutoff_z'},
    'sig_x':                        {'key': 'sigma_x'},
    'spot_size':                    {'key': 'sigma_x'},
    'sig_clock':                    {'key': 'sigma_t'},
    'offset_x':                     {'key': 'offset_x'},
    'offset_y':                     {'key': 'offset_y'},
    'plateau_rise_time':            {'value': 0},
    'thermal_emittance':            {'key': 'thermal_emittance'},
    'tracking_code':                {'value': 'ASTRA'},
    }

    def __init__(self, framework):
        super().__init__(framework)
        self.Framework_key = 'generator'
        self.update_parameters()
