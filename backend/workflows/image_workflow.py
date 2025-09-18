"""
LangGraph를 활용한 이미지 조회 워크플로우
"""
import os
import base64
from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from PIL import Image
import cv2
import numpy as np
from io import BytesIO
import json

from typing import TypedDict

class ImageWorkflowState(TypedDict):
    """이미지 워크플로우 상태"""
    query: str
    image_path: str
    image_data: Optional[bytes]
    extracted_text: str
    image_description: str
    search_results: List[Dict]
    final_response: str
    error_message: str
    workflow_id: str

class ImageWorkflow:
    """LangGraph 기반 이미지 조회 워크플로우"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=1000
        )
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        
    def initialize_workflow(self, query: str, image_path: str, workflow_id: str) -> ImageWorkflowState:
        """워크플로우 초기화"""
        return {
            "query": query,
            "image_path": image_path,
            "image_data": None,
            "extracted_text": "",
            "image_description": "",
            "search_results": [],
            "final_response": "",
            "error_message": "",
            "workflow_id": workflow_id
        }
    
    def load_image(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """이미지 로드"""
        try:
            if os.path.exists(state["image_path"]):
                with open(state["image_path"], 'rb') as f:
                    state["image_data"] = f.read()
                print(f"[{state['workflow_id']}] 이미지 로드 완료: {state['image_path']}")
            else:
                state["error_message"] = f"이미지 파일을 찾을 수 없습니다: {state['image_path']}"
        except Exception as e:
            state["error_message"] = f"이미지 로드 오류: {str(e)}"
        
        return state
    
    def extract_text_from_image(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """이미지에서 텍스트 추출 (OCR)"""
        try:
            if not state["image_data"]:
                state["error_message"] = "이미지 데이터가 없습니다"
                return state
            
            # OpenCV를 사용한 이미지 전처리
            image = Image.open(BytesIO(state["image_data"]))
            image_array = np.array(image)
            
            # 그레이스케일 변환
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # 노이즈 제거 및 이진화
            denoised = cv2.medianBlur(gray, 5)
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR 수행 (Tesseract)
            import pytesseract
            extracted_text = pytesseract.image_to_string(binary, lang='kor+eng')
            state["extracted_text"] = extracted_text.strip()
            
            print(f"[{state['workflow_id']}] OCR 텍스트 추출 완료: {len(state['extracted_text'])} 문자")
            
        except Exception as e:
            state["error_message"] = f"OCR 텍스트 추출 오류: {str(e)}"
            print(f"[{state['workflow_id']}] OCR 오류: {str(e)}")
        
        return state
    
    def describe_image(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """이미지 내용 설명 생성"""
        try:
            if not state["image_data"]:
                state["error_message"] = "이미지 데이터가 없습니다"
                return state
            
            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(state["image_data"]).decode('utf-8')
            
            # GPT-4 Vision을 사용한 이미지 설명
            messages = [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"다음 이미지를 자세히 분석하고 설명해주세요. 특히 텍스트, 도표, 그래프, 표 등이 있다면 그 내용을 포함해서 설명해주세요.\n\n사용자 쿼리: {state['query']}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                )
            ]
            
            response = self.llm.invoke(messages)
            state["image_description"] = response.content
            
            print(f"[{state['workflow_id']}] 이미지 설명 생성 완료")
            
        except Exception as e:
            state["error_message"] = f"이미지 설명 생성 오류: {str(e)}"
            print(f"[{state['workflow_id']}] 이미지 설명 오류: {str(e)}")
        
        return state
    
    def search_related_policies(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """관련 정책 검색"""
        try:
            # 추출된 텍스트와 이미지 설명을 결합하여 검색
            search_text = f"{state['query']}\n{state['extracted_text']}\n{state['image_description']}"
            
            # 여기서는 간단한 키워드 기반 검색으로 구현
            # 실제로는 벡터 데이터베이스에서 검색
            keywords = state['query'].split() + state['extracted_text'].split()[:10]
            
            # 샘플 검색 결과 (실제로는 데이터베이스에서 검색)
            state["search_results"] = [
                {
                    "policy_id": 1,
                    "policy_name": "보험약관 샘플",
                    "relevance_score": 0.85,
                    "matched_text": "보험금 지급 관련 조항",
                    "source": "image_analysis"
                }
            ]
            
            print(f"[{state['workflow_id']}] 관련 정책 검색 완료: {len(state['search_results'])}개 결과")
            
        except Exception as e:
            state["error_message"] = f"정책 검색 오류: {str(e)}"
            print(f"[{state['workflow_id']}] 정책 검색 오류: {str(e)}")
        
        return state
    
    def generate_final_response(self, state: ImageWorkflowState) -> ImageWorkflowState:
        """최종 응답 생성"""
        try:
            # 추출된 정보를 바탕으로 최종 응답 생성
            response_parts = []
            
            if state["extracted_text"]:
                response_parts.append(f"**이미지에서 추출된 텍스트:**\n{state['extracted_text'][:500]}...")
            
            if state["image_description"]:
                response_parts.append(f"**이미지 분석 결과:**\n{state['image_description']}")
            
            if state["search_results"]:
                response_parts.append("**관련 정책 정보:**")
                for result in state["search_results"]:
                    response_parts.append(f"- {result['policy_name']} (관련도: {result['relevance_score']:.2f})")
                    response_parts.append(f"  {result['matched_text']}")
            
            state["final_response"] = "\n\n".join(response_parts)
            
            print(f"[{state['workflow_id']}] 최종 응답 생성 완료")
            
        except Exception as e:
            state["error_message"] = f"최종 응답 생성 오류: {str(e)}"
            print(f"[{state['workflow_id']}] 최종 응답 생성 오류: {str(e)}")
        
        return state
    
    def create_workflow_graph(self) -> StateGraph:
        """LangGraph 워크플로우 그래프 생성"""
        workflow = StateGraph(ImageWorkflowState)
        
        # 노드 추가
        workflow.add_node("load_image", self.load_image)
        workflow.add_node("extract_text", self.extract_text_from_image)
        workflow.add_node("describe_image", self.describe_image)
        workflow.add_node("search_policies", self.search_related_policies)
        workflow.add_node("generate_response", self.generate_final_response)
        
        # 엣지 추가 (순차적 실행)
        workflow.set_entry_point("load_image")
        workflow.add_edge("load_image", "extract_text")
        workflow.add_edge("extract_text", "describe_image")
        workflow.add_edge("describe_image", "search_policies")
        workflow.add_edge("search_policies", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    async def process_image_query(self, query: str, image_path: str, workflow_id: str) -> Dict[str, Any]:
        """이미지 쿼리 처리"""
        try:
            # 워크플로우 그래프 생성
            graph = self.create_workflow_graph()
            
            # 초기 상태 설정
            initial_state = self.initialize_workflow(query, image_path, workflow_id)
            
            # 워크플로우 실행
            result = await graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "query": query,
                "image_path": image_path,
                "extracted_text": result["extracted_text"],
                "image_description": result["image_description"],
                "search_results": result["search_results"],
                "final_response": result["final_response"],
                "error_message": result["error_message"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error_message": f"워크플로우 실행 오류: {str(e)}"
            }

# 워크플로우 인스턴스 생성
image_workflow = ImageWorkflow()
