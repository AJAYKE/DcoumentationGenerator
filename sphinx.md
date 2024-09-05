# Generating Documentation with Sphinx

To generate documentation for your project using the Sphinx library, follow these steps:

### 1. Ensure `__init__.py` Files Are Present

Make sure there is an `__init__.py` file in every folder for which you want the modules to be included in the documentation.

### 2. Setting Up Sphinx

#### Step-by-Step Instructions:

```bash
# Create a directory for your documentation
mkdir docs

# Navigate into the docs directory
cd docs

# Install Sphinx and additional dependencies
pip install sphinx
pip install rinohtype
pip install sphinx-rtd-theme
pip install sphinxcontrib-httpdomain

# Initialize Sphinx configuration
sphinx-quickstart

# Move back to the project root
cd ..

# Generate .rst files for every module with an __init__.py file
# This generates documentation for the current folder. You can specify a specific folder if needed.
sphinx-apidoc -o docs .

# Ensure that each folder you want to document has an __init__.py file.
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