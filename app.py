import ast
import csv
import hashlib
import inspect
from typing import Dict, List, Optional

import networkx as nx  # type: ignore
from flask import Flask  # type: ignore

# Initialize the CSV for storing processed functions
csv_filename = 'processed_functions.csv'
csv_headers = ['endpoint', 'file_path', 'func_name', 'unique_id', 'docstring']

# Function to generate unique ID based on file and function name
def generate_unique_id(file_path: str, func_name: str) -> str:
    unique_string = f"{file_path}:{func_name}"
    return hashlib.md5(unique_string.encode()).hexdigest()

# Function to extract API endpoints from a Flask app
def extract_api_endpoints(app: Flask) -> Dict[str, List[str]]:
    rules = app.url_map.iter_rules()
    endpoints = {rule.endpoint: list(rule.methods) for rule in rules}
    return endpoints

# Function to build the function call graph for a specific API endpoint
def build_call_graph_for_endpoint(endpoint: str, app: Flask) -> nx.DiGraph:
    call_graph = nx.DiGraph()
    func_to_file = {}
    
    # Inspect the app to find the function corresponding to the endpoint
    view_func = app.view_functions.get(endpoint)
    if not view_func:
        return call_graph, func_to_file
    
    file_path = inspect.getfile(view_func)
    source_lines, start_lineno = inspect.getsourcelines(view_func)
    
    # Parse the source file to build the call graph
    tree = ast.parse(''.join(source_lines))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            call_graph.add_node(func_name)
            func_to_file[func_name] = file_path
            # Add edges for function calls within this function
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    call_graph.add_edge(func_name, child.func.id)
    
    return call_graph, func_to_file

# Function to check if a function has already been processed
def is_function_processed(unique_id: str) -> bool:
    try:
        with open(csv_filename, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            return any(row['unique_id'] == unique_id for row in reader)
    except FileNotFoundError:
        return False

# Function to save function details to the CSV
def save_function_details(endpoint: str, file_path: str, func_name: str, unique_id: str, docstring: str):
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([endpoint, file_path, func_name, unique_id, docstring])

class DocstringInserter(ast.NodeTransformer):
    def __init__(self, docstring):
        self.docstring = docstring
        self.inserted = False

    def visit_FunctionDef(self, node):
        if not self.inserted:
            node.body.insert(0, ast.Expr(value=ast.Constant(value=self.docstring)))
            self.inserted = True
        return node

def get_function_code(file_path, func_name):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                start_lineno = node.lineno - 1
                end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else None
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    function_code = ''.join(lines[start_lineno:end_lineno])
                    return function_code
    return ""

def insert_docstring(file_path, func_name, docstring):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
        inserter = DocstringInserter(docstring)
        new_tree = inserter.visit(tree)
        fixed_tree = ast.fix_missing_locations(new_tree)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(ast.unparse(fixed_tree))

def generate_docstring(function_code, child_context=""):
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

def fetch_docstring_from_csv(unique_id: str) -> Optional[str]:
    with open(csv_filename, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row['unique_id'] == unique_id:
                return row['docstring']
    return None

# Function to get the child context for a function
def get_child_context(call_graph: nx.DiGraph, func_name: str, func_to_file: Dict[str, str], processed_functions: Dict[str, str]) -> str:
    child_context = ""
    for child in call_graph.successors(func_name):
        child_file_path = func_to_file[child]
        child_unique_id = generate_unique_id(child_file_path, child)
        child_docstring = processed_functions.get(child_unique_id)
        if child_docstring:
            child_context += f"Function: {child}\nDocstring: {child_docstring}\n\n"
    return child_context

# Main function to process the codebase based on API endpoints
def process_codebase_by_endpoint(app: Flask, specific_endpoint: Optional[str] = None):
    """Process the codebase by generating docstrings for functions, based on API endpoints."""
    endpoints = extract_api_endpoints(app)

    if specific_endpoint and specific_endpoint not in endpoints:
        print(f"Endpoint {specific_endpoint} not found.")
        return

    selected_endpoints = [specific_endpoint] if specific_endpoint else endpoints.keys()

    for endpoint in selected_endpoints:
        call_graph, func_to_file = build_call_graph_for_endpoint(endpoint, app)

        # Create a dictionary to store processed functions and their docstrings
        processed_functions = {}

        leaves = [node for node in call_graph if call_graph.out_degree(node) == 0]

        while leaves:
            new_leaves = []
            for func_name in leaves:
                file_path = func_to_file[func_name]
                unique_id = generate_unique_id(file_path, func_name)

                if is_function_processed(unique_id):
                    # If already processed, fetch from CSV
                    processed_functions[unique_id] = fetch_docstring_from_csv(unique_id)
                    continue

                function_code = get_function_code(file_path, func_name)
                
                # Retrieve context from child functions if any
                child_context = get_child_context(call_graph, func_name, func_to_file, processed_functions)
                
                # Generate the docstring
                docstring = generate_docstring(function_code, child_context)

                # Insert the docstring into the function and save the file
                insert_docstring(file_path, func_name, docstring)

                # Save function details to the CSV
                save_function_details(endpoint, file_path, func_name, unique_id, docstring)

                # Add the processed docstring to the dictionary
                processed_functions[unique_id] = docstring

                # Remove the processed node from the graph
                call_graph.remove_node(func_name)

                # Check for new leaves
                new_leaves.extend([n for n in call_graph.nodes if call_graph.out_degree(n) == 0])

            leaves = new_leaves

# Example usage
app = Flask(__name__)
process_codebase_by_endpoint(app, specific_endpoint=None)
