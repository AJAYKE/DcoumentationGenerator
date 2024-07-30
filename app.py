import ast
import os
from ast import NodeTransformer, fix_missing_locations

import networkx as nx  # type: ignore
import openai  # type: ignore

openai.api_key = 'your-openai-api-key'

class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}
        self.current_func = None

    def visit_FunctionDef(self, node):
        func_name = node.name
        self.functions[func_name] = node
        self.current_func = func_name
        self.generic_visit(node)
        self.current_func = None

    def visit_Call(self, node):
        if self.current_func and isinstance(node.func, ast.Name):
            called_func = node.func.id
        self.generic_visit(node)

def extract_functions_from_file(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)
        collector = FunctionCollector()
        collector.visit(tree)
    return collector.functions

def build_call_graph(dir_path):
    call_graph = nx.DiGraph()
    func_to_file = {}

    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                functions = extract_functions_from_file(file_path)
                for func_name, func_node in functions.items():
                    call_graph.add_node(func_name, filepath=file_path)
                    func_to_file[func_name] = file_path
                    for call in ast.walk(func_node):
                        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                            called_func = call.func.id
                            call_graph.add_edge(func_name, called_func)

    return call_graph, func_to_file

def generate_docstring(function_code, child_context=""):
    prompt = f"""
    Generate a Google-style Python docstring for the following function. Only return the docstring, without any additional text.

    Function code:
    {function_code}

    Context from child functions (if any):
    {child_context}

    Docstring:
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt.strip(),
        max_tokens=150
    )
    return response.choices[0].text.strip()

class DocstringInserter(NodeTransformer):
    def __init__(self, docstring):
        self.docstring = docstring
        self.inserted = False

    def visit_FunctionDef(self, node):
        if not self.inserted:
            node.body.insert(0, ast.Expr(value=ast.Constant(value=self.docstring)))
            self.inserted = True
        return node

def get_function_code(file_path, func_name):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                start_lineno = node.lineno - 1
                end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else None
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    function_code = ''.join(lines[start_lineno:end_lineno])
                    return function_code
    return ""

def insert_docstring(file_path, func_name, docstring):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)
        inserter = DocstringInserter(docstring)
        new_tree = inserter.visit(tree)
        fixed_tree = fix_missing_locations(new_tree)

    with open(file_path, 'w') as file:
        file.write(ast.unparse(fixed_tree))

def process_codebase(dir_path):
    call_graph, func_to_file = build_call_graph(dir_path)

    # Process leaf functions first
    leaves = [node for node in call_graph if call_graph.out_degree(node) == 0]

    while leaves:
        new_leaves = []
        for func_name in leaves:
            file_path = func_to_file[func_name]
            function_code = get_function_code(file_path, func_name)

            # Generate docstring
            child_context = ""
            if call_graph.in_degree(func_name) > 0:
                parent_funcs = list(call_graph.predecessors(func_name))
                for parent in parent_funcs:
                    # Optionally, retrieve child context information here
                    pass
            docstring = generate_docstring(function_code, child_context)

            # Insert docstring into the function and save the file
            insert_docstring(file_path, func_name, docstring)

            # Remove the processed node from the graph
            call_graph.remove_node(func_name)

            # Check for new leaves
            new_leaves.extend([n for n in call_graph.nodes if call_graph.out_degree(n) == 0])

        leaves = new_leaves

# Example usage
process_codebase('path/to/your/codebase')
