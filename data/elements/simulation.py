from .element import element

class simulation(element):

    parameters = {
    'tracking_code':       {'value': 'elegant'},
    'csr':                 {'value': True},
    'csr_bins':            {'value': 200},
    'lsc':                 {'value': True},
    'lsc_bins':            {'value': 200},
    }

    def __init__(self):
        super().__init__(None)
        self.Framework_key = 'simulation'
        self.update_parameters()
