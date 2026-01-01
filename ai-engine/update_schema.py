import psycopg2
import os

POSTGRES_CONN = "postgresql://postgres:2005@localhost:5432/coact_ai"

def update_schema():
    print("Updating schema to use JSONB...")
    try:
        conn = psycopg2.connect(POSTGRES_CONN)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if table exists first
        cur.execute("SELECT to_regclass('public.sessions');")
        if not cur.fetchone()[0]:
            print("Table 'sessions' does not exist yet. It will be created on app start.")
            return

        # Alter columns
        # Note: In Postgres, if types are compatible (text/json -> jsonb), this works directly.
        # IF they were created as 'text' (default sqlalchemy string/text fallback sometimes) or 'json', 
        # casting to jsonb is safe.
        
        commands = [
            "ALTER TABLE sessions ALTER COLUMN transcript TYPE jsonb USING transcript::jsonb;",
            "ALTER TABLE sessions ALTER COLUMN report_data TYPE jsonb USING report_data::jsonb;",
            "ALTER TABLE sessions ALTER COLUMN meta TYPE jsonb USING meta::jsonb;"
        ]
        
        for cmd in commands:
            try:
                cur.execute(cmd)
                print(f"✅ Executed: {cmd}")
            except Exception as e:
                print(f"⚠️ Error executing '{cmd}': {e}")
                
        conn.close()
        print("Schema update complete.")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    update_schema()
