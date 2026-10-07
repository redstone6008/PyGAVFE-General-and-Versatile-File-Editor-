#!/usr/bin/env python
import os, sys, argparse
from collections.abc import Callable
from typing import Any
from pathlib import Path
from blessed import Terminal
from prompt_toolkit import prompt

class Edit:
    class Cursor:
        def __init__(self, pos: int, buffer: list[str]) -> None:
            self.buffer = buffer
            self.buffrange = range(1, len(self.buffer)+1)
            self.pos: int = pos if pos in self.buffrange else 0
            self.buffer: list[str] = buffer
            self.hold: str = buffer[self.pos-1] if self.pos > 0 else "<empty hold>"
        def up(self, *count: int) -> None:
            self.buffrange = range(1, len(self.buffer)+1)
            if self.pos + 1 in self.buffrange: 
                self.pos += 1
                if count and len(count) == 1:
                    for _ in range(count[0]-1):
                        self.pos += 1
        def down(self, *count: int) -> None:
            self.buffrange = range(1, len(self.buffer)+1)
            if self.pos - 1 in self.buffrange: 
                self.pos -= 1
                if count and len(count) == 1:
                    for _ in range(count[0]-1):
                        self.pos -= 1
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
            while Path(f"Untitled{untitledNumber}.txt").exists(): untitledNumber += 1
            self.file = self.cwd / (f"Untitled{untitledNumber}.txt")
            return None
        elif not file.exists():
            self.file = self.cwd / file
            return None
        elif file.is_dir():
            input("This is a directory, not a file. Cannot open.")
            untitledNumber = 0
            while Path(f"Untitled{untitledNumber}.txt").exists(): untitledNumber += 1
            self.file = self.cwd / Path(f"Untitled{untitledNumber}.txt")
            return None
        with open(file, "r") as r:
            for l in r:
                self.buffer.append(l.strip("\n\r"))
            self.cwd = file.parent.absolute()
    def save(self, file: Path, buffer: list[str]) -> None:
        if not file.exists():
            file = Path(self.__cbreak_input("", str(file)))
        with open(file, "w") as wtb:
            wtb.writelines(f"{line}\n" for line in buffer)
    def insertLine(self, content: str, lnum: int, buffer: list[str]) -> None:
        buffer.insert(lnum-1, content)
    def changeLine(self, content: str, lnum: int, buffer: list[str]) -> None:
        buffer[lnum-1] = content
    def deleteLine(self, lnum: int, buffer: list[str]) -> None:
        buffer.pop(lnum-1)
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
                print() # Move to the next line
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
    def menu(self) -> None:
        self.load(self.file)
        savedbuff = self.buffer.copy()
        cursor = self.Cursor(1, self.buffer)
        with self.term.cbreak():
            while True:
                ## File Info Section
                os.system("clear")
                print(f"-- PyGAVFE (Python General and Versatile File Editor) {self.version} --")
                print(f"Editing File: '{Path(str(self.file).split("/")[-1])}'", end=" ")
                if not self.file.exists() or self.buffer != savedbuff:
                    print(f"(Unsaved{", No Content" if self.buffer == [] else ""})") 
                else:
                    print("(No Content)" if self.buffer == [] else "")
                print(f"Current Directory: '{self.cwd}'")
                dividerLength = max(len(str(self.cwd)) + 21,
                                    len(str(self.file).split("/")[-1]) + 16,
                                    len(self.version) + 57,
                                    max(len(x) for x in self.buffer) if self.buffer != [] else 0
                                )
                print("".join("—" for _ in range(dividerLength)))

                ## File Content Section
                ln = 0
                for l in self.buffer:
                    ln += 1
                    print(f"{"\033[0;30;47m" if cursor.pos == ln else ""}{"".join([" " for _ in range(len(str(len(self.buffer)-1))-len(str(ln)))])}{ln}\033[0m|{"\033[4m" if cursor.pos == ln else ""}{l}\033[0m")

                ## Bottom Menu
                val = self.term.inkey(timeout=60)
                if val:
                    if ord(val[0]) == 27:
                        if len(val) == 2 and val[1] == "i":
                            content = self.__cbreak_input("Insert > ")
                            line = cursor.pos
                            self.insertLine(content, line, self.buffer)
                        elif len(val) == 2 and val[1] == "c":
                            content = self.__cbreak_input("Change > ", )
                            line = cursor.pos
                            self.insertLine(content, line, self.buffer)
                        elif len(val) == 2 and val[1] == "s":
                            self.save(self.file, self.buffer)
                        elif len(val) == 3 and [val[1], val[2]] == ["[", "A"]:
                            print("down")
                            cursor.down()
                        elif len(val) == 3 and [val[1], val[2]] == ["[", "B"]:
                            print("up")
                            cursor.up()
                    elif ord(val) == 24: # Ctrl+X ASCII code
                        os.system("clear")
                        sys.exit()
                """if input() == "edb101":
                    match input():
                        case "insert":
                            content = input()
                            line = cursor.pos
                            self.insertLine(content, line, self.buffer)
                        case "change":
                            content = prompt("", default=cursor.hold)
                            line = cursor.pos
                            self.changeLine(content, line, self.buffer)
                        case "delete":
                            line = cursor.pos
                            self.deleteLine(line, self.buffer)
                        case "save":
                            self.save(self.file, self.buffer)
                        case "\x1B[A":
                            cursor.down()
                        case "\x1B[B":
                            cursor.up()
                        case "exit":
                            break"""
def main() -> None:
    version: str = "v0.3.0-Beta1" 
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=Path("/__null__"), help="File Path (Absolute and Relative)", type=Path)
    parser.add_argument("--version", action="store_true", help="Show Program Version")
    args = parser.parse_args()
    if args.version:
        print(f"PyGAVFE {version}")
        sys.exit()
    editor = Edit(args.file, version)
    editor.menu()
    

if __name__ == "__main__":
    main()
