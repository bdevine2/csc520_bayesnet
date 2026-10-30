import re


class FileLine:

    def __init__(self, unparsed_line):
        self.raw_line = unparsed_line.strip()

    def is_node_line(self):
        # if there are uppercase letters only then it is a header line,
        # all lines with a float at the end are truth table values
        if re.fullmatch(r'[^0-9]*', self.raw_line):
            return True
        return False

    def is_end_of_object(self):
        return self.raw_line.strip() == ''

    def nodes(self):
        # get the full raw list of nodes for this class
        if self.is_node_line():
            return self.raw_line.split()
        else:
            return None
