from app.core.snowflake import get_snowflake_session
from typing import List, Optional, Dict
import json
import logging

logger = logging.getLogger(__name__)

class SnowflakeVectorService:
    @property
    def session(self):
        return get_snowflake_session()

    def search_similar_products(self, query_vector: List[float], limit: int = 5) -> List[dict]:
        """
        Searches for similar products using Snowflake Vector Search (Cosine Similarity).
        """
        try:
            # Snowflake requires the vector to be passed as a string representation in SQL ?? 
            # Or usually we can pass it as a parameter if using snowpark.
            # But the SQL syntax is VECTOR_COSINE_SIMILARITY(embedding, TO_VECTOR(?))
            
            # Construct SQL query
            # We convert the list to a SQL array string
            vector_str = str(query_vector)
            
            cmd = f"""
            SELECT id, name, description, price, image_url, source_url, 
                   VECTOR_COSINE_SIMILARITY(embedding, PARSE_JSON('{vector_str}')::VECTOR(FLOAT, 3072)) as score
            FROM products
            ORDER BY score DESC
            LIMIT {limit}
            """
            
            # Execute
            results = self.session.sql(cmd).collect()
            
            # Parse results
            output = []
            for row in results:
                output.append({
                    "id": row['ID'],
                    "name": row['NAME'],
                    "description": row['DESCRIPTION'],
                    "price": row['PRICE'],
                    "image_url": row['IMAGE_URL'],
                    "source_url": row['SOURCE_URL'],
                    "score": row['SCORE']
                })
            return output
            
        except Exception as e:
            logger.error(f"Vector Search Failed: {e}")
            return []

    def insert_product(self, product_data: Dict, embedding: List[float]):
        """
        Inserts a product with its embedding into Snowflake.
        """
        try:
            # We use a merge (upsert) logic ideally, but for now simple insert
            id = product_data.get('id')
            name = product_data.get('name').replace("'", "''")
            desc = product_data.get('description', '').replace("'", "''")
            price = product_data.get('price', 0.0)
            img = product_data.get('image_url', '').replace("'", "''")
            src = product_data.get('source_url', '').replace("'", "''")
            vector_str = str(embedding)
            
            cmd = f"""
            MERGE INTO products AS target
            USING (SELECT '{id}' AS id) AS source
            ON target.id = source.id
            WHEN MATCHED THEN
                UPDATE SET 
                    name = '{name}', 
                    description = '{desc}', 
                    price = {price}, 
                    image_url = '{img}', 
                    source_url = '{src}',
                    embedding = PARSE_JSON('{vector_str}')::VECTOR(FLOAT, 3072)
            WHEN NOT MATCHED THEN
                INSERT (id, name, description, price, image_url, source_url, embedding)
                VALUES ('{id}', '{name}', '{desc}', {price}, '{img}', '{src}', PARSE_JSON('{vector_str}')::VECTOR(FLOAT, 3072))
            """
            self.session.sql(cmd).collect()
            self.session.sql(cmd).collect()
            return True, "Success"
        except Exception as e:
            logger.error(f"Insert Product Failed: {e}")
            return False, str(e)

snowflake_vector_service = SnowflakeVectorService()
