from config import get_connection

connection = get_connection()
cursor = connection.cursor()

cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")

connection.commit()
cursor.close()
connection.close()

print("All tables deleted successfully!")