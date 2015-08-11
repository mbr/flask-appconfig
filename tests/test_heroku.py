from flask import Flask
from flask_appconfig import HerokuConfig


def create_sample_app():
    app = Flask('testapp')
    HerokuConfig(app)
    return app


def test_herokupostgres(monkeypatch):
    monkeypatch.setenv('HEROKU_POSTGRESQL_ORANGE_URL', 'heroku-db-uri')

    app = create_sample_app()
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'heroku-db-uri'
