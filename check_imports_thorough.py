import os
import ast
import sys
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def check_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            print(f"❌ Syntax Error in {file_path}: {e}")
            return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                check_module(file_path, module_name, node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                # ignore relative imports for this basic check
                if node.level == 0:
                    check_module(file_path, module_name, node.lineno)

def check_module(file_path, module_name, lineno):
    # Standard library or installed site-packages
    # We will try to resolve it.
    try:
        # We only care about local project modules that might be incorrectly referenced.
        # Let's see if we can resolve it in the current sys.path (which has project_root).
        __import__(module_name)
    except ModuleNotFoundError as e:
        # If the missing module is exactly the module_name we tried to import
        if e.name == module_name:
            print(f"⚠️  {file_path.relative_to(project_root)}:{lineno} -> Could not resolve '{module_name}'")
    except Exception as e:
        # Other errors during import (like missing dependencies of dependencies)
        # We'll ignore these as they mean the module WAS found but failed to execute
        pass

for root, _, files in os.walk(project_root):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') and file != 'check_imports_thorough.py':
            check_file(Path(root) / file)
