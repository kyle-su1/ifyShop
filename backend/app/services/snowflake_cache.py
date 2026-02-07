from app.core.snowflake import get_snowflake_session
import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SnowflakeCacheService:
    @property
    def session(self):
        return get_snowflake_session()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Check cache, return if valid (not expired).
        """
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
        try:
            # Escape single quotes for SQL
            params_str = json.dumps(params).replace("'", "''")
            result_str = json.dumps(result).replace("'", "''")
            
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
