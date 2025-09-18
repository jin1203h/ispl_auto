from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "USER"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PolicyCreate(BaseModel):
    company: str
    category: str
    product_type: str
    product_name: str
    sale_start_dt: Optional[str] = None
    sale_end_dt: Optional[str] = None
    sale_stat: Optional[str] = None
    summary: Optional[str] = None
    security_level: str = "public"

class PolicyResponse(BaseModel):
    policy_id: int
    company: Optional[str]
    category: Optional[str]
    product_type: Optional[str]
    product_name: str
    sale_start_dt: Optional[str]
    sale_end_dt: Optional[str]
    sale_stat: Optional[str]
    summary: Optional[str]
    original_path: Optional[str]
    md_path: Optional[str]
    pdf_path: Optional[str]
    file_path: Optional[str]
    created_at: datetime
    security_level: Optional[str]

    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str
    policy_ids: Optional[List[int]] = None
    limit: int = 10
    security_level: str = "public"

class SearchResult(BaseModel):
    policy_id: int
    policy_name: str
    company: str
    chunk_text: str
    similarity_score: float
    chunk_index: int

class SearchResponse(BaseModel):
    results: List[SearchResult]

class WorkflowLogResponse(BaseModel):
    log_id: int
    workflow_id: str
    step_name: str
    status: str
    input_data: Optional[dict]
    output_data: Optional[dict]
    error_message: Optional[str]
    execution_time: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
