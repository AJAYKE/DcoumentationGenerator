import ast
import os
import hashlib
import networkx as nx  # type: ignore
import numpy as np  # type: ignore
import pinecone  # type: ignore
from pytorch import torch  # type: ignore
from transformers import AutoModel, AutoTokenizer  # type: ignore
import openai # type: ignore


# Initialize Pinecone
pinecone.init(api_key='your-pinecone-api-key', environment='us-west1-gcp')
index_name = 'docstring-index'
if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=768)

index = pinecone.Index(index_name)

# Initialize Transformers model
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-mpnet-base-v2")


openai.api_key = 'your-openai-api-key'


class CodeParser(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}
        self.call_graph = nx.DiGraph()
        self.current_func = None

    def visit_FunctionDef(self, node):
        func_name = node.name
        self.functions[func_name] = node
        self.call_graph.add_node(func_name, filepath=node.filename)
        self.current_func = func_name
        self.generic_visit(node)
        self.current_func = None

    def visit_Call(self, node):
        if self.current_func and isinstance(node.func, ast.Name):
            called_func = node.func.id
            self.call_graph.add_edge(self.current_func, called_func)
        self.generic_visit(node)

    def parse_file(self, file_path):
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    node.filename = file_path
            self.visit(tree)

    def build_call_graph(self, dir_path):
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.py'):
                    self.parse_file(os.path.join(root, file))

def generate_unique_id(func_name, file_path):
    unique_string = f"{file_path}:{func_name}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def generate_embeddings(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

def store_embeddings(func_id, docstring_embeddings, code_embeddings, docstring):
    index.upsert([(func_id, np.concatenate([docstring_embeddings, code_embeddings]).tolist(), {"docstring": docstring})])


def generate_docstring(code_snippet, context=""):
    prompt = f"Generate a Python docstring for the following function with the given context:\n\nContext:\n{context}\n\nFunction:\n{code_snippet}\n\nDocstring:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

def process_codebase(dir_path):
    parser = CodeParser()
    parser.build_call_graph(dir_path)
    call_graph = parser.call_graph
    functions = parser.functions

    # Process nodes
    for func_name in nx.topological_sort(call_graph):
        func_node = functions[func_name]
        file_path = func_node.filename

        # Generate unique ID
        func_id = generate_unique_id(func_name, file_path)

        # Check if the function ID is already in the vector database
        response = index.fetch(ids=[func_id])
        if func_id in response['vectors']:
            continue

        # Generate docstring
        code_snippet = ast.unparse(func_node)
        docstring = ""
        if call_graph.out_degree(func_name) > 0:
            # Gather context from children
            children = list(call_graph.successors(func_name))
            context = "\n\n".join([
                f"Child Function: {child}\nDocstring: {response['vectors'][child]['metadata']['docstring']}\n"
                f"Docstring Embeddings: {response['vectors'][child]['values'][:768]}\n"
                f"Code Embeddings: {response['vectors'][child]['values'][768:]}"
                for child in children
            ])
            docstring = generate_docstring(code_snippet, context)
        else:
            docstring = generate_docstring(code_snippet)

        # Insert docstring into function node
        func_node.body.insert(0, ast.Expr(value=ast.Constant(value=docstring)))

        # Generate embeddings
        docstring_embeddings = generate_embeddings(docstring)
        code_embeddings = generate_embeddings(code_snippet)

        # Store in vector database
        store_embeddings(func_id, docstring_embeddings, code_embeddings, docstring)

        # Update function with new docstring
        functions[func_name] = func_node

    # Optionally, save the updated files back to disk


# Example usage
process_codebase('path/to/your/codebase')
