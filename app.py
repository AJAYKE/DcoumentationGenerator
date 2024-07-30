import ast
import csv
import hashlib
import inspect
import os
from ast import NodeTransformer, fix_missing_locations
from typing import Dict, List, Optional, Tuple

import networkx as nx  # type: ignore
from flask import Flask  # type: ignore

# Initialize the CSV for storing processed functions
csv_filename = 'processed_functions.csv'
csv_headers = ['endpoint', 'file_path', 'func_name', 'unique_id', 'docstring']


def generate_unique_id(file_path: str, func_name: str) -> str:
    """Generate a unique ID based on file path and function name."""
    unique_string = f"{file_path}:{func_name}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def extract_api_endpoints(app: Flask) -> Dict[str, List[str]]:
    """Extract all API endpoints from a Flask app."""
    rules = app.url_map.iter_rules()
    endpoints = {rule.endpoint: list(rule.methods) for rule in rules}
    return endpoints


def build_call_graph_for_endpoint(endpoint: str, app: Flask) -> Tuple[nx.DiGraph, Dict[str, str]]:
    """Build a call graph for a specific API endpoint in a Flask app."""
    call_graph = nx.DiGraph()
    func_to_file = {}

    view_func = app.view_functions.get(endpoint)
    if not view_func:
        return call_graph, func_to_file

    file_path = inspect.getfile(view_func)
    try:
        source_lines, start_lineno = inspect.getsourcelines(view_func)
    except OSError:
        return call_graph, func_to_file

    tree = ast.parse(''.join(source_lines))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            call_graph.add_node(func_name)
            func_to_file[func_name] = file_path
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    call_graph.add_edge(func_name, child.func.id)

    return call_graph, func_to_file


def is_function_processed(unique_id: str) -> bool:
    """Check if a function has already been processed based on its unique ID."""
    if not os.path.exists(csv_filename):
        return False
    with open(csv_filename, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        return any(row['unique_id'] == unique_id for row in reader)


def save_function_details(endpoint: str, file_path: str, func_name: str, unique_id: str, docstring: str):
    """Save function details to a CSV file."""
    if not os.path.exists(csv_filename):
        with open(csv_filename, 'w', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(csv_headers)

    with open(csv_filename, 'a', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([endpoint, file_path, func_name, unique_id, docstring])


class DocstringInserter(NodeTransformer):
    """AST transformer to insert a docstring into a function definition."""
    def __init__(self, docstring: str):
        self.docstring = docstring
        self.inserted = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if not self.inserted:
            node.body.insert(0, ast.Expr(value=ast.Constant(value=self.docstring)))
            self.inserted = True
        return node


def get_function_code(file_path: str, func_name: str) -> str:
    """Retrieve the code of a specific function from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                start_lineno = node.lineno - 1
                end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else None
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    return ''.join(lines[start_lineno:end_lineno])
    return ""


def insert_docstring(file_path: str, func_name: str, docstring: str):
    """Insert a docstring into a specific function in a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
        inserter = DocstringInserter(docstring)
        new_tree = inserter.visit(tree)
        fixed_tree = fix_missing_locations(new_tree)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(ast.unparse(fixed_tree))


def generate_docstring(function_code: str, child_context: str = "") -> str:
    """Generate a Google-style Python docstring for a function."""
    prompt = f"""
    Generate a Google-style Python docstring for the following function. Only return the docstring, without any additional text.

    Function code:
    {function_code}

    Context from child functions (if any):
    {child_context}

    Docstring:
    """
    # response = openai.Completion.create(
    #     engine="text-davinci-003",
    #     prompt=prompt.strip(),
    #     max_tokens=150
    # )
    # return response.choices[0].text.strip()
    # Placeholder for actual OpenAI response
    return "Generated docstring"


def process_codebase_by_endpoint(app: Flask, specific_endpoint: Optional[str] = None):
    """Process the codebase by generating docstrings for functions, based on API endpoints."""
    endpoints = extract_api_endpoints(app)

    if specific_endpoint and specific_endpoint not in endpoints:
        print(f"Endpoint {specific_endpoint} not found.")
        return

    selected_endpoints = [specific_endpoint] if specific_endpoint else endpoints.keys()

    for endpoint in selected_endpoints:
        call_graph, func_to_file = build_call_graph_for_endpoint(endpoint, app)

        leaves = [node for node in call_graph if call_graph.out_degree(node) == 0]

        while leaves:
            new_leaves = []
            for func_name in leaves:
                file_path = func_to_file[func_name]
                unique_id = generate_unique_id(file_path, func_name)

                if is_function_processed(unique_id):
                    continue

                function_code = get_function_code(file_path, func_name)
                child_context = ""  # Retrieve context from child functions if any
                docstring = generate_docstring(function_code, child_context)

                insert_docstring(file_path, func_name, docstring)

                save_function_details(endpoint, file_path, func_name, unique_id, docstring)

                call_graph.remove_node(func_name)
                new_leaves.extend([n for n in call_graph.nodes if call_graph.out_degree(n) == 0])

            leaves = new_leaves


# Example usage
app = Flask(__name__)
process_codebase_by_endpoint(app, specific_endpoint=None)
