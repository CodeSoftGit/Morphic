
# !!! SECURITY WARNING !!!
# Modcharts are executable Python scripts that run with the same privileges as the game.
# While this system attempts to restrict harmful operations:
#  - It cannot guarantee complete security
#  - Malicious code could potentially damage your system or compromise your data
# 
# SAFETY GUIDELINES:
# - Only run modcharts from trusted, reputable sources
# - Review the code before execution if possible
# - Consider running the game in a restricted environment for untrusted modcharts

import ast

# Placeholder functions if not defined in the modchart
def onHit(*args, **kwargs):
    pass

def onMiss(*args, **kwargs):
    pass

def onKeyPress(*args, **kwargs):
    pass

def onUpdate(*args, **kwargs):
    pass

def onBeat(*args, **kwargs):
    pass

def onStep(*args, **kwargs):
    pass

def onSongStart(*args, **kwargs):
    pass

def onSongEnd(*args, **kwargs):
    pass

def onNoteCreation(*args, **kwargs):
    pass

def create_generic_modchart_funcs():
    return {
        "onHit": onHit,
        "onMiss": onMiss,
        "onKeyPress": onKeyPress,
        "onUpdate": onUpdate,
        "onBeat": onBeat,
        "onStep": onStep,
        "onSongStart": onSongStart,
        "onSongEnd": onSongEnd,
        "onNoteCreation": onNoteCreation,
    }

def check_modchart(code):
    """
    Checks if the provided modchart code is valid Python code.
    Only allows imports from a predefined list of safe modules.
    
    Args:
        code (str): The modchart code to validate
        
    Returns:
        bool: True if the code is valid and safe
        
    Raises:
        ValueError: If disallowed modules are imported
        SyntaxError: If the code contains syntax errors
    """
    # Safe modules that don't provide file or system access
    allowed_modules = [
        "pygame", "math", "random", "copy", "time", "datetime",
        "collections", "itertools", "functools", "operator", 
        "statistics", "re", "json", "array", "bisect", "heapq",
        "decimal", "fractions", "numbers", "cmath",
        "enum", "typing", "dataclasses", "abc", "contextlib",
        "difflib", "hashlib", "textwrap", "unicodedata", "uuid",
        "colorsys", "calendar", "zoneinfo", "graphlib", "weakref",
        "string", "fnmatch", "base64", "urllib.parse", "hmac",
        "pydoc", "types", "keyword", "reprlib", "argparse",
        "builtins", "gettext", "locale", "warnings", 
        "concurrent.futures", "queue", "threading", "multiprocessing",
        "asyncio", "html", "xml.etree.ElementTree"
    ]
    
    # Explicitly disallow these modules that could be problematic
    disallowed_modules = [
        "os", "sys", "subprocess", "shutil", "pathlib", "io", 
        "open", "file", "tempfile", "glob", "socket", "urllib.request",
        "requests", "ftplib", "smtplib", "pickle", "shelve", "dbm"
    ]
    
    # Check for syntax errors first
    try:
        compile(code, "<string>", "exec")
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in modchart code: {e.msg}")
    
    # Parse the AST to find imports
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Check for import statements
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_name = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
                base_module = module_name.split('.')[0]
                if base_module not in allowed_modules:
                    raise ValueError(f"Disallowed module import: {base_module}")
                if base_module in disallowed_modules or module_name in disallowed_modules:
                    raise ValueError(f"Explicitly disallowed module import: {module_name}")
    except Exception as e:
        raise ValueError(f"Error analyzing imports: {str(e)}")
    
    # If no issues found, return True
    return True

def runModchart(code, game_context=None):
    """Runs a modchart string (python) and returns various callback functions.
    
    Args:
        code (str): The modchart code to be executed.
        game_context (dict, optional): Game state and objects to expose to the modchart.
    
    Returns:
        dict: Dictionary containing all defined callback functions.
        
    Raises:
        ValueError: If disallowed modules are imported
        SyntaxError: If the code contains syntax errors
    """
    # Check if the modchart code is safe to run
    check_modchart(code)
    
# Create a dictionary to store the functions
    functions = create_generic_modchart_funcs()
    
    # Add init function 
    functions["init"] = None
    
    # Create environment for the modchart
    environment = {}
    
    # Add game context to environment if provided
    if game_context:
        environment.update(game_context)
        
    # Define the function to be executed in the modchart
    def execute_modchart():
        nonlocal functions
        # Execute the code with the environment and functions as scope
        exec(code, environment, functions)
        
        # Call init function if it exists
        if functions["init"] and callable(functions["init"]):
            functions["init"]()

    # Execute the modchart code
    execute_modchart()

    # Return all functions as a dictionary for more flexibility
    return functions