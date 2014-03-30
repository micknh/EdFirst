import sqlite3 as sqlite

with sqlite.connect('data-dev.sqlite') as connection:
	cursed = connection.cursor()
	sqlinsert = """
		insert into languages(language) values (?)
	"""
	cursed.execute(sqlinsert,('English',))
	cursed.execute(sqlinsert,('Chinese',))
	cursed.execute(sqlinsert,('Thai',))
	cursed.execute(sqlinsert,('Korean',))
	cursed.execute(sqlinsert,('Vietnamese',))
	cursed.execute(sqlinsert,('Mandarin',))

	cursed.execute('Update languages set active = 1')



