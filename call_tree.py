import ast
import os

from helpers import generate_unique_id, is_function_processed


class CallTree:
    """
    Generates a call tree for a given function in a Python file.

    This class provides a way to analyze the call tree of a function within a Python file. It takes the file path and function name as input, and recursively traverses the call graph to build a tree-like structure representing the function calls.

    The `get_call_tree` method is the main entry point for this functionality. It performs the following steps:

    1. Generates a unique identifier for the function based on its file path and name.
    2. Checks if the function has already been processed by looking up the unique identifier in a CSV file.
    3. Reads the contents of the Python file and parses the abstract syntax tree (AST) using the `ast` module.
    4. Finds the node in the AST that corresponds to the specified function.
    5. Extracts the children (i.e., function calls) of the function node.
    6. Stores the function name, source code, and file path in the class attributes.
    7. Recursively calls `get_call_tree` for each child function, if the child function has not been processed before.
    8. Returns the call tree, source code, and file path mappings.

    The class also provides helper methods to:
    - Find the node in the AST that corresponds to a given function name.
    - Extract the children (function calls) from a function node.
    - Determine the file path of a child function based on the current file and imports.
    - Check if a function exists in a given file.
    - Extract the import statements from a file.
    - Find the file path of a module based on the import statements.

    Args:
        None

    Attributes:
        tree (dict): A dictionary that stores the call tree, where the keys are function names and the values are lists of child function names.
        source_code (dict): A dictionary that stores the source code of each function.
        func_to_files (dict): A dictionary that maps function names to their corresponding file paths.

    Returns:
        tuple: A tuple containing the call tree, source code, and file path mappings.
    """

    def __init__(self):
        """Initializes the necessary data structures for the code management software.

        The __init__ method sets up the following data structures:

        1. `self.tree`: A dictionary that represents the file structure of the codebase. The keys in this dictionary are the file paths, and the values are dictionaries representing the contents of each file.

        2. `self.source_code`: A dictionary that stores the actual source code of each file in the codebase. The keys in this dictionary are the file paths, and the values are the corresponding source code.

        3. `self.func_to_files`: A dictionary that maps function names to the files in which they are defined. This data structure is used to quickly locate the file containing a specific function.

        These data structures are essential for the code management software to efficiently store, retrieve, and manipulate the codebase.
        """
        self.tree = {}
        self.source_code = {}
        self.func_to_files = {}

    def get_call_tree(self, filepath, function_name):
        """
        Generates a call tree for a given function in a Python file.

        Args:
            filepath (str): The path to the Python file containing the function.
            function_name (str): The name of the function to generate the call tree for.

        Returns:
            tuple: A tuple containing three dictionaries:
                - `tree`: A dictionary where the keys are function names and the values are lists of child function names.
                - `source_code`: A dictionary where the keys are function names and the values are the source code segments for the corresponding functions.
                - `func_to_files`: A dictionary where the keys are function names and the values are the file paths where the corresponding functions are defined.

        Raises:
            None

        This function first generates a unique ID for the given function using the `generate_unique_id` function. It then checks if the function has already been processed by checking the `is_function_processed` function. If the function has already been processed, the function returns without doing anything.

        If the function has not been processed, the function reads the contents of the Python file and parses it using the `ast.parse` function. It then uses the `get_node_in_file` function to find the node corresponding to the given function name.

        If the function node is not found, the function returns without doing anything.

        If the function node is found, the function gets the children of the function node using the `get_children` function. It then adds the child function names to the `tree` dictionary, and the source code segment for the function to the `source_code` dictionary. It also adds the file path to the `func_to_files` dictionary.

        Finally, the function recursively calls itself for each child function, passing the file path and function name as arguments. The function returns the `tree`, `source_code`, and `func_to_files` dictionaries.
        """
        try:
            unique_id = generate_unique_id(file_path=filepath, func_name=function_name)
            if is_function_processed(unique_id=unique_id):
                return
            with open(filepath, "r") as file:
                file_content = file.read()
                node = ast.parse(file_content, filename=filepath)
        except:
            print(filepath, function_name)
            return

        function_node = self.get_node_in_file(node, function_name)

        if function_node is None:
            return

        children = self.get_children(function_node)
        self.tree[function_name] = []

        for child in children:
            try:
                self.tree[function_name].append(child.id)
            except AttributeError:
                continue

        self.source_code[function_name] = ast.get_source_segment(
            file_content, function_node
        )
        self.func_to_files[function_name] = filepath

        for child_function_name in self.tree[function_name]:
            if child_function_name in self.tree:
                continue
            child_filepath = self.get_child_filepath(filepath, child_function_name)
            if child_filepath:
                self.get_call_tree(child_filepath, child_function_name)

        return self.tree, self.source_code, self.func_to_files

    def get_node_in_file(self, node, function_name):
        """Finds a node in the given AST (Abstract Syntax Tree) that represents a function with the specified name.

        Args:
            node (ast.AST): The root node of the AST to search.
            function_name (str): The name of the function to find.

        Returns:
            ast.FunctionDef or ast.ClassDef or None: The node representing the function with the specified name, or None if the function is not found.

        Raises:
            None

        This function iterates through the body of the given AST node and checks if each item is an instance of either `ast.FunctionDef` or `ast.ClassDef`. If the name of the item matches the `function_name` argument, the function returns the item. If the function is not found, the function returns `None`.
        """
        for item in node.body:
            if (
                isinstance(item, (ast.FunctionDef, ast.ClassDef))
                and item.name == function_name
            ):
                return item
        return None

    def get_children(self, function_node):
        """Retrieve the children nodes from a given function node in the abstract syntax tree (AST).

        This function traverses the AST starting from the provided `function_node` and collects all the child nodes that represent function calls and variable names. The function returns a list of these child nodes.

        The function logic is as follows:
        1. Initialize an empty list `children` to store the collected child nodes.
        2. Iterate through each node in the AST starting from the `function_node` using `ast.walk()`.
        3. For each node, check if it is an instance of `ast.Call`:
           - If the `func` attribute of the `ast.Call` node is an `ast.Name`, append the `func` node to the `children` list.
           - If the `func` attribute of the `ast.Call` node is an `ast.Attribute`, append the `value` attribute of the `func` node to the `children` list.
        4. If the node is an instance of `ast.Name`, append the node to the `children` list.
        5. Return the `children` list containing the collected child nodes.

        Args:
            function_node (ast.FunctionDef): The function node in the AST from which to retrieve the children nodes.

        Returns:
            list[ast.AST]: A list of child nodes representing function calls and variable names.
        """
        children = []
        for item in ast.walk(function_node):
            if isinstance(item, ast.Call):
                if isinstance(item.func, ast.Name):
                    children.append(item.func)
                elif isinstance(item.func, ast.Attribute):
                    children.append(item.func.value)

            elif isinstance(item, ast.Name):
                children.append(item)

        return children

    def get_child_filepath(self, current_file, function_name):
        """Finds the file path where a given function is defined.

        Args:
            current_file (str): The current file path.
            function_name (str): The name of the function to search for.

        Returns:
            str: The file path where the function is defined, or None if the function is not found.

        Raises:
            None

        This function first checks if the given function exists in the current file. If it does, it returns the current file path.
        If the function is not found in the current file, the function extracts the imports from the current file and then
        searches for the file where the function is defined based on the imported modules.
        """
        node = self.function_exists_in_file(current_file, function_name)
        if node:
            return current_file
        imports = self.extract_imports(current_file)
        return self.find_file_from_imports(imports, function_name)

    def function_exists_in_file(self, filepath, function_name):
        """Checks if a function with the given name exists in the specified file.

        Args:
            filepath (str): The path to the file to be checked.
            function_name (str): The name of the function to search for.

        Returns:
            bool: True if the function exists in the file, False otherwise.

        Raises:
            None

        This function reads the contents of the file at the given `filepath` and uses the `ast` module to parse the file content into an abstract syntax tree (AST). It then searches the AST for a function definition with the given `function_name` and returns `True` if the function is found, `False` otherwise.
        """
        with open(filepath, "r", encoding="utf-8") as file:
            file_content = file.read()
            node = ast.parse(file_content, filename=filepath)
        return self.get_node_in_file(node, function_name) is not None

    def extract_imports(self, filepath):
        """Extracts the import statements from a Python file.

        Args:
            filepath (str): The path to the Python file.

        Returns:
            list: A list of strings representing the imported modules and packages.

        Raises:
            None

        This function uses the `ast` module to parse the contents of the Python file specified by `filepath`. It then walks through the abstract syntax tree (AST) and collects all the `Import` and `ImportFrom` statements, extracting the module or package names. The resulting list of import statements is returned.
        """
        imports = []
        with open(filepath, "r") as file:
            node = ast.parse(file.read(), filename=filepath)
        for item in ast.walk(node):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    imports.append(alias.name)
            elif isinstance(item, ast.ImportFrom):
                imports.append(item.module)
        return imports

    def find_file_from_imports(self, imports, function_name):
        """Find the file containing the specified function from a list of imports.

        This function takes a list of imports and a function name as input, and searches for the file
        that contains the specified function. It does this by converting the module path of each import
        to a file path, and then checking if the file exists and if the function exists in the file.

        If the function is found in one of the files, the function returns the file path. If the function
        is not found in any of the files, the function returns `None`.

        Args:
            imports (list): A list of import statements as strings.
            function_name (str): The name of the function to search for.

        Returns:
            str or None: The file path containing the specified function, or `None` if the function is not found.
        """
        for imp in imports:
            module_path = imp.replace(".", "/")  # Convert module path to file path
            module_file = f"./{module_path}.py"
            if os.path.isfile(module_file) and self.function_exists_in_file(
                module_file, function_name
            ):
                return module_file
        return None


if __name__ == "__main__":
    call_tree = CallTree()
    tree, source_code, func_to_files = call_tree.get_call_tree(
        "./analysis_service_v9/app.py", "get_last_data_refresh_timestamp"
    )
