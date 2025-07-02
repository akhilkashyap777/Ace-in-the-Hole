import ast
import os
import re
from collections import defaultdict

def extract_imports_from_file(filepath):
    """Extract imports from a single Python file using multiple methods"""
    imports = set()
    
    # Method 1: AST parsing (most reliable)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except:
        # Method 2: Regex parsing (fallback for files that can't be parsed)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find import statements
            import_patterns = [
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
            ]
            
            for line in content.split('\n'):
                line = line.strip()
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        imports.add(match.group(1))
        except:
            print(f"Could not parse: {filepath}")
    
    return imports

def scan_project_imports(project_dir='.'):
    """Scan all Python files in project for imports"""
    all_imports = set()
    file_imports = defaultdict(set)
    
    for root, dirs, files in os.walk(project_dir):
        # Skip common non-essential directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', '.env']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                imports = extract_imports_from_file(filepath)
                
                if imports:
                    file_imports[filepath] = imports
                    all_imports.update(imports)
    
    return all_imports, file_imports

def filter_standard_library(imports):
    """Separate standard library from third-party imports"""
    # Common standard library modules (not exhaustive)
    stdlib_modules = {
        'os', 'sys', 'json', 'time', 'datetime', 'random', 'math', 'collections',
        'itertools', 're', 'urllib', 'http', 'socket', 'threading', 'multiprocessing',
        'subprocess', 'pathlib', 'shutil', 'glob', 'csv', 'xml', 'sqlite3',
        'logging', 'argparse', 'configparser', 'ast', 'inspect', 'types',
        'functools', 'operator', 'copy', 'pickle', 'base64', 'hashlib',
        'hmac', 'secrets', 'uuid', 'decimal', 'fractions', 'statistics',
        'array', 'struct', 'codecs', 'unicodedata', 'stringprep', 'textwrap',
        'io', 'email', 'mimetypes', 'warnings', 'contextlib', 'abc'
    }
    
    third_party = []
    standard = []
    
    for imp in sorted(imports):
        if imp in stdlib_modules:
            standard.append(imp)
        else:
            third_party.append(imp)
    
    return third_party, standard

if __name__ == "__main__":
    print("Scanning project for imports...")
    print("=" * 50)
    
    all_imports, file_imports = scan_project_imports()
    third_party, standard = filter_standard_library(all_imports)
    
    print(f"\n📦 THIRD-PARTY PACKAGES (for buildozer.spec):")
    print("-" * 30)
    for imp in third_party:
        print(f"  {imp}")
    
    print(f"\n📚 STANDARD LIBRARY MODULES:")
    print("-" * 30)
    for imp in standard:
        print(f"  {imp}")
    
    print(f"\n📋 BUILDOZER.SPEC REQUIREMENTS LINE:")
    print("-" * 40)
    # Add common Kivy/Android requirements
    base_requirements = ['python3', 'kivy']
    if third_party:
        all_requirements = base_requirements + third_party
    else:
        all_requirements = base_requirements
    
    print(f"requirements = {','.join(all_requirements)}")
    
    print(f"\n📁 DETAILED BREAKDOWN BY FILE:")
    print("-" * 35)
    for filepath, imports in sorted(file_imports.items()):
        if imports:
            print(f"\n{filepath}:")
            for imp in sorted(imports):
                marker = "📦" if imp in third_party else "📚"
                print(f"  {marker} {imp}")
    
    print(f"\n✅ Found {len(all_imports)} total imports in {len(file_imports)} files")
    print(f"   - {len(third_party)} third-party packages")
    print(f"   - {len(standard)} standard library modules")