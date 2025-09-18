import os
import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Policy, EmbeddingTextEmbedding3, EmbeddingQwen, EmbeddingMultilingualE5, EmbeddingSnowflakeArctic
from services.workflow_service import WorkflowService
from schemas import SearchResult
import openai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class SearchService:
    def __init__(self):
        self.workflow_service = WorkflowService()
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 로컬 임베딩 모델들
        self.qwen_model = None
        self.multilingual_e5_model = None
        self.snowflake_arctic_model = None

    async def search_policies(
        self,
        query: str,
        policy_ids: Optional[List[int]] = None,
        limit: int = 10,
        security_level: str = "public",
        db: Session = None,
        workflow_id: str = None
    ) -> List[SearchResult]:
        """약관 검색 (간단한 텍스트 검색)"""
        try:
            # 간단한 텍스트 검색으로 대체
            policies = db.query(Policy).all()
            
            # 검색 결과 생성
            formatted_results = []
            for policy in policies[:limit]:
                # 간단한 텍스트 매칭
                if query.lower() in (policy.product_name or "").lower() or \
                   query.lower() in (policy.summary or "").lower():
                    search_result = SearchResult(
                        policy_id=policy.policy_id,
                        policy_name=policy.product_name or "Unknown",
                        company=policy.company or "Unknown",
                        chunk_text=policy.summary or "No summary available",
                        similarity_score=0.8,  # 임시 점수
                        chunk_index=0
                    )
                    formatted_results.append(search_result)
            
            # 결과가 없으면 샘플 데이터 반환
            if not formatted_results:
                sample_result = SearchResult(
                    policy_id=1,
                    policy_name="샘플 보험약관",
                    company="샘플 보험사",
                    chunk_text=f"'{query}'에 대한 검색 결과가 없습니다. 아직 약관이 업로드되지 않았습니다.",
                    similarity_score=0.0,
                    chunk_index=0
                )
                formatted_results.append(sample_result)
            
            # 워크플로우 로깅 (올바른 형식으로)
            if workflow_id:
                self.workflow_service.log_step(workflow_id, "text_search", "completed", 
                                             {"query": query, "result_count": len(formatted_results)})
            
            return formatted_results
            
        except Exception as e:
            print(f"검색 오류: {e}")
            # 오류 시 샘플 데이터 반환
            sample_result = SearchResult(
                policy_id=1,
                policy_name="검색 오류",
                company="시스템",
                chunk_text=f"검색 중 오류가 발생했습니다: {str(e)}",
                similarity_score=0.0,
                chunk_index=0
            )
            return [sample_result]

    async def _create_query_embedding(self, query: str, security_level: str) -> List[float]:
        """쿼리 임베딩 생성"""
        if security_level == "closed":
            # Qwen 모델 사용
            if self.qwen_model is None:
                self.qwen_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            embedding = self.qwen_model.encode([query])[0]
            return embedding.tolist()
        else:
            # OpenAI 모델 사용
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=[query]
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI 임베딩 생성 오류: {e}")
                # 폴백으로 로컬 모델 사용
                if self.multilingual_e5_model is None:
                    self.multilingual_e5_model = SentenceTransformer('intfloat/multilingual-e5-large-instruct')
                embedding = self.multilingual_e5_model.encode([query])[0]
                return embedding.tolist()

    async def _vector_search(
        self,
        query_embedding: List[float],
        policy_ids: Optional[List[int]] = None,
        limit: int = 10,
        security_level: str = "public",
        db: Session = None
    ) -> List[dict]:
        """벡터 검색 수행"""
        embedding_dim = len(query_embedding)
        
        # 보안 수준에 따른 테이블 선택
        if security_level == "closed":
            table_name = "embeddings_qwen"
            embedding_column = "embedding"
        elif security_level == "semi_closed":
            table_name = "embeddings_text_embedding_3"
            embedding_column = "embedding"
        else:
            # 공개망에서는 text-embedding-3-large 사용
            table_name = "embeddings_text_embedding_3"
            embedding_column = "embedding"
        
        # 정책 ID 필터 조건
        policy_filter = ""
        if policy_ids:
            policy_ids_str = ','.join(map(str, policy_ids))
            policy_filter = f"AND policy_id IN ({policy_ids_str})"
        
        # 벡터 유사도 검색 쿼리
        query_sql = f"""
        SELECT 
            policy_id,
            chunk_text,
            chunk_index,
            1 - ({embedding_column} <=> %s) as similarity_score
        FROM {table_name}
        WHERE {embedding_column} IS NOT NULL {policy_filter}
        ORDER BY {embedding_column} <=> %s
        LIMIT %s
        """
        
        # 쿼리 실행
        result = db.execute(
            text(query_sql),
            [query_embedding, query_embedding, limit]
        )
        
        return [dict(row) for row in result]

    async def generate_answer(
        self,
        query: str,
        search_results: List[SearchResult],
        security_level: str = "public"
    ) -> str:
        """검색 결과를 바탕으로 답변 생성"""
        try:
            # 검색 결과를 컨텍스트로 구성
            context = "\n\n".join([
                f"약관: {result.policy_name} (보험사: {result.company})\n내용: {result.chunk_text}"
                for result in search_results[:5]  # 상위 5개 결과만 사용
            ])
            
            # LLM을 사용한 답변 생성
            if security_level == "closed":
                # 폐쇄망에서는 로컬 모델 사용 (여기서는 간단한 템플릿 응답)
                return self._generate_template_answer(query, search_results)
            else:
                # OpenAI API 사용
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "당신은 보험약관 전문가입니다. 주어진 약관 내용을 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요."
                            },
                            {
                                "role": "user",
                                "content": f"질문: {query}\n\n관련 약관 내용:\n{context}"
                            }
                        ],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    print(f"OpenAI 답변 생성 오류: {e}")
                    return self._generate_template_answer(query, search_results)
                    
        except Exception as e:
            print(f"답변 생성 오류: {e}")
            return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다."

    def _generate_template_answer(self, query: str, search_results: List[SearchResult]) -> str:
        """템플릿 기반 답변 생성"""
        if not search_results:
            return "관련된 약관을 찾을 수 없습니다."
        
        answer = f"질문: {query}\n\n"
        answer += "관련 약관 정보:\n\n"
        
        for i, result in enumerate(search_results[:3], 1):
            answer += f"{i}. {result.policy_name} ({result.company})\n"
            answer += f"   유사도: {result.similarity_score:.3f}\n"
            answer += f"   내용: {result.chunk_text[:200]}...\n\n"
        
        return answer
