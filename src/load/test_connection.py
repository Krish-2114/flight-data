import os

import psycopg2
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


connection = psycopg2.connect(
    host=os.getenv("SUPABASE_DB_HOST"),
    port=os.getenv("SUPABASE_DB_PORT"),
    database=os.getenv("SUPABASE_DB_NAME"),
    user=os.getenv("SUPABASE_DB_USER"),
    password=os.getenv("SUPABASE_DB_PASSWORD")
)


cursor = connection.cursor()

cursor.execute(
    "SELECT current_database(), current_user;"
)

result = cursor.fetchone()

print("Connected successfully!")
print("Database:", result[0])
print("User:", result[1])


cursor.close()
connection.close()