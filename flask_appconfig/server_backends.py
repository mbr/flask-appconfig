from collections import namedtuple
from multiprocessing import cpu_count

from .util import try_import


def _get_cpu_count():
    try:
        return cpu_count()
    except NotImplementedError:
        raise RuntimeError('Could not determine CPU count and no '
                           '--instance-count supplied.')


DEFAULT = 'tornado,meinheld,gunicorn,werkzeug-threaded,werkzeug'

backends = {}


def backend(name):
    def _(cls):
        backends[name] = cls
        cls.name = name
        return cls

    return _


BackendInfo = namedtuple('BackendInfo', 'version,extra_info')


class ServerBackend(object):
    vulnerable = True

    def __init__(self, processes=None):
        if not hasattr(self, 'processes'):
            if processes is None:
                processes = _get_cpu_count()
            self.processes = processes

    @classmethod
    def get_info(cls):
        """Return information about backend and its availability.

        :return: A BackendInfo tuple if the import worked, none otherwise.
        """
        mod = try_import(cls.mod_name)
        if not mod:
            return None
        version = getattr(mod, '__version__', None) or getattr(mod, 'version',
                                                               None)
        return BackendInfo(version or 'deprecated', '')

    def run_server(self, app, host, port):
        raise NotImplementedError

    def __str__(self):
        return '{} {}'.format(self.name, self.get_info().version)


@backend('werkzeug')
class WerkzeugBackend(ServerBackend):
    threaded = False
    mod_name = 'werkzeug'

    def run_server(self, app, host, port):
        app.run(host,
                port,
                debug=False,
                use_evalex=False,
                threaded=self.threaded,
                processes=self.processes)


@backend('werkzeug-threaded')
class WerkzeugThreaded(WerkzeugBackend):
    threaded = True
    processes = 1


@backend('tornado')
class TornadoBackend(ServerBackend):
    mod_name = 'tornado'

    def run_server(self, app, host, port):
        from tornado.wsgi import WSGIContainer
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop

        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(port, address=host)
        IOLoop.instance().start()


@backend('gunicorn')
class GUnicornBackend(ServerBackend):
    mod_name = 'gunicorn'

    def run_server(self, app, host, port):
        import gunicorn.app.base

        class FlaskGUnicornApp(gunicorn.app.base.BaseApplication):
            options = {
                'bind': '{}:{}'.format(host, port),
                'workers': self.processes
            }

            def load_config(self):
                for k, v in self.options.items():
                    self.cfg.set(k.lower(), v)

            def load(self):
                return app

        FlaskGUnicornApp().run()


@backend('meinheld')
class MeinHeldBackend(ServerBackend):
    mod_name = 'meinheld'

    def run_server(self, app, host, port):
        from meinheld import server

        server.listen((host, port))
        server.run(app)
