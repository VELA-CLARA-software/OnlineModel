import database.run_parameters_parser as yaml_parser
import database.database_reader as database_reader
import database.database_writer as database_writer
import database.database_creator as database_creator

class DatabaseController():

    def __init__(self):
        ### Check/Create database
        self.creator = database_creator.DatabaseCreator()
        self.creator.create_simulation_database(clean=False)
        
        self.reader = database_reader.DatabaseReader()
        self.writer = database_writer.DatabaseWriter()
        self.settings_dict = None
    ## NEED TO CHECK IF YAML_DICT HAS BEEN SET, OTHERWISE USE ARGUMENT.
    def are_settings_in_database(self, settings_to_read=None):
        if settings_to_read == None:
            if self.settings_dict != None:
                settings = self.settings_dict.copy()
                print('Checking YAML settings against database...')
                return self.reader.are_settings_in_database(settings)
            else:
                print('Supply a settings dictionary, or load yaml settings before checking database')
        else:
            settings = settings_to_read.copy()
            print('Checking Dictionary settings against database...', self.reader.are_settings_in_database(settings))
            return self.reader.are_settings_in_database(settings)

    def get_run_id_for_settings(self, settings_to_read=None):
        if settings_to_read == None:
            if self.settings_dict != None:
                settings = self.settings_dict.copy()
                print('Searching for RUN ID for YAML settings...')
                return self.reader.get_run_id_for_settings(settings)
            else:
                print('Supply a settings dictionary, or load yaml settings before checking database')
        else:
            settings = settings_to_read.copy()
            print('Searching for RUN ID for Dictionary settings...', self.reader.get_run_id_for_settings(settings))
            return self.reader.get_run_id_for_settings(settings)

    def load_yaml_settings(self, yaml_filename):
        self.settings_dict = yaml_parser.parse_parameter_input_file(yaml_filename)

    def save_settings_to_database(self, settings_to_save=None, run_id=None):
        if settings_to_save == None:
            if self.settings_dict != None:
                # settings_to_check = self.reader.prepare_dict_for_checking(self.settings_dict)
                if not self.are_settings_in_database(self.settings_dict):
                    print('Saving YAML settings...')
                    self.writer.save_dict_to_db(self.settings_dict, run_id)
            else:
                print('Supply a settings dictionary, or load yaml settings before checking database')
        else:
            if not self.are_settings_in_database(settings_to_save):
                print('Saving Dictionary settings...')
                self.writer.save_dict_to_db(settings_to_save, run_id)
                self.reader.add_to_run_id_and_settings_dict_from_database(run_id)
            # else:
            #     print('setting exist!')

    def get_all_run_ids(self):
        return self.reader.run_id_settings_dict.keys()

    def save_run_information(self, *args):
        self.writer.save_entry_to_run_table(*args)

    def clean_database(self, tables=None):
        self.creator.create_simulation_database(clean=True, tables=tables)

if __name__ == '__main__':
    dbc = DatabaseController()
    for value in range(0,1):
    #     filename = 'scan_settings_'+str(value)+'.yaml'
        filename = 'scan_settings.yaml'
        dbc.load_yaml_settings(filename)
        if dbc.are_settings_in_database():
            print(dbc.get_run_id_for_settings())
        else:
            ## May need to create a 'refresh' function to update
            ## settings dictionary when new settings have been saved.
            dbc.writer.save_dict_to_db(dbc.settings_dict)
