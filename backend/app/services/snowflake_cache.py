from app.core.snowflake import get_snowflake_session
import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SnowflakeCacheService:
    @property
    def session(self):
        s = get_snowflake_session()
        if not s:
            print("!!! SNOWFLAKE SESSION IS NONE !!! Check credentials.")
        return s

    def generate_key(self, product_name: str) -> str:
        """
        Generate a safe cache key using SHA-256 hash.
        ULTRA-AGGRESSIVE normalization to handle Lens returning different languages/details.
        """
        import hashlib
        import re
        
        normalized = product_name.lower().strip()
        
        # Remove common variable parts
        # 1. Remove anything in parentheses
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        
        # 2. Remove storage specs (256GB, 128 GB, 1TB)
        normalized = re.sub(r'\b\d+\s*(gb|tb|mb)\b', '', normalized, flags=re.IGNORECASE)
        
        # 3. Remove model numbers (A2482, SM-G998U)
        normalized = re.sub(r'\b[A-Z]{1,3}\d{3,}[A-Z]*/?\w*\b', '', normalized, flags=re.IGNORECASE)
        
        # 4. Remove common suffixes
        normalized = re.sub(r'\b(unlocked|renewed|refurbished|certified|pre-owned)\b', '', normalized, flags=re.IGNORECASE)
        
        # 5. Remove numbers (oz, ml, pack sizes, etc.)
        normalized = re.sub(r'\b\d+\.?\d*\s*(oz|ounce|ml|l|pack|ct|count|bottles?|bouteilles?)\b', '', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\b\d+\b', '', normalized)  # Remove standalone numbers
        
        # 6. Remove non-ASCII chars (handles accented chars from French/Spanish)
        normalized = re.sub(r'[^\x00-\x7F]+', '', normalized)
        
        # 7. Remove extra whitespace and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # 8. CRITICAL: Keep only the first 4 words (brand + product type)
        words = normalized.split()[:4]
        normalized = ' '.join(words)
        
        print(f"[CacheKey] Original: '{product_name[:50]}...' -> Core: '{normalized}'")
        
        hash_digest = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        return hash_digest  # 64 hex chars



    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Check cache, return if valid (not expired).
        """
        if not self.session:
            # logger.debug("Snowflake session not available. Skipping cache.")
            return None

        try:
            # We filter by expires_at > CURRENT_TIMESTAMP()
            query = f"""
            SELECT cached_result, expires_at 
            FROM QUERY_CACHE 
            WHERE cache_key = '{cache_key}' 
              AND expires_at > CURRENT_TIMESTAMP()
            """
            results = self.session.sql(query).collect()
            
            if results:
                # Increment hit count asynchronously (fire and forget ideally, but here synchronous)
                # We use a simple UPDATE
                try:
                    self.session.sql(f"UPDATE QUERY_CACHE SET hit_count = hit_count + 1 WHERE cache_key = '{cache_key}'").collect()
                except Exception as e:
                    logger.warning(f"Failed to update hit_count for {cache_key}: {e}")
                
                # Parse JSON result
                # Snowflake returns VARIANT as string JSON in python connector sometimes, 
                # or native dict if using snowpark dataframe properly. 
                # .collect() returns Row objects.
                # 'CACHED_RESULT' column.
                result_json = results[0]['CACHED_RESULT']
                if isinstance(result_json, str):
                    return json.loads(result_json)
                return result_json
                
            return None
        except Exception as e:
            logger.error(f"Cache GET failed: {e}")
            return None

    def set(self, cache_key: str, cache_type: str, params: Dict, result: Dict, ttl_minutes: int):
        """
        Store result with expiry using MERGE (upsert).
        """
        if not self.session:
            return False

        try:
            # CRITICAL: Properly escape for SQL and ensure no newlines break PARSE_JSON
            # 1. Serialize to JSON with ensure_ascii to handle unicode
            # 2. Replace newlines with escaped versions
            # 3. Escape single quotes for SQL string
            params_json = json.dumps(params, ensure_ascii=True, separators=(',', ':'))
            result_json = json.dumps(result, ensure_ascii=True, separators=(',', ':'))
            
            # Replace actual newlines with escaped newlines (for multi-line strings in values)
            params_str = params_json.replace('\n', '\\n').replace('\r', '\\r').replace("'", "''")
            result_str = result_json.replace('\n', '\\n').replace('\r', '\\r').replace("'", "''")
            
            # Safe MERGE query
            query = f"""
            MERGE INTO QUERY_CACHE AS target
            USING (SELECT '{cache_key}' AS cache_key) AS source
            ON target.cache_key = source.cache_key
            WHEN MATCHED THEN UPDATE SET 
                cache_type = '{cache_type}',
                query_params = PARSE_JSON('{params_str}'),
                cached_result = PARSE_JSON('{result_str}'),
                expires_at = DATEADD(minute, {ttl_minutes}, CURRENT_TIMESTAMP()),
                hit_count = 0 
            WHEN NOT MATCHED THEN INSERT 
                (cache_key, cache_type, query_params, cached_result, expires_at)
            VALUES 
                ('{cache_key}', '{cache_type}', PARSE_JSON('{params_str}'), 
                 PARSE_JSON('{result_str}'), DATEADD(minute, {ttl_minutes}, CURRENT_TIMESTAMP()))
            """
            self.session.sql(query).collect()
            return True
        except Exception as e:
            logger.error(f"Cache SET failed: {e}")
            return False

# Global instance
snowflake_cache_service = SnowflakeCacheService()
