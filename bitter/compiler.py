import os

from lark import Lark, Tree

from lark.exceptions import UnexpectedToken, UnexpectedCharacters

import sys

import os

import glob

from pathlib import Path

from .sb3.project import Project, Sprite, Stage

from .terminal import pretty_join, error_collector, gSyntaxError

def tokenise(parser: Lark, source):
    try:
        return parser.parse(source)

    except UnexpectedToken as exception:
        error_collector.throw(gSyntaxError(
            f"An unexpected token {repr(exception.token.value)} took the place of {pretty_join(list(exception.expected), ' or ')}.",
            None, # error_collector.patch(last.line, last.column, last.value, parser),
            (exception.line, exception.column)
        ))

    except UnexpectedCharacters as exception:
        error_collector.throw(gSyntaxError(
            f"An unexpected character {repr(exception.char)} is unrelated to the expected tokens.",
            error_collector.patch_before(exception.line - 1, exception.column - 1, parser),
            (exception.line, exception.column)
        ))

    error_collector.render()
    exit(1)
    
def compile_code(path, debug_mode: bool):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    grammar_file = os.path.join(current_dir, "syntax", "grammar.lark")

    with open(grammar_file, "r") as file:
        grammar_data = file.read()

    parser = Lark(grammar_data, start='start')

    if path.is_dir():
        project = Project()

        file = Path(path / "stage.gs")
        if file.is_file():
            with file.open("r") as file_object:
                file_data = file_object.read()
            
            error_collector.set_source(file_data)
            tree = tokenise(parser, file_data)

            target = Stage(tree, path)

            project.add_target(target)

        files = filter(lambda file: "stage.gs" not in file.name, path.glob("*.gs"))
        for index, file in enumerate(files):
            with file.open("r") as file_object:
                file_data = file_object.read()

            error_collector.set_source(file_data)
            tree = tokenise(parser, file_data)

            target = Sprite(file.name, tree, path)
            target.layer_order = index + 1

            project.add_target(target)

        project.build(parser)
        
        debug, project_zip = project.render(debug_mode)

        if debug_mode:
            assert debug is not None
            with open(f"{path.stem}.debug.json", 'w') as file:
                file.write(debug)

        if len(error_collector.errors) == 0:
            with open(f"{path.stem}.sb3", 'wb') as file:
                file.write(project_zip.getvalue())
