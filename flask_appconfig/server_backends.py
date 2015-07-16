from multiprocessing import cpu_count
import socket


DEFAULT = 'tornado,werkzeug-threaded,werkzeug'


def _get_cpu_count():
    try:
        return cpu_count()
    except NotImplementedError:
        raise RuntimeError('Could not determine CPU count and no '
                           '--instance-count supplied.')


def werkzeug_threaded(app, hostname, port):
    return _run_werkzeug(app, hostname, port, processes=1, threaded=False)


def werkzeug(app, hostname, port):
    return _run_werkzeug(app, hostname, port, processes=_get_cpu_count(),
                         threaded=False)


def _run_werkzeug(app, hostname, port, **kwargs):
    try:
        app.run(hostname, port, debug=False, use_evalex=False, **kwargs)
        return True
    except socket.error as e:
        if not port < 1024 or e.errno != 13:
            raise

        # helpful message when trying to run on port 80 without room
        # permissions
        raise RuntimeError('Could not open socket on {}:{}: {}. '
                           'Do you have root permissions?'
                           .format(hostname, port, e))


def tornado(app, hostname, port):
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port, address=hostname)
    IOLoop.instance().start()
    return True
