from dataclasses import dataclass, field

from typing import Dict, Union, TypeAlias

from rich.console import Console

from json import dumps

from uuid import uuid4

import difflib

import rich.repr

from .utils import uid

from ..terminal import *

@dataclass
class FunctionReferencePrimitive:
    uuid: str
    
    def render(self):
        return [
            1,
            self.uuid
        ]

@dataclass
class ReferencePrimitive:
    uuid: str
    
    def render(self):
        return [
            2,
            self.uuid
        ]

@dataclass
class NumberPrimitive:
    value: Union[float, int]
    
    def render(self):
        return [
            1,
            [
                4,
                repr(self.value)
            ]
        ]

@dataclass
class PositiveNumberPrimitive:
    value: Union[float, int]
    
    def render(self):
        return [
            1,
            [
                5,
                repr(self.value)
            ]
        ]

@dataclass
class IntegerPrimitive:
    value: int
    
    def render(self):
        return [
            1,
            [
                7,
                repr(self.value)
            ]
        ]

@dataclass
class PositiveIntegerPrimitive:
    value: int
    
    def render(self):
        return [
            1,
            [
                6,
                repr(self.value)
            ]
        ]

@dataclass
class AnglePrimitive:
    value: int
    
    def render(self):
        return [
            1,
            [
                8,
                repr(self.value)
            ]
        ]

@dataclass
class ColorPrimitive:
    r: int
    g: int
    b: int
    
    def render(self):
        return [
            1,
            [
                9,
                f"#{self.r:02x}{self.g:02x}{self.b:02x}"
            ]
        ]

@dataclass
class StringPrimitive:
    value: str
    
    def render(self):
        return [
            1,
            [
                10,
                self.value
            ]
        ]
        
@dataclass
class BroadcastPrimitive:
    name: str
    uuid: str
    
    def render(self):
        return [
            1,
            [
                11,
                self.name
            ]
        ]


@dataclass
class VariablePrimitive:
    name: str
    uuid: str
    
    def render(self):
        return [
            3,
            [
                12,
                self.name,
                self.uuid
            ],
            [
                 # TODO: put correct type here
                4,
                "0"
            ]
        ]


@dataclass
class ListPrimitive:
    name: str
    uuid: str
    
    def render(self):
        return [
            3,
            [
                13,
                self.name,
                self.uuid
            ],
            [
                # TODO: put correct type here
                4,
                "0"
            ]
        ]

@dataclass
class BlockPrimitive:
    uuid: str
    
    def render(self):
        return [
            1,
            self.uuid
        ]

@dataclass
class ErrorPrimitive:
    def render(self):
        return [
            None
        ]

BaseExpression: TypeAlias = Union[ReferencePrimitive,
                                  FunctionReferencePrimitive,
                                  NumberPrimitive, 
                                  PositiveNumberPrimitive,
                                  IntegerPrimitive,
                                  PositiveIntegerPrimitive,
                                  AnglePrimitive,
                                  ColorPrimitive,
                                  StringPrimitive,
                                  BroadcastPrimitive,
                                  VariablePrimitive,
                                  ListPrimitive,
                                  BlockPrimitive,
                                  ErrorPrimitive,
                                  None]

@dataclass
class Shadow:
    front: BaseExpression 
    back: BaseExpression

    def render(self):
        assert self.front is not None
        assert self.back is not None

        return [
            3,
            self.front.render()[1],
            self.back.render()[1]
        ]

Expression: TypeAlias = Union[ReferencePrimitive,
                              FunctionReferencePrimitive,
                              NumberPrimitive, 
                              PositiveNumberPrimitive,
                              IntegerPrimitive,
                              PositiveIntegerPrimitive,
                              AnglePrimitive,
                              ColorPrimitive,
                              StringPrimitive,
                              BroadcastPrimitive,
                              VariablePrimitive,
                              ListPrimitive,
                              BlockPrimitive,
                              ErrorPrimitive,
                              Shadow]

@dataclass
class VariableField:
    name: str
    uuid: str

    def render(self):
        return [
            self.name,
            self.uuid
        ]

@dataclass
class InputField:
    name: str

    def render(self):
        return [
            self.name,
            None
        ]

HATS = {
    # Motion
    "onflag": ["event_whenflagclicked", {}, {}]
}

