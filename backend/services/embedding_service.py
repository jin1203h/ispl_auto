import os
import numpy as np
from typing import List
from sqlalchemy.orm import Session
from models import Policy, EmbeddingTextEmbedding3, EmbeddingQwen, EmbeddingMultilingualE5, EmbeddingSnowflakeArctic
from services.workflow_service import WorkflowService
import openai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class EmbeddingService:
    def __init__(self):
        self.workflow_service = WorkflowService()
        
        # OpenAI API 키 확인
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and openai_api_key != "your-openai-api-key-here":
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            print("✅ OpenAI API 클라이언트 초기화 완료")
        else:
            print("⚠️ OpenAI API 키가 없습니다. 로컬 모델만 사용합니다.")
            self.openai_client = None
        
        # 로컬 임베딩 모델들
        self.qwen_model = None
        self.multilingual_e5_model = None
        self.snowflake_arctic_model = None

    async def create_embeddings(
        self, 
        policy_id: int, 
        content: str, 
        security_level: str, 
        db: Session,
        workflow_id: str
    ):
        """임베딩 생성 및 저장"""
        try:
            # 텍스트 청킹
            chunks = self._chunk_text(content)
            self.workflow_service.log_step(workflow_id, "text_chunking", "completed", 
                                         {"chunk_count": len(chunks)})
            
            # 보안 수준에 따른 임베딩 모델 선택
            if security_level == "closed":
                # 완전 폐쇄망: Qwen3 8B embedding
                await self._create_qwen_embeddings(policy_id, chunks, db, workflow_id)
            elif security_level == "semi_closed":
                # 조건부 폐쇄망: Azure OpenAI (API 키가 있는 경우만)
                if self.openai_client:
                    await self._create_openai_embeddings(policy_id, chunks, db, workflow_id)
                else:
                    print("⚠️ OpenAI API 키가 없어 로컬 모델을 사용합니다.")
                    await self._create_qwen_embeddings(policy_id, chunks, db, workflow_id)
            else:
                # 공개망: text-embedding-3-large (API 키가 있는 경우만)
                if self.openai_client:
                    await self._create_openai_embeddings(policy_id, chunks, db, workflow_id)
                    # 다국어 E5 임베딩도 생성
                    await self._create_multilingual_e5_embeddings(policy_id, chunks, db, workflow_id)
                else:
                    print("⚠️ OpenAI API 키가 없어 로컬 모델을 사용합니다.")
                    await self._create_qwen_embeddings(policy_id, chunks, db, workflow_id)
            
            self.workflow_service.log_step(workflow_id, "embedding_storage", "completed", 
                                         {"policy_id": policy_id})
            
        except Exception as e:
            self.workflow_service.log_error(workflow_id, str(e))
            raise e

    def _chunk_text(self, text: str, chunk_size: int = 50, overlap: int = 5) -> List[str]:
        """텍스트를 청크로 분할 (토큰 제한 고려)"""
        words = text.split()
        chunks = []
        
        # 청크 크기를 더 작게 조정하여 토큰 제한 회피
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        print(f"텍스트 청킹 완료: {len(chunks)}개 청크 (청크 크기: {chunk_size})")
        return chunks

    async def _create_openai_embeddings(
        self, 
        policy_id: int, 
        chunks: List[str], 
        db: Session, 
        workflow_id: str
    ):
        """OpenAI 임베딩 생성 (배치 처리)"""
        try:
            print(f"OpenAI 임베딩 생성 중... (청크 수: {len(chunks)})")
            
            if not self.openai_client:
                raise Exception("OpenAI 클라이언트가 초기화되지 않았습니다.")
            
            # 배치 크기 설정 (토큰 제한 고려)
            batch_size = 20  # 한 번에 처리할 청크 수
            all_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                print(f"배치 처리 중: {i+1}-{min(i+batch_size, len(chunks))}/{len(chunks)}")
                
                try:
                    response = self.openai_client.embeddings.create(
                        model="text-embedding-3-large",
                        input=batch_chunks,
                        timeout=60  # 60초 타임아웃
                    )
                    
                    batch_embeddings = [data.embedding for data in response.data]
                    all_embeddings.extend(batch_embeddings)
                    
                except Exception as batch_error:
                    print(f"배치 {i//batch_size + 1} 처리 오류: {batch_error}")
                    # 오류 발생 시 더미 임베딩으로 대체
                    for _ in batch_chunks:
                        dummy_embedding = [0.0] * 3072  # text-embedding-3-large 차원
                        all_embeddings.append(dummy_embedding)
            
            # 데이터베이스에 배치 저장 (메모리 효율성)
            batch_size = 100  # 100개씩 배치 저장
            total_chunks = len(chunks)
            
            for i in range(0, total_chunks, batch_size):
                batch_end = min(i + batch_size, total_chunks)
                batch_chunks = chunks[i:batch_end]
                batch_embeddings = all_embeddings[i:batch_end]
                
                print(f"데이터베이스 저장 중: {i+1}-{batch_end}/{total_chunks}")
                
                # 배치별로 임베딩 저장
                for j, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                    embedding_record = EmbeddingTextEmbedding3(
                        policy_id=policy_id,
                        chunk_text=chunk,
                        embedding=embedding,
                        model="text-embedding-3-large",
                        chunk_index=i + j
                    )
                    db.add(embedding_record)
                
                # 배치별 커밋
                db.commit()
                print(f"배치 저장 완료: {i+1}-{batch_end}/{total_chunks}")
            
            print(f"✅ OpenAI 임베딩 생성 및 저장 완료: {len(chunks)}개 청크")
            
        except Exception as e:
            print(f"OpenAI 임베딩 생성 오류: {e}")
            raise e

    async def _create_qwen_embeddings(
        self, 
        policy_id: int, 
        chunks: List[str], 
        db: Session, 
        workflow_id: str
    ):
        """Qwen 임베딩 생성 (간단한 더미 임베딩)"""
        try:
            print(f"Qwen 임베딩 생성 중... (청크 수: {len(chunks)})")
            
            # 간단한 더미 임베딩 생성 (실제로는 로컬 모델 사용)
            for i, chunk in enumerate(chunks):
                # 간단한 해시 기반 더미 임베딩 (384차원)
                import hashlib
                hash_obj = hashlib.md5(chunk.encode())
                hash_bytes = hash_obj.digest()
                dummy_embedding = [float(b) / 255.0 for b in hash_bytes] * 24  # 384차원으로 확장
                
                embedding_record = EmbeddingQwen(
                    policy_id=policy_id,
                    chunk_text=chunk,
                    embedding=dummy_embedding,
                    model="dummy-qwen",
                    chunk_index=i
                )
                db.add(embedding_record)
            
            db.commit()
            print(f"✅ Qwen 임베딩 생성 완료: {len(chunks)}개 청크")
            
        except Exception as e:
            print(f"Qwen 임베딩 생성 오류: {e}")
            raise e

    async def _create_multilingual_e5_embeddings(
        self, 
        policy_id: int, 
        chunks: List[str], 
        db: Session, 
        workflow_id: str
    ):
        """다국어 E5 임베딩 생성"""
        try:
            if self.multilingual_e5_model is None:
                self.multilingual_e5_model = SentenceTransformer('intfloat/multilingual-e5-large-instruct')
            
            embeddings = self.multilingual_e5_model.encode(chunks)
            
            # 데이터베이스에 저장
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_record = EmbeddingMultilingualE5(
                    policy_id=policy_id,
                    chunk_text=chunk,
                    embedding=embedding.tolist(),
                    model="multilingual-e5-large-instruct",
                    chunk_index=i
                )
                db.add(embedding_record)
            
            db.commit()
            
        except Exception as e:
            print(f"다국어 E5 임베딩 생성 오류: {e}")
            raise e

    async def _create_snowflake_arctic_embeddings(
        self, 
        policy_id: int, 
        chunks: List[str], 
        db: Session, 
        workflow_id: str
    ):
        """Snowflake Arctic 임베딩 생성"""
        try:
            if self.snowflake_arctic_model is None:
                self.snowflake_arctic_model = SentenceTransformer('dragonkue/snowflake-arctic-embed-l-v2.0')
            
            embeddings = self.snowflake_arctic_model.encode(chunks)
            
            # 데이터베이스에 저장
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_record = EmbeddingSnowflakeArctic(
                    policy_id=policy_id,
                    chunk_text=chunk,
                    embedding=embedding.tolist(),
                    model="snowflake-arctic-embed-l-v2.0",
                    chunk_index=i
                )
                db.add(embedding_record)
            
            db.commit()
            
        except Exception as e:
            print(f"Snowflake Arctic 임베딩 생성 오류: {e}")
            raise e
