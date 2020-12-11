from collections import OrderedDict

class element(OrderedDict):

    parameters = {
    }

    def __init__(self, framework=None):
        super().__init__()
        self.Framework = framework
        self.Framework_key = None

    def update_parameters(self, key=None, parameters=None):
        """Create key/value pairs in the dictionary based on parameters."""
        if parameters is None:
            parameters = self.parameters
        if key is not None:
            self[key] = OrderedDict()
            dic = self[key]
        else:
            dic = self
        for k, v in parameters.items():
            dic.update({k: OrderedDict()})
            if 'key' in v:
                dic[k].update({'value': self.Framework[self.Framework_key][v['key']]})
            elif 'value' in v:
                dic[k].update({'value': v['value']})
            dic[k].update({'type': self.Framework_key})

    def update_element(self, key=None):
        """Create key/value pairs in the dictionary based on parameters for magnet elements."""
        if key is not None:
            self[key] = OrderedDict()
            dic = self[key]
        else:
            dic = self
        for k, v in self.parameters.items():
            if 'key' in v:
                dic.update({k: self.Framework[self.Framework_key][v['key']]})
            elif 'value' in v:
                dic.update({k: v['value']})
