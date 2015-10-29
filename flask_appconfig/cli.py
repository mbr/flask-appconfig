from collections import OrderedDict
import os
import socket
import sys
import time

import click
from flask import current_app

from . import server_backends
from .middleware import ReverseProxied

ENV_DEFAULT = '.env'
APP_ENVVAR = 'FLASK_APP'


def register_cli(cli):
    @cli.command(help='Runs a development server with extras.')
    @click.option('--host',
                  '-h',
                  default='localhost',
                  help='Hostname to bind to. Defaults to localhost')
    @click.option('--port',
                  '-p',
                  type=int,
                  default=5000,
                  help='Port to listen on. Defaults to 5000')
    @click.option('--ssl',
                  '-S',
                  flag_value='adhoc',
                  default=None,
                  help='Enable SSL with a self-signed cert')
    @click.option('--flask-debug/--no-flask-debug',
                  '-e/-E',
                  default=None,
                  help='Enable/disable Flask-Debug or Flask-DebugToolbar '
                  'extensions. By default, both are enabled if debug is '
                  'enabled.')
    @click.option(
        '--extended-reload',
        '-R',
        default=2,
        type=float,
        help='Seconds before restarting the app if a non-recoverable '
        'exception occured (e.g. SyntaxError). Set this to 0 '
        'to disable (default: 2.0)')
    def dev(host, port, ssl, flask_debug, extended_reload):
        # FIXME: support all options of ``flask run``
        app = current_app
        extra_files = []

        # add configuration file to extra_files if passed in
        config_env_name = app.name.upper() + '_CONFIG'
        if config_env_name in os.environ:
            extra_files.append(os.environ[config_env_name])

        msgs = []

        # try to load debug extensions
        if flask_debug is None:
            flask_debug = app.debug

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
            app.config['SERVER_NAME'] = '{}:{}'.format(host, port)

            # taking off the safety wheels
            app.config['FLASK_DEBUG_DISABLE_STRICT'] = True

        if DebugToolbarExtension:
            # Flask-Debugtoolbar does not check for debugging settings at
            # runtime. this hack enabled debugging if desired before
            # initializing the extension
            if app.debug:

                # set the SECRET_KEY, but only if we're in debug-mode
                if not app.config.get('SECRET_KEY', None):
                    msgs.append('SECRET_KEY not set, using insecure "devkey"')
                    app.config['SECRET_KEY'] = 'devkey'

            DebugToolbarExtension(app)

        def on_off(ext):
            return 'on' if ext is not None else 'off'

        msgs.insert(0, 'Flask-Debug: {}'.format(on_off(Debug)))
        msgs.insert(
            0, 'Flask-DebugToolbar: {}'.format(on_off(DebugToolbarExtension)))

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
                        'App exited with exit code {}. Will attempted restart '
                        ' in {} seconds.'.format(status, extended_reload),
                        fg='red')
                    time.sleep(extended_reload)

                return status

            ReloaderLoop.restart_with_reloader = _mp_restart

        app.run(host, port, ssl_context=ssl, extra_files=extra_files)

    @cli.command(help='Runs a production server.')
    @click.option('--host',
                  '-H',
                  default='0.0.0.0',
                  help='Hostname to bind to. Defaults to 0.0.0.0')
    @click.option('--port',
                  '-p',
                  type=int,
                  default=80,
                  help='Port to listen on. Defaults to 80')
    @click.option('--processes',
                  '-w',
                  type=int,
                  default=1,
                  help='When possible, run this many instances in separate '
                  'processes. 0 means determine automatically. Default: 1')
    @click.option('--backends',
                  '-b',
                  default=server_backends.DEFAULT,
                  help='Comma-separated list of backends to try. Default: {}'
                  .format(server_backends.DEFAULT))
    @click.option(
        '--list',
        '-l',
        'list_only',
        is_flag=True,
        help='Do not run server, but list available backends for app.')
    @click.option(
        '--reverse-proxied',
        is_flag=True,
        help='Enable HTTP-reverse proxy middleware. Do not activate '
        'this unless you need it, it becomes a security risks when used '
        'incorrectly.')
    @click.pass_obj
    def serve(obj, host, port, processes, backends, list_only,
              reverse_proxied):
        if processes <= 0:
            processes = None

        click.secho('flask serve is currently experimental. Use it at your '
                    'own risk',
                    fg='yellow',
                    err=True)
        app = current_app
        wsgi_app = app

        if reverse_proxied:
            wsgi_app = ReverseProxied(app)

        if list_only:
            found = False

            for backend in backends.split(','):
                try:
                    bnd = server_backends.backends[backend]
                except KeyError:
                    click.secho('{:20s} invalid'.format(backend), fg='red')
                    continue

                info = bnd.get_info()

                if info is None:
                    click.secho('{:20s} missing module'.format(backend),
                                fg='red')
                    continue

                fmt = {}
                if not found:
                    fmt['fg'] = 'green'
                    found = True

                click.secho(
                    '{b.name:20s} {i.version:10s} {i.extra_info}'.format(b=bnd,
                                                                         i=info),
                    **fmt)
            return

        # regular operation
        for backend in backends.split(','):
            bnd = server_backends.backends[backend]
            info = bnd.get_info()
            if not info:
                continue

            b = bnd(processes)

            rcfg = OrderedDict()
            rcfg['app'] = app.name
            rcfg['# processes'] = str(b.processes)
            rcfg['backend'] = str(b)
            rcfg['addr'] = '{}:{}'.format(host, port)

            for k, v in rcfg.items():
                click.echo('{:15s}: {}'.format(k, v))

            try:
                b.run_server(wsgi_app, host, port)
            except socket.error as e:
                if not port < 1024 or e.errno != 13:
                    raise

                # helpful message when trying to run on port 80 without room
                # permissions
                click.echo('Could not open socket on {}:{}: {}. '
                           'Do you have root permissions?'
                           .format(host, port, e))
                sys.exit(13)
            except RuntimeError as e:
                click.echo(str(e), err=True)
                sys.exit(1)
        else:
            click.echo('Exhausted list of possible backends', err=True)
            sys.exit(1)

    @cli.group()
    @click.option('--model',
                  '-m',
                  default='.model',
                  help='Name of the module that contains the model')
    @click.option('--db', '-d', default='db', help='SQLAlchemy instance name')
    @click.option('--echo/--no-echo',
                  '-e/-E',
                  default=True,
                  help='Overrides SQLALCHEMY_ECHO')
    @click.pass_obj
    def db(obj, model, db, echo):
        click.secho('flask db is currently experimental. Use it at your '
                    'own risk',
                    fg='yellow',
                    err=True)

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
