import psycopg2

DATABASE_URL = "postgresql://neondb_owner:npg_3gl5MUntALYv@ep-sweet-frost-axd0ebwe-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_connection():
    return psycopg2.connect(DATABASE_URL)

try:
    conn = get_connection()
    print(" Connection Successful!")

    conn.close()

except Exception as e:
    print(" Connection Failed!")
    print("Error:", e)