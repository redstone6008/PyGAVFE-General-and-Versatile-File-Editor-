import os, sys
import shutil, readline
import argparse
from pathlib import Path
from pathvalidate import is_valid_filename as ivf
from prompt_toolkit import prompt

## MISC FUNCTIONS

# CONSOLE
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# PARSING
def tags(command):
    finalTags = []
    tagGroups = [x.lstrip('-') for x in command.split() if x.startswith('-')]
    for ch in tagGroups:
        for c in ch:
            finalTags.append(c)
    return set(finalTags)

# TERMINAL RENDERING
def render(style, content):
    if style == "Minimal":
        if content == "MenuHelp":
            print("""
-- Command List --
- Commands -
    H - Show this command list
    N - New File
        <newfilename>
        -x
    E <file/filepath> - Edit File
        -n <number>
    D <file/filepath> - Delete File
        -n <number>
    L <dirpath> - Look in Directory
    S - Open Settings
        -f
    X - Exit

- Placeholders -
    <number> - by number next to shown files
    <file/filepath> - by file or file path
    <newfilename> - write new blank file with file name
    <dirpath> - directory path

- Tags -
    'n' - by number: ED
    'f' - edit config file: S
    'x' - force action: D; skip to editor (prompts save when exits): N
""")
    elif style == "AsciiInter":
        if content == "MenuHelp":
            print("Tiki Tiki")

def terminal_clip(text, width):
    if width <= 0:
        return ""
    return str(text)[:width]

## MAIN FUNCTIONS
def newFileEdit(file):
    if file == '':
        edit('')
    else:
        try:
            with open(file, "w") as c:
                c.write("")
            edit(file)
        except Exception as e:
            if input("Something went wrong making new file.") == "DEB":
                input(e)

def saveFile(file, contents):
    try:
        with open(file, "w") as w:
            w.writelines(l + "\n" for l in contents)
    except Exception as e:
        if input("An error happend trying to save this file (Type 'DEBUG' to see error message): ") == "DEBUG":
            input(e)


