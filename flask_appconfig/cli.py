import os
import sys
import time
import warnings

import click

from . import server_backends
from .util import honcho_parse_env

try:
    import importlib
except ImportError:
    click.echo('You do not have importlib installed. Please install a '
               'backport for versions < 2.7/3.1 first.')
    sys.exit(1)

ENV_DEFAULT = '.env'
APP_ENVVAR = 'FLASK_APP'


@click.group(invoke_without_command=True)
@click.option('--app', '-a', 'app_name',
              envvar=APP_ENVVAR,
              help='App to import')
@click.option('--configfile', '-c',
              type=click.Path(exists=True,
                              dir_okay=False),
              help='Configuration file to pass as the first parameter to '
              'create_app')
@click.option('--env', '-e',
              default=None,
              type=click.Path(exists=True,
                              dir_okay=False),
              help='Load environment variables from file (default: "{}")'
              .format(ENV_DEFAULT))
@click.option('-m/-M', '--amend-path/--no-amend-path',
              default=True,
              help='Add the local directory to sys.path (default: on)')
@click.pass_context
def cli(ctx, app_name, configfile, env, amend_path):
    extra_files = []
    if configfile:
        extra_files.append(configfile)

    if env is None and os.path.exists(ENV_DEFAULT):
        env = ENV_DEFAULT

    if env:
        extra_files.append(env)
        buf = open(env).read()
        os.environ.update(honcho_parse_env(buf))

        # disabled: this functionality will be hard if not impossible to
        # implemend in flask 1.0. disable it for now
        # if app_name is None and APP_ENVVAR in os.environ:
        #     app_name = os.environ[APP_ENVVAR]

    if app_name is None:
        click.echo('No --app parameter and FLASK_APP is not set.')
        sys.exit(1)

    try:
        mod = importlib.import_module(app_name)
    except ImportError:
        if not amend_path:
            raise
        sys.path.append('.')
        mod = importlib.import_module(app_name)

    app = mod.create_app(configfile)

    obj = {}
    obj['app'] = app
    obj['extra_files'] = extra_files
    obj['app_mod'] = mod

    ctx.obj = obj

    if ctx.invoked_subcommand is None:
        ctx.invoke(dev)


@cli.command(
    help='Imports a module passed on the commandline, instantiates an app by '
    'calling imported_module.create_app() with an optional configuration '
    'file and runs it in debug mode.')
@click.option('--debug/--no-debug', '-d/-D',
              default=True,
              help='Enabled/disable debug (enabled by default)')
@click.option('--hostname', '-H',
              default='localhost',
              help='Hostname to bind to. Defaults to localhost')
@click.option('--port', '-p',
              type=int,
              default=5000,
              help='Port to listen on. Defaults to 5000')
@click.option('--ssl', '-S',
              flag_value='adhoc',
              default=None,
              help='Enable SSL with a self-signed cert')
@click.option('--flask-debug/--no-flask-debug', '-e/-E',
              default=None,
              help='Enable/disable Flask-Debug or Flask-DebugToolbar '
              'extensions (default: same as --debug)')
@click.option('--extended-reload', '-R',
              default=2,
              type=float,
              help='Seconds before restarting the app if a non-recoverable '
              'exception occured (e.g. SyntaxError). Set this to 0 '
              'to disable (default: 2.0)')
@click.pass_obj
def dev(obj, debug, hostname, port, ssl, flask_debug, extended_reload):
    app = obj['app']

    msgs = []

    if flask_debug is None:
        flask_debug = debug

    Debug = None
    DebugToolbarExtension = None

    if flask_debug:
        try:
            from flask_debug import Debug
        except ImportError:
            pass

        try:
            from flask_debugtoolbar import DebugToolbarExtension
        except ImportError:
            pass

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
        on_off(DebugToolbarExtension)))

    if msgs:
        click.echo(' * {}'.format(', '.join(msgs)))

    if extended_reload > 0:
        # we need to moneypatch the werkzeug reloader for this feature
        from werkzeug._reloader import ReloaderLoop
        orig_restart = ReloaderLoop.restart_with_reloader

        def _mp_restart(*args, **kwargs):
            while True:
                status = orig_restart(*args, **kwargs)

                if status == 0:
                    break
                # an error occured, possibly a syntax or other
                click.secho(
                    'App exited with exit code {}. Will attempted restart in '
                    '{} seconds.'.format(status, extended_reload),
                    fg='red')
                time.sleep(extended_reload)

            return status

        ReloaderLoop.restart_with_reloader = _mp_restart

    app.run(hostname, port,
            ssl_context=ssl,
            debug=debug,
            extra_files=obj['extra_files'])


@cli.command()
@click.option('--hostname', '-H',
              default='0.0.0.0',
              help='Hostname to bind to. Defaults to 0.0.0.0')
@click.option('--port', '-p',
              type=int,
              default=80,
              help='Port to listen on. Defaults to 80')
@click.option('--backends', '-b',
              default=server_backends.DEFAULT,
              help='Comma-separated list of backends to try. Default: {}'
              .format(server_backends.DEFAULT))
@click.pass_obj
def serve(obj, hostname, port, backends):
    warnings.warn('flask serve is currently experimental. Use it at your '
                  'own risk')
    app = obj['app']

    for backend in backends.split(','):
        func = getattr(server_backends, backend.replace('-', '_'), None)
        if not callable(func):
            click.echo('Not a valid backend: {}'.format(backend))
            continue
        click.echo('Trying backend {}'.format(backend))

        try:
            if func(app, hostname, port) is None:
                continue
            break
        except RuntimeError as e:
            click.echo(str(e), err=True)
            sys.exit(1)
        except ImportError:
            continue
    else:
        click.echo('Exhausted list of possible backends', err=True)
        sys.exit(1)


@cli.group()
@click.option('--model', '-m',
              default='.model',
              help='Name of the module that contains the model')
@click.option('--db', '-d', default='db', help='SQLAlchemy instance name')
@click.option('--echo/--no-echo', '-e/-E',
              default=True,
              help='Overrides SQLALCHEMY_ECHO')
@click.pass_obj
def db(obj, model, db, echo):
    warnings.warn('flask db is currently experimental. Use it at your '
                  'own risk')

    model_mod = importlib.import_module(model, obj['app_mod'].__package__)
    db_obj = getattr(model_mod, db)
    obj['db'] = db_obj

    obj['app'].config['SQLALCHEMY_ECHO'] = echo

    with obj['app'].app_context():
        click.echo('Connected to database: {}'.format(obj['db']))


@db.command()
@click.pass_obj
def reset(obj):
    db = obj['db']

    with obj['app'].app_context():
        click.echo('Resetting database')
        db.drop_all()
        db.create_all()


@click.command()
@click.argument('app', nargs=-1)
def flaskdev(app):
    if not app:
        app = 'yourapp'
    else:
        app = app[0]

    click.echo('flaskdev has been deprecated in favor of the \'flask\' '
               'utility. flask is included with Flask-Appconfig. '
               'To perform the same action as before, run\n\n'
               '    flask --app={} dev\n\n'
               'Note that this tool is provisional, as Flask 1.0 will likely '
               'ship with a built-in tool of the same name.'.format(app))
