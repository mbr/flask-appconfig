#!/usr/bin/env python

import os
from six.moves.urllib_parse import urlparse


def from_docker_envvars(config):
    # linked postgres database (link name 'pg' or 'postgres')
    if 'PG_PORT' in os.environ:
        pg_url = urlparse(os.environ['PG_PORT'])

        if not pg_url.scheme == 'tcp':
            raise ValueError('Only tcp scheme supported for postgres')

        host, port = pg_url.netloc.split(':')

        uri = 'postgres://{user}:{password}@{host}:{port}/{database}'.format(
            user=os.environ.get('PG_ENV_POSTGRES_USER', 'postgres'),
            password=os.environ.get('PG_ENV_POSTGRES_PASSWORD', ''),
            host=host,
            port=port,
            database=os.environ.get('PG_ENV_POSTGRES_DB'))

        config['SQLALCHEMY_DATABASE_URI'] = uri
