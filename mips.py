from argparse import ArgumentParser
import re
from shutil import copy2
import operator

parser = ArgumentParser()
parser.add_argument("file", help="input readable assembly code from FILE", nargs='?',
                    default="readable.s")
parser.add_argument("-o", "--out", dest="output",
                    help="write output to FILE", metavar="FILE",
                    default="cellular.s")
parser.add_argument("-V", "--verbose", type=int, nargs='?', const=1, help="logging level from 1 to 2, defaults if no number is supplied")

parser.add_argument("-p", "--prettify", action="store_true")
parser.add_argument("-P", "--prettify-only", action="store_true", dest="prettify_only")
parser.add_argument("-r", "--replace", action="store_true", help="in-place prettifier, replace input file")

parser.add_argument("-s", "--structure", action="store_true", help="show label structures of functions")
parser.add_argument("-i", "--identifiers", action="store_true", help="show identifiers and associated registers")
parser.add_argument("--locals", action="store_true", help="show identifiers and associated registers")
parser.add_argument("--docs", action="store_true", help="include auto-generated documentation")
args = parser.parse_args()
if args.verbose: print('Args', args)

identifier_regex = r"%\w+"
identifier_arg_regex = r"%\w+(\.\w+)?"
labels_regex = r"^\w*:"

CEND    = '\33[0m'
CBLACK  = '\33[30m'
CRED    = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW = '\33[33m'
CBLUE   = '\33[34m'
CVIOLET = '\33[35m'
CBEIGE  = '\33[36m'
CGREY   = '\33[90m'

NUM_TABS_AFTER_INSTRUCTION = 2
NUM_TABS_BEFORE_COMMENT = 8

