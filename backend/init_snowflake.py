from app.core.snowflake import get_snowflake_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    print("Connecting to Snowflake...")
    try:
        session = get_snowflake_session()
        print("Connected!")
        
        # Read the migration file
        with open("app/db/snowflake_migrations.sql", "r") as f:
            sql_content = f.read()
            
        # Split by statements (simple split by semicolon, might be fragile but okay for this file)
        statements = sql_content.split(";")
        
        for statement in statements:
            if statement.strip():
                print(f"Executing: {statement[:50]}...")
                session.sql(statement).collect()
                print("Success.")
                
        print("Migration complete! Table 'products' created.")
        
    except Exception as e:
        print(f"Migration Failed: {e}")

if __name__ == "__main__":
    run_migration()
