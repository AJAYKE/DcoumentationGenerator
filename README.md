# Generating Documentation for Your Codebase

This guide will help you generate structured documentation for your project using LLMs (like Claude) and the Sphinx library.

## How Does Sphinx Work?

Sphinx compiles all the docstrings from the files and folders you specify, generating a well-structured, organized documentation. To automate the process of writing docstrings, we can leverage Large Language Models (LLMs) like Claude, GPT, etc.

Once the docstrings are ready, Sphinx will handle the rest, creating documentation from the structured content.

---

## Step 1: Docstring Generation Using LLMs

### **Docstring Generator**

The **Docstring Generator** automates the creation of docstrings for your code. Pass the files you want to document to the generator, and it will output well-structured docstrings for your functions, classes, and modules.

For this example, we are using **Claude** for docstring generation, but feel free to use any LLM model of your choice.

There are three objects in this docstring generator.

1.  GenerateDocumentation
    Generate documentation for a given file or a specific function.

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

2.  CallTree
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

3.  Docstring Handler
    Generates docstrings for a given function or for all the methods in a given class.

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

---

## Step 2: Setting Up Sphinx

### Step 2.1: Ensure `__init__.py` Files Are Present

Make sure that every folder you want to include in the documentation has an `__init__.py` file. This is required for Sphinx to recognize and document the modules.

### Step 2.2: Install and Configure Sphinx

#### Instructions:

````bash
# Step 1: Create a directory for your documentation
mkdir docs

# Step 2: Navigate into the docs directory
cd docs

# Step 3: Install Sphinx and additional dependencies
pip install sphinx rinohtype sphinx-rtd-theme sphinxcontrib-httpdomain

# Step 4: Initialize the Sphinx configuration
sphinx-quickstart

# Step 5: Go back to the project root
cd ..

# Step 6: Generate .rst files for each module (folders containing __init__.py files)
sphinx-apidoc -o docs .

# Ensure each folder you want to document has an __init__.py file.

3. Editing Documentation Files

   1. Edit the modules.rst file:
      Add the module to index.rst to include it in the documentation index.
   2. Customize .rst files:
      Modify the titles and sections in the .rst files to structure the documentation to your liking.

4. Configuring conf.py
   1. Update the conf.py file in the docs directory by adding the necessary extensions:

```bash
# Ensure the system path is set up correctly
import os
import sys
sys.path.insert(0, os.path.abspath(".."))

# Add these extensions to the list in conf.py
extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
]
````

5. Building the Documentation
   Once everything is set up, build the HTML documentation by running the following command:

```bash
# Navigate into the docs directory
cd docs

# Build the HTML documentation
./make.bat html    # On Windows
# make html         # On Linux/Mac

```

After this step, your documentation will be generated and available in the docs/\_build/html/ directory.
Open index.html page and check.
