#!/usr/bin/env python

import json
import os

class AppConfig(object):
    def __init__(self, app=None):
        if app:
            self.init_app(app)
        return self

    def init_app(self, app):
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['appconfig'] = self

    def from_envvars(self, envvars=None, environ=os.environ, prefix='FLASK_',
                           as_json=True):
        """Load environment variables as Flask configuration settings.

        Values are parsed as JSON. If parsing fails with a ValueError,
        values are instead used as verbatim strings.

        :param envvars: A dictionary of mappings of environment-variable-names
                        to Flask configuration names. If a list is passed
                        instead, names are mapped 1:1. If ``None``, see prefix
                        argument.
        :param environ: The environment to get values from.
        :param prefix: If ``None`` is passed as envvars, all variables from
                       ``environ`` starting with this prefix are imported. The
                       prefix is stripped upon import.
        :param as_json: If False, values will not be parsed as JSON first.
        """

    # if it's a list, convert to dict
    if isinstance(envvars, list):
        envvars = { k:k for k in envvars }

    if not envvars:
        envvars = { k:k[len(prefix):] for k in environ.iterkeys()
                     if k.startswith(prefix) }

    for env_name, name in envvars.iteritems():
        if as_json:
            try:
                conf[name] = json.loads(environ[env_name])
            except ValueError:
                conf[name] = environ[env_name]
        else:
            conf[name] = environ[env_name]