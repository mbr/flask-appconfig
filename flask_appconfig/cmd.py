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
    parser.add_argument('-H', '--hostname', default='localhost',
                        help='Hostname to bind to. Defaults to localhost.')
    parser.add_argument('-p', '--port', default=5000, type=int,
                        help='Port to listen on. Defaults to 5000.')
    parser.add_argument('-S', '--ssl', default=None, action='store_const',
                        const='adhoc',
                        help='Enable SSL with a self-signed cert.')

    args = parser.parse_args()
    mod = importlib.import_module(args.module_name)
    mod.create_app(args.configfile).run(args.hostname, args.port,
                                        ssl_context=args.ssl,
                                        debug=True)
