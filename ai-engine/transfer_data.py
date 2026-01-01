import sqlite3
import psycopg2
import json
import os

SQLITE_DB = "instance/coact_ai.db"
POSTGRES_CONN = "postgresql://postgres:2005@localhost:5432/coact_ai"

def transfer():
    if not os.path.exists(SQLITE_DB):
        print("❌ SQLite DB not found.")
        return

    # 1. Read from SQLite
    print("Reading from SQLite...")
    sl_conn = sqlite3.connect(SQLITE_DB)
    sl_cur = sl_conn.cursor()
    
    try:
        sl_cur.execute("SELECT framework, stage, question FROM questions")
        rows = sl_cur.fetchall()
        print(f"Read {len(rows)} questions from SQLite.")
    except Exception as e:
        print(f"Error reading SQLite: {e}")
        return
    finally:
        sl_conn.close()

    # 2. Write to Postgres
    # First, let ensure tables exist. 
    # We can rely on app.py running 'db.create_all()' but safer to do it via app context or SQL here.
    # To keep it simple, let's use app context to init tables first.
    
    # We need to run this part inside a script that uses app context, 
    # OR we can just insert assuming tables are created by app.py first.
    # Let's use psycopg2 directly for insertion, but we need table creation.
    # So actually, let's rely on app.py to create tables, THEN insert.
    
    # But app.py isn't running with Postgres yet (it's running with SQLite conf in memory? No, I updated .env).
    # If I run `python app.py` it will start and create tables.
    # So I should start app.py, let it create tables, then run this transfer.
    # OR I can manually create the table here.
    
    print("Connecting to Postgres...")
    pg_conn = psycopg2.connect(POSTGRES_CONN)
    pg_cur = pg_conn.cursor()
    
    # Create table manually to be sure
    pg_cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        framework VARCHAR,
        stage VARCHAR,
        question TEXT
    );
    """)
    pg_conn.commit()
    
    # Check if empty
    pg_cur.execute("SELECT COUNT(*) FROM questions")
    count = pg_cur.fetchone()[0]
    
    if count > 0:
        print(f"⚠️ Postgres table has {count} rows. Skipping transfer.")
        pg_conn.close()
        return

    print("Inserting data into Postgres...")
    args_str = ','.join(pg_cur.mogrify("(%s,%s,%s)", x).decode('utf-8') for x in rows)
    pg_cur.execute("INSERT INTO questions (framework, stage, question) VALUES " + args_str)
    
    pg_conn.commit()
    print(f"✅ Transferred {len(rows)} rows to Postgres.")
    
    pg_cur.close()
    pg_conn.close()

if __name__ == "__main__":
    transfer()