def tabs(l, maximum):
    return ('\t' * max(1, maximum - l // 4))

def prettify():
    if args.replace:
        backupfile = args.file + '.bak'
        copy2(args.file, backupfile)
        outfileName = args.file
    else:
        backupfile = args.file
        filenameParts = args.file.rpartition('.')
        outfileName = filenameParts[0] + '.pretty' + filenameParts[1] + filenameParts[2]

    # Instructions without a comma in signature
    includeInstructions = ('jal', 'jr', 'b')

    with open(backupfile, 'r') as f:
        outfile = open(outfileName, 'w')
        lineNum = 1
        linesChanged = 0

        for line in f:
            line = line.rstrip()
            lineParts = line.partition('#')
            stripped = lineParts[0].lstrip()

            # If line starts with a tab or four spaces
            isIndented = False
            if line:
                if line[0] == '\t':
                    isIndented = True
                else:
                    if args.verbose == 2: print(line[:3] == '    ', line[:4])
                    if len(line) > 4 and line[:3].isspace():
                        isIndented = True

            # Handle lines with instructions
            if (isIndented and stripped and stripped[0] != '#' and 
                (',' in line or any(stripped.startswith(x) for x in includeInstructions))):

                splitted = stripped.split()
                if args.verbose: print(splitted)
                lineOut = "\t"

                instructionLen = len(splitted[0]) 
                if (instructionLen > 1 and instructionLen <= 4) or splitted[0] in includeInstructions:
                    lineOut += splitted[0] + tabs(instructionLen, NUM_TABS_AFTER_INSTRUCTION)

                length = len(splitted)
                lenArgs = 0
                for i in range(1, length):
                    if splitted[i] == '#':
                        break

                    # Insert space after commas
                    commaPos = splitted[i].find(',')
                    if commaPos < len(splitted[i]) - 1:
                        splitted[i] = ', '.join(splitted[i].split(',')).rstrip()

                    lineOut += splitted[i]
                    lenArgs += len(splitted[i])

                    if i != length - 1:
                        lineOut += ' '
                        lenArgs += 1

                # If line has comment
                if lineParts[1]:
                    lineOut += tabs(lenArgs, NUM_TABS_BEFORE_COMMENT)
                    lineOut += lineParts[1] + ' ' + lineParts[2].lstrip()

                if args.verbose: print(lineOut)
                if args.verbose or lineOut != line:
                    print(CGREY + "Line " + str(lineNum) + ": " + CEND + line)
                    print(CVIOLET + "Line " + str(lineNum) + ": " + CEND + lineOut)
                    linesChanged += 1
            else:
                lineOut = line

            outfile.write(lineOut + '\n')
            lineNum += 1

        outfile.close()
        print("{} lines were changed.".format(linesChanged))
        print("Output written to '{}'".format(outfileName))
        if args.replace: print("Backup written to '{}'".format(backupfile))
        return outfileName

if args.prettify or args.prettify_only:
    outfileName = prettify()
    if args.prettify_only: 
        exit()
    elif outfileName:
        args.file = outfileName
    else:
        exit(1)


def fix_instruction_part_spacing(i):
    s = i.split("\t")
    parts = []
    for a in s:
        if len(a.strip()) > 0:
            parts.append(a.strip())
    if args.verbose: print(parts)
    if len(parts) != 2: return i
    return (" " * 4) + parts[0] + (" " * (10 - len(parts[0])) + parts[1])


def fix_comment_spacing(text):
    result = ""
    lines = text.split("\n")
    lineNum = 0
    for l in lines:
        if "\t" in l:
            splitted = l.split("\t")
            t_count = len(splitted)
            if args.verbose == 2: print(lineNum, 'splitted', splitted)
            if t_count > 2:
                s = l.split("# ")

                p_0 = s[0].rstrip()
                p_0 = fix_instruction_part_spacing(p_0)

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
    
def first_startswith(strings, substring):
    return next((i for i, string in enumerate(strings) if string.startswith(substring)), -1)

def create_identifiers_mapping(text):
    available_registers = ["$t{}".format(i) for i in range(10)]
    available_registers.extend("$s{}".format(i) for i in range(10))
    identifiers = {}
    identifiersFlags = {}
    matches = re.finditer(identifier_arg_regex, text, re.MULTILINE)

    if args.verbose: idents = set()

    for matchNum, match in enumerate(matches, start=1):
        identifier = match.group()
        matchStart = match.start()
        newLineStartPos = match.string[:matchStart].rfind('\n')
        if newLineStartPos > 0:
            if '#' in match.string[newLineStartPos:matchStart]:
                continue

        if '.' in identifier:
            identifierTrim, _, flag = identifier.partition('.')
            identifiersFlags[identifier] = identifierTrim
            identifier = identifierTrim
            print('Identifier {} has flag {}'.format(identifier, flag))

            if identifier in identifiers:
                print(CRED+'Identifier {} declared before flag {}'.format(identifier, flag) + CEND)
            else:
                identIndex = first_startswith(available_registers, '$s')
                if identIndex != -1:
                    identifiers[identifier] = available_registers[identIndex]
                    available_registers.pop(identIndex)
                else:
                    print(CRED+'Identifier {} exceeded available $s registers'.format(identifier) + CEND)
            continue

        if args.verbose: idents.add(identifier)

        if identifier not in identifiers:
            identifiers[identifier] = available_registers[0]
            available_registers.pop(0)

    if args.verbose: print(len(idents), idents)

    return (identifiers, identifiersFlags)

def perform_replacements(text, identifiers):
    for i, r in identifiers.items():
        text = text.replace(i, r)
    return text

def extract_labels(text):
    labels = []
    matches = re.finditer(labels_regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        labels.append(match.group())
    return labels

available_registers = ["$t{}".format(i) for i in range(10)]
# available_registers.extend("$s{}".format(i) for i in range(10))

labels = []

# Function names in order
# function_names = ["main", "get_param", "run_generation", "print_generation"]
function_names = ["main", "run_generation", "print_generation"]
functions = dict(zip(function_names, [[] for x in range(len(function_names))]))

text = open(args.file, "r").read()
lines = text.split("\n")

labels = extract_labels(text)
# print(labels)

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

if args.verbose: print(functions.keys())

for functionName in function_names:
    print(functionName)
    f_text = functions[functionName]
    f_text = f_text[0]
    identifiers, identifiersFlags = create_identifiers_mapping(f_text)

    if args.identifiers:
        print(CGREEN + functionName + CEND)
        print(CGREY + 'Identifiers ' + CEND + ' '.join(identifiers.keys()))
        print(CGREY + 'Registers   ' + CEND + ' '.join(identifiers.values()))
        print(CGREY + 'Sorted      ' + CEND + ' '.join(sorted(identifiers.values())))
        print('')

    if args.locals or args.docs:
        VARS_HEADING_INDENT = 12
        LOCALS_HEADING = 'Locals:'
        LOCALS_BULLET = '- '
        STRUCTURE_HEADING = 'Structure:'
        STRUCTURE_BULLET = '- '
        FUNCTION_DOCS_INDENT = 8
        FRAME_REGISTERS = ('fp', 'ra', 'sp')
        FRAME_REGISTERS = ('$' + x for x in FRAME_REGISTERS)

        headingPrefix = '<' + str(VARS_HEADING_INDENT)
        comment = ""

        print(CGREEN + functionName + CEND)

        # Frame
        savedIdents = ["$s" + str(i) for i in range(10)]
        savedIdents = [x for x in savedIdents if (x in identifiers.values() or x in f_text)]

        frameIdents = savedIdents[:]
        frameIdents.extend(x for x in FRAME_REGISTERS if (x in identifiers.values() or x in f_text))
        comment += format('Frame: ', headingPrefix)
        comment += ', '.join(sorted(frameIdents))
        comment += '\n'
        frameIdents = None

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
        if 1 or args.clobbers:
            CLOBBERS_HEADING = 'Clobbers:'
            clobbers = "# clobbers: $a0,$a1"

            clobberStart = clobbers.find('$')
            if clobberStart > 0:
                clobbers = clobbers[clobberStart:]
                comment += format(CLOBBERS_HEADING, headingPrefix)
                comment += ', '.join(sorted([x.strip() for x in clobbers.split(',')]))
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
    if args.structure or args.docs:
        # Structure
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

        print(comment)

    max_length = -1
    for l in comment.split("\n"):
        max_length = max_length if len(l) < max_length else len(l)

    comment = "#" * (max_length + 2) + "\n" + functionName + "\n\n" + comment

    f_text = perform_replacements(f_text, identifiersFlags)
    f_text = perform_replacements(f_text, identifiers)
    if comment and args.docs:
        for cLine in comment.splitlines():
            result_text += ('# ' if len(cLine) else '') + cLine + '\n'
    result_text += f_text

# text = perform_replacements(text, identifiers)

# r = fix_comment_spacing(result_text)
# print(r)
with open(args.output, "w") as f:
    f.write(fix_comment_spacing(pre_text + result_text))