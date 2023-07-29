from typing import List, Union, Dict, Tuple

import rich.repr

from io import BytesIO

from random import randint

import zipfile

import json

from pathlib import Path

from .utils import uid

from .blocks import Blocks

from .costumes import cast_to_costume, Costume, Vector, Bitmap

from .sounds import Sound

# from rich.console import Console

class Project:
    def __init__(self):
        self.targets: List[Target] = []
        self.monitors: List = []
        self.extensions: List[str] = []
        self.meta: Meta = Meta()

        self.file_buffer = {}

        # self.console = Console()

    def build(self, parser):
        for target in self.targets:
            target.build(parser)

    def add_target(self, target):
        self.targets.append(target)

    def render(self, debug_mode: bool) -> Tuple[Union[None, str], BytesIO]:
        project = {
            "targets": [target.render(self.file_buffer) for target in self.targets],
            "monitors": self.monitors,
            "extensions": self.extensions,
            "meta": self.meta.render()
        }

        json_project = json.dumps(project, indent = 0, separators=(',', ':'))

        output_buffer = BytesIO()
        with zipfile.ZipFile(output_buffer, 'w') as zip_file:
            zip_file.writestr("project.json", json_project)
            for name, data in list(self.file_buffer.items()):
                zip_file.writestr(name, data)

        if debug_mode:
            json_debug = json.dumps(project, indent=4)
        else:
            json_debug = None

        return json_debug, output_buffer
    
    def __rich_repr__(self) -> rich.repr.Result:
        yield "targets", self.targets
        yield "monitors", self.monitors
        yield "extensions", self.extensions
        yield "meta", self.meta

class Meta:
    def __init__(self):
        self.meta: Dict[str, str] = {
            "semver": "3.0.0",
            "vm": "0.2.0",
            "agent": ""
        }
    
    def render(self):
        return self.meta

    def __rich_repr__(self) -> rich.repr.Result:
        yield "meta", self.meta

class Target:
    def __init__(self, name, tree, working_directory):
        self.is_stage: bool = False
        self.name: str = name
        self.g_variables: Dict[str, gVariable] = {}
        self.g_lists: List[gList] = []
        self.broadcasts: List[Broadcast] = []  
        self.blocks = Blocks(tree, self)
        self.comments: Dict = {}
        self.current_costume: int = 0
        self.costumes: List[Union[Vector, Bitmap]] = []
        self.sounds: List[Sound] = []
        self.volume: int = 100
        self.layer_order: int = 0
        self.tempo: int = 60
        self.video_transparency: int = 50
        self.video_state: str = "on"
        self.text_to_speech_language: Union[None, str] = None

        self.working_directory = working_directory
    
    def build(self, parser):
        self.blocks.build(parser)

    # def add_vector(self, vector: Union[Costume, Vector, Bitmap]):
    #     self.costumes.append(vector)

    def ensure_variable(self, name: str, namespace: str) -> str:
        if namespace is None:
            internal_name = name

        else:
            internal_name = f"{namespace}.{name}"

        if internal_name in self.g_variables.keys():
            return self.g_variables[internal_name].uuid

        else:
            variable = gVariable(internal_name)
            self.g_variables.update({internal_name: variable})
            return variable.uuid

    def variable_uuid_if_exists(self, name: str, namespace) -> Union[str, None]:
        if namespace is None:
            internal_name = name

        else:
            internal_name = f"{namespace}.{name}"

        if internal_name in list(self.g_variables.keys()):
            return self.g_variables[internal_name].uuid

        else:
            return None


    def local_variable_uuid_if_exists(self, name: str, namespace) -> Union[str, None]:
        internal_name = f"{namespace}.{name}"

        if internal_name in list(self.g_variables.keys()):
            return self.g_variables[internal_name].uuid

        else:
            return None

    def global_variable_uuid_if_exists(self, name: str) -> Union[str, None]:
        internal_name = name

        if internal_name in list(self.g_variables.keys()):
            return self.g_variables[internal_name].uuid

        else:
            return None

    def add_costume(self, path):
        file = Path(path)
        self.costumes.append(cast_to_costume(file, self.working_directory))

    def render(self, file_buffer):
        return {
            "isStage": self.is_stage,
            "name": self.name,
            "variables": {g_variable.uuid: g_variable.render() for g_variable in self.g_variables.values()},
            "lists": {g_list.uuid: g_list.render() for g_list in self.g_lists},
            "broadcasts": {broadcast.uuid: broadcast.render() for broadcast in self.broadcasts},
            "blocks": self.blocks.project['blocks'],
            "comments": self.comments,
            "current_costume": self.current_costume,
            "costumes": [costume.render(file_buffer) for costume in self.costumes],
            "sounds": [sound.render() for sound in self.sounds],
            "volume": self.volume,
            "layerOrder": self.layer_order,
            "tempo": self.tempo,
            "videoTransparency": self.video_transparency,
            "videoState": self.video_state,
            "TextToSpeechLanguage": self.text_to_speech_language
        }

