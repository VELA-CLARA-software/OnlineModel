import yaml
from collections import OrderedDict


def parse_parameter_input_file(filename):
    with open(filename, 'r') as stream:
        yaml_parameter_dict = yaml.safe_load(stream)
        return yaml_parameter_dict


def write_parameter_output_file(filename, parameter_dict):
    # This representer tells pyYaml to treat an OrderedDict as it would a regular dict.
    yaml.add_representer(OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
    with open(filename, 'w') as output_file:
        # default flow-style = FALSE allows us to write our python dict out
        # in the key-value mapping that is standard in YAML. If this is set
        # to true; the output looks more like JSON, so best to leave it.
        yaml.dump(parameter_dict, output_file, default_flow_style=False)
        # currently the values that are output for each key will be surrounding with ''
        # which does not matter for this purpose as everything gets put into a string
        # format anyway. It may just introduce inconsistencies between hand-written and
        # computer-generated YAML files, but we can deal with that when a problem arises.
