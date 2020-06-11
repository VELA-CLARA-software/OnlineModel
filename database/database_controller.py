import run_parameters_parser as yaml_parser
import database_reader 
import database_writer

class DatabaseController():

    def __init__(self, *args, **kwargs):
        self.reader = database_reader.DatabaseReader()
        self.writer = database_writer.DatabaseWriter()
        self.settings_dict = None
    ## NEED TO CHECK IF YAML_DICT HAS BEEN SET, OTHERWISE USE ARGUMENT.
    def are_settings_in_database(self, settings_to_save=None):
        if settings_to_save == None:
            if self.settings_dict != None:
                print('Checking YAML settings against database...')
                return self.reader.prepare_dict_for_checking(self.settings_dict)
            else:
                print('Supply a settings dictionary, or load yaml settings before checking database')
        else:
            print('Checking Dictionary settings against database...')
            settings_to_check = self.reader.prepare_dict_for_checking(settings_to_save)
            return self.reader.are_settings_in_database(settings_to_check)
        
    def get_run_id_for_settings(self, settings_to_save=None):   
        if settings_to_save == None:
            if self.settings_dict != None:
                print('Searching for RUN ID for YAML settings...')
                settings_to_check = self.reader.prepare_dict_for_checking(self.settings_dict)
                return self.reader.get_run_id_for_settings(settings_to_check)
            else:
                print('Supply a settings dictionary, or load yaml settings before checking database')
        else:
            print('Searching for RUN ID for Dictionary settings...')
            settings_to_check = self.reader.prepare_dict_for_checking(settings_to_save)
            return self.reader.get_run_id_for_settings(settings_to_check)
            
    def load_yaml_settings(self, yaml_filename):
        self.settings_dict = yaml_parser.parse_parameter_input_file(yaml_filename)
        
        
        
        
        
if __name__ == '__main__':
    dbc = DatabaseController()
    dbc.load_yaml_settings('scan_settings.yaml')
    if dbc.are_settings_in_database():
        print(dbc.get_run_id_for_settings())
    else:
        print('FAILURE;')
        
    dbc_2 = DatabaseController()
    settings_dict = yaml_parser.parse_parameter_input_file('scan_settings.yaml')
    if dbc_2.are_settings_in_database(settings_dict):
        print(dbc_2.get_run_id_for_settings(settings_dict))
    else:
        print('FAILURE;')