class Stage(Target):
    def __init__(self, tree, working_directory):
        super().__init__('Stage', tree, working_directory)
        self.is_stage = True

    def render(self, file_buffer):
        return {
            "isStage": self.is_stage,
            "name": self.name,
            "variables": {g_variable.uuid: g_variable.render() for g_variable in self.g_variables.values()},
            "lists": {g_list.uuid: g_list.render() for g_list in self.g_lists},
            "broadcasts": {broadcast.uuid: broadcast.render() for broadcast in self.broadcasts},
            "blocks": self.blocks.project['blocks'],
            "comments": self.comments,
            "current_costume": self.current_costume,
            "costumes": [costume.render(file_buffer) for costume in self.costumes],
            "sounds": [sound.render() for sound in self.sounds],
            "volume": self.volume,
            "layerOrder": self.layer_order,
            "tempo": self.tempo,
            "videoTransparency": self.video_transparency,
            "videoState": self.video_state,
            "TextToSpeechLanguage": self.text_to_speech_language
        }

    def __rich_repr__(self) -> rich.repr.Result:
        yield "is_stage", self.is_stage
        yield "name", self.name
        yield "variables", self.g_variables
        yield "broadcasts", self.broadcasts
        yield "blocks", self.blocks
        yield "comments", self.comments
        yield "current_costume", self.current_costume
        yield "sounds", self.sounds
        yield "volume", self.volume
        yield "layer_order", self.layer_order
        yield "tempo", self.tempo
        yield "video_transparency", self.video_transparency
        yield "video_state", self.video_state
        yield "text_to_speech_language", self.text_to_speech_language

class Sprite(Target):
    def __init__(self, name, tree, working_directory):
        super().__init__(name, tree, working_directory)
        self.is_stage = False
        self.visible: bool = True
        self.x: int = 0
        self.y: int = 0
        self.size: int = 100
        self.direction: int = 90
        self.draggable: bool = False
        self.rotation_style: str = "all around"

    def render(self, file_buffer):
        return {
            "isStage": self.is_stage,
            "name": self.name,
            "variables": {g_variable.uuid: g_variable.render() for g_variable in self.g_variables.values()},
            "lists": {g_list.uuid: g_list.render() for g_list in self.g_lists},
            "broadcasts": {broadcast.uuid: broadcast.render() for broadcast in self.broadcasts},
            "blocks": self.blocks.project['blocks'],
            "comments": self.comments,
            "current_costume": self.current_costume,
            "costumes": [costume.render(file_buffer) for costume in self.costumes],
            "sounds": [sound.render() for sound in self.sounds],
            "volume": self.volume,
            "layerOrder": self.layer_order,
            "visible": self.visible,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "direction": self.direction,
            "draggable": self.draggable,
            "rotationStyle": self.rotation_style,
        }

    def __rich_repr__(self) -> rich.repr.Result:
        yield "is_stage", self.is_stage
        yield "name", self.name
        yield "variables", self.g_variables
        yield "broadcasts", self.broadcasts
        yield "blocks", self.blocks
        yield "comments", self.comments
        yield "current_costume", self.current_costume
        yield "sounds", self.sounds
        yield "volume", self.volume
        yield "layer_order", self.layer_order
        yield "visible", self.visible
        yield "x", self.x
        yield "y", self.y
        yield "size", self.size
        yield "direction", self.direction
        yield "draggable", self.draggable
        yield "rotation_style", self.rotation_style

class gVariable:
    def __init__(self, name: str):
        self.name: str = name
        self.uuid: str = uid()

    def render(self):
        return [
            self.name,
            0
        ]

class gList:
    def __init__(self, name: str):
        self.name: str = name
        self.uuid: str = uid()

    def render(self):
        return {
            self.name,
            0
        }

class Broadcast:
    def __init__(self, name: str):
        self.name: str = name
        self.uuid: str = uid()

    def render(self):
        return {
            self.name,
            0
        }