BLOCKS = {
    # Motion
    "move":           ["motion_movesteps",        {"STEPS": "number"},                              {}],
    "turnright":      ["motion_turnright",        {"DEGREES": "number"},                            {}],
    "turnleft":       ["motion_turnleft",         {"DEGREES": "number"},                            {}],
    "goto":           ["motion_gotoxy",           {"X": "number", "Y": "number"},                   {}],
    "glide":          ["motion_glidesecstoxy",    {"SECS": "number", "X": "number", "Y": "number"}, {}],
    "point":          ["motion_pointindirection", {"DIRECTION": "angle"},                           {}],
    "changex":        ["motion_changexby",        {"DX": "number"},                                 {}],
    "setx":           ["motion_setx",             {"X": "number"},                                  {}],
    "changey":        ["motion_changeyby",        {"DY": "number"},                                 {}],
    "sety":           ["motion_sety",             {"Y": "number"},                                  {}],
    "ifonedgebounce": ["motion_ifonedgebounce",   {},                                               {}],

    # Looks
    "say": ["looks_say", {"MESSAGE": "string"}, {}],

    # Sound

    # Events

    # Control
    "wait": ["control_wait", {"DURATION": "positive_number"}, {}],

    # Sensing

    # Variables

    # Lists

    # Pen
    "clear":         ["pen_clear",              {},                 {}],
    "stamp":         ["pen_stamp",              {},                 {}],
    "pendown":       ["pen_penDown",            {},                 {}],
    "penup":         ["pen_penUp",              {},                 {}],
    "setpencolor":   ["pen_setPenColorToColor", {"COLOR": "color"}, {}],
    "setpensize":    ["pen_setPenSizeTo",       {"SIZE": "number"}, {}],
    "changepensize": ["pen_changePenSizeBy",    {"SIZE": "number"}, {}],
}

OPERATORS = {
    # Motion

    # Looks

    # Sound

    # Events

    # Control

    # Operators
    'eq':     ['operator_equals',   {'OPERAND1': 'string', 'OPERAND2': 'string'}, {}                             ],
    'gt':     ['operator_gt',       {'OPERAND1': 'string', 'OPERAND2': 'string'}, {}                             ],
    'lt':     ['operator_lt',       {'OPERAND1': 'string', 'OPERAND2': 'string'}, {}                             ],
                             
    'notop':  ['operator_not',      {'OPERAND': 'block'},                         {}                             ],
                             
    'add':    ['operator_add',      {'NUM1': 'number', 'NUM2': 'number'},         {}                             ],
    'sub':    ['operator_subtract', {'NUM1': 'number', 'NUM2': 'number'},         {}                             ],
    'mul':    ['operator_multiply', {'NUM1': 'number', 'NUM2': 'number'},         {}                             ],
    'div':    ['operator_divide',   {'NUM1': 'number', 'NUM2': 'number'},         {}                             ],
                             
    'random': ['operator_random',   {'FROM': 'number', 'TO': 'number'},           {}                             ],

    'sin':    ['operator_mathop',   {'NUM': 'number'},                            {'OPERATOR': InputField('sin')}],

    # Sensing
    "mousex": ["sensing_mousex",    {},                                           {}                             ],
    "mousey": ["sensing_mousey",    {},                                           {}                             ],

    # Variables

    # Lists
}

@dataclass
class Block:
    opcode: str
    inputs: Dict[str, Expression]
    fields: dict
    next_block: Union[None, str] = None
    parent: Union[None, str] = None
    uuid: Union[None, str] = None
    shadow: bool = False
    top_level: bool = False
    block_type: str = 'block'

    def __rich_repr__(self) -> rich.repr.Result:
        yield "uuid", self.uuid
        yield "opcode", self.opcode
        yield "next_block", self.next_block
        yield "parent", self.parent
        yield "inputs", self.inputs
        yield "fields", self.fields
        yield "shadow", self.shadow
        yield "top_level", self.top_level

    def render(self):
        return {
            self.uuid: {
                "opcode": self.opcode,
                "next": self.next_block,
                "parent": self.parent,
                "inputs": {name: item.render() for name, item in self.inputs.items()},
                "fields": {name: item.render() for name, item in self.fields.items()},
                "shadow": self.shadow,
                "topLevel": self.top_level,
            }
        }

@dataclass
class HatBlock(Block):
    top_level: bool = True
    x: int = 0
    y: int = 0
    block_type: str = 'hat'

    def __rich_repr__(self) -> rich.repr.Result:
        yield "uuid", self.uuid
        yield "opcode", self.opcode
        yield "next_block", self.next_block
        yield "parent", self.parent
        yield "inputs", self.inputs
        yield "fields", self.fields
        yield "shadow", self.shadow
        yield "top_level", self.top_level
        yield "x", self.x
        yield "y", self.y

    def render(self):
        return {
            self.uuid: {
                "opcode": self.opcode,
                "next": self.next_block,
                "parent": self.parent,
                "inputs": {name: item.render() for name, item in self.inputs.items()},
                "fields": {name: item.render() for name, item in self.fields.items()},
                "shadow": self.shadow,
                "topLevel": self.top_level,
                "x": self.x,
                "y": self.y
            }
        }

