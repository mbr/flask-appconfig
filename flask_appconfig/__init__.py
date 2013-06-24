#!/usr/bin/env python

import json
import os

DEFAULT_ENV_PREFIX = 'FLASK_'


class AppConfig(object):
    def __init__(self, app=None, *args, **kwargs):
        if app:
            self.init_app(app, *args, **kwargs)
        return self

    def init_app(self, app,
                 configfile=None, envvar=True, default_settings=True,
                 from_envvars='json', from_envvars_prefix=DEFAULT_ENV_PREFIX):
        if default_settings == True:
            default_settings = app.name + '.default_settings'

        if default_settings:
            app.config.from_object(default_settings)

        # load supplied configuration file
        if configfile:
            app.config.from_pyfile(config)

        # load configuration file from environment
        if envvar == True:
            envvar = app.name.upper() + '_SETTINGS'

        if envvar and envvar in os.environ:
            app.config.from_envvar(envvar)

        # load environment variables
        if from_envvars:
            self.from_envvars(as_json=('json' == from_envvars),
                              prefix=from_envvars_prefix)

        # register extension
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['appconfig'] = self

    def from_envvars(self, envvars=None,
                           prefix=DEFAULT_ENV_PREFIX,
                           as_json=True):
        """Load environment variables as Flask configuration settings.

        Values are parsed as JSON. If parsing fails with a ValueError,
        values are instead used as verbatim strings.

        :param envvars: A dictionary of mappings of environment-variable-names
                        to Flask configuration names. If a list is passed
                        instead, names are mapped 1:1. If ``None``, see prefix
                        argument.
        :param prefix: If ``None`` is passed as envvars, all variables from
                       ``environ`` starting with this prefix are imported. The
                       prefix is stripped upon import.
        :param as_json: If False, values will not be parsed as JSON first.
        """

        # if it's a list, convert to dict
        if isinstance(envvars, list):
            envvars = { k:None for k in envvars }

        if not envvars:
            envvars = { k:k[len(prefix):] for k in environ.iterkeys()
                         if k.startswith(prefix) }

        for env_name, name in envvars.iteritems():
            if name == None:
                name = env_name

            if not env_name in envvars:
                continue

            if as_json:
                try:
                    conf[name] = json.loads(environ[env_name])
                except ValueError:
                    conf[name] = environ[env_name]
            else:
                conf[name] = environ[env_name]
