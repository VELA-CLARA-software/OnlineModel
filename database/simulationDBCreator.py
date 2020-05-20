import sys, os, shutil, time
import sqlite3
import uuid
import time
sys.path.append(os.path.dirname(os.path.dirname( os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname( os.path.abspath(__file__))) + '../')
#import data.data as data
import run_parameters_parser as yaml_parser
import collections
import json

class Save_State():

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()
        self.machine_area_directories = dict()
        self.machine_area_directory_status = dict()
        self.re_run_from = ''
        # self.create_table('BA1')
        # self.create_table('EBT')
        # self.create_table('C2V')
        # self.create_table('generator')
        # self.create_table('INJ')
        # self.create_table('S02')
        # self.create_simulation_table()
        # self.create_scan_table()
        # self.create_runs_table()

    def tempname(self):
        return str(uuid.uuid4())

    def flatten(self, d, parent_key='', sep='£'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.abc.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def save_dict_to_db(self, found_in_db):
        ### NEEDS TO CHECK THE STATE OF RESULTS IN TABLE ###
        ### AS SOON AS AN ENTRY DOES NOT EXIST, WRITE IT TO TABLE ###
        newdict = self.flatten(self.yaml_dict)
        runno = self.tempname()
        for k,v in newdict.items():
            splitstr = k.split('£')
            table_name = splitstr[0]
            splitstr.remove(table_name)
            if(table_name != 'scan' and table_name != 'simulation'):
                print(found_in_db)
                if (found_in_db[table_name] == 'NOT FOUND'):
                    self.save_entry_to_machine_area_table(runno, table_name, splitstr, v)
                    self.save_entry_to_runs_table(runno, table_name, runno)
                else:
                    print(self.machine_area_directories[table_name])
                    if (runno != self.machine_area_directories[table_name]):
                        self.save_entry_to_runs_table(runno, table_name, self.machine_area_directories[table_name])
                    else:
                        self.save_entry_to_runs_table(runno, table_name, runno)
            elif (table_name == 'scan'):
                self.save_entry_to_scan_table(runno, splitstr, v)
            elif (table_name == 'simulation'):
                self.save_entry_to_simulation_table(runno, splitstr, v)
            else:
                print('TABLE : ', table_name, ' not found')
        self.conn.commit()

    def save_entry_to_runs_table(self, runno, area, directory):
        if (self.check_entry_in_runs_table(runno, area, directory)):
            print("NOT SAVING TO RUN TABLE")
        else:
            print("SAVING TO RUN TABLE")
            print("RUN NUMBER: ", runno, " AREA: ", area,  " DIRECTORY: ", directory)
            run_columnstring = '(runnumber, area, directory)'
            run_valuestring = '(?,?,?)'
            run_sql = '''INSERT INTO runs '''+run_columnstring+''' VALUES '''+run_valuestring
            self.cursor.execute(run_sql, [runno,area,directory])
            self.conn.commit()

    def save_entry_to_machine_area_table(self, runno, table_name, data, values):
        columnstring = '(runnumber,name,parameter,value)'
        valuestring =  '(?,' + ','.join(['?' for i in range(len(data)+1)]) + ')'
        sql = ''' INSERT INTO ''' + table_name + ''' '''+columnstring+'''
               VALUES''' + valuestring
        self.cursor.execute(sql, [runno] + data + [str(json.dumps(values))])



    def save_entry_to_scan_table(self, runno, data, values):
        columnstring = '(runnumber, name, parameter, value)'
        valuestring = '(?,?,?,?)'
        if (len(data) < 2):
            data.insert(0,None)
        sql = '''INSERT INTO scan ''' + columnstring + ''' VALUES ''' + valuestring
        self.cursor.execute(sql, [runno] + data + [str(json.dumps(values))])


    def save_entry_to_simulation_table(self, runno, data, values):
        columnstring = '(runnumber, name, parameter, value)'
        if (len(data) < 2):
            data.append(json.dumps(None))
        valuestring = '(?,' + ','.join(['?' for i in range(len(data)+1)]) + ')'
        sql = '''INSERT INTO simulation ''' + columnstring + '''VALUES''' + valuestring
        self.cursor.execute(sql, [runno] + data + [str(json.dumps(values))])
        
##### FUNCTIONS FOR CHECKING IF ENTRIES ARE IN TABLES ALREADY #####
    def check_entry_in_machine_area_table(self, table_name, data, values):
        columnstring = '(name=? AND parameter=? AND value=?)'
        valuestring =  '(?,' + ','.join(['?' for i in range(len(data)+1)]) + ')'
        sql = '''SELECT EXISTS(SELECT 1 FROM ''' + table_name +''' WHERE '''+ columnstring +''')'''
        exe_handle = self.cursor.execute(sql, data + [str(json.dumps(values))])
        result = exe_handle.fetchall()
        if (result == [(1,)]):
            return True
        else:
            print('ENTRY ', data + [str(json.dumps(values))], " NOT FOUND IN TABLE: ", table_name)
            return False

    def check_entry_in_scan_table(self, table_name, data, values):
        columnstring = '(parameter=? AND value=?)'
        valuestring = '(?,?)'
        sql = '''SELECT EXISTS(SELECT 1 FROM ''' + table_name +''' WHERE '''+ columnstring +''')'''
        exe_handle = self.cursor.execute(sql, data + [str(json.dumps(values))])
        result = exe_handle.fetchall()
        if (result == [(1,)]):
            return True
        else:
            print('ENTRY ', data + [str(json.dumps(values))], " NOT FOUND IN TABLE: ", table_name)
            return False
    
    def check_entry_in_simulation_table(self, table_name, data, values):
        if (len(data) < 2):
            columnstring = '(name=? AND value=?)'
            valuestring = '(?,?)'
        else:
            columnstring = '(name=? AND parameter=? AND value=?)'
            valuestring = '(?,?,?)'   
        sql = '''SELECT EXISTS(SELECT 1 FROM ''' + table_name +''' WHERE '''+ columnstring +''')'''
        exe_handle = self.cursor.execute(sql, data + [str(json.dumps(values))])
        result = exe_handle.fetchall()
        if(result == [(1,)]):
            return True
        else:
            print('ENTRY ', data + [str(json.dumps(values))], " NOT FOUND IN TABLE: ", table_name)
            return False
 
    def check_entry_in_runs_table(self, runno, area, directory):
        run_check_columnstring = '(runnumber=? AND area=?)'
        run_check_sql = '''SELECT directory FROM runs WHERE '''+ run_check_columnstring
        #print("SQL: ", run_check_sql, [runno,area,directory])
        exe_handle = self.cursor.execute(run_check_sql,[runno,area])
        result = exe_handle.fetchall()
        if (result):
            print('DIRECTORY NOT EQUAL TO NOT FOUND')
            if (result[0][0] == directory):
                print(result[0][0], ' ' ,directory)
                print("RUN NUMBER ALREADY EXISTS")    
                return True
        else:
            print('DIRECTORY EQUAL TO NOT FOUND')
            directory_check_columnstring = '(runnumber=? AND area=?)'
            directory_check_sql = '''SELECT directory FROM runs WHERE '''+directory_check_columnstring
            exe_handle = self.cursor.execute(directory_check_sql,[runno, area])
            directory_check_result = exe_handle.fetchall()
            if (directory_check_result):
                print("RUN NUMBER: ", runno, " USED DIRECTORY: ", directory_check_result[:][0])
                return True
            else:
                print("CANNOT FIND RUN NUMBER")
                return False
##### END OF FUNCTIONS FOR CHECKING IF ENTRIES ARE IN TABLES ALREADY #####


    def add_keys(self, d, l, c=None):
        if len(l) > 1:
            d[l[0]] = d.get(l[0], {})
            self.add_keys(d[l[0]], l[1:], c)
        else:
            d[l[0]] = c

    def read_db_to_dict(self, runno):
        data_dict = dict()
        tables = self.get_table_names_from_db()
        for t in tables:
            if t != 'runs':
                data_dict[t] = self.read_each_db_to_dict(t, runno)
        return data_dict

    def read_each_db_to_dict(self, db, runno):
        sql = '''select * from ''' + db + ''' where "runnumber" = "'''+runno+'''"'''
        exe = self.cursor.execute(sql)
        data = exe.fetchall()
        data_dict = dict()
        for l in data:
            l = [ll for ll in l if not ll == 'null']
            self.add_keys(data_dict, l[1:-1], json.loads(l[-1]))
        return data_dict

    def get_runnumbers_from_db(self):
        sql = '''select runnumber from BA1 UNION
                 select runnumber from C2V UNION
                 select runnumber from INJ UNION
                 select runnumber from S02 UNION
                 select runnumber from EBT UNION
                 select runnumber from generator UNION
                 select runnumber from simulation UNION
                 select runnumber from scan'''
        exe = self.cursor.execute(sql)
        return [a[0] for a in exe.fetchall()]

    def load_yaml_file(self, filename):
        self.yaml_dict = yaml_parser.parse_parameter_input_file(filename)
    
    def create_runs_table(self):
        sql = 'CREATE TABLE IF NOT EXISTS "runs" ( \
            runnumber TEXT,\
            area TEXT,\
            directory TEXT\
            );'
        self.cursor.execute(sql)
        sql = 'delete from runs;'
        self.cursor.execute(sql)
        self.conn.commit()
    def create_table(self, table_name):
        sql = 'CREATE TABLE IF NOT EXISTS "' + table_name +'" ( \
            runnumber TEXT,\
            name TEXT,\
            parameter TEXT,\
            value TEXT\
            );'
        
        self.cursor.execute(sql)
        sql = 'delete from ' + table_name + ';'
        self.cursor.execute(sql)
        self.conn.commit()

    def create_scan_table(self, table_name='scan'):
        sql = 'CREATE TABLE IF NOT EXISTS "'+table_name+'"(\
        runnumber TEXT,\
        name TEXT,\
        parameter TEXT,\
        value TEXT\
        );'        
        self.cursor.execute(sql)
        sql = 'delete from ' + table_name + ';'
        self.cursor.execute(sql)
        self.conn.commit()

    def create_simulation_table(self, table_name='simulation'):
        sql = 'CREATE TABLE IF NOT EXISTS "'+table_name+'"(\
        runnumber TEXT,\
        name TEXT,\
        parameter TEXT,\
        value TEXT\
        );'
        self.cursor.execute(sql)
        sql = 'delete from ' + table_name + ';'
        self.cursor.execute(sql)
        self.conn.commit()

    def pretty(self, d, indent=0):
       for key, value in d.items():
          print('  ' * indent + str(key))
          if isinstance(value, dict):
             self.pretty(value, indent+1)
          else:
             print('  ' * (indent+1) + str(value))

    def get_table_names_from_db(self):
        sql = 'SELECT name FROM sqlite_master WHERE type="table" ORDER BY name'
        exe = self.cursor.execute(sql)
        result = exe.fetchall()
        db = [r[0] for r in result]
        return db

    def get_results_directory_for_runnumbers(self):
        ### NEED TO CHAIN TOGETHER THESE WITH ANDS.
        results_directory = ''
        sql_commands = list()
        for area, runnumber in self.machine_area_directories.items():
           query_string = '(directory=\''+runnumber+'\' AND area=\''+area+'\')'
           sql = '''SELECT runnumber FROM runs WHERE '''+query_string + ''' INTERSECT '''
           sql_commands.append(sql)
        sql_select_directories = '''SELECT * FROM ('''
        for command in sql_commands:
            sql_select_directories += command
        sql_select_directories = sql_select_directories.rsplit('INTERSECT',1)[0]
        sql_select_directories += ''')'''
        exe_handle = self.conn.execute(sql_select_directories)
        result = exe_handle.fetchall()
        if (not result):
           results_directory = 'NOT FOUND'
        if (len(result[0]) > 1):
            print("FOUND MORE THAN ONE DIRECTORY")
            print(result[0][:])
        else:
           results_directory = result[0][0]
        return results_directory
    
    def get_runnumber_for_machine_area_settings(self, area):
        area_entries = self.yaml_dict[area]
        area_settings_dict = self.flatten(area_entries)
        run_number_for_settings = ""
        sql_commands = list()
        for k,values in  area_settings_dict.items():
            splitstr = k.split('£')
            query_string = '(name=\''+splitstr[0]+'\' AND parameter=\''+splitstr[1]+'\' AND value=\''+str(json.dumps(values))+'\')'
            sql = '''SELECT runnumber FROM '''+area+''' WHERE '''+query_string+''' INTERSECT '''
            sql_commands.append(sql)
        sql_select_runnumbers = '''SELECT * FROM ('''
        for command in sql_commands:
            sql_select_runnumbers += command
        #remove last INTERSECT appended to sql command.
        sql_select_runnumbers = sql_select_runnumbers.rsplit('INTERSECT',1)[0]
        sql_select_runnumbers += ''')'''
        exe_handle = self.conn.execute(sql_select_runnumbers)
        result = exe_handle.fetchall()
        if (not result):
            print("RESULT EMPTY")
            # We could not find settings in the database for this section of the machine
            return({area: "NOT FOUND"})
        else:
            # We found settings in the database for this section, return the run-number.
            if (len(result) > 1):
                # Here we got more than one result for the settings, need to return the one consistent with last result
                directories_list = list(self.machine_area_directories.values())
                # get last directory value (-1)
                last_directory_found = directories_list[-1]
                dir_in_result=""
                directories_found = [entry[-1] for entry in result if entry[-1] == last_directory_found]
                print('Directories found for ',area,' are: ', directories_found)
                if (directories_found):
                    dir_in_result = directories_found[0]
                    print('Chosen Directory: ', dir_in_result)
                else:
                    # result > 1, but no directory in result matched the last directory we added
                    # This means that we could not find any results that are consistent with the settings
                    # of the last directory we added to machine_area_directories.
                    print("COULD NOT FIND: ", last_directory_found, " IN ", result[:][0])
                    dir_in_result = "NOT FOUND"
                # return result consistent with last_directory_found
                return({area : dir_in_result})
            else:
                # We only found one result, so we just return it
                # using extra index to only get directory value from tuple
                print('Directories found for ',area,' are: ', result[:][0])
                return({area:result[0][0]})
    
    def get_areas_before(self, area):
        area_list = ["generator", "INJ", "S02", "C2V", "EBT", "BA1"]
        area_index = area_list.index(area)
        area_check_list = area_list[0:area_index]
        return area_check_list
    def get_areas(self):
        return ["generator", "INJ", "S02", "C2V", "EBT", "BA1"]

    def check_for_full_run_settings(self, areas):
        if (not areas):
            return True
        else:
            checking_areas = self.get_areas_before(areas[-1])
            if (checking_areas):
                if (self.machine_area_directories[areas[-1]] == 'NOT FOUND'):
                    print(areas[-1], " DIRECTORY NOT FOUND")
                    self.machine_area_directory_status[areas[-1]] = False
                if (self.machine_area_directories[checking_areas[-1]] == 'NOT FOUND'):
                    print(checking_areas[-1], " DIRECTORY NOT FOUND")
                    self.machine_area_directory_status[checking_areas[-1]] = False
                elif (self.machine_area_directories[areas[-1]] != self.machine_area_directories[checking_areas[-1]]):
                    print (areas[-1], " USED DIFFERENT ", checking_areas[-1])
                    print ("SEARCH FOR ", checking_areas[-1], " WITH RUN NUMBER ",self.machine_area_directories[areas[-1]]," AND DIRECTORY ", self.machine_area_directories[checking_areas[-1]])
                    sql = '''SELECT EXISTS(SELECT 1 FROM runs WHERE(runnumber=? AND area=? AND directory=?));'''
                    search_area = checking_areas[-1]
                    search_runnumber = self.machine_area_directories[areas[-1]]
                    search_directory = self.machine_area_directories[checking_areas[-1]]
                    exe_handle = self.conn.execute(sql, [search_runnumber, search_area, search_directory])
                    found_entry = exe_handle.fetchall()
                    if (found_entry == [(1,)]):
                        print("RUN OKAY")
                        self.machine_area_directory_status[checking_areas[-1]] = True
                        self.machine_area_directory_status[areas[-1]] = True
                    else:
                        print(checking_areas[-1], self.machine_area_directories[checking_areas[-1]])
                        self.machine_area_directory_status[checking_areas[-1]] = False
                else:
                    print (areas[-1], " USED SAME ", checking_areas[-1])
                    self.machine_area_directory_status[areas[-1]] = True
                    self.machine_area_directory_status[checking_areas[-1]] = True
                self.check_for_full_run_settings(checking_areas)
            else:
                print("END OF LINE")
    
    def need_to_save(self):
        need_to_save = False
        for area, directory in state.machine_area_directories.items():
            if directory == 'NOT FOUND':
                need_to_save = True
                break
        return need_to_save

    def update_machine_area_directories(self):
        self.machine_area_directories.clear()
        areas = self.get_areas()
        for area in areas:
            self.machine_area_directories.update(self.get_runnumber_for_machine_area_settings(area))
        return self.machine_area_directories

    def get_area_to_re_run_from(self):
        for area, status in state.machine_area_directory_status.items():
            if not status:
                state.re_run_from = area
                break
        return state.re_run_from
if __name__ == '__main__':
    state = Save_State()
    start = time.time()
    state.load_yaml_file('settings_5.yaml')
    print('Time to load YAML: ', time.time() - start)
    state.update_machine_area_directories()
    state.check_for_full_run_settings(state.get_areas())
    if state.get_area_to_re_run_from() != '':
        print("-------- RE RUN FROM: ", state.re_run_from," ------------")
        if state.need_to_save():
            print("SAVING NEW RUN TO TABLES")
            state.save_dict_to_db(state.machine_area_directories)
    else:
        print("-----NO RERUN NEEDED-----")
        print("RESULTS CAN BE FOUND IN DIRECTORY: ", state.get_results_directory_for_runnumbers())
    settings = dict()
    for directory in state.machine_area_directories.values():
        settings.update(state.read_db_to_dict(directory))
    state.pretty(settings)

