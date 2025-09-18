from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from services.workflow_service import WorkflowService
from services.search_service import SearchService
from schemas import SearchResult
from sqlalchemy.orm import Session

class SearchWorkflowState:
    """검색 워크플로우 상태"""
    def __init__(self):
        self.workflow_id: str = ""
        self.query: str = ""
        self.policy_ids: List[int] = None
        self.limit: int = 10
        self.security_level: str = "public"
        self.query_embedding: List[float] = []
        self.search_results: List[SearchResult] = []
        self.answer: str = ""
        self.status: str = "pending"
        self.error_message: str = ""
        self.db_session: Session = None

class SearchWorkflow:
    """검색 워크플로우"""
    
    def __init__(self):
        self.workflow_service = WorkflowService()
        self.search_service = SearchService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(SearchWorkflowState)
        
        # 노드 추가
        workflow.add_node("query_processing", self._query_processing_node)
        workflow.add_node("embedding_generation", self._embedding_generation_node)
        workflow.add_node("vector_search", self._vector_search_node)
        workflow.add_node("result_ranking", self._result_ranking_node)
        workflow.add_node("answer_generation", self._answer_generation_node)
        workflow.add_node("error_handling", self._error_handling_node)
        
        # 엣지 추가
        workflow.set_entry_point("query_processing")
        workflow.add_edge("query_processing", "embedding_generation")
        workflow.add_edge("embedding_generation", "vector_search")
        workflow.add_edge("vector_search", "result_ranking")
        workflow.add_edge("result_ranking", "answer_generation")
        workflow.add_edge("answer_generation", END)
        
        # 에러 처리
        workflow.add_edge("query_processing", "error_handling")
        workflow.add_edge("embedding_generation", "error_handling")
        workflow.add_edge("vector_search", "error_handling")
        workflow.add_edge("result_ranking", "error_handling")
        workflow.add_edge("answer_generation", "error_handling")
        workflow.add_edge("error_handling", END)
        
        return workflow.compile()

    async def _query_processing_node(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """쿼리 처리 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "query_processing", 
                "in_progress",
                {"query": state.query}
            )
            
            # 쿼리 전처리 로직
            state.query = state.query.strip()
            if not state.query:
                raise ValueError("Empty query")
            
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "query_processing", 
                "completed",
                {"query_length": len(state.query)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _embedding_generation_node(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """임베딩 생성 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "embedding_generation", 
                "in_progress"
            )
            
            # 쿼리 임베딩 생성
            state.query_embedding = await self.search_service._create_query_embedding(
                state.query, 
                state.security_level
            )
            
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "embedding_generation", 
                "completed",
                {"embedding_dimension": len(state.query_embedding)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _vector_search_node(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """벡터 검색 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "vector_search", 
                "in_progress"
            )
            
            # 벡터 검색 수행
            search_results = await self.search_service._vector_search(
                state.query_embedding,
                state.policy_ids,
                state.limit,
                state.security_level,
                state.db_session
            )
            
            # SearchResult 객체로 변환
            from models import Policy
            formatted_results = []
            for result in search_results:
                policy = state.db_session.query(Policy).filter(Policy.policy_id == result['policy_id']).first()
                if policy:
                    search_result = SearchResult(
                        policy_id=result['policy_id'],
                        policy_name=policy.product_name,
                        company=policy.company or "Unknown",
                        chunk_text=result['chunk_text'],
                        similarity_score=float(result['similarity_score']),
                        chunk_index=result['chunk_index']
                    )
                    formatted_results.append(search_result)
            
            state.search_results = formatted_results
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "vector_search", 
                "completed",
                {"result_count": len(formatted_results)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _result_ranking_node(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """결과 랭킹 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "result_ranking", 
                "in_progress"
            )
            
            # 유사도 점수 기준으로 정렬
            state.search_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "result_ranking", 
                "completed",
                {"top_score": state.search_results[0].similarity_score if state.search_results else 0}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _answer_generation_node(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """답변 생성 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "answer_generation", 
                "in_progress"
            )
            
            # 답변 생성
            state.answer = await self.search_service.generate_answer(
                state.query,
                state.search_results,
                state.security_level
            )
            
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "answer_generation", 
                "completed",
                {"answer_length": len(state.answer)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _error_handling_node(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """에러 처리 노드"""
        self.workflow_service.log_error(state.workflow_id, state.error_message)
        state.status = "error"
        return state

    async def execute_workflow(self, state: SearchWorkflowState) -> SearchWorkflowState:
        """워크플로우 실행"""
        return await self.graph.ainvoke(state)
