from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
from dotenv import load_dotenv

# 환경 변수 로드 및 데이터베이스 URL 설정
load_dotenv()
os.environ.setdefault("DATABASE_URL", "postgresql://admin:admin@localhost:5433/ISPLDB")

from database import get_db, engine, Base
from models import User, Policy, EmbeddingTextEmbedding3, EmbeddingQwen, EmbeddingMultilingualE5, EmbeddingSnowflakeArctic, WorkflowLog
from services.auth_service import AuthService
from services.policy_service import PolicyService
from services.embedding_service import EmbeddingService
from services.search_service import SearchService
from services.workflow_service import WorkflowService
from workflows.image_workflow import image_workflow
from schemas import (
    UserCreate, UserLogin, PolicyCreate, PolicyResponse, 
    SearchRequest, SearchResponse, WorkflowLogResponse
)

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="ISPL Insurance Policy AI",
    description="보험약관 기반 Agentic AI 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 서비스 인스턴스
auth_service = AuthService()
policy_service = PolicyService()
embedding_service = EmbeddingService()
search_service = SearchService()
workflow_service = WorkflowService()

# 보안 설정
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """현재 사용자 인증"""
    token = credentials.credentials
    user = auth_service.verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

@app.get("/")
async def root():
    return {"message": "ISPL Insurance Policy AI API"}

@app.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """사용자 등록"""
    try:
        user = auth_service.create_user(user_data, db)
        return {"message": "User created successfully", "user_id": user.user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=dict)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인"""
    try:
        print(f"로그인 시도: {login_data.email}")
        token = auth_service.authenticate_user(login_data.email, login_data.password, db)
        print(f"로그인 성공: {login_data.email}")
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        print(f"로그인 실패: {login_data.email} - {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/auth/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """토큰 검증 및 사용자 정보 반환"""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role
    }

@app.post("/policies/upload", response_model=PolicyResponse)
async def upload_policy(
    file: UploadFile = File(...),
    company: str = Form(...),
    category: str = Form(...),
    product_type: str = Form(...),
    product_name: str = Form(...),
    security_level: str = Form("public"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """약관 파일 업로드 및 처리"""
    try:
        print(f"업로드 시작: {file.filename}, 사용자: {current_user.email}")
        print(f"업로드 정보: 회사={company}, 카테고리={category}, 제품={product_name}")
        
        # 워크플로우 시작
        workflow_id = workflow_service.start_workflow("policy_upload")
        
        # 파일 저장 및 처리
        policy = await policy_service.process_policy_file(
            file, company, category, product_type, product_name, 
            security_level, current_user.user_id, db, workflow_id
        )
        
        print(f"업로드 성공: {policy.policy_id}")
        return policy
    except Exception as e:
        print(f"업로드 실패: {str(e)}")
        if 'workflow_id' in locals():
            workflow_service.log_error(workflow_id, str(e))
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")

@app.get("/policies", response_model=List[PolicyResponse])
async def get_policies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """저장된 약관 목록 조회"""
    policies = policy_service.get_policies(db, skip=skip, limit=limit)
    return policies

@app.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 약관 조회"""
    policy = policy_service.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@app.post("/search", response_model=SearchResponse)
async def search_policies(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """약관 검색"""
    try:
        # 워크플로우 시작
        workflow_id = workflow_service.start_workflow("policy_search")
        
        results = await search_service.search_policies(
            search_request.query,
            search_request.policy_ids,
            search_request.limit,
            search_request.security_level,
            db,
            workflow_id
        )
        
        return SearchResponse(results=results)
    except Exception as e:
        workflow_service.log_error(workflow_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/logs", response_model=List[WorkflowLogResponse])
async def get_workflow_logs(
    workflow_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """워크플로우 실행 로그 조회"""
    logs = workflow_service.get_workflow_logs(db, workflow_id, limit)
    return logs


@app.get("/policies/{policy_id}/pdf")
async def get_policy_pdf(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """약관 PDF 파일 다운로드"""
    try:
        print(f"PDF 요청: policy_id={policy_id}")
        policy = policy_service.get_policy(db, policy_id)
        if not policy:
            print(f"정책을 찾을 수 없음: {policy_id}")
            raise HTTPException(status_code=404, detail="Policy not found")
        
        print(f"정책 정보: {policy.product_name}, file_path={policy.file_path}")
        
        # PDF 파일 경로 생성
        pdf_path = policy.file_path if policy.file_path else policy.original_path
        print(f"PDF 파일 경로: {pdf_path}")
        
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"PDF 파일이 존재하지 않음: {pdf_path}")
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # PDF 파일 읽기
        with open(pdf_path, "rb") as file:
            pdf_content = file.read()
        
        print(f"PDF 파일 읽기 완료: {len(pdf_content)} bytes")
        
        # 파일명 인코딩 처리
        import urllib.parse
        safe_filename = urllib.parse.quote(policy.product_name.encode('utf-8'))
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{safe_filename}.pdf"
            }
        )
    except Exception as e:
        print(f"PDF 다운로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies/{policy_id}/md")
async def get_policy_md(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """약관 MD 파일 조회"""
    try:
        print(f"MD 요청: policy_id={policy_id}")
        policy = policy_service.get_policy(db, policy_id)
        if not policy:
            print(f"정책을 찾을 수 없음: {policy_id}")
            raise HTTPException(status_code=404, detail="Policy not found")
        
        print(f"정책 정보: {policy.product_name}, md_path={policy.md_path}")
        
        # MD 파일 경로 생성
        md_path = policy.md_path if policy.md_path else None
        
        if not md_path or not os.path.exists(md_path):
            print(f"MD 파일이 존재하지 않음: {md_path}")
            raise HTTPException(status_code=404, detail="MD file not found")
        
        # MD 파일 읽기
        with open(md_path, "r", encoding="utf-8") as file:
            md_content = file.read()
        
        print(f"MD 파일 읽기 완료: {len(md_content)} 문자")
        
        return {"content": md_content}
        
    except Exception as e:
        print(f"MD 다운로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/policies/{policy_id}")
async def delete_policy(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """약관 삭제"""
    try:
        success = policy_service.delete_policy(db, policy_id)
        if not success:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {"message": "Policy deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/image/analyze")
async def analyze_image(
    query: str = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """이미지 분석 및 관련 정책 조회"""
    try:
        # 워크플로우 시작
        workflow_id = workflow_service.start_workflow("image_analysis")
        
        # 이미지 파일 저장
        image_path = f"backend/data/temp_{workflow_id}_{image.filename}"
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        with open(image_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        print(f"이미지 분석 시작: {image.filename}, 워크플로우: {workflow_id}")
        print(f"이미지 파일 크기: {len(content)} bytes")
        print(f"이미지 저장 경로: {image_path}")
        
        # LangGraph 워크플로우 실행
        result = await image_workflow.process_image_query(query, image_path, workflow_id)
        
        # 워크플로우 로그 저장
        workflow_service.log_step(
            workflow_id, 
            "image_analysis", 
            "completed" if result["success"] else "error",
            {"query": query, "image_filename": image.filename},
            {"result": result},
            db=db
        )
        
        # 임시 파일 삭제
        try:
            os.remove(image_path)
        except:
            pass
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error_message"])
            
    except Exception as e:
        print(f"이미지 분석 오류: {str(e)}")
        if 'workflow_id' in locals():
            workflow_service.log_error(workflow_id, str(e), db=db)
        raise HTTPException(status_code=500, detail=f"이미지 분석 실패: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
