from .element import element

class gun(element):

    parameters = {
    'bsol_tracking':       {'value': True},
    'h_min':               {'value': 0.0001},
    'h_max':               {'value': 0.001},
    }

    def __init__(self):
        super().__init__(None)
        self.Framework_key = 'simulation'
        self.update_parameters()

#           self[gun]['bsol_tracking'] = {'value': True, 'type': 'simulation'}
            # self[gun]['h_min'] = {'value': 0.0001, 'type': 'simulation'}
            # self[gun]['h_max'] = {'value': 0.0001, 'type': 'simulation'}
