from app.core.snowflake import get_snowflake_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_schema():
    print("Connecting to Snowflake...")
    try:
        session = get_snowflake_session()
        print("Dropping table 'products'...")
        session.sql("DROP TABLE IF EXISTS products").collect()
        print("Table dropped.")
    except Exception as e:
        print(f"Reset Failed: {e}")

if __name__ == "__main__":
    reset_schema()
