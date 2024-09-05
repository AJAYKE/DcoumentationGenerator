import csv
import hashlib
import os

csv_filename = "processed_functions.csv"
csv_headers = ["file_path", "func_name", "unique_id", "docstring"]


def initialize_csv():
    """Initialize the CSV file with headers if it does not exist."""
    if not os.path.exists(csv_filename):
        with open(csv_filename, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(csv_headers)


def generate_unique_id(file_path: str, func_name: str) -> str:
    """Generate a unique identifier for a function based on its file path and name.

    This function takes the file path and function name as input, and generates a unique identifier
    using the MD5 hash of the concatenation of these two values. The resulting hash is returned as a
    hexadecimal string.

    The purpose of this function is to provide a unique identifier for a function that can be used
    to track or reference the function, for example, in logging or monitoring systems.

    Args:
        file_path (str): The full file path of the function.
        func_name (str): The name of the function.

    Returns:
        str: A unique identifier for the function, based on its file path and name.
    """
    unique_string = f"{file_path}:{func_name}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def is_function_processed(unique_id: str) -> bool:
    """Checks if a unique ID has been processed in a CSV file.

    This function reads a CSV file and checks if the provided unique_id is present in any of the rows. If the file is not found, it returns False.

    Args:
        unique_id (str): The unique identifier to search for in the CSV file.

    Returns:
        bool: True if the unique_id is found in the CSV file, False otherwise.

    Raises:
        FileNotFoundError: If the CSV file is not found.
    """
    try:
        with open(csv_filename, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)

            return any(row["unique_id"] == unique_id for row in reader)
    except FileNotFoundError:
        return False


def fetch_docstring_from_csv(unique_id: str):
    """Fetch the docstring from a CSV file based on a unique identifier.

    This function reads a CSV file and searches for a row where the 'unique_id' column matches the provided `unique_id` parameter. If a matching row is found, the function returns the value of the 'docstring' column from that row.

    If the CSV file is not found, the function returns `None`.

    Args:
        unique_id (str): The unique identifier to search for in the CSV file.

    Returns:
        str or None: The docstring value from the matching row, or `None` if the file is not found or no matching row is found.
    """
    try:
        with open(csv_filename, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row["unique_id"] == unique_id:
                    return row["docstring"]
    except FileNotFoundError:
        return None
    return None


def save_function_details(
    file_path: str, func_name: str, unique_id: str, docstring: str
):
    """Save function details to a CSV file.

    This function takes the file path, function name, unique identifier, and function docstring as input, and writes them to a CSV file. If the file does not exist or is empty, it will add the CSV headers before writing the data.

    Args:
        file_path (str): The file path where the function is defined.
        func_name (str): The name of the function.
        unique_id (str): A unique identifier for the function.
        docstring (str): The docstring of the function.

    Raises:
        IOError: If there is an error writing to the CSV file.
    """
    file_exists = os.path.isfile(csv_filename)
    file_empty = os.path.getsize(csv_filename) == 0 if file_exists else True

    try:
        with open(csv_filename, "a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)

            if file_empty:
                writer.writerow(csv_headers)

            writer.writerow([file_path, func_name, unique_id, docstring])
    except IOError:
        print("Error writing to CSV file.")
