from .element import element

class linac(element):

    parameters = {
    'zwake':               {'value': True},
    'trwake':              {'value': True},
    }

    def __init__(self):
        super().__init__(None)
        self.Framework_key = 'simulation'
        self.update_parameters()