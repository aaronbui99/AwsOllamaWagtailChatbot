import os
import sys
import psycopg2
from psycopg2 import OperationalError

def check_connection():
    try:
        conn = psycopg2.connect(
            dbname   = os.environ["RDS_DB_NAME"],
            user     = os.environ["RDS_USERNAME"],
            password = os.environ["RDS_PASSWORD"],
            host     = os.environ["RDS_HOSTNAME"],
            port     = os.environ.get("RDS_PORT", "5432"),
            sslmode  = "require"
        )
        conn.close()
        print("✅ SUCCESS: Connected to RDS PostgreSQL!")
    except OperationalError as e:
        print("❌ ERROR: Could not connect to RDS:")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    check_connection()
