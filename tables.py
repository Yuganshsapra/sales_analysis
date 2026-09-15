from config import get_connection

connection = get_connection()
cursor = connection.cursor()

# =====================================================
# USERS TABLE
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    email VARCHAR(100) UNIQUE NOT NULL,

    password VARCHAR(255) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

# =====================================================
# UPLOAD HISTORY
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS upload_history(

    id INT AUTO_INCREMENT PRIMARY KEY,

    file_name VARCHAR(255) NOT NULL,

    dataset_id INT NOT NULL,

    s3_key VARCHAR(255) NOT NULL,

    total_rows INT NOT NULL,

    total_columns INT NOT NULL,

    uploaded_by VARCHAR(100) NOT NULL,

    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

# =====================================================
# SHARED SALES DATA TABLE
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_data(

    id INT AUTO_INCREMENT PRIMARY KEY,

    dataset_id INT NOT NULL,

    uploaded_by VARCHAR(100) NOT NULL,

    order_id VARCHAR(100),

    order_date DATE,

    product VARCHAR(255),

    category VARCHAR(255),

    quantity INT,

    sales DOUBLE,

    profit DOUBLE

)
""")

connection.commit()

print("Database tables created successfully!")

cursor.close()
connection.close()