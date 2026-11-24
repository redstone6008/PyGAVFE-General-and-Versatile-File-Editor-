#!/usr/bin/env python
import os, sys, argparse, tty, signal, termios, shutil
from pathlib import Path
from blessed import Terminal


class Edit:
    class Cursor:
        def __init__(self, pos: int, buffer: list[str]) -> None:
            self.buffer = buffer
            self.buffrange = range(1, len(self.buffer) + 1)
            self.pos: int = pos if pos in self.buffrange else 0
            self.buffer: list[str] = buffer
            self.hold: str = buffer[self.pos - 1] if self.pos > 0 else "<empty hold>"

        def up(self, count=1) -> None:
            self.buffrange = range(1, len(self.buffer) + 1)
            if self.pos + 1 in self.buffrange:
                for _ in range(count):
                    self.pos += 1

        def down(self, count=1) -> None:
            self.buffrange = range(1, len(self.buffer) + 1)
            if self.pos - 1 in self.buffrange:
                for _ in range(count):
                    self.pos -= 1

        def set(self, pos) -> None:
            if pos in self.buffrange:
                self.pos = pos

    def __init__(self, file: Path, version: str) -> None:
        self.file: Path = file.absolute()
        self.buffer: list[str] = []
        self.cwd: Path = Path.cwd()
        self.width: int = 20
        self.height: int = 20
        self.version: str = version
        self.term = Terminal()

    def load(self, file: Path) -> None:
        if file == Path("/__null__"):
            untitledNumber = 0
            while Path(f"Untitled{untitledNumber}.txt").exists():
                untitledNumber += 1
            self.file = self.cwd / (f"Untitled{untitledNumber}.txt")
        elif not file.exists():
            self.file = self.cwd / file
        elif file.is_dir():
            input("This is a directory, not a file. Cannot open.")
            untitledNumber = 0
            while Path(f"Untitled{untitledNumber}.txt").exists():
                untitledNumber += 1
            self.file = self.cwd / Path(f"Untitled{untitledNumber}.txt")
        with open(file, "r") as r:
            for l in r:
                self.buffer.append(l.strip("\n\r"))
            self.cwd = file.parent.absolute()

    def save(self, file: Path, buffer: list[str]) -> tuple[list[str], Path]:
        if not file.exists():
            file = Path(self.__cbreak_input("", str(file)))
        with open(file, "w") as wtb:
            wtb.writelines(f"{line}\n" for line in buffer)
        return (buffer.copy(), file)

    def insertLine(self, content: str, lnum: int, buffer: list[str]) -> None:
        buffer.insert(lnum - 1, content)

    def changeLine(self, content: str, lnum: int, buffer: list[str]) -> None:
        buffer[lnum - 1] = content

    def deleteLine(self, lnum: int, buffer: list[str]) -> None:
        buffer.pop(lnum - 1)

    def copyLine(self, lnum: int, buffer: list[str]) -> None:
        raise NotImplementedError

    def pasteLine(self, lnum: int, buffer: list[str]) -> None:
        raise NotImplementedError

    def __cbreak_input(self, prompt="", default=""):
        """A drop-in replacement for input() that echoes text inside cbreak mode."""
        print(f"{prompt}{default}", end="", flush=True)
        text_string = default

        while True:
            key = self.term.inkey()

            # Stop collecting when Enter is pressed
            if key.name == "KEY_ENTER":
                print()  # Move to the next line
                return text_string

            # Handle Backspace manually
            elif key.name == "KEY_BACKSPACE" or key == "\x7f":
                if len(text_string) > 0:
                    text_string = text_string[:-1]
                    print("\b \b", end="", flush=True)
            # Only echo and save printable characters (ignore arrow keys, Ctrl codes)
            elif key and not key.is_sequence:
                text_string += key
                print(key, end="", flush=True)

    def getRawKey(*args, **kwargs):
        fd = sys.stdin.fileno()
        first_char = sys.stdin.read(1)

        if ord(first_char) == 27:
            old_flags = termios.tcgetattr(fd)
            new_flags = termios.tcgetattr(fd)
            new_flags[6][termios.VMIN] = 0  # cc index 6 is VMIN
            new_flags[6][termios.VTIME] = 0  # cc index 6 is VTIME
            termios.tcsetattr(fd, termios.TCSANOW, new_flags)

            try:
                next_chars = sys.stdin.read(2)
                if next_chars:
                    return first_char + next_chars
            finally:
                termios.tcsetattr(fd, termios.TCSANOW, old_flags)

        return first_char

    def termClip(self, text: str, termWidth: int, offset: int = 0):
        return text[offset:termWidth]

    def menu(self) -> None:
        self.load(self.file)
        savedbuff = self.buffer.copy()
        fd = sys.stdin.fileno()
        cursor = self.Cursor(1, self.buffer)
        old_settings = termios.tcgetattr(fd)
        new_settings = termios.tcgetattr(fd)
        new_settings[0] &= ~termios.IXON
        new_settings[3] &= ~termios.ISIG
        termios.tcsetattr(fd, termios.TCSANOW, new_settings)

        ## Initialize Configuration
        showLineNumbers = args.line_number
        showHelp = False
        displayLinesLength = 10
        scrollOffset = 5
        with self.term.cbreak():
            try:
                while True:
                    ## Setup
                    os.system("clear")
                    size = shutil.get_terminal_size()
                    termX = size.columns
                    if self.buffer == []:
                        buffEmpty = True
                    else:
                        buffEmpty = False

                    ## File Info Section
                    print(
                        f"-- PyGAVFE (Python General and Versatile File Editor) {self.version} --"
                    )
                    print(
                        f"Editing File: '{Path(str(self.file).split('/')[-1])}'",
                        end=" ",
                    )
                    if not self.file.exists() or self.buffer != savedbuff:
                        print(
                            self.termClip(
                                f"(Unsaved{', No Content' if self.buffer == [] else ''})",
                                termX,
                            )
                        )
                    else:
                        print(
                            self.termClip(
                                "(No Content)" if self.buffer == [] else "", termX
                            )
                        )
                    print(self.termClip(f"Current Directory: '{self.cwd}'", termX))
                    dividerLength = max(
                        len(str(self.cwd)) + 21,
                        len(str(self.file).split("/")[-1]) + 16,
                        len(self.version) + 57,
                        max(len(x) for x in self.buffer) if self.buffer != [] else 0,
                    )
                    print(
                        self.termClip("".join("—" for _ in range(dividerLength)), termX)
                    )
                    if showHelp:
                        print("""-- HELP --

Editing:
    i - Inserts Line at Current Cursor Position
    a - Append Line From Current Cursor Position
    c - Changes Line at Current Cursor Position
    d - Deletes Line at Current Cursor Position (Press 'd' to confirm)
    <ctrl>d - Same Function as 'd' With No Confirmation

File Actions:
    w/s - Saves File; Prompts File Name if the File Doesn't Exist
    q - Exits File With No Save w/ Confirmation
    <ctrl>q - Same as 'q' Without Confirmation
    
Navigation:
    j - Down
    k - Down

Miscellaneous:
    <ctrl>h - Shows this Help Section""")
                        print(
                            self.termClip(
                                "".join("—" for _ in range(dividerLength)), termX
                            )
                        )

                    ## File Content Section
                    ln = scrollOffset
                    viewScope: tuple = (scrollOffset, scrollOffset + displayLinesLength)
                    for l in self.buffer[viewScope[0] : viewScope[1]]:
                        ln += 1
                        if ln > displayLinesLength + scrollOffset:
                            break
                        pl = self.termClip(
                            l,
                            termX
                            - (
                                1
                                if not showLineNumbers
                                else len(
                                    [
                                        " "
                                        for _ in range(
                                            len(str(len(self.buffer) - 1))
                                            - len(str(ln))
                                        )
                                    ]
                                )
                                + len(str(ln))
                                + 1
                            ),
                        )
                        viewLine = f"{'\033[0;30;47m' if cursor.pos == ln else ''}{''.join([' ' for _ in range(len(str(len(self.buffer) - 1)) - len(str(ln)))]) if args.line_number else ''}{ln if args.line_number else ''}|\033[0m{'\033[4m' if cursor.pos == ln else ''}{pl}\033[0m"
                        print(viewLine)
                        # if l

                    ## Bottom Menu
                    val = self.getRawKey(timeout=60)
                    if val:
                        if val == "i":
                            content = self.__cbreak_input(
                                "Insert > ",
                            )
                            line = cursor.pos + scrollOffset
                            self.insertLine(content, line, self.buffer)
                            if buffEmpty:
                                cursor.up()
                        elif val == "a":
                            content = self.__cbreak_input(
                                "Append > ",
                            )
                            line = cursor.pos + 1 + scrollOffset
                            self.insertLine(content, line, self.buffer)
                            cursor.up()
                        elif val == "c":
                            content = self.__cbreak_input(
                                "Change > ", self.buffer[cursor.pos - 1 + scrollOffset]
                            )
                            line = cursor.pos + scrollOffset
                            self.changeLine(content, line, self.buffer)
                        elif val == "d" or val == "\x04":
                            if val == "d":
                                fval = self.getRawKey(timeout=60)
                            else:
                                fval = None
                            if fval == "d" or val == "\x04":
                                line = cursor.pos + scrollOffset
                                self.deleteLine(line, self.buffer)
                                cursor.down()
                        elif val == "q" or val == "\x11":
                            fval = None
                            if val == "q":
                                fval = self.getRawKey(timeout=60)
                            if fval == "q" or val == "\x11":
                                os.system("clear")
                                break
                        elif val == "w" or val == "s":
                            (savedbuff, self.file) = self.save(self.file, self.buffer)
                        elif val == "\x1b[A" or val == "k":
                            cursor.down()
                        elif val == "\x1b[B" or val == "j":
                            cursor.up()
                        elif val == "\x08":
                            if showHelp:
                                showHelp = False
                            else:
                                showHelp = True
            finally:
                termios.tcsetattr(fd, termios.TCSANOW, old_settings)


def main() -> None:
    global args

    def SIGPLSGONE(signum, frame):
        pass

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    signal.signal(signal.SIGINT, SIGPLSGONE)
    signal.signal(signal.SIGTSTP, SIGPLSGONE)
    version: str = "v0.3.0-Beta1"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        nargs="?",
        default=Path("/__null__"),
        help="File Path (Absolute and Relative)",
        type=Path,
    )
    parser.add_argument("--version", action="store_true", help="Show Program Version")
    parser.add_argument(
        "-n", "--line_number", action="store_true", help="Show Line Numbers"
    )
    args = parser.parse_args()
    if args.version:
        print(f"PyGAVFE {version}")
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        sys.exit()
    editor = Edit(args.file, version)
    editor.menu()
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
