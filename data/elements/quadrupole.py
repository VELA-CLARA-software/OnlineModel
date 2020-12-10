from .element import element

class quadrupole(element):

    parameters = {
    'type':             {'key': 'objecttype'},
    'k1l':              {'key': 'k1l'},
    'pv_suffix_alias':  {'key': 'SETI'},
    }

    def __init__(self, framework):
        super().__init__(framework)
        self.Framework_key = 'generator'

        for quad in self.Framework.getElementType('quadrupole'):
            self.Framework_key = quad['objectname']
            self.update_element(key=quad['objectname'])


        # for quad in self.Framework.getElementType('quadrupole'):
        #     self.quad_values.update({quad['objectname']: collections.OrderedDict()})
        #     self.quad_values[quad['objectname']].update({'type': quad['objecttype']})
        #     self.quad_values[quad['objectname']].update({'k1l': quad['k1l']})
        #     self.quad_values[quad['objectname']].update({'pv_suffix_alias': "SETI"})
