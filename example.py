from sqlalchemy.schema import Table, Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship, mapper

from flask import Flask, url_for, abort, redirect
from flask.ext.simplesqla import SimpleSQLA

app = Flask('__name__')

app.config['SQLALCHEMY_ENGINE_URL'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_ENGINE_ECHO'] = True

db = SimpleSQLA(app)


# Address defined with mapper configuration
addresses = Table('addresses', db.metadata,
    Column('id', Integer, primary_key=True),
    Column('email', String, nullable=False),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
)

class Address(object):
    def __init__(self, email):
        self.email = email
    
    def __str__(self):
        return self.email

mapper(Address, addresses)


# User defined with declarative
class User(db.Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

    addresses = relationship(Address, backref='user', cascade='all, delete-orphan')
    
    def url(self):
        return url_for('user_page', id=self.id, name=self.name)


def init_db():
    db.metadata.create_all(db.engine)
    admin = User(name="BlaXpirit", fullname="Oleh Prypin", password="dev", addresses=[Address('blaxpirit@gmail.com')])
    db.session.add(admin)
    db.session.commit()


@app.route('/users/<int:id>/')
@app.route('/users/<int:id>/<name>')
def user_page(id, name=None):
    user = db.query(User).get(id) or abort(404)
    if name!=user.name:
        return redirect(user.url())
    return '<h1>{0.name}</h1> <p>{0.fullname}</p> <p>{0.addresses[0]}</p>'.format(user)

@app.route('/users/')
def users_index():
    users = db.query(User)
    return '<ul>'+''.join('<li><a href="{}">{}</a></li>'.format(user.url(), user.name) for user in users)+'</ul>'


if __name__=='__main__':
    import sys
    if list(sys.argv[1:])==['init_db']:
        init_db()
    else:
        app.run(debug=True)