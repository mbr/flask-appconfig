#!/usr/bin/env python

import os
import warnings

from . import env, heroku, docker
from .util import try_import


class AppConfig(object):
    def __init__(self, app=None, *args, **kwargs):
        if app:
            self.init_app(app, *args, **kwargs)

    def init_app(self,
                 app,
                 configfile=None,
                 envvar=True,
                 default_settings=True,
                 from_envvars='json',
                 from_envvars_prefix=None,
                 enable_cli=True):

        if from_envvars_prefix is None:
            from_envvars_prefix = app.name.upper().replace('.', '_') + '_'

        if default_settings is True:
            defs = try_import(app.name + '.default_config')
            if defs:
                app.config.from_object(defs)
        elif default_settings:
            app.config.from_object(default_settings)

        # load supplied configuration file
        if configfile is not None:
            warnings.warn('The configfile-parameter is deprecated and will '
                          'be removed (it is currently ignored). If you are '
                          'trying to load a configuration file, use the '
                          '_CONFIG envvar instead. During tests, simply '
                          'populate app.config before or after AppConfig.',
                          DeprecationWarning)

        # load configuration file from environment
        if envvar is True:
            envvar = app.name.upper() + '_CONFIG'

        if envvar and envvar in os.environ:
            app.config.from_envvar(envvar)

        # load environment variables
        if from_envvars:
            env.from_envvars(app.config,
                             from_envvars_prefix,
                             as_json=('json' == from_envvars))

        # register extension
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['appconfig'] = self

        # register command-line functions if available
        if enable_cli:
            cli_mod = try_import('flask_cli', 'flask.cli')

            if hasattr(cli_mod, 'FlaskCLI') and not hasattr(app, 'cli'):
                # auto-load flask-cli if installed
                cli_mod.FlaskCLI(app)

            if hasattr(app, 'cli'):
                from .cli import register_cli, register_db_cli
                register_cli(app.cli)

                # conditionally register db api
                if try_import('flask_sqlalchemy'):
                    register_db_cli(app.cli, cli_mod)

        return app


class HerokuConfig(AppConfig):
    def init_app(self, app, *args, **kwargs):
        super(HerokuConfig, self).init_app(app, *args, **kwargs)

        heroku.from_heroku_envvars(app.config)


class DockerConfig(AppConfig):
    def init_app(self, app, *args, **kwargs):
        super(DockerConfig, self).init_app(app, *args, **kwargs)

        docker.from_docker_envvars(app.config)
