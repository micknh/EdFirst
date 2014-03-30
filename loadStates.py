import sqlite3 as sqlite

with sqlite.connect('data-dev.sqlite') as connection:
	cursed = connection.cursor()
	sqlinsert = """
		insert into states(state) values (?)
	"""
	cursed.execute(sqlinsert,('NY',))
	cursed.execute(sqlinsert,('NH',))
	cursed.execute(sqlinsert,('MA',))
	cursed.execute(sqlinsert,('CT',))
	cursed.execute(sqlinsert,('CA',))
	cursed.execute(sqlinsert,('ME',))
	cursed.execute(sqlinsert,('VT',))
	cursed.execute(sqlinsert,('RI',))
	cursed.execute(sqlinsert,('NZ',))

	cursed.execute('Update states set active = 1')



