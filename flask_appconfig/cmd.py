import argparse
import sys


def main_flaskdev():
    try:
        import importlib
    except ImportError:
        print ('You do not have importlib installed. Please install a '
               'backport for versions < 2.7/3.1 of it first.')
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Imports a module passed on the commandline, instantiates '
                    'an app by calling imported_module.create_app() with an '
                    'optional configuration file and runs it in debug mode.',
    )
    parser.add_argument('module_name', help='Name of the module to import.')
    parser.add_argument('-c', '--configfile',
                        help='Configuration file to pass as the first '
                        'parameter to create_app.')

    args = parser.parse_args()
    mod = importlib.import_module(args.module_name)
    mod.create_app(args.configfile).run(debug=True)
