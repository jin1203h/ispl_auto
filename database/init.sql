-- PostgreSQL 데이터베이스 초기화 스크립트
-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id             SERIAL PRIMARY KEY,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    role                VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'USER')),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 약관 테이블
CREATE TABLE IF NOT EXISTS policies (
    policy_id           SERIAL PRIMARY KEY,
    company             VARCHAR(100),
    category            VARCHAR(100),
    product_type        VARCHAR(100),
    product_name        VARCHAR(255) NOT NULL,
    sale_start_dt       VARCHAR(8),
    sale_end_dt         VARCHAR(8),
    sale_stat           VARCHAR(10),
    summary             TEXT,
    original_path       VARCHAR(500),
    md_path             VARCHAR(500),
    pdf_path            VARCHAR(500),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    security_level      VARCHAR(20)
);

-- text-embedding-3 임베딩 테이블 (3072차원)
CREATE TABLE IF NOT EXISTS embeddings_text_embedding_3 (
    id                  SERIAL PRIMARY KEY,
    policy_id           INTEGER NOT NULL REFERENCES policies(policy_id),
    chunk_text          TEXT NOT NULL,
    embedding           VECTOR(3072) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    chunk_index         INTEGER NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Qwen 임베딩 테이블 (4096차원)
CREATE TABLE IF NOT EXISTS embeddings_qwen (
    id                  SERIAL PRIMARY KEY,
    policy_id           INTEGER NOT NULL REFERENCES policies(policy_id),
    chunk_text          TEXT NOT NULL,
    embedding           VECTOR(4096) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    chunk_index         INTEGER NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 다국어 E5 임베딩 테이블 (1024차원)
CREATE TABLE IF NOT EXISTS embeddings_multilingual_e5 (
    id                  SERIAL PRIMARY KEY,
    policy_id           INTEGER NOT NULL REFERENCES policies(policy_id),
    chunk_text          TEXT NOT NULL,
    embedding           VECTOR(1024) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    chunk_index         INTEGER NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Snowflake Arctic 임베딩 테이블 (1024차원)
CREATE TABLE IF NOT EXISTS embeddings_snowflake_arctic (
    id                  SERIAL PRIMARY KEY,
    policy_id           INTEGER NOT NULL REFERENCES policies(policy_id),
    chunk_text          TEXT NOT NULL,
    embedding           VECTOR(1024) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    chunk_index         INTEGER NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 워크플로우 실행 로그 테이블
CREATE TABLE IF NOT EXISTS workflow_logs (
    log_id              SERIAL PRIMARY KEY,
    workflow_id         VARCHAR(100) NOT NULL,
    step_name           VARCHAR(100) NOT NULL,
    status              VARCHAR(20) NOT NULL,
    input_data          JSONB,
    output_data         JSONB,
    error_message       TEXT,
    execution_time      INTEGER, -- milliseconds
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 벡터 검색을 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_embeddings_text_embedding_3_vector 
ON embeddings_text_embedding_3 USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_embeddings_qwen_vector 
ON embeddings_qwen USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_embeddings_multilingual_e5_vector 
ON embeddings_multilingual_e5 USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_embeddings_snowflake_arctic_vector 
ON embeddings_snowflake_arctic USING ivfflat (embedding vector_cosine_ops);

-- 기본 관리자 계정 생성 (비밀번호: admin123)
INSERT INTO users (email, password_hash, role) 
VALUES ('admin@ispl.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/9.8.8.8', 'ADMIN')
ON CONFLICT (email) DO NOTHING;
