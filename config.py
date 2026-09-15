import pymysql
import boto3

# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DB_HOST = "YOUR_RDS_ENDPOINT"
DB_USER = "YOUR_DATABASE_USERNAME"
DB_PASSWORD = "YOUR_DATABASE_PASSWORD"
DB_NAME = "YOUR_DATABASE_NAME"
DB_PORT = 3306


def get_connection():

    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


# =====================================================
# AWS S3 CONFIGURATION
# =====================================================

S3_BUCKET = "YOUR_S3_BUCKET_NAME"

AWS_REGION = "YOUR_AWS_REGION"


# =====================================================
# AWS S3 CLIENT
# =====================================================

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)