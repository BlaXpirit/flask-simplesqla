Flask-SimpleSQLA
================

This module is meant to be a simple replacement for [Flask-SQLAlchemy][flask-sqlalchemy]. It provides only the most basic functionality and doesn't enforce much upon you.

## Quickstart

The basic setup may look like this:

    from flask import Flask
    from flask.ext.simplesqla import SimpleSQLA

    app = Flask('__name__')

    app.config['SQLALCHEMY_ENGINE_URL'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_ENGINE_ECHO'] = True

    db = SimpleSQLA(app)

Then you can define your SQLAlchemy tables and classes using `db.metadata`, `db.engine` and (optionally) `db.Base`.

In your routes you can use `db.session` which is just SQLAlchemy's `scoped_session`. A database session will be started only if you use it in your routes, and it will be closed when the request ends.

Committing, however, is your responsibility. If you don't use `db.commit()` appropriately, the changes will be lost (unless `SQLALCHEMY_COMMIT_ON_TEARDOWN` is set to `True`, which is not recommended).

Your routes may look like this:

    @app.route('/users/<int:id>/')
    @app.route('/users/<int:id>/<name>')
    def user_page(id, name=None):
        user = db.query(User).get(id) or abort(404)
        if name!=user.name:
            return redirect(user.url())
        return render_template('user.html', user=user)

Note that `db.query` is the same as `db.session.query` because all the missing attributes are redirected to the `session`.



[flask-sqlalchemy]: https://github.com/mitsuhiko/flask-sqlalchemy
