import os
import sys

import click
from flask import url_for

from .util import honcho_parse_env


ENV_DEFAULT = '.env'


@click.command(
    help='Imports a module passed on the commandline, instantiates an app by '
         'calling imported_module.create_app() with an optional configuration '
         'file and runs it in debug mode.'
)
@click.argument('module_name')
@click.option('--configfile', '-c',
              type=click.Path(exists=True, dir_okay=False),
              help='Configuration file to pass as the first parameter to '
                   'create_app')
@click.option('--debug/--no-debug', '-d/-D', default=True,
              help='Enabled/disable debug (enabled by default)')
@click.option('--hostname', '-H', default='localhost',
              help='Hostname to bind to. Defaults to localhost')
@click.option('--port', '-p', type=int, default=5000,
              help='Port to listen on. Defaults to 5000')
@click.option('--ssl', '-S', flag_value='adhoc', default=None,
              help='Enable SSL with a self-signed cert')
@click.option('--env', '-e', default=None,
              type=click.Path(exists=True, dir_okay=False),
              help='Load environment variables from file (default: ".env")')
@click.option('--flask-debug/--no-flask-debug', '-e/-E', default=True,
              help='Enable/disable Flask-Debug extension (enabled by default)')
def main(module_name, configfile, debug, hostname, port, ssl, env,
         flask_debug):
    try:
        import importlib
    except ImportError:
        click.echo('You do not have importlib installed. Please install a '
                   'backport for versions < 2.7/3.1 of it first.')
        sys.exit(1)

    Debug = None

    if flask_debug:
        try:
            from flask_debug import Debug
        except ImportError:
            click.echo(' * Flask-Debug: Not installed')
            Debug = None

    if env is None and os.path.exists(ENV_DEFAULT):
        env = ENV_DEFAULT

    if env:
        buf = open(env).read()
        os.environ.update(honcho_parse_env(buf))

    mod = importlib.import_module(module_name)
    app = mod.create_app(configfile)

    if Debug:
        Debug(app)
        app.config['SERVER_NAME'] = '{}:{}'.format(hostname, port)
        with app.app_context():
            click.echo(' * Flask-Debug active, available at {}'.format(
                url_for('debug.debug_root'),
            ))

        # taking off the safety wheels
        app.config['FLASK_DEBUG_DISABLE_STRICT'] = True

    app.run(hostname, port, ssl_context=ssl, debug=debug)
