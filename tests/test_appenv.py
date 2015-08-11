from flask import Flask
from flask_appconfig import AppConfig


def create_sample_app():
    app = Flask('testapp')
    AppConfig(app)
    return app


def test_envmocking(monkeypatch):
    monkeypatch.setenv('TESTAPP_CONFA', 'a')
    monkeypatch.setenv('TESTAPP_CONFB', 'b')

    app = create_sample_app()
    assert app.config['CONFA'] == 'a'
    assert app.config['CONFB'] == 'b'
