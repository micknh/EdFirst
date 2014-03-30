import sqlalchemy
sqlalchemy.__version__
from sqlalchemy import create_engine
# Creating an inmemory  sqlite database for the tutorial purposes
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import sessionmaker, aliased, relationship, backref
from sqlalchemy.orm.exc import MultipleResultsFound,NoResultFound
Session = sessionmaker()
# when engine is created Session.configure(bind=engine)
engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
Session.configure(bind=engine)

class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, Sequence('user_id_seq') ,primary_key=True)
	name = Column(String(50))
	fullname = Column(String(50))
	password = Column(String(12))

	def __repr__(self):
		return "<User(name='%s', fullname='%s', password='%s')>" % (self.name, self.fullname, self.password)

Base.metadata.create_all(engine)

class Address(Base):
	__tablename__ = 'Addresses'
	id = Column(Integer, primary_key=True)
	email_address = Column(String, nullable=False)
	user_id = Column(Integer, ForeignKey('users.id'))
	user = relationship("User", backref=backref('addresses', order_by=id))
	def __repr__(self):
		return "<Address(email_address=%s)>" % self.email_address

Base.metadata.create_all(engine)






session = Session()
ed_user = User(name='ed', fullname="Edward Jones", password='nonesuch')
session.add(ed_user)
chloe_user = User(name='Chloeoh', fullname="Chloe Tinker", password='bubba')
session.add(chloe_user)


# our_user = session.query(User).filter_by(name='Chloeoh').first()
# print our_user
# print ed_user is our_user

session.add_all([
	User(name='Evan', fullname='Evan Brennan-White', password="fx3k9c"),
	User(name='Leia', fullname='Leia Brennan-White', password="fx3k9c"),
	User(name='Chance', fullname='Chance Brennan-White', password="dog")])
chloe_user.password = 'ra++le'
# print session.dirty

# print session.new
session.commit()
# print chloe_user.id

# ed_user.name = 'Edwardo'
# fake_user = User(name='broofus', fullname='Broofass', 
# 	password='Nothing' )
# session.add(fake_user)
# print session.query(User).filter(User.name.in_(['Edwardo', 'broofus'])).all()
# session.rollback()
# print ed_user.name
# print fake_user in session
# print session.query(User).filter(User.name.in_(['ed', 'fake_user'])).all()
# for instance in session.query(User).order_by(User.id):
# 	print instance.name, instance.fullname

# for name, fullname in session.query(User.name, User.fullname):
# 	print name, fullname

# for row in session.query(User, User.name,).all():
# 	print row.User, row.name

# for row in session.query(User.name.label('full_label')).all():
# 	print row.full_label

# user_alias = aliased(User, name='user_alias')
# for row in session.query(user_alias, user_alias.name).all():
# 	print row.user_alias

# for u in session.query(User).order_by(User.id)[1:2]:
# 	print u

# for u in session.query(User).filter(User.name=='Chloeoh').\
# filter(User.fullname!='Broofus Tinker'):
# 	print u

# for u in session.query(User).filter(User.name.like('Leia')).\
# filter(User.fullname!='Broofus Tinker'):
# 	print u

# for u in session.query(User).filter(User.name.in_(['Evan', 'Chance'])).\
# filter(User.fullname!='Broofus Tinker'):
# 	print 'Boy',u

# for u in session.query(User).filter((User.name=='Leia') | (User.name=='Chloeoh')):
# 	print u.fullname


# u = session.query(User).filter(User.name.match('Chloeoh'))


query = session.query(User).filter(User.fullname.like('%Chloe%')).order_by(User.name)
# print query.all()

# for member in query:
# 	print member.name

# print query.first()

try:
	user = query.one()
	userid = user.id
	msg = ''
except MultipleResultsFound, e:
	user = query.first()
	userid = user.id
	msg = 'Multiple Results Found'
except NoResultFound,e:
	userid = 0
	msg = 'No Results Found'
print 'UserID:', userid,msg

jack = User(name="jack", fullname="Jack Bean", password="gjffdd")
jack.addresses = [
	Address(email_address='jack@google.com'),
	Address(email_address='j25@yahoo.com')
]
print jack.addresses[1]
print jack.addresses[1].user 
session.add(jack)
session.commit()
jack = session.query(User).\
	filter_by(name="jack").one()

# jack.addresses is a lazy load of the address information because of the backref
print jack, jack.addresses

for u, a in session.query(User, Address) \
	.filter(User.id==Address.user_id) \
	.filter(Address.email_address==\
		'jack@google.com')\
	.all():
	print u 
	print a 

qry = session.query(User).join(Address) \
	.filter(Address.email_address=='jack@google.com') \
	.all()
print qry

qry = query.join(Address, User.id==Address.user_id)
print qry.all()

# Using Aliases to query a table twice
adalias1 = aliased(Address)
adalias2 = aliased(Address)
for username, email1, email2 in \
	session.query(User.name, \
		adalias1.email_address, \
		adalias2.email_address, ) \
	.join(adalias1, User.addresses) \
	.join(adalias2, User.addresses) \
	.filter(adalias1.email_address=='jack@google.com') \
	.filter(adalias2.email_address=='j25@yahoo.com'):
	print username, email1, email2