class ProcedurePrototype(Block):
    def __init__(self, name):
        super().__init__('procedures_prototype', {}, {})
        
        self.name: str = name

        self.argumentids: List[str] = []
        self.argumentnames: List[str] = []
        self.argumentdefaults: List[Union[str, bool]] = []
        self.warp: bool = True

    def add_argument(self, name):
        self.argumentids.append(uid())
        self.argumentnames.append(name)
        self.argumentdefaults.append('')

    def render(self):
        #self.argumentdefaults.append("false")
        return {
            self.uuid: {
                "opcode": self.opcode,
                "next": self.next_block,
                "parent": self.parent,
                "inputs": {name: item.render() for name, item in self.inputs.items()},
                "fields": {name: item.render() for name, item in self.fields.items()},
                "shadow": self.shadow,
                "topLevel": self.top_level,
                "mutation": {
                    "tagName": "mutation",
                    "children": [],
                    "proccode": f"{self.name}{''.join((' %s' * len(self.argumentnames)))}",
                    "argumentids": dumps(self.argumentids, separators=(',', '')),
                    "argumentnames": dumps(self.argumentnames, separators=(',', '')),
                    "argumentdefaults": dumps(self.argumentdefaults, separators=(',', '')),
                    "warp": dumps(self.warp, separators=(',', ''))
                }
            }
        }

class ProcedureCall(Block):
    def __init__(self, name, inputs):
        super().__init__('procedures_call', inputs, {})
        
        self.proccode: str = ''
        self.argumentids: List[str] = []
        self.warp: bool = True

    def mutate(self, mutators: Dict):
        self.proccode = mutators['proccode']
        self.argumentids = mutators['argumentids']
        self.warp = mutators['warp']

    def render(self):
        return {
            self.uuid: {
                "opcode": self.opcode,
                "next": self.next_block,
                "parent": self.parent,
                "inputs": {name: item.render() for name, item in self.inputs.items()},
                "fields": {name: item.render() for name, item in self.fields.items()},
                "shadow": self.shadow,
                "topLevel": self.top_level,
                "mutation": {
                    "tagName": "mutation",
                    "children": [],
                    "proccode": self.proccode,
                    "argumentids": dumps(self.argumentids, separators=(',', '')),
                    "warp": dumps(self.warp, separators=(',', ''))
                }
            }
        }

def validate_arg(arg, target_type, target):
    return validate_args((arg,), (target_type,), target)[0]

def validate_args(args, target_types, target):
    if len(args) > len(target_types):
        error_collector.throw(ArgumentError(
            f"Too many arguments supplied, requested {len(target_types)}, got {len(args)} ({pretty_repr_join(args)}).", 
            f"The requested types are {pretty_join(target_types)}, {len(target_types)} in total.", 
            None
        ))
        args = args[:len(target_types)]

    if len(args) < len(target_types):
        error_collector.throw(ArgumentError(
            f"Too few arguments supplied, requested {len(target_types)}, got {len(args)}.", 
            f"Add {len(target_types) - len(args)} argument{'s' if len(target_types) - len(args) > 0 else ''}.", 
            None
        ))
        args = list(args)
        args += [None] * (len(target_types) - len(args))

    casted_args = []
    for arg, target_type in zip(args, target_types):
        if isinstance(cast := cast_arg(arg, target_type, target), ErrorPrimitive):
            # TODO: Implement proper error handler
            error_collector.throw(gTypeError(
                f"Can't cast {repr(arg)} to {target_type}.", 
                f"Replace the value in the input with a {target_type.replace('_', ' ')}.", 
                None
            ))
        casted_args.append(cast)

    return tuple(casted_args)

def cast_arg(arg, target_type, target):
    if isinstance(arg, Shadow | BlockPrimitive | FunctionReferencePrimitive | ReferencePrimitive | VariablePrimitive):
        return arg
        
    match target_type:
        case 'number':
            try:
                cast = float(arg) if float(arg) % 1 > 0 else int(arg)
                return NumberPrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case 'positive_number':
            try:
                assert (cast := float(arg) if float(arg) % 1 > 0 else int(arg)) >= 0
                return PositiveNumberPrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case 'integer':
            try:
                cast = int(arg)
                return IntegerPrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case 'positive_integer':
            try:
                assert (cast := int(arg)) >= 0
                return PositiveIntegerPrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case 'angle':
            try:
                assert 0 <= (cast := int(arg)) <= 360
                return AnglePrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case 'functionreference':
            try:
                cast = str(arg)
                return FunctionReferencePrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case 'reference':
            try:
                cast = str(arg)
                return ReferencePrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case 'string':
            try:
                cast = str(arg)
                return StringPrimitive(cast)
            except:
                cast = ErrorPrimitive()

        case _:
            error_collector.throw(ImpossibleError(
                f"{repr(arg)} can't be cast to non-existant type {repr(target_type)}.", 
                None
            ))

            cast = None
            
    return cast

def generate_default_primitive(target_type):
    match target_type:
        case 'number':
            return NumberPrimitive(0)

        case 'positive_number':
            return PositiveNumberPrimitive(0)

        case 'integer':
            return IntegerPrimitive(0)

        case 'positive_integer':
            return PositiveIntegerPrimitive(0)

        case 'angle':
            return AnglePrimitive(0)

        case 'string':
            return StringPrimitive('')

        case _:
            error_collector.throw(ImpossibleError(
                f"{repr(target_type)} has no default.", 
                None
            ))

            cast = None
            
    return cast
