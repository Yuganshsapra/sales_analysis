from config import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

tables = [
    "sales",
    "products",
    "customers",
    "users"
]

for table in tables:
    cursor.execute(f"DROP TABLE IF EXISTS `{table}`")

cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

conn.commit()
cursor.close()
conn.close()

print("Database reset successfully!")