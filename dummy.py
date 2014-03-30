import sqlite3 as sqlite

with sqlite.connect('data-dev.sqlite') as connection:
	cursed = connection.cursor()
	sqlinsert = """
		insert into countries(country) values (?)
	"""
	cursed.execute(sqlinsert,('USA',))
	cursed.execute(sqlinsert,('China',))
	cursed.execute(sqlinsert,('Singapore',))
	cursed.execute(sqlinsert,('South Korea',))
	cursed.execute(sqlinsert,('Vietnam',))
	cursed.execute(sqlinsert,('Thailand',))



