Flask-AppConfig
===============

Allows you to configure an application using pre-set methods::

    from flask.ext.appconfig import AppConfig

    def create_app(configfile=None):
        app = Flask('myapp')
        AppConfig(app, configfile)
        return app

The application returned by ``create_app`` will, in order:

1. Load default settings from a module called ``myapp.default_settings``, if it
   exists. (method described in
   <http://flask.pocoo.org/docs/config/#configuring-from-files>_)
2. Load settings from a configuration file whose name is given in the
   environment variable ``MYAPP_SETTINGS`` (see link from 1.).
3. Load json or string values directly from environment variables that start
   with a prefix of ``FLASK_``, i.e. setting ``FLASK_SQLALCHEMY_ECHO=true``
   will cause the setting of ``SQLALCHEMY_ECHO`` to be ``True``.

Any of these behaviors can be altered or disabled by passing the appropriate
options to the constructor or ``init_app()``.

Heroku support
--------------

Flask-AppConfig supports configuring a number of services through
``HerokuConfig``::

    from flask.ext.appconfig import HerokuConfig

    def create_app(configfile=None):
        app = Flask('myapp')
        HerokuConfig(app, configfile)
        return app

Works like the example above, but environment variables set by various Heroku
addons will be parsed as json and converted to configuration variables
accordingly. Forexample, when enabling `Mailgun
<https://addons.heroku.com/mailgun>`_, the configuration of `Flask-Mail
<http://pythonhosted.org/Flask-Mail/>`_ will be automatically be set correctly.

Installation
------------

Via `PyPI <http://pypi.python.org/pypi/flask-appconfig>`_::

    $ pip install flask-appconfig

Requires Python 2.7.


Thoughts on Configuration
-------------------------

There is a lot of ways to configure a Flask application and often times,
less-than-optimal ones are chosen in a hurry.

This extension aims to do three things:

1. Set a "standard" of doing configuration that is flexible and in-line with
   the official docs and (what I consider) good practices.
2. Make it as convenient as possible to provide these configuration methods in
   an application.
3. Auto-configure on Heroku as much as possible without sacrificing 1. and 2.

`12factor.net <http://12factor.net/>`_ seems to capture a good amount of good
thoughts on the issue and Flask-Appconfig should aid you in writing an
application that follows the principles laid out there.

Providing defaults
******************

Defaults should be included and overridable, without altering the file
containing the defaults.

Separate code and configuration
*******************************

It should be possible to install the app to a read-only (possibly system-wide)
location, without having to store configuration files (or, even worse,
configuration modules) inside its folders.

Environment variables and instance folders make this possible. As an added
benefit, configuration does not need to be stored alongside the code in version
control.

No code necessary for most deployments using the factory-method pattern
***********************************************************************

When deploying with gunicorn, passing ``myapp:create_app()`` suffices to create
an app instance, no boilerplate code to create the WSGI app should be necessary.

Multiple instances
******************

Running multiple apps inside the same interpreter should also be possible. While
this is slightly more complicated and may occasionally violate the "no-code"
guideline above, it's still straightforward by using configuration file
parameters.


Development
-----------
Flask-AppConfig is under "conceptional development". The API or semantics
may change in the future.

Send pull requests for more Heroku-apps to be supported. Send feedback via mail.
