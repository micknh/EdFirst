from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request,Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask.ext.login import UserMixin, AnonymousUserMixin
from . import db, login_manager


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    # author = db.relationship('BlogPost', backref='author', lazy='dynamic')
    # author = db.relationship('BlogPost',backref=db.backref('authorid', lazy='joined'))

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        self.followed.append(Follow(followed=self))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# class Country(db.Model):
#     __tablename__ = 'countries'
#     countryid = db.Column(db.Integer, primary_key=True)
#     country = db.Column(db.String(35), unique=True, index=True)
#     active = db.Column(db.Boolean, default=True)

#     @staticmethod
#     def generate_countries():
#         Countries = ['United States',"China", 'Vietnam', 'South Korea', 'Singapore', 'Thailand']
#         for ctry in Countries:
#             c = Country(country=ctry)
#             db.session.add(c)
#             db.session.commit()

# class RelationType(db.Model):  # pylint: disable-msg=R0903
#     """
#     Holds RelationTypes names for the database to load during the registration page.

#     SQLalchemy ORM table object which is used to load, and push, data from the
#     server memory scope to, and from, the database scope.
#     """
#     __tablename__ = "RelationTypes"

#     relationTypeid   = db.Column(db.Integer, primary_key=True)
#     relationType = db.Column(db.String(35), unique=True)
#     active = db.Column(db.Boolean, default=True)

#     # def __init__(self, relationtype_name):
#     #     """
#     #     Used to create a relationType object in the python server scope
#     #     """
#     #     self.relationtype_name = relationtype_name

#     @staticmethod
#     def generate_relationtypes():
#         RelationTypes = ['Self',"Mother", 'Father', 'Grandparent', 'Sibling', 'Other']
#         for rt in RelationTypes:
#             c = RelationType(relationtype_name=rt)
#             db.session.add(c)
#             db.session.commit()

# class Contact(db.Model):
#     __tablename__ = "contacts"
#     contactid = db.Column(db.Integer, primary_key=True)
#     firstname = db.Column(db.String(60))
#     lastname = db.Column(db.String(60))
#     relationTypeid = db.Column(db.Integer, db.ForeignKey("RelationTypes.relationTypeid"))
#     contactTypeid = db.Column(db.Integer, db.ForeignKey('contactTypes.contactTypeid'))
#     preferredContact = db.Column(db.String(60))
#     timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     active = db.Column(db.Boolean, default=True)

#     def __init__(self, lastname):
#         """
#         Used to create a Contact object in the python server scope
#         """
#         self.lastname = lastname

# class AdminUser(db.Model):
#     __tablename__ = "adminUsers"
#     contactid = db.Column(db.Integer, primary_key=True)
#     userid = db.Column(db.Integer,db.ForeignKey('users.id'))
#     addressline1 = db.Column(db.String(60))
#     addressline2 = db.Column(db.String(60))
#     city = db.Column(db.String(20))
#     stateid = db.Column(db.Integer, db.ForeignKey('states.stateid'))
#     countryid = db.Column(db.Integer, db.ForeignKey('countries.countryid'))
#     preferredContactID = db.Column(db.Integer, db.ForeignKey('contactTypes.contactTypeid'))
#     email = db.Column(db.String(45))
#     phone = db.Column(db.String(20))
#     mobile = db.Column(db.String(20))
#     facebook = db.Column(db.String(20))
#     twitter = db.Column(db.String(20))
#     googleplus = db.Column(db.String(20))
#     timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     active = db.Column(db.Boolean, default=True)

#     def __init__(self, email):
#         """
#         Used to create a AdminUser object in the python server scope
#         """
#         self.email = email

# class ContactType(db.Model):
#     __tablename__ = 'contactTypes'
#     contactTypeid = db.Column(db.Integer, primary_key=True)
#     contactType = db.Column(db.String(35), unique=True, index=True)
#     active = db.Column(db.Boolean, default=True)


#     @staticmethod
#     def generate_contactTypes():
#         Types = ['Landline', 'Mobile', 'Email', 'Twitter', 'Facebook', 'Google+', 'Other']
#         for type in Types:
#             t = ContactType(ctype=type)
#             db.session.add(t)
#             db.session.commit()

# class Language(db.Model):
#     __tablename__ = 'languages'
#     languageid = db.Column(db.Integer, primary_key=True)
#     language = db.Column(db.String(35), unique=True, index=True)
#     active = db.Column(db.Boolean, default=True)
#     language = db.relationship('BlogPost',backref=db.backref('languageid', lazy='joined'))
#     @staticmethod
#     def generate_languages():
#         Types = ['English', 'Chinese', 'Korean', 'Vietnamese', 'Thai', 'Other']
#         for type in Types:
#             t = Language(ctype=type)
#             db.session.add(t)
#             db.session.commit()


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    active = db.Column(db.Boolean, default=True)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

# class State(db.Model):  # pylint: disable-msg=R0903
#     """
#     Holds State names for the database to load during the registration page.

#     SQLalchemy ORM table object which is used to load, and push, data from the
#     server memory scope to, and from, the database scope.
#     """
#     __tablename__ = "states"

#     stateid = db.Column(db.Integer, primary_key=True)
#     state= db.Column(db.String(10), unique=True)
#     active = db.Column(db.Boolean, default=True)

#     def __init__(self, state_name):
#         """
#         Used to create a State object in the python server scope
#         """
#         self.state_name = state_name

#     def generate_states():
#         Types = ['NH', 'MA', 'CT', 'VT', 'ME', 'NY', 'RI']
#         for type in Types:
#             t = State(state_name=type)
#             db.session.add(t)
#             db.session.commit()

# class BlogPost(db.Model):
#     __tablename__ = 'blogPosts'
#     postID = db.Column(db.Integer, primary_key=True)
#     postTitle = db.Column(db.String(180), unique=True)
#     postBody = db.Column(db.Text)
#     postBody_html = db.Column(db.Text)
#     authorid = db.Column(db.Integer, db.ForeignKey('users.id'))
#     # languageid = db.Column(db.Integer, db.ForeignKey('languages.languageid'),nullable=False)
#     tranDate = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     active = db.Column(db.Integer, default=1)
#     # languageid_by = db.relationship('languages',
#     #                             foreign_keys=[languageid],)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
#     # authorid_by = db.relationship('User',
#     #                             foreign_keys=[id])
#     # authorid_by = db.relationship("User", backref=('users', order_by=id))

#     # authorid_by = db.relationship('User',
#     #                            foreign_keys=[User.id],
#     #                            backref=db.backref('users', lazy='joined'),
#     #                            lazy='dynamic',
#     #                            cascade='all, delete-orphan')

#     def __init__(self, title):
#         """
#         Used to create a State object in the python server scope
#         """
#         self.title = title


    


















db.event.listen(Post.body, 'set', Post.on_changed_body)
