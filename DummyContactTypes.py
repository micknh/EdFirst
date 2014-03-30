import sqlite3 as sqlite

with sqlite.connect('data-dev.sqlite') as connection:
	cursed = connection.cursor()
	sqlinsert = """
		insert into contactTypes(contactType) values (?)
	"""
	cursed.execute(sqlinsert,('Email',))
	cursed.execute(sqlinsert,('Phone',))
	cursed.execute(sqlinsert,('Mobile',))
	cursed.execute(sqlinsert,('Facebook',))
	cursed.execute(sqlinsert,('Twitter',))
	cursed.execute(sqlinsert,('GooglePlus',))
	cursed.execute('Update contactTypes set active = 1')



