import sys
import os
import re
import argparse

# <TITLE> <search name> <parse:y/n>  <commentary>
# parse if n and set the will not search but only print
# <name>.conf -> parser for cli
# option --show nb -> show contain of all fields of id

class Search:
    def __init__(self, cmd, config):
        # initialization
        self.conf_type = self.pre_parser()
        # set up attributes
        self.cmd = ' '.join(cmd)
        self.conf_dir = config['conf_dir']
        self.conf_file = self.conf_type + '.conf'
        self.conf_file_name = os.path.join(self.conf_dir, self.conf_file)
        if not os.path.isfile(self.conf_file_name):
            raise Exception('[ERROR] <name>.conf (%s) does not exist' % self.conf_file_name)
        self.history_file = self.conf_file_name + '.history'
        self.file_data = 'data.%s' % self.conf_type
        self.editor = config['editor']
        self.path_regex = config['path_regex']
        self.parser = None
        self.list_of_title = []
        self.list_of_arg = []
        self.tag_arg_list = []
        # main code
        self.argparser_generator()
        self.args = self.parser.parse_args()
        self.main()

    def pre_parser(self):
        # Parser not yet configured
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('file', help='<file>.conf, Conf file to use')
        self.parser.add_argument('OPTIONS', nargs=argparse.REMAINDER, help='<file>.conf options')
        arg = self.parser.parse_args()
        return arg.file


    def generate_parser_argument(self, line, line_nb):
        l = line.strip()
        regex = '^[\[\]\w]+[ ]+'
        regex += '[-]{1,2}[\w]+[ ]+'
        regex += '[y|n][ ]*'
        regex += '(#.*){0,1}$'
        if re.match(regex, l) is None:
            if l != '':
                raise Exception('[ERROR line %d] line should be : <TITLE> -[-]<search name> <parse:y/n>  #<commentary> or empty' %line_nb)
            return
        split = re.split(r'[ ]+', l)
        title = split[0]
        arg = split[1]
        parse = split[2]
        commentary = ' '.join(split[3:])[1:]
        if title in self.list_of_title:
            raise Exception('[ERROR line %d] title %s was already set' %(line_nb, arg))
        self.list_of_title += [title]
        if arg == '--show':
            raise Exception('[ERROR line %d] --show cannot be put as argument' %line_nb)
        if arg in self.list_of_arg:
            raise Exception('[ERROR line %d] arg %s was already set' %(line_nb, arg))
        self.list_of_arg += [arg]
        if parse == 'y':
            self.parser.add_argument(arg, nargs='+', default=None, help=commentary)
        elif parse == 'n':
            self.parser.add_argument(arg, action='store_true', help=commentary)
        else:
            raise Exception('Internal Error, parse should be y or n')
        arg = ''.join(arg.split('-'))
        self.tag_arg_list += [(title, arg)]

    def argparser_generator(self):
        # Parser not yet configured
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('file', help='<file>.conf, Conf file to use')
        self.parser.add_argument('OPTIONS', nargs=argparse.REMAINDER, help='<file>.conf options')
        arg = self.parser.parse_args()
        self.conf_type = arg.file
        if not os.path.isfile(self.conf_file_name):
            raise Exception('[ERROR] <name>.conf (%s) does not exist' % self.conf_file_name)
        # Configuration of the parser
        self.parser = argparse.ArgumentParser()
        conf = open(self.conf_file_name).readlines()
        self.list_of_arg = ['file', '--new', '--show']
        self.parser.add_argument(self.conf_type,
                help='Set %s to use configuration file %s'%(self.conf_type, self.conf_file_name))
        self.parser.add_argument('--new', action='store_true',
                help='Create new structured file')
        self.parser.add_argument('--history', action='store_true',
                help='Show result of previous research')
        self.parser.add_argument('--show' , type=int,
                help='Show the content of the file with corresponding id')
        for line_nb, line in enumerate(conf):
            self.generate_parser_argument(line, line_nb)

    def new_file(self):
        file_name = self.file_data
        if os.path.isfile(file_name):
            raise Exception('The file %s already exists' % file_name)
        f = open(file_name, 'w')
        for title in self.list_of_title:
            f.write(title)
            f.write('\n\n')
        f.close()
        os.system('%s %s' % (self.editor, file_name))

    def show_file(self, research_id):
        with open(self.history_file) as f:
            for line in f:
                regex = re.compile('^id:[ \t]*%d[ \t]+(%s)'
                        % (research_id, self.path_regex.pattern))
                file_name = re.findall(regex, line.strip())
                if len(file_name) == 1:
                    file_name = os.path.expanduser(file_name[0])
                    os.system('%s %s' % (self.editor, file_name))
                    exit(0)
        raise Exception('[ERROR] The id %d does not exists'%research_id)

    def search(self):
        if self.tag_arg_list is []:
            raise Exception('There are no arguments')
        args = vars(self.args)
        regex_list = []
        for tag, arg in self.tag_arg_list:
            if arg not in args :
                continue
            if args[arg] is None or isinstance(args[arg], bool):
                continue
            regex = ''
            regex_arg = ''
            excluded = '|'.join([x for x in self.list_of_title if x != tag])
            for a in args[arg]:
                regex_arg += '%s|' % re.escape(a)
            regex_arg = regex_arg[:-1]
            # The last separtors may be incomplet
            regex = '%s[ \n\r]((?!(%s)).)*(%s)[ ,;:\.\n\r\t]' % (re.escape(tag), excluded, regex_arg)
            regex_list += [re.compile(regex)]
        matching_files = []
        counter = 0
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if file == self.file_data:
                    file_path = os.path.join(root, file)
                    content = open(file_path).read()
                    match = map(lambda x: x.search(content) is not None, regex_list)
                    match = list(match)
                    if all(match):
                        matching_files += ['id:%3d\t%s\n' % (counter, file_path)]
                        counter += 1
        f = open(self.history_file, 'w')
        m = 'command:%s' % os.path.basename(self.cmd)
        print(m)
        f.write('%s\n' % m)
        for m in matching_files:
            print(m.strip())
            f.write(m)
        f.close()

    def main(self):
        if self.args.new:
            self.new_file()
            exit(0)
        if self.args.history:
            if os.path.isfile(self.history_file):
                print(open(self.history_file).read())
                exit(0)
            else:
                raise Exception('[INFO] No previous research')
        if self.args.show is not None:
            self.show_file(self.args.show)
        self.search()

if __name__ == '__main__':
    config = {
            'editor': 'vim',
            'conf_dir': os.path.join(os.path.expanduser('~'), '.search'),
            'path_regex': re.compile('[\w\./~\-\\\\]+') # adapt for windows
            }
    try:
        Search(sys.argv, config)
        exit(0)
    except Exception as e:
        print(e)
        exit(1)
