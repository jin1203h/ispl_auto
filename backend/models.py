from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, TypeDecorator
from sqlalchemy.sql import func
from database import Base

# VECTOR 타입을 직접 정의 (pgvector 호환)
class VECTOR(TypeDecorator):
    impl = Text
    cache_ok = True
    
    def __init__(self, dimension=None, **kwargs):
        self.dimension = dimension
        super().__init__(**kwargs)
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(Text())
        else:
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, list):
                return f"[{','.join(map(str, value))}]"
            return str(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            # 벡터 문자열을 파싱하여 리스트로 변환
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                return [float(x.strip()) for x in value[1:-1].split(',')]
        return value

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Policy(Base):
    __tablename__ = "policies"
    
    policy_id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100))
    category = Column(String(100))
    product_type = Column(String(100))
    product_name = Column(String(255), nullable=False)
    sale_start_dt = Column(String(8))
    sale_end_dt = Column(String(8))
    sale_stat = Column(String(10))
    summary = Column(Text)
    original_path = Column(String(500))
    md_path = Column(String(500))
    pdf_path = Column(String(500))
    file_path = Column(String(500))  # 원본 파일 경로
    created_at = Column(TIMESTAMP, server_default=func.now())
    security_level = Column(String(20))

class EmbeddingTextEmbedding3(Base):
    __tablename__ = "embeddings_text_embedding_3"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(VECTOR(3072), nullable=False)
    model = Column(String(100), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class EmbeddingQwen(Base):
    __tablename__ = "embeddings_qwen"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(VECTOR(4096), nullable=False)
    model = Column(String(100), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class EmbeddingMultilingualE5(Base):
    __tablename__ = "embeddings_multilingual_e5"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(VECTOR(1024), nullable=False)
    model = Column(String(100), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class EmbeddingSnowflakeArctic(Base):
    __tablename__ = "embeddings_snowflake_arctic"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(VECTOR(1024), nullable=False)
    model = Column(String(100), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class WorkflowLog(Base):
    __tablename__ = "workflow_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), nullable=False)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
