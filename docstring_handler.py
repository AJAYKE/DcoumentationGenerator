import ast
import os
import re

from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from llama_index.llms.anthropic import Anthropic

load_dotenv()

tokenizer = Anthropic().tokenizer
Settings.tokenizer = tokenizer
api_key = os.getenv("ANTHROPIC_API_KEY")
llm = Anthropic(api_key=api_key)
MODEL = "claude-3-haiku-20240307"
llm = Anthropic(model=MODEL)

PROMPT = '''Please generate a Google-style Python docstring for the above function.
        If there are any child functions, I will include the required context for them.
        This docstring will be directly used in the code, so strictly ensure it is formatted appropriately.
        Return only the docstring text without any code snippets. Strictly do not include function definition.
        Explain the function logic in the docstring.
        STRICTLY the generated docstring MUST start with """ and end with """
        '''


class DocstringHandler:
    """Generates docstrings for a given function or for all the methods in a given class.

    This function takes the file path and the class name/function name as input, and generates docstrings for all the methods within the class. 
    It uses the `ast` module to parse the file content, find the class definition, and then iterate through the methods within the class.

    For each method inside the class or for a normal function, it generates a docstring using the `generate_docstring` function, which takes the function code and any context from child functions as input. 
    The generated docstring is then inserted into the original file using the `insert_docstring` function.

    Args:
        filepath (str): The file path containing the class definition.
        class_name (str): The name of the class for which to generate docstrings.

    Raises:
        FileNotFoundError: If the specified file is not found.
        IOError: If there is an error reading or writing the file.
    """
    def generate_docstring(self, function_code, child_context=""):
        """Generate a docstring for a function based on the provided code and context.

        Args:
            function_code (str): The code of the function to generate the docstring for.
            child_context (str, optional): Any context from child functions that should be included in the docstring. Defaults to an empty string.

        Returns:
            str: The generated docstring for the function.

        This function takes the code of a function and any relevant context from child functions, and generates a Google-style Python docstring for the function. The docstring is generated using the Anthropic language model, and is formatted to be directly used in the code. The docstring includes a description of the function's logic and purpose, as well as the function's arguments and return value.
        """
        prompt = f"""

        Function code:
        {function_code}

        Context from child functions (if any):
        {child_context}

        {PROMPT}
        """
        messages = [
            ChatMessage(
                role="system",
                content="You are a code managing software engineer who writes clean and precise documentation.",
            ),
            ChatMessage(role="user", content=prompt),
        ]
        resp = Anthropic(model=MODEL).chat(messages)

        return resp.message.content.strip('"""')
    
    def generate_docstrings_for_all_methods_in_class(self, filepath, class_name):
        """Generate docstrings for all methods in a class.

        This function reads the content of a Python file, parses the AST, and generates docstrings for all methods defined within a specified class. It then inserts the generated docstrings into the original file.

        Args:
            filepath (str): The path to the Python file containing the class.
            class_name (str): The name of the class for which to generate docstrings.

        Raises:
            None

        Returns:
            None
        """
        with open(filepath, "r") as file:
            file_content = file.read()
            node = ast.parse(file_content, filename=filepath)

        function_node = self.get_node_in_file(node, class_name)
        methods = [n for n in function_node.body if isinstance(n, ast.FunctionDef)]

        for method in methods:
            method_node = self.get_node_in_file(node, method.name, class_name)
            function_code = ast.get_source_segment(file_content, method_node)
            if not function_code:
                continue
            docstring = self.generate_docstring(function_code)
            self.insert_docstring(filepath, method.name, docstring, function_code, True)

    def get_node_in_file(self, node, name, class_name=None):
        """Retrieve a node in the given AST (Abstract Syntax Tree) by its name and optional class name.

        Args:
            node (ast.AST): The root node of the AST to search.
            name (str): The name of the node to find.
            class_name (str, optional): The name of the class containing the node, if applicable.

        Returns:
            ast.AST or None: The node with the specified name, if found, otherwise `None`.

        Raises:
            None

        This function searches the given AST recursively to find a node with the specified name. If a class name is provided, it will first search for the class definition and then look for the node within that class. If the node is found, it is returned, otherwise `None` is returned.
        """
        for item in node.body:
            if (
                class_name
                and isinstance(item, ast.ClassDef)
                and item.name == class_name
            ):
                for sub_item in item.body:
                    if isinstance(sub_item, ast.FunctionDef) and sub_item.name == name:
                        return sub_item
            elif (
                isinstance(item, (ast.FunctionDef, ast.ClassDef)) and item.name == name
            ):
                return item
        return None

    def insert_docstring(
        self, file_path, func_name, docstring, function_code, is_class_func=False
    ):
        """Inserts a docstring into a Python file at the specified function or class.

        Args:
            file_path (str): The path to the Python file.
            func_name (str): The name of the function or class to insert the docstring for.
            docstring (str): The docstring to be inserted.
            function_code (str): The code of the function or class.
            is_class_func (bool, optional): Indicates whether the function is a class method. Defaults to False.

        Returns:
            None

        Raises:
            FileNotFoundError: If the specified file is not found.
            IOError: If there is an error reading or writing the file.

        This function first reads the contents of the specified Python file. It then searches for the
        definition of the function or class with the given name. If the function or class is found, the
        function inserts the provided docstring at the appropriate location in the file. If an existing
        docstring is found, it is replaced with the new docstring.

        The function handles both single-line and multi-line function definitions. It also correctly
        handles the case where the function is a class method, adjusting the indentation accordingly.

        If the function or class is not found in the file, a message is printed indicating that the
        function or class was not found.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()

            is_class = "class " in function_code.split("\n")[0]
            if is_class:
                func_def_pattern = rf"class {func_name}\s*(\([^)]*\))?:\n"
            else:
                func_def_pattern = rf"def {func_name}\(.*?\)?:\n"
                func_def_pattern_multiline = rf"def {func_name}\([\s\S]*?\)?:\n"

            match = re.search(func_def_pattern, file_content)
            if not match and not is_class:
                match = re.search(func_def_pattern_multiline, file_content)

            if not match:
                print(
                    f"{'Class' if is_class else 'Function'} {func_name} not found in {file_path}."
                )
                return

            start = match.end()
            indent = "        " if is_class_func else "    "

            existing_docstring_pattern = r'^\s*"""(.*?)"""\s*\n'
            existing_docstring_match = re.search(
                existing_docstring_pattern, file_content[start:], re.DOTALL
            )

            docstring = f'"""{docstring}"""'

            if existing_docstring_match:
                end = start + existing_docstring_match.end()
                new_content = (
                    file_content[:start] + f"{indent}{docstring}\n" + file_content[end:]
                )
            else:
                new_content = (
                    file_content[:start]
                    + f"{indent}{docstring}\n"
                    + file_content[start:]
                )

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(new_content)

        except (FileNotFoundError, IOError) as e:
            print(f"Error processing file: {file_path} - {e}")
