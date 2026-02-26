-- YCCE-AI Knowledge Table Setup
-- Run this in your Supabase SQL Editor to initialize the vector database.

-- 1. Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the knowledge table
CREATE TABLE IF NOT EXISTS ycce_knowledge (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding   VECTOR(768),           -- Gemini embedding dimension
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_ycce_knowledge_url
    ON ycce_knowledge (url);

CREATE INDEX IF NOT EXISTS idx_ycce_knowledge_hash
    ON ycce_knowledge (content_hash);

-- 4. Vector similarity search index (IVFFlat for speed)
CREATE INDEX IF NOT EXISTS idx_ycce_knowledge_embedding
    ON ycce_knowledge
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 5. Similarity search function (for chatbot queries)
CREATE OR REPLACE FUNCTION match_knowledge(
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id          BIGINT,
    url         TEXT,
    content     TEXT,
    metadata    JSONB,
    similarity  FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        yk.id,
        yk.url,
        yk.content,
        yk.metadata,
        1 - (yk.embedding <=> query_embedding) AS similarity
    FROM ycce_knowledge yk
    WHERE 1 - (yk.embedding <=> query_embedding) > match_threshold
    ORDER BY yk.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 6. Row Level Security (recommended)
ALTER TABLE ycce_knowledge ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (used by the pipeline)
CREATE POLICY "Service role full access"
    ON ycce_knowledge
    FOR ALL
    USING (true)
    WITH CHECK (true);
