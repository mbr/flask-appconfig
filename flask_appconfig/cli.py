import os
import sys

import click

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
@click.option('--flask-debug/--no-flask-debug', '-e/-E', default=None,
              help='Enable/disable Flask-Debug or Flask-DebugToolbar '
                   'extensions (default: same as --debug)')
def main(module_name, configfile, debug, hostname, port, ssl, env,
         flask_debug):
    # extra files for the reloader to watch
    extra_files = []

    if configfile:
        extra_files.append(configfile)

    try:
        import importlib
    except ImportError:
        click.echo('You do not have importlib installed. Please install a '
                   'backport for versions < 2.7/3.1 of it first.')
        sys.exit(1)

    msgs = []

    if flask_debug is None:
        flask_debug = debug

    Debug = None

    if flask_debug:
        try:
            from flask_debug import Debug
        except ImportError:
            Debug = None

        try:
            from flask_debugtoolbar import DebugToolbarExtension
        except ImportError:
            DebugToolbarExtension = None

    if env is None and os.path.exists(ENV_DEFAULT):
        env = ENV_DEFAULT

    if env:
        extra_files.append(env)
        buf = open(env).read()
        os.environ.update(honcho_parse_env(buf))

    mod = importlib.import_module(module_name)
    app = mod.create_app(configfile)

    if Debug:
        Debug(app)
        app.config['SERVER_NAME'] = '{}:{}'.format(hostname, port)

        # taking off the safety wheels
        app.config['FLASK_DEBUG_DISABLE_STRICT'] = True

    if DebugToolbarExtension:
        # Flask-Debugtoolbar does not check for debugging settings at runtime.
        # this hack enabled debugging if desired before initializing the
        # extension
        if debug:
            app.debug = True

            # set the SECRET_KEY, but only if we're in debug-mode
            if not app.config.get('SECRET_KEY', None):
                msgs.append('SECRET_KEY not set, using insecure "devkey"')
                app.config['SECRET_KEY'] = 'devkey'

        DebugToolbarExtension(app)

    def on_off(ext):
        return 'on' if ext is not None else 'off'

    msgs.insert(0, 'Flask-Debug: {}'.format(on_off(Debug)))
    msgs.insert(0, 'Flask-DebugToolbar: {}'.format(
        on_off(DebugToolbarExtension))
    )

    if msgs:
        click.echo(' * {}'.format(', '.join(msgs)))

    app.run(hostname, port, ssl_context=ssl, debug=debug,
            extra_files=extra_files)
