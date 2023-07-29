from typing import List, Tuple, Union

from lark import Token, Lark, UnexpectedEOF

import shutil

class ANSI:
    # Text color
    fg_black: str = '\033[30m'
    fg_red: str = '\033[31m'
    fg_green: str = '\033[32m'
    fg_yellow: str = '\033[33m'
    fg_blue: str = '\033[34m'
    fg_magenta: str = '\033[35m'
    fg_cyan: str = '\033[36m'
    fg_white: str = '\033[37m'

    fg_bright_black: str = '\033[90m'
    fg_bright_red: str = '\033[91m'
    fg_bright_green: str = '\033[92m'
    fg_bright_yellow: str = '\033[93m'
    fg_bright_blue: str = '\033[94m'
    fg_bright_magenta: str = '\033[95m'
    fg_bright_cyan: str = '\033[96m'
    fg_bright_white: str = '\033[97m'

    # Background color
    bg_black: str = '\033[40m'
    bg_red: str = '\033[41m'
    bg_green: str = '\033[42m'
    bg_yellow: str = '\033[43m'
    bg_blue: str = '\033[44m'
    bg_magenta: str = '\033[45m'
    bg_cyan: str = '\033[46m'
    bg_white: str = '\033[47m'

    bg_bright_black: str = '\033[100m'
    bg_bright_red: str = '\033[101m'
    bg_bright_green: str = '\033[102m'
    bg_bright_yellow: str = '\033[103m'
    bg_bright_blue: str = '\033[104m'
    bg_bright_magenta: str = '\033[105m'
    bg_bright_cyan: str = '\033[106m'
    bg_bright_white: str = '\033[107m'

    # Styles
    bold: str = '\033[1m'
    underline: str = '\033[4m'
    blink: str = '\033[5m'
    reverse: str = '\033[7m'

    # Reset
    reset: str = '\033[0m'

    @staticmethod
    def fg_color(hex):
        lv = len(hex)
        colors = tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return f"\033[38;2;{colors[0]};{colors[1]};{colors[2]}m"

    @staticmethod
    def bg_color(hex):
        lv = len(hex)
        colors = tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return f"\033[48;2;{colors[0]};{colors[1]};{colors[2]}m"

class ErrorCollector:
    def __init__(self):
        self.errors = []
        self.width, self.height = shutil.get_terminal_size((80, 20))
        self.content_width, self.content_height = max(self.width - 10, 10), max(self.height, 10)

    def throw(self, error):
        self.errors.append(error)

    def set_source(self, source: str):
        self.source = str(source).split('\n')

    def render(self):
        for error in self.errors:
            print(f"{ANSI.fg_red + ANSI.bold}Error: {ANSI.reset + ANSI.bg_red}{error.error_type}{ANSI.reset}")

            if error.reference is not None:
                line = error.reference[0]
                column = error.reference[1]
                
                for y in range(max(0, line - 5), line, 1):
                    if y == line - 1:
                        line_number = f"{1 + y:02}{ANSI.reset}"
                    else:
                        line_number = f"{ANSI.fg_bright_black}{1 + y:02}{ANSI.reset}"
                    print(f"{line_number} {repr(self.source[y])[1:-1]}")

                print(f"{' ' * (len(f'{column:02}') + column)}{ANSI.fg_red + ANSI.reverse + ANSI.bold}^{ANSI.reset}")

            print(f"{error.description}\n")

            if error.solution is not None:
                print(f"{ANSI.fg_blue + ANSI.bold}Hint:{ANSI.reset}")
                print(f"{error.solution}\n")

    def patch_after(self, line, column, value, parser: Lark):
        rebuilt_source = self.source[:line - 1]
        rebuilt_source.append(f'{self.source[line - 1][:column + len(value)]};')

        try:
            parsed = parser.parse("\n".join(rebuilt_source))

        except UnexpectedEOF as e:
            return self.render_missing_semicolon(rebuilt_source)
        
        except Exception as e:
            return None

    def patch_before(self, line, column, parser: Lark):
        rebuilt_source = self.source[:line]
        rebuilt_last = self.source[line][:column]

        if len(rebuilt_last.rstrip()) > 0:
            rebuilt_source.append(rebuilt_last)

        rebuilt_source[-1] += ';'

        try:
            parsed = parser.parse("\n".join(rebuilt_source))

        except UnexpectedEOF as e:
            return self.render_missing_semicolon(rebuilt_source)
        
        except Exception as e:
            return None

    def render_missing_semicolon(self, source: List[str]) -> str:
        line = len(source)
        column = len(repr(source[-1])[1:-1])

        patch = []
        for y in range(max(0, line - 5), line, 1):
            if y == line - 1:
                line_number = f"{1 + y:02}{ANSI.reset}"
            else:
                line_number = f"{ANSI.fg_bright_black}{1 + y:02}{ANSI.reset}"
            patch.append(f"{line_number} {repr(source[y])[1:-1]}")


        patch.append(f"{' ' * (len(f'{line:02}') + column)}{ANSI.fg_blue + ANSI.reverse + ANSI.bold}^{ANSI.reset}")
        patch.append("A semicolon might be missing here.")

        patch = "\n".join(patch)

        return patch

class Error:
    def __init__(self, error_type: str, description: str, solution: Union[None, str], reference: Union[None, Tuple[int, int]]):
        self.error_type: str = error_type
        self.description: str = description
        self.solution: Union[None, str] = solution
        self.reference: Union[None, Tuple[int, int]] = reference

class gSyntaxError(Error):
    def __init__(self, description: str, solution: Union[None, str] = None, reference: Union[None, Tuple[int, int]] = None):
        super().__init__("SyntaxError", description, solution, reference)

class ImpossibleError(Error):
    def __init__(self, description: str, reference: Union[None, Tuple[int, int]] = None):
        super().__init__("ImpossibleError", description, "This shouldn't happen. Please contact the developers.", reference)

class UnknownObjectError(Error):
    def __init__(self, description: str, solution: Union[None, str] = None, reference: Union[None, Tuple[int, int]] = None):
        super().__init__("UnknownObjectError", description, solution, reference)

class ArgumentError(Error):
    def __init__(self, description: str, solution: Union[None, str] = None, reference: Union[None, Tuple[int, int]] = None):
        super().__init__("ArgumentError", description, solution, reference)

class gTypeError(Error):
    def __init__(self, description: str, solution: Union[None, str] = None, reference: Union[None, Tuple[int, int]] = None):
        super().__init__("TypeError", description, solution, reference)

def pretty_join(items: List, separator: str = ' and '):
    return '' if len(items) == 0 else (', '.join(items[:-1])) + (separator if len(items) > 2 else '') + (items[-1])

def pretty_repr_join(items: List, separator: str = ' and '):
    return '' if len(items) == 0 else (', '.join([repr(item) for item in items[:-1]])) + (separator if len(items) > 2 else '') + (repr(items[-1]))

error_collector = ErrorCollector()