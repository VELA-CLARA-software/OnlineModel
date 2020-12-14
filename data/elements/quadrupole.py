from .element import element

class quadrupole(element):

    parameters = {
    'type':             {'key': 'objecttype'},
    'k1l':              {'key': 'k1l'},
    'pv_suffix_alias':  {'value': 'SETI'},
    }

    def __init__(self, framework):
        super().__init__(framework)
        self.Framework_key = 'generator'

        for quad in self.Framework.getElementType('quadrupole'):
            self.Framework_key = quad['objectname']
            self.update_element(key=quad['objectname'])
