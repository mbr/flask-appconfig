from __future__ import print_function

import argparse
import os
import sys


# the function below has been lifted from the honcho source
#
# Copyright (c) 2012 Nick Stenning, http://whiteink.com/
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import re
def honcho_parse_env(content):
        values = {}
        for line in content.splitlines():
            m1 = re.match(r'\A([A-Za-z_0-9]+)=(.*)\Z', line)
            if m1:
                key, val = m1.group(1), m1.group(2)

                m2 = re.match(r"\A'(.*)'\Z", val)
                if m2:
                    val = m2.group(1)

                m3 = re.match(r'\A"(.*)"\Z', val)
                if m3:
                    val = re.sub(r'\\(.)', r'\1', m3.group(1))

                values[key] = val
        return values
# end of honcho source


def main_flaskdev():
    try:
        import importlib
    except ImportError:
        print ('You do not have importlib installed. Please install a '
               'backport for versions < 2.7/3.1 of it first.')
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Imports a module passed on the commandline, instantiates '
                    'an app by calling imported_module.create_app() with an '
                    'optional configuration file and runs it in debug mode.',
    )
    parser.add_argument('module_name', help='Name of the module to import.')
    parser.add_argument('-c', '--configfile',
                        help='Configuration file to pass as the first '
                        'parameter to create_app.')
    parser.add_argument('-D', '--no-debug', action='store_false',
                        dest='debug', default=True,
                        help='Do not run in debug mode.')
    parser.add_argument('-H', '--hostname', default='localhost',
                        help='Hostname to bind to. Defaults to localhost.')
    parser.add_argument('-p', '--port', default=5000, type=int,
                        help='Port to listen on. Defaults to 5000.')
    parser.add_argument('-S', '--ssl', default=None, action='store_const',
                        const='adhoc',
                        help='Enable SSL with a self-signed cert.')
    parser.add_argument('-e', '--env', default='.env',
                        help='Load environment variables from file.')

    args = parser.parse_args()

    if args.env and os.path.exists(args.env):
        buf = open(args.env).read()
        os.environ.update(honcho_parse_env(buf))

    mod = importlib.import_module(args.module_name)
    mod.create_app(args.configfile).run(args.hostname, args.port,
                                        ssl_context=args.ssl,
                                        debug=args.debug)
