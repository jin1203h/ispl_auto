from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from services.workflow_service import WorkflowService
from services.embedding_service import EmbeddingService
from services.search_service import SearchService
from sqlalchemy.orm import Session

class PolicyWorkflowState:
    """정책 처리 워크플로우 상태"""
    def __init__(self):
        self.workflow_id: str = ""
        self.file_path: str = ""
        self.company: str = ""
        self.category: str = ""
        self.product_type: str = ""
        self.product_name: str = ""
        self.security_level: str = "public"
        self.extracted_text: str = ""
        self.markdown_content: str = ""
        self.summary: str = ""
        self.chunks: List[str] = []
        self.embeddings: List[List[float]] = []
        self.policy_id: int = None
        self.status: str = "pending"
        self.error_message: str = ""
        self.db_session: Session = None

class PolicyWorkflow:
    """정책 처리 워크플로우"""
    
    def __init__(self):
        self.workflow_service = WorkflowService()
        self.embedding_service = EmbeddingService()
        self.search_service = SearchService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(PolicyWorkflowState)
        
        # 노드 추가
        workflow.add_node("file_upload", self._file_upload_node)
        workflow.add_node("text_extraction", self._text_extraction_node)
        workflow.add_node("markdown_conversion", self._markdown_conversion_node)
        workflow.add_node("summary_generation", self._summary_generation_node)
        workflow.add_node("text_chunking", self._text_chunking_node)
        workflow.add_node("embedding_creation", self._embedding_creation_node)
        workflow.add_node("database_storage", self._database_storage_node)
        workflow.add_node("error_handling", self._error_handling_node)
        
        # 엣지 추가
        workflow.set_entry_point("file_upload")
        workflow.add_edge("file_upload", "text_extraction")
        workflow.add_edge("text_extraction", "markdown_conversion")
        workflow.add_edge("markdown_conversion", "summary_generation")
        workflow.add_edge("summary_generation", "text_chunking")
        workflow.add_edge("text_chunking", "embedding_creation")
        workflow.add_edge("embedding_creation", "database_storage")
        workflow.add_edge("database_storage", END)
        
        # 에러 처리
        workflow.add_edge("file_upload", "error_handling")
        workflow.add_edge("text_extraction", "error_handling")
        workflow.add_edge("markdown_conversion", "error_handling")
        workflow.add_edge("summary_generation", "error_handling")
        workflow.add_edge("text_chunking", "error_handling")
        workflow.add_edge("embedding_creation", "error_handling")
        workflow.add_edge("database_storage", "error_handling")
        workflow.add_edge("error_handling", END)
        
        return workflow.compile()

    async def _file_upload_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """파일 업로드 노드"""
        try:
            # 파일 업로드 로직
            self.workflow_service.log_step(
                state.workflow_id, 
                "file_upload", 
                "in_progress",
                {"file_path": state.file_path}
            )
            
            # 실제 파일 처리 로직은 여기에 구현
            # 예: 파일 검증, 저장 등
            
            state.status = "completed"
            self.workflow_service.log_step(
                state.workflow_id, 
                "file_upload", 
                "completed",
                {"file_path": state.file_path}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _text_extraction_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """텍스트 추출 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "text_extraction", 
                "in_progress"
            )
            
            # PDF 텍스트 추출 로직
            import PyPDF2
            with open(state.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            state.extracted_text = text
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "text_extraction", 
                "completed",
                {"text_length": len(text)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _markdown_conversion_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """Markdown 변환 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "markdown_conversion", 
                "in_progress"
            )
            
            # Markdown 변환 로직
            lines = state.extracted_text.split('\n')
            markdown_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    markdown_lines.append("")
                    continue
                    
                if len(line) < 100 and any(keyword in line for keyword in ['제', '장', '조', '항', '목']):
                    markdown_lines.append(f"## {line}")
                else:
                    markdown_lines.append(line)
            
            state.markdown_content = '\n'.join(markdown_lines)
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "markdown_conversion", 
                "completed",
                {"markdown_length": len(state.markdown_content)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _summary_generation_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """요약 생성 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "summary_generation", 
                "in_progress"
            )
            
            # 간단한 요약 생성 (실제로는 LLM 사용)
            sentences = state.markdown_content.split('.')
            summary_sentences = sentences[:3]
            state.summary = '. '.join(summary_sentences) + '.'
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "summary_generation", 
                "completed",
                {"summary_length": len(state.summary)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _text_chunking_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """텍스트 청킹 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "text_chunking", 
                "in_progress"
            )
            
            # 텍스트 청킹 로직
            words = state.markdown_content.split()
            chunks = []
            chunk_size = 200
            overlap = 20
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk = ' '.join(words[i:i + chunk_size])
                if chunk.strip():
                    chunks.append(chunk.strip())
            
            state.chunks = chunks
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "text_chunking", 
                "completed",
                {"chunk_count": len(chunks)}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _embedding_creation_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """임베딩 생성 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "embedding_creation", 
                "in_progress"
            )
            
            # 임베딩 생성 로직
            await self.embedding_service.create_embeddings(
                state.policy_id,
                state.markdown_content,
                state.security_level,
                state.db_session,
                state.workflow_id
            )
            
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "embedding_creation", 
                "completed",
                {"policy_id": state.policy_id}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _database_storage_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """데이터베이스 저장 노드"""
        try:
            self.workflow_service.log_step(
                state.workflow_id, 
                "database_storage", 
                "in_progress"
            )
            
            # 데이터베이스 저장 로직은 이미 PolicyService에서 처리됨
            state.status = "completed"
            
            self.workflow_service.log_step(
                state.workflow_id, 
                "database_storage", 
                "completed",
                {"policy_id": state.policy_id}
            )
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            self.workflow_service.log_error(state.workflow_id, str(e))
        
        return state

    async def _error_handling_node(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """에러 처리 노드"""
        self.workflow_service.log_error(state.workflow_id, state.error_message)
        state.status = "error"
        return state

    async def execute_workflow(self, state: PolicyWorkflowState) -> PolicyWorkflowState:
        """워크플로우 실행"""
        return await self.graph.ainvoke(state)
