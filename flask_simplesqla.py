# -*- coding: utf-8 -*-
"""
    flask.ext.simplesqla
    ~~~~~~~~~~~~~~~~~~~~~~~

    Extension providing basic support of SQLAlchemy in Flask applications

    :copyright: (c) 2014 by Oleh Prypin <blaxpirit@gmail.com>
    :license: BSD, see LICENSE for more details.
"""

__version__ = '0.1-dev'

__all__ = ['SimpleSQLA']


import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.orm.exc
import werkzeug.utils
import flask


class SimpleSQLA(object):
    def __init__(self, app=None, engine_options={}, session_options={}):
        self.app = app
        self._engine_options = engine_options
        self._session_options = session_options
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initializes the application with some default settings and teardown listener.
        """
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

    @werkzeug.utils.cached_property
    def metadata(self):
        """An `sqlalchemy.MetaData` object.
        Created upon first access.
        """
        return sqlalchemy.MetaData()
    
    @werkzeug.utils.cached_property
    def Base(self):
        """An instance of `sqlalchemy.ext.declarative.declarative_base` based on `self.metadata`.
        Created upon first access.
        Provided for convenience. You don't have to use this. You may create your own declarative base (and even 
        overwrite this one), just use the provided `metadata` to construct it."""
        import sqlalchemy.ext.declarative
        return sqlalchemy.ext.declarative.declarative_base(metadata=self.metadata)

    @werkzeug.utils.cached_property
    def engine(self):
        """An `sqlalchemy.engine.Engine` object. Constructed using `sqlalchemy.engine_from_config` with options from
        application config starting with 'SQLALCHEMY_ENGINE_' and (with higher priority) `engine_options` dict supplied
        to the constructor.
        Created upon first access.
        """
        config = _prefixed_config(self.app.config, 'SQLALCHEMY_ENGINE_')
        config.update(self._engine_options)
        return sqlalchemy.engine_from_config(config, prefix='')

    @werkzeug.utils.cached_property
    def session(self):
        """An instance of `sqlalchemy.orm.scoped_session`. Constructed based on `self.engine` with options from 
        application config starting with 'SQLALCHEMY_SESSION_' and (with higher priority) `session_options` supplied to 
        the constructor.
        Created upon first access.
        """
        config = _prefixed_config(self.app.config, 'SQLALCHEMY_SESSION_')
        config.update(self._session_options)
        sessionmaker = sqlalchemy.orm.sessionmaker(self.engine, **config)
        return sqlalchemy.orm.scoped_session(sessionmaker)

    def __getattr__(self, name):
        """Redirects access to unset attributes to `self.session`.
        """
        return getattr(self.session, name)


def _prefixed_config(config, prefix):
    """Returns a dictionary containing only items from the supplied dictionary `config` which start with `prefix`, also 
    converting the key to lowercase and removing that prefix from it.
    
        _prefixed_config({'ONE': 1, 'MYPREFIX_TWO': 'MYPREFIX_'}) == {'two': 2}
    """
    result = {}
    for k, v in config.items():
        if k.startswith(prefix):
            result[k[len(prefix):].lower()] = v
    return result