-- Snowflake Migration for CxC App (Vector Search)

-- 1. Create Products Table with Vector support
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    price FLOAT,
    image_url TEXT,
    source_url TEXT,
    -- Vector embedding (3072 dimensions for gemini-embedding-001)
    embedding VECTOR(FLOAT, 3072), 
    metadata VARIANT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 4. Create Cache Table
CREATE TABLE IF NOT EXISTS QUERY_CACHE (
    cache_key VARCHAR(64) PRIMARY KEY,
    cache_type VARCHAR(50),
    query_params VARIANT,
    cached_result VARIANT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    expires_at TIMESTAMP_NTZ,
    hit_count INT DEFAULT 0
);

-- 2. Create Reviews Table (optional, for historical data)
CREATE TABLE IF NOT EXISTS reviews (
    id VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(255),
    text TEXT,
    rating FLOAT,
    source VARCHAR(50),
    sentiment_score FLOAT, -- Storing pre-calculated sentiment from Gemini
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 3. Create Search Function (using Snowflake Cortex Vector Similarity)
-- Note: VECTOR_COSINE_SIMILARITY is a built-in function, so no user-defined function needed.
-- Usage: SELECT name, VECTOR_COSINE_SIMILARITY(embedding, :query_vector) as score FROM products ORDER BY score DESC LIMIT 5;
