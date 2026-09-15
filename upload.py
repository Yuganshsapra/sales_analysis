from flask import Blueprint, request, session, redirect
import auth
from config import s3, S3_BUCKET, get_connection

import pandas as pd
import re
from datetime import datetime
from io import BytesIO

upload = Blueprint("upload", __name__)

# =====================================================
# Convert Pandas Data Type to MySQL
# =====================================================

def get_mysql_type(dtype):

    dtype = str(dtype)

    if "int" in dtype:
        return "INT"

    elif "float" in dtype:
        return "DOUBLE"

    elif "datetime" in dtype:
        return "DATE"

    else:
        return "VARCHAR(255)"


# =====================================================
# Clean Column Names
# =====================================================

def sanitize_column_name(column):

    column = column.strip().lower()

    column = column.replace(" ", "_")

    column = re.sub(r"[^a-zA-Z0-9_]", "", column)

    column = re.sub(r"_+", "_", column)

    return column


# =====================================================
# Validate Dataset
# =====================================================

def validate_sales_dataset(df):

    # Support product_name
    if "product_name" in df.columns:

        df.rename(
            columns={
                "product_name": "product"
            },
            inplace=True
        )

    required_columns = [

        "order_id",

        "order_date",

        "product",

        "category",

        "quantity",

        "sales",

        "profit"

    ]

    missing = [

        col

        for col in required_columns

        if col not in df.columns

    ]

    return missing
    


# =====================================================
# Generate S3 Key
# =====================================================

def generate_s3_key(filename):

    return f"uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
@upload.route("/upload", methods=["POST"])
def upload_csv():

    if "user" not in session:
        return redirect("/login")

    if "csv_file" not in request.files:
        return "No file selected."

    file = request.files["csv_file"]

    if file.filename == "":
        return "No file selected."

    if not file.filename.lower().endswith(".csv"):
        return "Please upload a CSV file."

    connection = None
    cursor = None

    try:

        # ==========================================
        # Read uploaded file into memory
        # ==========================================

        file_bytes = file.read()

        if len(file_bytes) == 0:
            raise Exception("Uploaded file is empty.")

        # ==========================================
        # Read CSV
        # ==========================================

        df = None

        for encoding in [

            "utf-8",

            "cp1252",

            "latin1"

        ]:

            try:

                df = pd.read_csv(
                    BytesIO(file_bytes),
                    encoding=encoding
                )

                break

            except UnicodeDecodeError:

                continue

        if df is None:

            raise Exception("Unable to read CSV.")

        # ==========================================
        # Clean Data
        # ==========================================

        df.columns = [

            sanitize_column_name(col)

            for col in df.columns

        ]

        df.drop_duplicates(inplace=True)

        df.dropna(inplace=True)

        missing = validate_sales_dataset(df)

        if missing:

            return f"Missing Columns: {', '.join(missing)}"

        total_rows = len(df)

        total_columns = len(df.columns)

        # ==========================================
        # Upload to AWS S3
        # ==========================================

        s3_key = generate_s3_key(file.filename)

        s3.upload_fileobj(

            BytesIO(file_bytes),

            S3_BUCKET,

            s3_key

        )

        # ==========================================
        # Database
        # ==========================================

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("""

            SELECT IFNULL(MAX(dataset_id),0)+1

            FROM upload_history

        """)

        dataset_id = cursor.fetchone()[0]

        print("Dataset ID:", dataset_id)
                # ==========================================
        # Insert into Shared sales_data Table
        # ==========================================

        insert_query = """
        INSERT INTO sales_data
        (
            dataset_id,
            uploaded_by,
            order_id,
            order_date,
            product,
            category,
            quantity,
            sales,
            profit
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,%s
        )
        """

        records = []

        for _, row in df.iterrows():

            records.append(

                (

                    dataset_id,

                    session["user"],

                    str(row["order_id"]),

                    str(row["order_date"]),

                    str(row["product"]),

                    str(row["category"]),

                    int(row["quantity"]),

                    float(row["sales"]),

                    float(row["profit"])

                )

            )

        cursor.executemany(

            insert_query,

            records

        )

        # ==========================================
        # Save Upload History
        # ==========================================

        cursor.execute(
            """
            INSERT INTO upload_history
            (
                file_name,
                dataset_id,
                s3_key,
                total_rows,
                total_columns,
                uploaded_by
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s
            )
            """,
            (
                file.filename,
                dataset_id,
                s3_key,
                total_rows,
                total_columns,
                session["user"]
            )
        )

        connection.commit()

        # ==========================================
        # Store Current Dataset in Session
        # ==========================================

        session["current_dataset"] = dataset_id

        session["upload_status"] = {

            "file_name": file.filename,

            "dataset_id": dataset_id,

            "total_rows": total_rows,

            "total_columns": total_columns

        }

        print("Upload Successful")

        return redirect("/dashboard")

    except Exception as e:

        if connection:

            connection.rollback()

        print("UPLOAD ERROR:", e)

        return f"""
        <h2>Upload Failed</h2>
        <br>
        <pre>{e}</pre>
        """

    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()