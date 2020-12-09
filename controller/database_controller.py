import sys, os, time
import database.run_parameters_parser as yaml_parser
import database.database_reader as database_reader
import database.database_writer as database_writer
import database.database_creator as database_creator

class DatabaseController():
    """Top-level controller for DB operations."""

    def __init__(self, database='SimulationDatabase.db', verbose=True):
        self.database = database
        self.verbose = verbose
        ### Check/Create database
        self.change_database(self.database)
        self.settings_dict = None

    def change_database(self, database=None):
        """Change the database and re-initialise the reader and writer objects."""
        self.database = database
        self.creator = database_creator.DatabaseCreator(self.database)
        self.creator.create_simulation_database(clean=False)
        self.reader = database_reader.DatabaseReader(self.database, verbose=self.verbose)
        self.writer = database_writer.DatabaseWriter(self.database)

    ## NEED TO CHECK IF YAML_DICT HAS BEEN SET, OTHERWISE USE ARGUMENT.
    def are_settings_in_database(self, settings_to_read=None):
        """Check wether the YAML exists in the DB."""
        # I'm not sure we need this top bit??
        if settings_to_read == None:
            if self.settings_dict != None:
                settings = self.settings_dict.copy()
                print('Checking YAML settings against database...')
                return self.reader.are_settings_in_database(settings)
            else:
                print('Supply a settings dictionary, or load yaml settings before checking database')
        else:
            # We make a copy because we don't want to overwrite anything in the original YAML (this might not be needed anymore?)
            settings = settings_to_read.copy()
            return self.reader.are_settings_in_database(settings)

    def get_run_id_for_settings(self, settings_to_read=None):
        """Return the run_id of an existing run."""
        # I'm not sure we need this top bit??
        if settings_to_read == None:
            if self.settings_dict != None:
                settings = self.settings_dict.copy()
                print('Searching for RUN ID for YAML settings...')
                return self.reader.get_run_id_for_settings(settings)
            else:
                print('Supply a settings dictionary, or load yaml settings before checking database')
        else:
            # We make a copy because we don't want to overwrite anything in the original YAML (this might not be needed anymore?)
            settings = settings_to_read.copy()
            return self.reader.get_run_id_for_settings(settings)

    def save_settings_to_database(self, settings_to_save=None, run_id=None):
        """Save the settings YAML file to the DB."""
        # I'm not sure we need this top bit??
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
                # Settings don't exist, but we only want to save the settings that are not duplicates, so find them
                __, lattices_to_be_saved = self.reader.find_lattices_that_dont_exist(settings_to_save)
                # lattices_to_be_saved list all of the *new* lattices
                self.writer.save_dict_to_db(settings_to_save, run_id, lattices=lattices_to_be_saved)
                # We also need to save entries to the run table
                self.reader.add_to_run_id_and_settings_dict_from_database(run_id)
            # elif 'scan' in settings_to_save and settings_to_save['scan']['parameter_scan']:
                # If we run a scan, but a settings exists, we still need to add it to the scans table, so we can join all of the scan files up
                # Some of the directories will be common but we will be unique in the parameter and the start/stop/step/value parameters
                # self.save_scan_information(run_id, **settings_to_save['scan'])

    def get_all_run_ids(self):
        """Return all run IDs."""
        return self.reader.get_all_run_ids()

    def get_all_run_timestamps(self):
        """Return all run timestamps."""
        return self.reader.get_all_run_timestamps()

    def save_scan_information(self, *args, **kwargs):
        """Save scan information to the DB."""
        self.writer.save_entry_to_scan_table(*args, **kwargs)

    def save_run_information(self, *args):
        """Save run information to the DB."""
        self.writer.save_entry_to_run_table(*args)

    def clean_database(self, tables=None):
        """Clean the DB."""
        self.creator.create_simulation_database(clean=True, tables=tables)

    def delete_run_id_from_database(self, run_id):
        """Delete a run from the DB."""
        print('Attempting to delete', run_id,'from the DB!')
        self.writer.delete_run_id(run_id)
        self.reader.delete_run_id_from_settings_dict(run_id)

    def find_run_id_for_each_lattice(self, run_id=''):
        """Return the run IDs for each lattice of a run."""
        return self.reader.get_run_id_for_each_lattice(run_id)

if __name__ == '__main__':
    dbc = DatabaseController()
    run_ids = list(dbc.get_all_run_ids())
    print(dbc.find_run_id_for_each_lattice(run_ids[1]))
