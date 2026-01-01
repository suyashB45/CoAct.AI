import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        conn = psycopg2.connect(
            user="postgres", 
            password="2005", 
            host="localhost"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        db_name = "coact_ai"
        
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database '{db_name}'...")
            cur.execute(f"CREATE DATABASE {db_name}")
            print("✅ Database created.")
        else:
            print(f"✅ Database '{db_name}' already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error creating database: {e}")

if __name__ == "__main__":
    create_database()
