# -*- coding: utf-8 -*-
"""
    flask_simplesqla
    ~~~~~~~~~~~~~~~~

    Extension providing basic support of SQLAlchemy in Flask applications

    :copyright: (c) 2014-2015 by Oleh Prypin <blaxpirit@gmail.com>
    :license: BSD, see LICENSE for more details.
"""

__version__ = '1.0'

__all__ = ['SimpleSQLA']


import sqlalchemy
import sqlalchemy.orm
from flask.helpers import locked_cached_property


class SimpleSQLA(object):
    def __init__(self, app=None):
        self.app = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initializes the application with some default settings and teardown listener.
        """
        self.app = app
        app.config.setdefault('SQLALCHEMY_COMMIT_ON_TEARDOWN', False)
        app.config.setdefault('SQLALCHEMY_ENGINE_CONVERT_UNICODE', True)

        try:
            teardown = app.teardown_appcontext
        except AttributeError: # Flask<0.9
            teardown = app.teardown_request

        @teardown
        def on_teardown(exception):
            if app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']:
                if exception is None:
                    self.session.commit()
            self.session.remove()

    @locked_cached_property
    def metadata(self):
        """An `sqlalchemy.MetaData` object.
        Created upon first access. If you overwrite this before accessing it, it will not be created.
        """
        return sqlalchemy.MetaData()

    @locked_cached_property
    def Base(self):
        """An instance of `sqlalchemy.ext.declarative.declarative_base` based on `self.metadata`.
        Created upon first access. If you overwrite this before accessing it, it will not be created.
        """
        import sqlalchemy.ext.declarative
        return sqlalchemy.ext.declarative.declarative_base(metadata=self.metadata)

    @locked_cached_property
    def engine(self):
        """An `sqlalchemy.engine.Engine` object. Constructed using `sqlalchemy.engine_from_config` with options from
        application config starting with 'SQLALCHEMY_ENGINE_'.
        Created upon first access. If you overwrite this before accessing it, it will not be created.
        """
        try:
            config = _prefixed_config(self.app.config, 'SQLALCHEMY_ENGINE_')
        except AttributeError:
            config = {}
        if 'url' not in config:
            raise KeyError("SQLALCHEMY_ENGINE_URL not provided")
        return sqlalchemy.engine_from_config(config, prefix='')

    @locked_cached_property
    def session(self):
        """An instance of `sqlalchemy.orm.scoped_session`. Constructed based on `self.engine` with options from 
        application config starting with 'SQLALCHEMY_SESSION_' and (with higher priority) `session_options` supplied to
        the constructor.
        Created upon first access. If you overwrite this before accessing it, it will not be created.
        Note that any missing attribute on the `SimpleSQLA` object will be redirected to `session` meaning you may write
        `db.query` instead of `db.session.query`, etc.
        """
        try:
            config = _prefixed_config(self.app.config, 'SQLALCHEMY_SESSION_')
        except AttributeError:
            config = {}
        sessionmaker = sqlalchemy.orm.sessionmaker(self.engine, **config)
        return sqlalchemy.orm.scoped_session(sessionmaker)

    def __getattr__(self, name):
        """Redirects access to unset attributes to `self.session`.
        """
        return getattr(self.session, name)


def _prefixed_config(config, prefix):
    """Returns a dictionary containing only items from the supplied dictionary `config` which start with `prefix`, also
    converting the key to lowercase and removing that prefix from it.

        _prefixed_config({'ONE': 1, 'MYPREFIX_TWO': 2}, 'MYPREFIX_') == {'two': 2}
    """
    result = {}
    for k, v in config.items():
        if k.startswith(prefix):
            result[k[len(prefix):].lower()] = v
    return result
