import re

class DBURT_Parser(dict):

    def __init__(self):
        super(DBURT_Parser, self).__init__()
        # set up regular expressions
        # use https://regexper.com to visualise these if required
        self.rx_dict = {
            'date_time': re.compile(r'DATE_TIME:(?P<date_time>.*);\n'),
            'keywords': re.compile(r'KEY_WORDS:(?P<keywords>.*);\n'),
            'beam_area': re.compile(r'BEAM_AREA:(?P<beam_area>.*);\n'),
            'data_start': re.compile(r'START_OF_DATA;\n'),
            'number_of_objects': re.compile(r'NUMBER_OF_OBJECTS:(?P<beam_area>.*);\n'),
            'magnet_object': re.compile(r'(?P<name>.*):(?P<status>\b(ON|OFF)\b):(?P<setI>(\d|.|-)+):(?P<readI>(\d|.|-)+);\n'),
            'end_of_data': re.compile(r'END_OF_DATA;\n'),
        }

    def _parse_line(self, line):
        """
        Do a regex search against all defined regexes and
        return the key and match result of the first matching regex

        """

        for key, rx in self.rx_dict.items():
            match = rx.search(line)
            if match:
                return key, match
        # if there are no matches
        return None, None

    def parse_DBURT(self, filename):
        """
        Parse an old-style DBURT file
        return a dictionary containing DBURT parameters
        Magnet parameters are stored in data['magnets']:
            name: Magnet name
            setI: Set current
            readI: Readback current
            status: True if ON or False if OFF

        """

        self.data = {}  # create an empty dictionary to store the data
        # open the file and read through it line by line
        with open(filename, 'r') as file_object:
            line = file_object.readline()
            while line:
                # at each line check for a match with a regex
                key, match = self._parse_line(line)
                if key == 'data_start':
                    self.data['magnets'] = {}
                elif key == 'magnet_object':
                    d = match.groupdict()
                    d['status'] = True if d['status'] == "ON" else False
                    self.data['magnets'][d['name']] = d
                elif key == 'end_of_data':
                    break
                elif key is not None and match is not None:
                    self.data[key] = match.group(1)
                line = file_object.readline()
        return self.data

if __name__ == '__main__':
   parser = DBURT_Parser()
   data = parser.parse_DBURT(r'\\fed.cclrc.ac.uk\Org\NLab\ASTeC\Projects\VELA\Snapshots\DBURT\CLARA_2_BA1_BA2_2020-03-09-1602_5.5MeV Beam Transport.dburt')
   print(data['magnets'])
