import ast
import os
import re

def analyze_file(filepath):
    print(f"=== Analyzing {filepath} ===")
    if not os.path.exists(filepath):
        print("File does not exist")
        return
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # 1. Parse AST to check syntax and basic structure
    try:
        tree = ast.parse(content, filename=filepath)
        print("AST parsed successfully. No syntax errors.")
    except SyntaxError as e:
        print(f"Syntax Error: {e.msg} at line {e.lineno}, col {e.offset}")
        return

    # 2. Check for duplicate imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append((f"{node.module}.{alias.name}", node.lineno))
    
    seen = {}
    for imp, line in imports:
        if imp in seen:
            print(f"Duplicate import: '{imp}' at line {line} (first seen at line {seen[imp]})")
        seen[imp] = line

    # 3. Check for commonly used files and check if they exist or if paths are correct
    # Look for string literals containing paths (e.g., matching common extensions or / or \)
    paths_in_code = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if any(ext in val for ext in ['.pkl', '.keras', '.csv', '.png', '.jpg', '.pdf']):
                paths_in_code.append((val, node.lineno))
    
    print("\nPaths found in code:")
    for path, line in paths_in_code:
        # Check if path is relative or absolute
        exists = os.path.exists(path)
        print(f"  Line {line}: '{path}' -> exists={exists}")

    # 4. Check for undefined names (simplistic static analysis)
    # We can collect all names that are defined (functions, classes, variables, imports)
    defined_names = set()
    # Add builtins
    import builtins
    defined_names.update(dir(builtins))
    
    # Add imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                defined_names.add(name.asname or name.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                defined_names.add(node.module.split('.')[0])
            for name in node.names:
                defined_names.add(name.asname or name.name)
        elif isinstance(node, ast.FunctionDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
                elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                    for el in target.elts:
                        if isinstance(el, ast.Name):
                            defined_names.add(el.id)
    
    # Check used names
    used_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.append((node.id, node.lineno))
            
    undefined = []
    for name, line in used_names:
        if name not in defined_names and name not in ['st', 'pd', 'np', 'px', 'go', 'joblib', 'Image', 'datetime', 'time', 'colors', 'SimpleDocTemplate', 'Table', 'TableStyle', 'Paragraph', 'getSampleStyleSheet', 'option_menu', 'load_model']: # standard imports allowed
            undefined.append((name, line))
    
    if undefined:
        print("\nPossibly undefined variables:")
        for name, line in sorted(list(set(undefined))):
            print(f"  Line {line}: {name}")

analyze_file("dashboard/app.py")
analyze_file("src/prediction.py")