def edit(file):
    global curDir
    global files
    global args
    contents = {}
    curFile = file
    sideScroll = 0

    ## Configuration
    contentBorderLength = 12
    defaultStartDisplayLine = 0
    contentDisplayHeight = 25
    permissionMode = 1

    ## Setup
    startDisplayLine = defaultStartDisplayLine
    if args.read:
        permissionMode = 0

    if curFile != '':
        try: 
            with open(curFile, 'r') as r:
                for i, l in enumerate(r):
                    contents[i] = l.replace('\n', '').replace('\r', '').replace('\t', '    ')
        except:
                input("File doesnt exist")
                return None
    else:
        n = 0
        while True:
            if f"Untitled-{n}.txt" not in files:
                curFile = f"Untitled-{n}.txt"
                break
            n += 1

    while True:
        tcolumns = max(1, shutil.get_terminal_size().columns)
        ## Edit Menu

        clear()
        print(terminal_clip(f"Editing File: {curFile}", tcolumns))
        if len(contents.keys()) != 0:
            if max([len(x) for x in contents.values()]) > 12 or len(curFile)+14 > 12:
                if max([len(x) for x in contents.values()]) < len(curFile)+14:
                    contentBorderLength = len(curFile)+14
                else:
                    contentBorderLength = max([len(x) for x in contents.values()])
            visibleBorder = "".join(["_" for c in range(contentBorderLength)])
            print(terminal_clip(visibleBorder, tcolumns))
        else:
            print("____________\n(Empty File)")
        dc = 0 - startDisplayLine
        for l in contents.keys():
            dc += 1
            if l < startDisplayLine:
                continue
            if dc > contentDisplayHeight:
                break
            visibleLine = contents[l][sideScroll:sideScroll + tcolumns]
            print(terminal_clip(f"{"".join([" " for x in range(len(str(max(contents.keys()))) - len(str(l))) ])}{l}|" + visibleLine, tcolumns))
        borderPrompt = terminal_clip("".join(["_" for c in range(contentBorderLength)])[sideScroll:sideScroll + tcolumns], tcolumns)
        editorCommand = input(borderPrompt + "\n>> ")
        if editorCommand == '':
            continue
        if editorCommand.split()[0][0] == '>' and set(editorCommand.split()[0]).issubset(">>>>>"):
            sideScroll += 2 ** len(editorCommand.split()[0])+2
            continue
        if editorCommand.split()[0][0] == '<' and set(editorCommand.split()[0]).issubset("<<<<<"):
            sideScroll = max(0, sideScroll - (2 ** len(editorCommand.split()[0]) + 2))
            continue
        if editorCommand.split()[0][0] == 'u' and set(editorCommand.split()[0]).issubset("uuuuu"):
            startDisplayLine = min((len(contents)//2)*2, startDisplayLine + (2 ** len(editorCommand.split()[0])))
            continue
        if editorCommand.split()[0][0] == 'j' and set(editorCommand.split()[0]).issubset("jjjjj"):
            startDisplayLine = max(0, startDisplayLine - (2 ** len(editorCommand.split()[0])))
            continue
        if editorCommand.split()[0][0] == 'H':
            input("""
-- Command List -- 
- Commands -
    H - Show this command list
    I - Insert Line (if no specifed line number then append)
        -l <linenumber>
    D - Delete Line (if no specifed line number then pop)
        -l <linenumber>
    C - Change Line
        -l <linenumber>
        -w
    X - Wipe File (Saves after wipe)
        -x
        -s
    R - Remove File
        -x
        -s
    W - Write to File
        -x
    > - Sidescroll Right (More arrows means double the scroll length for each)
    < - Sidescroll Left (More arrows means double the scroll length for each)
    S - Open Settings (local file settings)
        -g
        -f
    E - Exit Edit (No Write)
        -x
        -w

- Placeholders -
    <linenumber> - the line number in you file

- Tags -
    !!Make sure to combine tags like this (-lw) not (-l -w)!!

    'l' - specify line: DIC
    'x' - force task / supress prompts: XREW
    's' - dont save after wipe: X; stay in deleted file editor: R
    'g' - open global settings: S
    'f' - edit config file/s
    'w' - rewrite line: C; write to file: E

Press Enter to Leave""")
        elif editorCommand.split()[0] == "E":
            if tags(editorCommand).issubset(['x']) and len(tags(editorCommand)) != 0:
                break
            else:
                if input(">>Do you want to exit? Make sure you've saved your files (Type 'y' for yes)") == "y":
                    break
        elif editorCommand.split()[0] == "I":
            if permissionMode == 1:
                if tags(editorCommand).issubset(['l']) and len(tags(editorCommand)) != 0:
                    try:
                        editLineNum = editorCommand.split()[2]
                    except:
                        editLineNum = len(contents.keys())
                else:
                    editLineNum = input(">>Line Number: ")
                try:
                    editContent = input(">>Content:\n" + "".join([" " for x in range(len(str(max(contents.keys()))))]) + "|")
                except: editContent = input(">>Content:\n" + " |")
                editContent = editContent.expandtabs(4)
                if editLineNum == '':
                    editLineNum = len(contents.keys())
                ld = list(contents.values())
                ld.insert(int(editLineNum), editContent)
                contents = {}
                for i, c in enumerate(ld):
                    contents[i] = c
            else:
                input("You're in read-only mode. Cannot perform file-modifying action.")
        elif editorCommand.split()[0] == "D":
            if permissionMode == 1:
                if tags(editorCommand).issuperset("l"):
                    if len(editorCommand.split()) < 3:
                        delLineNum = "undef"
                    else:
                        delLineNum = editorCommand.split()[2]
                else:
                    delLineNum = input(">>Delete Line: ")
                try:
                    delLineNum = int(delLineNum)
                except:
                    delLineNum = "undef"
                ld = list(contents.values())
                try:
                    if delLineNum == "undef":
                        ld.pop()
                    else:
                        ld.pop(delLineNum)
                except:
                    pass
                contents = {}
                for i, c in enumerate(ld):
                    contents[i] = c
            else:
                input("You're in read-only mode. Cannot perform file-modifying action.")
        elif editorCommand.split()[0] == "C":
            if permissionMode == 1:
                if len(editorCommand.split()) > 2 and tags(editorCommand).issuperset('l'):
                    changeLineNum = editorCommand.split()[2]
                elif tags(editorCommand).issuperset('l'):
                    changeLineNum = ''
                else:
                    changeLineNum = input(">>Change Line: ")
                if changeLineNum == '':
                    try:
                        changeLineNum = list(contents.keys())[len(contents.keys())-1]
                    except:
                        changeLineNum = 0
                try:
                    changeLineNum = int(changeLineNum)
                    list(contents.keys())[changeLineNum]
                    if tags(editorCommand).issuperset("w"):
                        changeLineContent = input(">>Content:\n" + "".join([" " for x in range(len(str(max(contents.keys()))))]) + "|")
                    else:
                        changeLineContent = prompt(">>Content:\n" + "".join([" " for x in range(len(str(max(contents.keys()))))]) + "|", default=contents[changeLineNum])
                    contents[changeLineNum] = changeLineContent.expandtabs(4)
                except:
                    pass
            else:
                input("You're in read-only mode. Cannot perform file-modifying action.")
        elif editorCommand.split()[0] == "W":
            if permissionMode == 1:
                if tags(editorCommand).issuperset("x"):
                    saveFile(curFile, contents.values())
                else:
                    if input(">> Overwrite File? Type 'y' to overwrite: ") == 'y':
                        if not Path(curFile).exists():
                            newCurName = input(">> New File Name: ")
                            if newCurName != "":
                                if ivf(newCurName):
                                    curFile = newCurName
                                else:
                                    input("Invalid File Name")
                        saveFile(curFile, contents.values())
            else:
                input("You're in read-only mode. Cannot perform file-modifying action.")
        elif editorCommand.split()[0] == "X":
            if permissionMode == 1:
                confirm = "YES"
                if "x" not in tags(editorCommand):
                    confirm = input(">>Wipe cont][p nts of this file? Type 'YES' to confirm: ")
                    if confirm == "YES":
                        contents = {}
                else:
                    contents = {}
                if "s" not in tags(editorCommand):
                    saveFile(curFile, contents.values())
            else:
                input("You're in read-only mode. Cannot perform file-modifying action.")

def main():
    ## Globalising Variables
    global curDir
    global files
    global args

    ## Initialising Variables
    #tuiStyle = "Mimal" 
    sys.stdout.write("\x1b[3g")  # Clear all existing tab stops
    readline.parse_and_bind("set editing-mode emacs")
    readline.parse_and_bind(r'"\t": "    "')

    # Command Line Arguments
    parser = argparse.ArgumentParser(description="GAVFE is a basic but useful file editor.")
    parser.add_argument("-f", "--file",type=str, help="File Name (Path to File)")
    parser.add_argument("-l", "--look", type=str, default='.', help="Search and Act In Directory")
    parser.add_argument("-d", "--directory", type=str, default='.', help="Open Directory")
    parser.add_argument("-r", "--read", action="store_true", help="Read only the file, and blocks edits.")
    parser.add_argument("--version", action="store_true", help="Shows Editor Version")
    args = parser.parse_args()

    # Styles (Editor Mode: BLLII): Minimal, AsciiInter, InterfaceQ, CoreLinear
    # Styles (Editor Mode: ATUI): Minimal, AsciiInter, InterfaceQ, OpenTUI

    curDir = Path.cwd()
    version = "Beta 2"
    if args.file:
        try:
            edit(args.file)
            clear()
        except:
            input("Cant open file")
    if args.version == True:
        print(f"GAVFE Version: {version}")
        sys.exit()
    if args.look:
        if Path(f"{args.look}").is_dir():
            curDir = Path(args.look).resolve()
        else:
            input("Invalid Directory")

    # Main Menu Loop
    while True:
        tcolumns = max(1, shutil.get_terminal_size().columns)
        clear()
        try:
            files = [f.name for f in curDir.iterdir() if f.is_file()]
            dirs = [d.name for d in curDir.iterdir() if d.is_dir()]
        except:
            input("Unable to List Directory")
            curDir = Path("~").expanduser()
            files = [f.name for f in curDir.iterdir() if f.is_file()]
            dirs = [d.name for d in curDir.iterdir() if d.is_dir()]
        print(terminal_clip(f"-- GAVFE (General and Versatile File Editor) {version} --", tcolumns))
        print(terminal_clip(f"Type 'H' to display command list", tcolumns))
        print(terminal_clip(f"CURRENT DIRECTORY: {curDir}", tcolumns))
        print(terminal_clip(f"EDIT FILES:", tcolumns))
        for i, file in enumerate(files):
            print(terminal_clip(f"    [{i}] -> {file}", tcolumns))
        print(terminal_clip(f"LOOK IN DIRECTORIES:", tcolumns))
        for i, dir in enumerate(dirs):
            print(terminal_clip(f"    [{i}] -> {dir}", tcolumns))
        command = input(terminal_clip(">> ", tcolumns))
        if command != '':
            if command.split()[0] == "H":
                print("""
-- Command List --
- Commands -
    H - Show this command list
    N - New File
        <newfilename>
        -x
    E <file/filepath> - Edit File
        -n <number>
    D <file/filepath> - Delete File
        -n <number>
        -x
    L <dirpath> - Look in Directory
    S - Open Settings
        -f
    X - Exit

- Placeholders -
    <number> - by number next to shown files
    <file/filepath> - by file or file path
    <newfilename> - write new blank file with file name
    <dirpath> - directory path

- Tags -
    'n' - by number: ED
    'f' - edit config file: S
    'x' - force action: D; skip to editor (prompts save when exits): N
""")
                input("Press Enter to Leave")
            elif command.split()[0] == "E":
                if tags(command).issubset(['n']) and len(tags(command)) != 0:
                    try: 
                        edit(str(curDir) + '/' + dict(enumerate(files))[int(command.split()[2])])
                    except Exception as e:
                        input(f"File Not Listed {e}")
                else:
                    if len(command.split()) > 1:
                        edit(command.split()[1])
                    else:
                        input("Incomplete Command")
            elif command.split()[0] == "X":
                clear()
                break
            elif command.split()[0] == "N":
                if "x" in tags(command):
                    newFileEdit('')
                elif len(command.split()) == 2:
                    filePath = command.split()[1]
                    newFileEdit(filePath)
                else:
                    newFileName = input("New File Name: ")
                    pathToFileDir = input("Create In Directory (Enter Directory Path): ").rstrip("/")
                    if pathToFileDir == "":
                        pathToFileDir = curDir
                    filePath = f"{pathToFileDir}/{newFileName}"
                    newFileEdit(filePath)
            elif command.split()[0] == "L":
                if len(command.split()) == 2:
                    newPath = Path(command.split()[1]).expanduser()
                else:
                    newPath = Path(input("Look in Directory (Directory Path): ")).expanduser()

                if (curDir / newPath).exists():
                    curDir = Path.resolve(curDir / newPath)
                else:
                    input("Invalid Directory")

            elif command.split()[0] == "D":
                if "n" in tags(command):
                    deleteFile = str(curDir) + "/" + files[int(command.split()[2])]
                else:
                    deleteFile = input("Delete which file? (Enter File Path): ")
                try:
                    with open(deleteFile, "r") as r:
                        r.read()
                except Exception as e:
                    input("File path invalid or nonexistent")
                    input(e)
                    continue
                if "x" in tags(command):
                    os.remove(deleteFile)
                else:
                    if input("Delete ALL contents and the file itself (HELLYES/n)") == "HELLYES":
                        os.remove(deleteFile)
                
if __name__ == "__main__":
    main()
