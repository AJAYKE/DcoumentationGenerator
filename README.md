# Generating Documentation for Your Project

To generate documentation for your project using the Sphinx library, follow these steps:

## Prerequisite: Add Docstrings

Ensure every function in your codebase has a proper docstring if you want to generate meaningful documentation.

### Docstring Generator

We also offer a **Docstring Generator** to automate docstring generation for specified files. Simply pass in the files, and it will handle the rest. In fact, the documentation for this codebase is generated using this very tool!

---

## Step 1: Ensure `__init__.py` Files Are Present

Include an `__init__.py` file in every folder that you want to document. This ensures that the modules are correctly included in the generated documentation.

## Step 2: Setting Up Sphinx

### Instructions:

```bash
# Create a directory for your documentation
mkdir docs

# Navigate into the docs directory
cd docs

# Install Sphinx and additional dependencies
pip install sphinx rinohtype sphinx-rtd-theme sphinxcontrib-httpdomain

# Initialize Sphinx configuration
sphinx-quickstart

# Go back to the project root
cd ..

# Generate .rst files for every module with an __init__.py file
sphinx-apidoc -o docs .

# Ensure each folder you want to document has an __init__.py file.
```

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
```

5. Building the Documentation
   Once everything is set up, build the HTML documentation by running the following command:

```bash
# Navigate into the docs directory
cd docs

# Build the HTML documentation
./make.bat html #on windows
# make html on linux

```

After this step, your documentation will be generated and available in the docs/\_build/html/ directory.
Open index.html page and check.
