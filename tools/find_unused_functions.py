"""
Analiza el repositorio buscando definiciones de funciones y llamadas.
Genera un informe con funciones que parecen no ser usadas (solo aparecen en su propia definición).

Uso: python tools\find_unused_functions.py

Limitaciones: intenta detectar llamadas por nombre y accesos por atributo. No detecta usos dinámicos (eval, getattr dinámico, referencias por string) ni usos desde otros procesos externos.
"""
import ast
import os
import json
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

py_files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    # Ignorar __pycache__ y .git u otros ocultos
    if '__pycache__' in dirpath:
        continue
    if dirpath.split(os.sep)[-1].startswith('.'):
        continue
    for f in filenames:
        if f.endswith('.py'):
            py_files.append(os.path.join(dirpath, f))

# Map: func_key -> {'file': file, 'lineno': lineno, 'type': 'function'|'method'|'nested', 'name': name, 'qualname': qual}
defs = {}
# usage counts by simple name
usage_counts = defaultdict(int)
# attribute usage counts (name used as attribute)
attr_usage = defaultdict(int)

for path in py_files:
    try:
        src = open(path, 'r', encoding='utf-8').read()
        tree = ast.parse(src, filename=path)
    except Exception as e:
        print(f"ERROR parsing {path}: {e}")
        continue

    # Walk to find function defs with qualname
    class DefVisitor(ast.NodeVisitor):
        def __init__(self, path):
            self.path = path
            self.scope = []
        def visit_FunctionDef(self, node):
            qual = '.'.join(self.scope + [node.name])
            key = f"{self.path}::{qual}"
            defs[key] = {'file': self.path, 'lineno': node.lineno, 'name': node.name, 'qualname': qual, 'type': 'function' if len(self.scope)==0 else 'method_or_nested'}
            # Enter scope for nested defs
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()
        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)
        def visit_ClassDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

    DefVisitor(path).visit(tree)

    # Walk to find call sites
    class CallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            # different call expressions
            func = node.func
            if isinstance(func, ast.Name):
                usage_counts[func.id] += 1
            elif isinstance(func, ast.Attribute):
                # attribute access like obj.foo()
                attr_usage[func.attr] += 1
            # also visit nested
            self.generic_visit(node)
        def visit_Attribute(self, node):
            # attribute access (not call) could be used as reference
            # ignore, since many attrs are not functions
            self.generic_visit(node)

    CallVisitor().visit(tree)

# Now decide which defs are unused: if name not in usage_counts and not in attr_usage
unused = []
for key, info in defs.items():
    name = info['name']
    used = False
    if usage_counts.get(name, 0) > 0 or attr_usage.get(name, 0) > 0:
        used = True
    # special-case: if function name starts with _ (private), still consider it only-if-unused
    if not used:
        unused.append({'file': info['file'], 'lineno': info['lineno'], 'qualname': info['qualname'], 'name': name})

report = {
    'root': ROOT,
    'num_py_files': len(py_files),
    'num_defs': len(defs),
    'num_unused_candidates': len(unused),
    'unused': sorted(unused, key=lambda x:(x['file'], x['lineno']))
}

out = os.path.join(os.path.dirname(__file__), 'unused_functions_report.json')
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False)

print(f"Report written to: {out}")
print(json.dumps({'num_files': len(py_files), 'num_defs': len(defs), 'num_unused_candidates': len(unused)}))
