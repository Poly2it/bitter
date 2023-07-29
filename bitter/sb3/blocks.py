from typing import List, Union, Tuple, TypeAlias, Type, Literal, Callable

from lark import Lark, Token, Transformer, Tree

from lark.visitors import Transformer, Interpreter, Visitor, _Leaf_T

from rich.console import Console

from .primitives import *

from ..terminal import error_collector, ImpossibleError, UnknownObjectError

class Blocks:
    def __init__(self, tree, target):
        self.project = {
            "blocks": {}
        }

        self.tree = tree

        self.target = target

        self.expr_stack: List[Expression] = []
        self.block_stack = []
        self.expr_stack = []

        # when nesting, put the current block stack on hold
        # in the nested stack
        self.nested_block_stacks: List[List] = []
        self.nested_expr_stacks: List[List] = []

        self.console = Console()

        self.functions = {}
        self.function_mutators = {}

    def build(self, parser):
        self.parser = parser
        self.visit_declr(self.tree)

    def visit_declr(self, tree: Tree[Tree]):
        node_has_name: Callable[[Tree[Tree]], bool] = lambda child: child.data == 'declr_function'
        for function in list(filter(node_has_name, tree.children)):
            self.generate_function(function.children[0], function.children[1:-1], function.children[-1], False)
            
        node_has_name: Callable[[Tree[Tree]], bool] = lambda child: child.data == 'declr_function_nowarp'
        for function in list(filter(node_has_name, tree.children)):
            self.generate_function(function.children[0], function.children[1:-1], function.children[-1], True)

        for node in tree.children:
            # self.console.log(node)
            
            node_type: str = node.data
            match node_type:
                case 'declr_costumes':
                    self.declr_costumes(node)

                case 'declr_onflag':
                    # this implementation is naive because Lark should catch
                    # all possible errors in lexing

                    uuid = uuid4().hex
                    block = HatBlock('event_whenflagclicked', {}, {})
                    block.next_block = self.foster_stack(uuid, node.children[0], None)
                    block.uuid = uuid

                    self.block_stack.append(block)

                case 'declr_function':
                    pass
            
                case 'declr_function_nowarp':
                    pass

                case _:
                    error_collector.throw(ImpossibleError(
                        f"{repr(node_type)} is not a known declaration.", 
                        None
                    ))

        self.order()

    def generate_function(self, name, arguments, stack, nowarp):
        definition_uuid = uuid4().hex
        prototype_uuid = uuid4().hex

        definition = HatBlock('procedures_definition', {'custom_block': FunctionReferencePrimitive(prototype_uuid)}, {})
        definition.uuid = definition_uuid

        prototype = ProcedurePrototype(name.value)
        prototype.uuid = prototype_uuid
        prototype.parent = definition_uuid
        prototype.shadow = True
        prototype.warp = not nowarp

        for argument in arguments:
            prototype.add_argument(argument.value)

            self.nest()
            argument_block = Block('argument_reporter_string_number', {}, {'VALUE': InputField(argument.value)})
            argument_block.parent = prototype_uuid
            argument_block.uuid = uuid4().hex
            argument_block.shadow = True
            argument_block_reference = argument_block.uuid
            self.block_stack.append(argument_block)
            self.unnest()

            prototype.inputs.update({prototype.argumentids[-1]: FunctionReferencePrimitive(argument_block_reference)})

        self.block_stack.append(prototype)
        self.order()

        self.functions.update({name.value: ['procedures_call', {prototype_id: 'string' for prototype_id in prototype.argumentids}]})
        self.function_mutators.update(
            {
                name: {
                    'proccode': f"{prototype.name}{''.join((' %s' * len(prototype.argumentnames)))}",
                    'argumentids': prototype.argumentids,
                    'warp': prototype.warp
                }   
            }
        )
        self.function_variables = [argument.value for argument in arguments]

        definition.next_block = self.foster_stack(definition_uuid, stack, name.value)
        self.block_stack.append(definition)
        self.order()

    def declr_costumes(self, node):
        for costume in node.children:
            if not (costume_name := costume.strip("\"")) == costume:
                self.target.add_costume(costume_name)
            else:
                #TODO: supply proper error
                print("Please submit a string literal in declr_costumes.")

    def visit_blocks(self, node, namespace):
        for block in node:
            block_type = block.data
            match block_type:
                case 'block':
                    self.block_stack.append(self.generate_block(block, namespace)) 

                case 'block_if_else':
                    self.generate_branching_block(
                        block, 
                        'control_if_else',
                        [(1, 'SUBSTACK', 'substack'), (2, 'SUBSTACK2', 'substack'), (0, 'CONDITION', 'reference')],
                        namespace
                    )

                case 'repeat':
                    self.generate_branching_block(
                        block, 
                        'control_repeat',
                        [(0, 'TIMES', 'positive_integer'), (1, 'SUBSTACK', 'substack')],
                        namespace
                    )

                case 'until':
                    self.generate_branching_block(
                        block, 
                        'control_repeat_until',
                        [(0, 'CONDITION', 'reference'), (1, 'SUBSTACK', 'substack')],
                        namespace
                    )

                case 'forever':
                    self.generate_branching_block(
                        block, 
                        'control_forever',
                        [(0, 'SUBSTACK', 'substack')],
                        namespace
                    )

                case 'localvar':
                    uuid = uuid4().hex

                    variable_name = block.children[0].value
                    variable_uuid = self.target.ensure_variable(variable_name, namespace)
                    assert variable_uuid is not None

                    variable_data = self.foster_expr(uuid, block.children[1], 'string', namespace)
                    variable_data_primitive = validate_arg(variable_data, 'string', self.target)

                    generated = Block('data_setvariableto', {'VALUE': variable_data_primitive}, {'VARIABLE': VariableField(f"{namespace}.{variable_name}", variable_uuid)})
                    generated.uuid = uuid

                    self.block_stack.append(generated)

                case 'varset':
                    uuid = uuid4().hex

                    variable_name = block.children[0].value
                    variable_uuid = self.target.ensure_variable(variable_name, None)
                    assert variable_uuid is not None

                    variable_data = self.foster_expr(uuid, block.children[1], 'string', namespace)
                    variable_data_primitive = validate_arg(variable_data, 'string', self.target)

                    generated = Block('data_setvariableto', {'VALUE': variable_data_primitive}, {'VARIABLE': VariableField(variable_name, variable_uuid)})
                    generated.uuid = uuid

                    self.block_stack.append(generated)

                case _:
                    error_collector.throw(ImpossibleError(
                        f"The node type of {repr(block_type)} is not known.",
                        None
                    ))

    def generate_branching_block(self, block, opcode: str, input_order: List[Tuple[int, str, str]], namespace):
        uuid = uuid4().hex

        expressions = block.children

        inputs = {}
        for key, name, g_type in input_order:
            expression = expressions[key]
            if g_type == 'substack':
                reference = self.foster_stack(uuid, expression, namespace)
                g_type = 'reference'

            else:
                reference = self.foster_expr(uuid, expression, g_type, namespace)

            primitive = validate_arg(reference, g_type, self.target)

            inputs.update({name: primitive})

        generated = Block(opcode, inputs, {})
        generated.uuid = uuid

        self.block_stack.append(generated)

    def generate_block(self, block, namespace) -> Block:
        block_name = block.children[0]
        
        expressions = []
        if len(block.children) > 2:
            expressions = block.children[1:-1]
        lcomment = block.children[-1]
        
        uuid = uuid4().hex

        if block_name in BLOCKS:
            frame = BLOCKS[block_name]
            input_types = list(frame[1].values())
            input_names = list(frame[1].keys())

            if len(expressions) > len(input_types) and expressions[-1] is not None:
                block_explanation = None
                if len(input_types) == 0:
                    block_explanation = f"{repr(block_name.value)} takes 0 arguments, got {len(expressions)}."
                if len(input_types) == 1:
                    block_explanation = f"{repr(block_name.value)} takes 1 argument: {pretty_join(input_types)}, got {len(expressions)}."
                if len(input_types) > 1:
                    block_explanation = f"{repr(block_name.value)} takes {len(input_types)} arguments: {pretty_join(input_types)}, got {len(expressions)}."

                assert block_explanation is not None

                error_collector.throw(UnknownObjectError(
                    f"Block was supplied with too many arguments.\n{block_explanation}",
                    error_collector.patch_after(block_name.line, block_name.column, block_name.value, self.parser),
                    (block_name.line, block_name.column)
                ))

            expression_primitives = []
            for expression, target_type in zip(expressions, input_types):
                primitive = self.foster_expr(uuid, expression, target_type, namespace)
                if isinstance(primitive, BaseExpression):
                    expression_primitives.append(Shadow(primitive, generate_default_primitive(target_type)))
                else:
                    expression_primitives.append(primitive)

            inputs = {input_names[index]: arg for index, arg in enumerate(validate_args(expression_primitives, input_types, self.target))}

            block = Block(frame[0], inputs, {})
            block.uuid = uuid

            return block

        elif block_name in self.functions:
            frame = self.functions[block_name]
            input_types = list(frame[1].values())
            input_names = list(frame[1].keys())

            if len(expressions) > len(input_types) and expressions[-1] is not None:
                block_explanation = None
                if len(input_types) == 0:
                    block_explanation = f"{repr(block_name.value)} takes 0 arguments, got {len(expressions)}."
                elif len(input_types) == 1:
                    block_explanation = f"{repr(block_name.value)} takes 1 argument, got {len(expressions)}."
                elif len(input_types) > 1:
                    block_explanation = f"{repr(block_name.value)} takes {len(input_types)} arguments, got {len(expressions)}."

                assert block_explanation is not None

                error_collector.throw(UnknownObjectError(
                    f"Function was supplied with too many arguments.\n{block_explanation}",
                    error_collector.patch_after(block_name.line, block_name.column, block_name.value, self.parser),
                    (block_name.line, block_name.column)
                ))

            expression_primitives = []
            for expression, target_type in zip(expressions, input_types):
                expression_primitives.append(self.foster_expr(uuid, expression, target_type, namespace))

            inputs = {input_names[index]: arg for index, arg in enumerate(validate_args(expression_primitives, input_types, self.target))}

            block = ProcedureCall(frame[0], inputs)
            block.mutate(self.function_mutators[block_name])
            block.uuid = uuid

            return block

        else:
            print(self.functions)

            closest_match = difflib.get_close_matches(block_name, BLOCKS.keys(), n=1)
            error_collector.throw(UnknownObjectError(
                f"{repr(block_name.value)} is not a known function or block.", 
                f"Did you mean {repr(closest_match[0])}?" if len(closest_match) > 0 else None, 
                (block_name.line, block_name.column)
            ))

            block = Block("error", {}, {})
            block.uuid = uuid

            return block


    def generate_operator(self, block, namespace) -> Block:
        block_name = block.children[0]
        
        expressions = []
        if len(block.children) > 1:
            expressions = block.children[1:]
        uuid = uuid4().hex

        if block_name in OPERATORS:
            frame = OPERATORS[block_name]
            input_types = list(frame[1].values())
            input_names = list(frame[1].keys())

            expression_primitives = []
            for expression, target_type in zip(expressions, input_types):
                expression_primitives.append(self.foster_expr(uuid, expression, target_type, namespace))

            inputs = {input_names[index]: arg for index, arg in enumerate(validate_args(expression_primitives, input_types, self.target))}


            block = Block(frame[0], inputs, frame[2])
            block.uuid = uuid

            return block

        else:
            closest_match = difflib.get_close_matches(block_name, OPERATORS.keys(), n=1)
            error_collector.throw(UnknownObjectError(
                f"{repr(block_name.value)} is not a known operator.", 
                f"Did you mean {repr(closest_match[0])}?" if len(closest_match) > 0 else None, 
                (block_name.line, block_name.column)
            ))

            block = Block("error", {}, {})
            block.uuid = uuid

            return block

    def generate_inline_operator(self, block, namespace) -> Block:
        block_name = block.data
        
        expressions = block.children
        uuid = uuid4().hex

        if block_name in OPERATORS:
            frame = OPERATORS[block_name]
            input_types = list(frame[1].values())
            input_names = list(frame[1].keys())

            expression_primitives = []
            for expression, target_type in zip(expressions, input_types):
                expression_primitives.append(self.foster_expr(uuid, expression, target_type, namespace))
                try:
                    assert expression_primitives[-1] is not None
                except AssertionError as e:
                    error_collector.throw(ImpossibleError(
                        f"Expression primitive in inline operator had None value.",
                        None, 
                        None
                    ))

            inputs = {input_names[index]: arg for index, arg in enumerate(validate_args(expression_primitives, input_types, self.target))}

            block = Block(frame[0], inputs, frame[2])
            block.uuid = uuid

            return block

        else:
            closest_match = difflib.get_close_matches(block_name, OPERATORS.keys(), n=1)
            error_collector.throw(UnknownObjectError(
                f"{repr(block_name)} is not a known operator.", 
                f"Did you mean {repr(closest_match[0])}?" if len(closest_match) > 0 else None, 
                None
            ))

            block = Block("error", {}, {})
            block.uuid = uuid

            return block

    def visit_expr(self, expr, parent_uuid, target_type, namespace):
        expr_type = expr.data
        match expr_type:
            case 'eq':
                uuid = uuid4().hex

                expr_1 = expr.children[0]
                expr_2 = expr.children[1]

                expr_1_primitive = self.foster_expr(uuid, expr_1, target_type, namespace)
                expr_2_primitive = self.foster_expr(uuid, expr_2, target_type, namespace)

                operand_1, operand_2 = validate_args((expr_1_primitive, expr_2_primitive), ('number', 'number'), self.target)

                generated = Block('operator_equals', {'OPERAND1': operand_1, 'OPERAND2': operand_2}, {})
                generated.uuid = uuid

                self.block_stack.append(generated)

            case 'lt' | 'gt' | 'add' | 'sub' | 'mul' | 'div' | 'notop':
                self.block_stack.append(self.generate_inline_operator(expr, namespace))

            case 'minus': # minus is a special case operator when compiling for example '--1'
                uuid = uuid4().hex

                expr_2 = expr.children[0]

                expr_1_primitive = 0
                expr_2_primitive = self.foster_expr(uuid, expr_2, target_type, namespace)

                number_1, number_2 = validate_args((expr_1_primitive, expr_2_primitive), ('number', 'number'), self.target)

                generated = Block('operator_subtract', {'NUM1': number_1, 'NUM2': number_2}, {})
                generated.uuid = uuid

                self.block_stack.append(generated)

            case 'argument':
                uuid = uuid4().hex

                variable_token = expr.children[0]
                variable_name = variable_token.value[1:]

                if namespace is not None and variable_name in self.function_variables:
                    argument_ids = list(self.functions[namespace][1].keys())
                    this_argument_id = argument_ids[self.function_variables.index(variable_name)]

                    self.nest()
                    argument_block = Block('argument_reporter_string_number', {}, {'VALUE': InputField(variable_name)})
                    argument_block.parent = parent_uuid
                    argument_block.uuid = uuid4().hex
                    argument_block_reference = argument_block.uuid
                    self.block_stack.append(argument_block)
                    self.unnest()

                    variable_primitive = Shadow(BlockPrimitive(argument_block_reference), generate_default_primitive(target_type))

                    self.expr_stack.append(variable_primitive)
                else:
                    error_collector.throw(UnknownObjectError(
                        f"{repr(variable_name)} is not a function argument.",
                        None,
                        (variable_token.line, variable_token.column)
                    ))

            case 'var':
                uuid = uuid4().hex

                variable_token = expr.children[0]
                variable_name = variable_token.value

                if self.target.local_variable_uuid_if_exists(variable_name, namespace) is not None:
                    variable_primitive = VariablePrimitive(f"{namespace}.{variable_name}", uuid)
                    
                    self.expr_stack.append(variable_primitive)

                elif namespace is not None and variable_name in self.function_variables:
                    argument_ids = list(self.functions[namespace][1].keys())
                    this_argument_id = argument_ids[self.function_variables.index(variable_name)]

                    self.nest()
                    argument_block = Block('argument_reporter_string_number', {}, {'VALUE': InputField(variable_name)})
                    argument_block.parent = parent_uuid
                    argument_block.uuid = uuid4().hex
                    argument_block_reference = argument_block.uuid
                    self.block_stack.append(argument_block)
                    self.unnest()

                    variable_primitive = Shadow(BlockPrimitive(argument_block_reference), generate_default_primitive(target_type))

                    self.expr_stack.append(variable_primitive)

                elif namespace is not None:
                    self.target.ensure_variable(variable_name, None)
                    variable_primitive = VariablePrimitive(variable_name, uuid)
                    
                    self.expr_stack.append(variable_primitive)

                elif self.target.global_variable_uuid_if_exists(variable_name) is not None:
                    variable_primitive = VariablePrimitive(variable_name, uuid)
                    
                    self.expr_stack.append(variable_primitive)
                else:
                    error_collector.throw(UnknownObjectError(
                        f"{repr(variable_name)} has not been defined.\nDefined currently {'are' if len(self.target.g_variables) > 1 else 'is'} {pretty_repr_join(list(self.target.g_variables.keys()))}.",
                        None,
                        (variable_token.line, variable_token.column)
                    ))

            case 'reporter':
                self.block_stack.append(self.generate_operator(expr, namespace)) 

            case 'expr':
                data = expr.children[0]
                if isinstance(data, Tree):
                    self.visit_expr(data, parent_uuid, target_type, namespace)
                else:
                    data_type = data.type
                    literal = self.extract_literal(data.value, data_type)
                    assert literal is not None
                    self.expr_stack.append(literal)

            case _:
                error_collector.throw(ImpossibleError(
                    f"The expression type of {repr(expr_type)} is not known.",
                    None
                ))

    def extract_literal(self, data, data_type):
        """
        Extract the inner data from a literal.
        """

        match data_type:
            case 'NUMBER':
                return data
            case 'FLOAT':
                return data
            case 'STRING':
                if not (inner_string := data.strip("\"")) == data:
                    return inner_string
                else:
                    error_collector.throw(ImpossibleError(
                        f"Could not extract literal from {inner_string}; matches {data}.",
                        None
                    ))
            case _:
                error_collector.throw(ImpossibleError(
                    f"{data_type} could not be matched to any literal.",
                    None
                ))


    def foster_expr(self, parent_uuid, expr, target_type, namespace) -> Union[str, Expression, None]:
        """
        Either turn an expression into blocks onto the project, or a returned literal.
        Sets the parent of the fostered expression to the uuid supplied to this function.

        Returns
        -------
        either:
        -   uuid  
                uuid of the rendered block
        -   literal  
                a rendered literal of the child
        """

        # nest
        self.nested_block_stacks.append(self.block_stack)
        self.block_stack = []
        self.nested_expr_stacks.append(self.expr_stack)
        self.expr_stack = []

        # recursively run everything on the child
        self.visit_expr(expr, parent_uuid, target_type, namespace)

        # make parent adopt child
        if len(self.block_stack) > 0:
            self.block_stack[-1].parent = parent_uuid

            child_reference = ReferencePrimitive(self.block_stack[-1].uuid)

        elif len(self.expr_stack) > 0:
            child_reference = self.expr_stack[-1]

        else:
            child_reference = None

        # render child
        self.order()

        # exit nest
        self.block_stack = self.nested_block_stacks[-1]
        self.nested_block_stacks.pop(-1)
        self.expr_stack = self.nested_expr_stacks[-1]
        self.nested_expr_stacks.pop(-1)

        return child_reference

    def foster_stack(self, parent_uuid, stack, namespace) -> Union[None, str]:
        """
        Render a stack onto the project.
        Sets the parent of the fostered expression to the uuid supplied to this function.

        Returns
        -------
        -   uuid  
                uuid of the rendered stack parent
        """

        # nest
        self.nested_block_stacks.append(self.block_stack)
        self.block_stack = []

        # recursively run everything on the child
        self.visit_blocks(stack.children, namespace)

        # make parent adopt child
        if len(self.block_stack) > 0:
            self.block_stack[0].parent = parent_uuid

            child_reference = self.block_stack[0].uuid
        else:
            child_reference = None

        # render child
        self.order()

        # exist nest
        self.block_stack = self.nested_block_stacks[-1]
        self.nested_block_stacks.pop(-1)

        return child_reference

    def order(self):
        for succeeding, current, preceeding in zip(
            [*self.block_stack, None, None][1:-1],
            [None, *self.block_stack, None][1:-1],
            [None, None, *self.block_stack][1:-1]
        ):
            # At this point, some blocks already have their parent flag set, hence
            # we don't replace the value with None from the Lists above 
            if preceeding is not None:
                if current.parent is None:
                    current.parent = preceeding.uuid
            if succeeding is not None:
                if current.next_block is None:
                    current.next_block = succeeding.uuid

        render = {block.uuid: block.render().get(block.uuid) for block in self.block_stack}
        self.project['blocks'].update(render)
        self.block_stack = [] 

    def nest(self):
        self.nested_block_stacks.append(self.block_stack)
        self.block_stack = []

    def unnest(self):
        self.order()
        self.block_stack = self.nested_block_stacks[-1]
        self.nested_block_stacks.pop(-1)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "blocks", self.project['blocks']
        