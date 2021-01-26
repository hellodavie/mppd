import argparse
import re
import operator
from shutil import copy2
from sys import stderr
from textwrap import dedent

__version__ = '1.1.0'
__description__ = 'A formatter and preprocessor for MIPS assembly.'
__copyright__ = 'Copyright (c) 2020 David Wu and Eric Holmstrom'

IDENTIFIER_REGEX = r"%\w+"
IDENTIFIER_ARG_REGEX = r"%\w+(\.\w+)?"
LABELS_REGEX = r"^\w*:"

NUM_TABS_AFTER_INSTRUCTION = 2
NUM_TABS_BEFORE_COMMENT = 8

CEND = '\33[0m'
CBLACK = '\33[30m'
CRED = '\33[31m'
CGREEN = '\33[32m'
CYELLOW = '\33[33m'
CBLUE = '\33[34m'
CVIOLET = '\33[35m'
CBEIGE = '\33[36m'
CGREY = '\33[90m'

LOG_PRETTIFY_PREFIX = CBLUE + '[PRETTIFY]' + CEND


def log_error(err):
    print(CRED + 'error:' + CEND + ' ' + err, file=stderr)


class MipsProcessor:

    def __init__(self, args):
        self.__args = args

    @staticmethod
    def append_filename_suffix(filename, suffix):
        path_parts = filename.rpartition('.')
        return path_parts[0] + suffix + path_parts[1] + path_parts[2]

    @staticmethod
    def align_tabs(length, maximum):
        return '\t' * max(1, maximum - length // 4)

    def fix_instruction_part_spacing(self, i):
        s = i.split("\t")
        parts = []
        for a in s:
            if len(a.strip()) > 0:
                parts.append(a.strip())
        if self.__args.verbose: print(parts)
        if len(parts) != 2: return i
        return (" " * 4) + parts[0] + (" " * (10 - len(parts[0])) + parts[1])

    def fix_comment_spacing(self, text):
        result = ""
        lines = text.split("\n")
        lineNum = 0
        for l in lines:
            if "\t" in l:
                splitted = l.split("\t")
                t_count = len(splitted)
                if self.__args.verbose == 2: print(lineNum, 'splitted', splitted)
                if t_count > 2:
                    s = l.split("# ")

                    p_0 = s[0].rstrip()
                    p_0 = self.fix_instruction_part_spacing(p_0)

                    # Fix command comment split
                    if len(s) == 2:
                        l = p_0 + (" " * (52 - len(p_0))) + "# " + s[1]
                    elif len(s) == 1:
                        l = p_0

                # Provide linting feedback
                elif t_count > 1:
                    if l[-1] != '#' and splitted[0] != '#' and len(splitted[1].split(" ")[0]) == 3:
                        print(CRED + "Line {}: there is no tab between the instruction and arguments.".format(lineNum))
                        print(CGREY + l.strip())
                        print(CEND)

                    # print(repr(l), len(s[0]))
            result += l + "\n"
            lineNum += 1
        return result

    def prettify(self):
        # Instructions without a comma in signature
        include_instructions = ('jal', 'jr', 'b')

        if self.__args.replace:
            path_backup = self.__args.file + '.bak'
            copy2(self.__args.file, path_backup)
            path_out = self.__args.file
        else:
            path_backup = self.__args.file
            path_out = self.append_filename_suffix(self.__args.file, '.pretty')

        file_input = open(path_backup, 'r')
        outfile = open(path_out, 'w')
        lines_changed = 0
        out_buffer = ''

        print(LOG_PRETTIFY_PREFIX)

        for line_num, line in enumerate(file_input, start=1):
            line = line.rstrip()
            line_parts = line.partition('#')
            stripped = line_parts[0].lstrip()

            # If line starts with a tab or four spaces
            is_indented: bool = line and (line[0] == '\t' or (len(line) > 4 and line[:3].isspace()))

            # Handle lines with instructions
            if (is_indented and stripped and stripped[0] != '#' and
                    (',' in line or any(stripped.startswith(x) for x in include_instructions))):

                split = stripped.split()
                if self.__args.verbose:
                    print('split', split)
                line_out = "\t"

                line_out += split[0]
                instruction_len = len(split[0])
                # Add whitespace after instruction code
                if (1 < instruction_len <= 4) or split[0] in include_instructions:
                    line_out += self.align_tabs(instruction_len, NUM_TABS_AFTER_INSTRUCTION)

                # Add arguments
                length = len(split)
                len_args = 0
                for i in range(1, length):
                    # Insert space after commas
                    comma_pos = split[i].find(',')
                    if 0 <= comma_pos < len(split[i]) - 1:
                        split[i] = ', '.join(split[i].split(',')).rstrip()

                    line_out += split[i]
                    len_args += len(split[i])

                    if i != length - 1:
                        line_out += ' '
                        len_args += 1

                # If line has comment
                if line_parts[1]:
                    line_out += self.align_tabs(len_args, NUM_TABS_BEFORE_COMMENT)
                    line_out += line_parts[1] + ' ' + line_parts[2].lstrip()

                if self.__args.verbose or line_out != line:
                    print(CGREY + "Line " + str(line_num) + ": " + CEND + line)
                    print(CVIOLET + "Line " + str(line_num) + ": " + CEND + line_out)
                    lines_changed += 1
            else:
                line_out = line

            if self.__args.space:
                out_buffer += line_out + '\n'
            else:
                outfile.write(line_out + '\n')

        if self.__args.space:
            outfile.write(self.fix_comment_spacing(out_buffer))

        outfile.close()
        file_input.close()

        print("{} lines were reformatted.".format(lines_changed))
        print("Prettified output written to '{}'".format(path_out))
        if self.__args.replace:
            print("Backup written to '{}'".format(path_backup))
        print()
        return path_out

    # Preprocessor functions
    @staticmethod
    def first_startswith(strings, substring):
        return next((i for i, string in enumerate(strings) if string.startswith(substring)), -1)

    def create_identifiers_mapping(self, text):
        available_registers = ["$t{}".format(i) for i in range(10)]
        available_registers.extend("$s{}".format(i) for i in range(10))
        identifiers = {}
        identifiersFlags = {}
        matches = re.finditer(IDENTIFIER_ARG_REGEX, text, re.MULTILINE)

        if self.__args.verbose: idents = set()

        for matchNum, match in enumerate(matches, start=1):
            identifier = match.group()
            match_start = match.start()
            new_line_start_pos = match.string[:match_start].rfind('\n')
            if new_line_start_pos > 0:
                if '#' in match.string[new_line_start_pos:match_start]:
                    continue

            if '.' in identifier:
                identifier_trim, _, flag = identifier.rpartition('.')
                identifiersFlags[identifier] = identifier_trim
                identifier = identifier_trim
                print("Identifier '{}' has flag '{}'".format(identifier, flag))

                if identifier in identifiers:
                    print(CRED + 'Identifier {} declared before flag {}'.format(identifier, flag) + CEND)
                else:
                    ident_index = self.first_startswith(available_registers, '$s')
                    if ident_index != -1:
                        identifiers[identifier] = available_registers[ident_index]
                        available_registers.pop(ident_index)
                    else:
                        print(CRED + 'Identifier {} exceeded available $s registers'.format(identifier) + CEND)
                continue

            if self.__args.verbose: idents.add(identifier)

            if identifier not in identifiers:
                identifiers[identifier] = available_registers[0]
                available_registers.pop(0)

        if self.__args.verbose: print(len(idents), idents)

        return identifiers, identifiersFlags

    @staticmethod
    def perform_replacements(text, identifiers):
        for i, r in sorted(identifiers.items(), key=lambda k: len(k[0]), reverse=True):
            text = text.replace(i, r)
        return text

    @staticmethod
    def extract_labels(text):
        labels = []
        matches = re.finditer(LABELS_REGEX, text, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            labels.append(match.group())
        return labels

    def process(self):
        if not self.__args.output:
            self.__args.output = self.append_filename_suffix(self.__args.file, '.out')

        # Run prettify
        if self.__args.prettify or self.__args.prettify_only:
            outfile_name = self.prettify()
            if self.__args.prettify_only:
                exit()
            elif outfile_name:
                self.__args.file = outfile_name
            else:
                exit(1)

        available_registers = ["$t{}".format(i) for i in range(10)]
        # available_registers.extend("$s{}".format(i) for i in range(10))

        # Open file
        text = open(self.__args.file, "r").read()
        lines = text.split("\n")

        # Read all labels
        labels = self.extract_labels(text)
        if self.__args.verbose: print(labels)

        # Default function names
        function_names_set = {"main", "run_generation", "print_generation"}

        # Add extra functions from arguments
        if self.__args.extra_functions:
            function_names_set.update([x.strip() for x in self.__args.extra_functions])

        # Get function names in order
        function_names = []
        for label in labels:
            label = label[:-1]
            if label in function_names_set:
                function_names.append(label)

        if self.__args.verbose:
            print('functions', function_names)

        functions = dict(zip(function_names, [[] for x in range(len(function_names))]))

        functions_found = 0
        current_function = None

        pre_text = ""

        for l in lines:
            l = l + "\n"
            if functions_found < len(function_names) and l.startswith(function_names[functions_found]):
                current_function = function_names[functions_found]
                functions_found += 1
                functions[current_function].append(l)
            elif current_function is not None:
                functions[current_function][0] += l
            else:
                pre_text += l

        result_text = ""

        if self.__args.verbose: print(functions.keys())

        for functionName in function_names:
            print(CGREEN + functionName + CEND)
            f_text = functions[functionName]
            f_text = f_text[0]
            identifiers, identifiersFlags = self.create_identifiers_mapping(f_text)
            comment = ""

            if self.__args.identifiers:
                print(CGREY + 'Identifiers ' + CEND + ' '.join(identifiers.keys()))
                print(CGREY + 'Registers   ' + CEND + ' '.join(identifiers.values()))
                print(CGREY + 'Sorted      ' + CEND + ' '.join(sorted(identifiers.values())))
                print()

            FUNCTION_DOCS_INDENT = 8

            if self.__args.locals or self.__args.docs:
                VARS_HEADING_INDENT = 12
                LOCALS_HEADING = 'Locals:'
                LOCALS_BULLET = '- '
                FRAME_REGISTERS = ('fp', 'ra', 'sp')
                FRAME_REGISTERS = ('$' + x for x in FRAME_REGISTERS)

                headingPrefix = '<' + str(VARS_HEADING_INDENT)

                # Frame
                allSavedIdents = ["$s" + str(i) for i in range(10)]
                savedIdents = [x for x in allSavedIdents if (x in identifiers.values() or x in f_text)]

                frameIdents = savedIdents[:]
                frameIdents.extend(x for x in FRAME_REGISTERS if (x in identifiers.values() or x in f_text))
                comment += format('Frame: ', headingPrefix)
                comment += ', '.join(sorted(frameIdents))
                comment += '\n'

                # Uses
                usedIdents = ["$t" + str(i) for i in range(10)]
                usedIdents.extend("$a" + str(i) for i in range(10))
                usedIdents = [x for x in usedIdents if (x in identifiers.values() or x in f_text)]
                usedIdents.extend(savedIdents)
                savedIdents = None
                comment += format('Uses: ', headingPrefix)
                comment += ', '.join(sorted(usedIdents))
                comment += '\n'

                # Clobbers
                CLOBBERS_HEADING = 'Clobbers:'
                clobbers = set(usedIdents).difference(frameIdents, allSavedIdents)
                comment += format(CLOBBERS_HEADING, headingPrefix)
                comment += ', '.join(sorted(clobbers))
                comment += '\n'

                # Locals
                if identifiers:
                    comment += '\n'
                    comment += LOCALS_HEADING + '\n'
                    localsFormat = '{:>' + str(FUNCTION_DOCS_INDENT) + "}"
                    localsFormat += "'{}' in {}"
                    for key, value in sorted(identifiers.items(), key=operator.itemgetter(1)):
                        comment += localsFormat.format(LOCALS_BULLET, key[1:], value)
                        comment += '\n'

            if self.__args.structure:
                # Structure
                STRUCTURE_HEADING = 'Structure:'
                STRUCTURE_BULLET = '- '

                found_start = False
                structureFormat = '{:>' + str(FUNCTION_DOCS_INDENT) + "}"
                structureFormat += "{}"
                comment += '\n'
                comment += STRUCTURE_HEADING + '\n'
                for label in labels:
                    label = label[:-1]
                    if found_start:
                        if label in function_names:
                            break
                        else:
                            comment += structureFormat.format(STRUCTURE_BULLET, label)
                            comment += '\n'
                    elif label == functionName:
                        found_start = True

            if comment:
                print(comment)

            # Perform pre-processing
            f_text = self.perform_replacements(f_text, identifiersFlags)
            f_text = self.perform_replacements(f_text, identifiers)

            if self.__args.docs:
                # Write documentation to output
                # Comment header
                max_length = -1
                for l in comment.split("\n"):
                    max_length = max_length if len(l) < max_length else len(l)
                result_text += "#" * (max_length + 4) + "\n"
                comment = functionName + "\n\n" + comment

                for cLine in comment.splitlines():
                    result_text += ('# ' if len(cLine) else '') + cLine + '\n'

            result_text += f_text

        # text = perform_replacements(text, identifiers)

        # r = fix_comment_spacing(result_text)
        # print(r)
        with open(self.__args.output, "w") as f:
            f.write(self.fix_comment_spacing(pre_text + result_text))
        print("\nOutput written to '{}'".format(self.__args.output))


def get_arg_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent('''\
            examples:
              $ mppd code.s
              $ mppd code.s -l
              $ mppd code.s --prettify --replace
              $ mppd code.s --function min --function max
              $ mppd code.s -p -r -l -d -s
            '''),
        description=__description__
    )

    parser.add_argument("file", help="Input filename of assembly code", nargs='?')
    parser.add_argument("-o", "--out", dest="output",
                        help="Output filename", metavar="OUT")

    parser.add_argument("-v", "--version", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-V", "--verbose", type=int, nargs='?', const=1,
                        help="Logging level 1-2, defaults to 1 if no LEVEL supplied",
                        metavar="LEVEL")
    # parser.add_argument("-q", "--quiet", action="store_true", help=argparse.SUPPRESS)

    parser.add_argument("-p", "--prettify", action="store_true",
                        help="Reformat assembly code")
    parser.add_argument("-P", "--prettify-only", action="store_true", dest="prettify_only",
                        help="Skip pre-processing")
    parser.add_argument("-r", "--replace", action="store_true",
                        help="In-place prettify, replace input file")
    parser.add_argument("-S", "--space", action="store_true",
                        help="Uses spaces instead of tabs for prettifying")

    parser.add_argument("-f", "--add-function", action="append", dest="extra_functions",
                        help="Append function to list of functions to process", metavar="LABEL")

    parser.add_argument("-i", "--identifiers", action="store_true",
                        help="Show identifiers and registers lists")
    parser.add_argument("-l", "--locals", action="store_true",
                        help="Show identifiers and associated registers")

    parser.add_argument("-d", "--docs", action="store_true",
                        help="Write generated documentation to output")
    parser.add_argument("-s", "--structure", action="store_true",
                        help="Include label structures in documentation")

    return parser


def main():
    parser = get_arg_parser()
    args = parser.parse_args()

    # Normalise arguments
    if args.version:
        print('v' + __version__)
        exit()

    print(__description__ + '\n' + __copyright__ + '\n')

    if args.verbose:
        print('Args', args)

    if not args.file:
        parser.print_usage(stderr)
        log_error('no input file specified')
        exit(1)

    processor = MipsProcessor(args)
    processor.process()


if __name__ == '__main__':
    main()
