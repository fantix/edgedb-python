import argparse
import importlib
import os
import pathlib
import sys

try:
    from mypy import stubgenc
except ImportError:
    print('Error: cannot import mypy. Consider "pip install mypy".', file=sys.stderr)
    sys.exit(1)

from . import EdgeDBModuleImporter
from ..blocking_con import connect

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        f"{os.path.basename(sys.executable)} -m edgedb.schema"
    )
    parser.add_argument("-I", "--instance")
    parser.add_argument("-n", "--namespace")
    args = parser.parse_args()

    conn = connect(args.instance)
    try:
        importer = EdgeDBModuleImporter(namespace=args.namespace).introspect(conn)
    finally:
        conn.close()

    if args.namespace:
        package = args.namespace
        mod = importlib.import_module(package)
        dir_name = pathlib.Path(mod.__file__).parent
        builtin = False
    else:
        package = __package__
        dir_name = pathlib.Path(__file__).parent
        builtin = True

    for name in importer.all(builtin=builtin):
        path = str(dir_name / f"{name}.pyi")
        print(f"Generating {path}")
        stubgenc.generate_stub_for_c_module(f"{package}.{name}", path)
