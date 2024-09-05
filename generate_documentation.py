import ast

from call_tree import CallTree
from docstring_handler import DocstringHandler
from helpers import (
    fetch_docstring_from_csv,
    generate_unique_id,
    initialize_csv,
    is_function_processed,
    save_function_details,
)


class GenerateDocumentation:
    """Generate documentation for a given file or function.

    This class provides a way to generate documentation for a Python file or a specific function within the file. It extracts all the functions from the file, generates docstrings for each function, and saves the docstrings to a CSV file.

    The `generate_documentation` method is the main entry point for this functionality. It performs the following steps:

    1. Extracts all the functions from the given file, or processes a specific function if provided.
    2. For each function, it generates a unique identifier based on the file path and function name.
    3. Checks if the function has already been processed by looking up the unique identifier in a CSV file.
    4. If the function has not been processed, it generates a call tree for the function using the `CallTree` class.
    5. Iterates through the functions in the call tree and generates docstrings for each function using the `DocstringHandler` class.
    6. Inserts the generated docstrings into the original file and saves the function details (file path, function name, unique identifier, and docstring) to a CSV file.

    The class also provides helper methods to:
    - Extract all the functions from a given file.
    - Iterate through the functions in the call tree.
    - Process a function and generate its docstring.
    - Get the child context (docstrings of child functions) for a function.

    Args:
        file (str): The file path containing the functions to be documented.
        function_name (str, optional): The name of the specific function to be documented. If not provided, all functions in the file will be documented.

    Raises:
        FileNotFoundError: If the specified file is not found.
        SyntaxError: If there is a syntax error in the file.

    Context from child functions (if any):
    {child_context}
    """

    def __init__(self):
        """Initializes the necessary data structures for the code management software.

        This function sets up the following data structures:

        - `self.processed_functions`: A dictionary to store the processed functions.
        - `self.tree`: A dictionary to store the function call tree.
        - `self.source_code`: A dictionary to store the source code of the functions.
        - `self.func_to_files`: A dictionary to map functions to the files they are defined in.

        These data structures are used to manage and analyze the code within the software.
        """
        self.processed_functions = {}
        self.tree = {}
        self.source_code = {}
        self.func_to_files = {}

    def generate_documentation(self, file, function_name=None):
        """Generate documentation for a given file or a specific function.

        This function extracts all the functions from the given file and generates docstrings for each function. If a specific function name is provided, it generates the docstring only for that function.

        The function first extracts all the functions from the given file using the `extract_all_functions` method. It then iterates through each function and generates a unique ID for the function using the `generate_unique_id` function. If the function has already been processed, it fetches the docstring from a CSV file using the `fetch_docstring_from_csv` function.

        If the function has not been processed, it generates a call tree for the function using the `get_call_tree` method of the `CallTree` class. It then iterates through the functions in the call tree and generates the docstrings using the `iterate_through_functions` and `processing` methods.

        If any errors occur during the process, the function skips the function and continues with the next one.

        Args:
            file (str): The path to the file containing the functions.
            function_name (str, optional): The name of the specific function to generate the documentation for. If not provided, the function will generate documentation for all functions in the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            SyntaxError: If there is a syntax error in the file.
        """
        try:
            functions_to_process = []
            if function_name:
                functions_to_process = [function_name]
            else:
                # Extract all functions from the file
                print(f"Extracting all the functions inside the given file {file}")
                functions_to_process = self.extract_all_functions(file)
                print("Extracted all the functions")
                print("Starting with generating docstrings for each function")

            for function_name in functions_to_process:
                try:
                    unique_id = generate_unique_id(file, function_name)
                    if unique_id in self.processed_functions:
                        continue

                    if is_function_processed(unique_id):
                        self.processed_functions[unique_id] = fetch_docstring_from_csv(
                            unique_id
                        )
                        continue

                    print(f"Generating call Tree for the function {function_name}")

                    callTree = CallTree()

                    (
                        self.tree,
                        self.source_code,
                        self.func_to_files,
                    ) = callTree.get_call_tree(file, function_name)

                    print(
                        f"Starting to generate docstrings for the functions in {function_name} call tree"
                    )

                    self.iterate_through_functions(function_name)
                    self.processing(function_name)
                except Exception as e:
                    print("skipping function coz of error ", function_name, end="\n")
                    print(e)
                    continue

        except (FileNotFoundError, SyntaxError) as e:
            print(f"Error generating call tree: {str(e)}")
            return

    def extract_all_functions(self, file):
        """Extract all function names from the given file.

        This function reads the contents of the provided file, parses it using the `ast` module, and returns a list of all function and class names defined in the file.

        The function uses the `ast.parse()` function to parse the contents of the file and create an abstract syntax tree (AST) representation of the code. It then iterates over the body of the AST and collects the names of all `ast.FunctionDef` and `ast.ClassDef` nodes, which represent function and class definitions, respectively.

        Args:
            file (str): The path to the file to be processed.

        Returns:
            list[str]: A list of all function and class names defined in the file.
        """
        with open(file, "r") as f:
            node = ast.parse(f.read())

        return [
            n.name
            for n in node.body
            if (isinstance(n, ast.FunctionDef) or isinstance(n, ast.ClassDef))
        ]

    def iterate_through_functions(self, function_name):
        """Iterates through the functions in the function tree.

        This function is responsible for iterating through the functions in the function tree. It takes a function name as input and checks if it exists in the tree. If the function exists, it iterates through the subfunctions associated with that function and calls the `processing` method for each subfunction.

        Args:
            function_name (str): The name of the function to iterate through.

        Raises:
            None

        Returns:
            None
        """
        if function_name not in self.tree:
            return
        for subfunc in self.tree.get(function_name, []):
            if subfunc != function_name:
                self.processing(subfunc)

    def processing(self, function_name):
        """Process a function and generate its docstring.

        This function is responsible for processing a given function and generating its docstring. It first checks if the function has already been processed and if so, retrieves the docstring from a CSV file. If the function has not been processed, it generates the docstring based on the function code and any child context.

        The function first checks if the function is part of a class or not. If it is a class, it generates docstrings for all the methods in the class. If it is not a class, it iterates through the functions and generates the docstring for each one.

        The function then generates the docstring using the `DocstringHandler` class and inserts it into the source code. It also saves the function details, including the unique ID, docstring, and function code, to a CSV file.

        Args:
            function_name (str): The name of the function to be processed.

        Returns:
            None
        """
        filepath = self.func_to_files.get(function_name)
        if not filepath:
            return

        unique_id = generate_unique_id(filepath, function_name)
        if unique_id in self.processed_functions:
            return

        if is_function_processed(unique_id):
            self.processed_functions[unique_id] = fetch_docstring_from_csv(unique_id)
            return

        function_code = self.source_code.get(function_name, "")

        if not function_code:
            return

        is_class = True if "class " in function_code.split("\n")[0] else False

        docstringHandler = DocstringHandler()

        if is_class:
            docstringHandler.generate_docstrings_for_all_methods_in_class(
                filepath, function_name
            )

        if not is_class:
            self.iterate_through_functions(function_name)

        child_context = self.get_child_context(function_name)

        docstring = docstringHandler.generate_docstring(function_code, child_context)

        if docstring:
            docstringHandler.insert_docstring(
                filepath, function_name, docstring, function_code
            )
            save_function_details(filepath, function_name, unique_id, docstring)

        self.processed_functions[unique_id] = docstring

    def get_child_context(self, function_name) -> str:
        """Get the context of child functions for a given function name.

        This function retrieves the context (function name and docstring) of the child functions associated with the provided function name. It iterates through the child functions, checks if they have been processed before, and retrieves their docstrings. The retrieved information is then concatenated and returned as a string.

        Args:
            function_name (str): The name of the function for which to retrieve the child context.

        Returns:
            str: The context of the child functions, including their names and docstrings, or an empty string if no child functions are found.

        Raises:
            KeyError: If the provided function name is not found in the function tree.
        """
        child_context = ""
        processed_children = set()

        try:
            for func in self.tree.get(function_name, []):
                if func not in processed_children:
                    func_file_path = self.func_to_files.get(func)
                    if func_file_path:
                        child_unique_id = generate_unique_id(func_file_path, func)

                        child_docstring = self.processed_functions.get(child_unique_id)
                        if child_docstring:
                            child_context += (
                                f"Function: {func}\nDocstring: {child_docstring}\n\n"
                            )
                            processed_children.add(func)
        except KeyError:
            pass

        return child_context


if __name__ == "__main__":
    initialize_csv()
    documentationGenerator = GenerateDocumentation()
    files = [
        "/Users/ajsmac/Desktop/PROJECTS/DcoumentationGenerator/generate_documentation.py"
    ]
    for file in files:
        documentationGenerator.generate_documentation(file)
