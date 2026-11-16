"""Reference kernels cannot obtain their answer from a production simulator."""

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.reference
ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'backend' / 'reference'
ALLOWED_ROOTS = sys.stdlib_module_names | {'numpy', 'scipy', 'pydantic'}


def check_imports(source, package='backend.reference'):
    """Walk nested/dead-code imports as well as top-level statements."""
    tree = ast.parse(source)
    dynamic_names = {'__import__', 'import_module'}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'importlib':
            dynamic_names.update(alias.asname or alias.name for alias in node.names
                                 if alias.name == 'import_module')
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            if node.level:
                module = importlib.util.resolve_name('.'*node.level+module, package)
            modules = [module]
        elif isinstance(node, ast.Call):
            function = node.func
            if ((isinstance(function, ast.Name) and function.id in dynamic_names)
                    or (isinstance(function, ast.Attribute)
                        and function.attr in {'__import__', 'import_module',
                                              'spec_from_file_location', 'exec_module'})):
                raise AssertionError(f'Dynamic import forbidden at line {node.lineno}')
        for module in modules:
            assert (module == 'backend.reference' or module.startswith('backend.reference.')
                    or module.split('.')[0] in ALLOWED_ROOTS), (
                        f'Forbidden reference import {module!r} at line {node.lineno}')


def test_reference_ast_imports_only_allow_independent_modules():
    modules = sorted(REFERENCE.rglob('*.py'))
    assert REFERENCE.is_dir() and modules
    for path in modules:
        relative = path.relative_to(ROOT).with_suffix('')
        package = '.'.join(relative.parts if path.name == '__init__.py'
                           else relative.parts[:-1])
        if package.endswith('.__init__'):
            package = package.removesuffix('.__init__')
        try:
            check_imports(path.read_text(encoding='utf-8'), package)
        except AssertionError as exc:
            raise AssertionError(f'{path.relative_to(ROOT)}: {exc}') from exc


@pytest.mark.parametrize('source', [
    'def hidden():\n    import qiskit\n',
    'if False:\n    from pennylane import numpy\n',
    'from ..quantum import inspect_state\n',
    'from backend.models import Gate\n',
    '__import__("qiskit")\n',
    'import importlib as loader\nloader.import_module("qiskit")\n',
    'from importlib import import_module as load\nload("qiskit")\n',
])
def test_import_guard_detects_hidden_and_dynamic_forbidden_imports(source):
    with pytest.raises(AssertionError):
        check_imports(source)


def test_reference_runtime_is_independent_in_fresh_interpreter():
    # A fresh -I interpreter cannot inherit already-imported Qiskit or production
    # modules from pytest. Both normal and importlib-driven imports are guarded.
    script = textwrap.dedent('''
        import builtins
        import importlib.abc
        import importlib.util
        import sys
        sys.path.insert(0, sys.argv[1])

        def forbidden(name):
            return (name.split('.')[0] in {'qiskit', 'qiskit_aer', 'pennylane'}
                    or (name.startswith('backend.')
                        and name != 'backend.reference'
                        and not name.startswith('backend.reference.')))

        class BlockProduction(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if forbidden(fullname):
                    raise AssertionError('Forbidden runtime import: '+fullname)
                return None

        normal_import = builtins.__import__
        def independent_import(name, globals=None, locals=None, fromlist=(), level=0):
            resolved = (importlib.util.resolve_name('.'*level+name, globals['__package__'])
                        if level else name)
            if forbidden(resolved):
                raise AssertionError('Forbidden runtime import: '+resolved)
            if resolved == 'backend':
                for item in fromlist or ():
                    if item != 'reference':
                        raise AssertionError('Forbidden backend member: '+item)
            return normal_import(name, globals, locals, fromlist, level)

        sys.meta_path.insert(0, BlockProduction())
        builtins.__import__ = independent_import
        from backend.reference.statevector import simulate_statevector
        from backend.reference.density import simulate_density, simulate_probabilities
        gates = [{'name': 'H', 'target': 2},
                 {'name': 'RY', 'target': 0, 'angle': .7},
                 {'name': 'CCX', 'target': 1, 'control': 2, 'control2': 0},
                 {'name': 'M', 'target': 0}]
        state = simulate_statevector(3, gates)
        density = simulate_density(3, gates, gate_error=.1)
        probabilities = simulate_probabilities(3, gates, gate_error=.1, readout_error=.2)
        assert state.shape == (8,) and density.shape == (8, 8)
        assert probabilities.shape == (8,) and abs(sum(probabilities)-1) < 1e-12
        assert not [name for name in sys.modules if forbidden(name)]
        print('isolated reference imports and execution passed')
    ''')
    result = subprocess.run([sys.executable, '-I', '-c', script, str(ROOT)],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'isolated reference imports and execution passed' in result.stdout
