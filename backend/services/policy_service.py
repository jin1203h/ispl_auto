import os
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from models import Policy
from schemas import PolicyResponse
from services.workflow_service import WorkflowService
from services.embedding_service import EmbeddingService
import aiofiles
from fastapi import UploadFile

class PolicyService:
    def __init__(self):
        self.workflow_service = WorkflowService()
        self.embedding_service = EmbeddingService()
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

    async def process_policy_file(
        self, 
        file: UploadFile, 
        company: str, 
        category: str, 
        product_type: str, 
        product_name: str, 
        security_level: str,
        user_id: int,
        db: Session,
        workflow_id: str
    ) -> PolicyResponse:
        """약관 파일 처리"""
        try:
            print(f"파일 처리 시작: {file.filename}")
            # 1. 파일 저장
            file_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1].lower()
            print(f"파일 ID: {file_id}, 확장자: {file_extension}")
            
            original_path = os.path.join(self.data_dir, f"{file_id}.{file_extension}")
            pdf_path = os.path.join(self.data_dir, f"{file_id}.pdf")
            md_path = os.path.join(self.data_dir, f"{file_id}.md")
            
            # 원본 파일 저장
            async with aiofiles.open(original_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            self.workflow_service.log_step(workflow_id, "file_upload", "completed", 
                                         {"file_size": len(content), "file_type": file_extension})
            
            # 2. PDF 변환 (필요시)
            if file_extension != 'pdf':
                # 여기서는 간단히 원본 파일을 PDF로 복사
                # 실제로는 적절한 변환 라이브러리 사용
                async with aiofiles.open(pdf_path, 'wb') as f:
                    await f.write(content)
            else:
                async with aiofiles.open(pdf_path, 'wb') as f:
                    await f.write(content)
            
            # 3. OCR 및 텍스트 추출
            text_content = await self._extract_text_from_pdf(pdf_path)
            self.workflow_service.log_step(workflow_id, "text_extraction", "completed", 
                                         {"text_length": len(text_content)}, db=db)
            
            # 4. Markdown 변환
            markdown_content = await self._convert_to_markdown(text_content)
            async with aiofiles.open(md_path, 'w', encoding='utf-8') as f:
                await f.write(markdown_content)
            
            self.workflow_service.log_step(workflow_id, "markdown_conversion", "completed", 
                                         {"markdown_length": len(markdown_content)}, db=db)
            
            # 5. 요약 생성
            summary = await self._generate_summary(markdown_content)
            self.workflow_service.log_step(workflow_id, "summary_generation", "completed", 
                                         {"summary_length": len(summary)}, db=db)
            
            # 6. 데이터베이스에 정책 저장
            policy = Policy(
                company=company,
                category=category,
                product_type=product_type,
                product_name=product_name,
                summary=summary,
                original_path=original_path,
                md_path=md_path,
                pdf_path=pdf_path,
                file_path=original_path,  # 원본 파일 경로 저장
                security_level=security_level
            )
            
            db.add(policy)
            db.commit()
            db.refresh(policy)
            
            # 7. 임베딩 생성 및 저장
            print(f"임베딩 생성 시작: 정책 ID {policy.policy_id}")
            try:
                await self.embedding_service.create_embeddings(
                    policy.policy_id, 
                    markdown_content, 
                    security_level, 
                    db, 
                    workflow_id
                )
                print(f"임베딩 생성 완료: 정책 ID {policy.policy_id}")
            except Exception as embedding_error:
                print(f"임베딩 생성 오류: {embedding_error}")
                # 임베딩 생성 실패해도 정책은 저장됨
                self.workflow_service.log_error(workflow_id, f"임베딩 생성 실패: {embedding_error}", db=db)
            
            self.workflow_service.log_step(workflow_id, "embedding_creation", "completed", 
                                         {"policy_id": policy.policy_id}, db=db)
            
            return PolicyResponse.from_orm(policy)
            
        except Exception as e:
            print(f"파일 처리 오류: {str(e)}")
            self.workflow_service.log_error(workflow_id, str(e), db=db)
            raise e

    async def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            print(f"PDF 텍스트 추출 시작: {pdf_path}")
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                page_count = len(pdf_reader.pages)
                print(f"PDF 페이지 수: {page_count}")
                
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        if i % 10 == 0:  # 10페이지마다 진행상황 출력
                            print(f"텍스트 추출 진행: {i+1}/{page_count} 페이지")
                    except Exception as page_error:
                        print(f"페이지 {i+1} 텍스트 추출 오류: {page_error}")
                        continue
                
                print(f"PDF 텍스트 추출 완료: {len(text)} 문자")
                return text
        except Exception as e:
            print(f"PDF 텍스트 추출 오류: {e}")
            # 빈 텍스트라도 반환하여 처리 계속
            return "PDF 텍스트 추출에 실패했습니다."

    async def _convert_to_markdown(self, text: str) -> str:
        """텍스트를 Markdown으로 변환"""
        # 간단한 Markdown 변환 로직
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append("")
                continue
                
            # 제목 감지 (간단한 휴리스틱)
            if len(line) < 100 and any(keyword in line for keyword in ['제', '장', '조', '항', '목']):
                markdown_lines.append(f"## {line}")
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)

    async def _generate_summary(self, content: str) -> str:
        """내용 요약 생성"""
        # 간단한 요약 로직 (실제로는 LLM 사용)
        sentences = content.split('.')
        summary_sentences = sentences[:3]  # 처음 3문장
        return '. '.join(summary_sentences) + '.'

    def get_policies(self, db: Session, skip: int = 0, limit: int = 100) -> List[PolicyResponse]:
        """저장된 약관 목록 조회"""
        policies = db.query(Policy).offset(skip).limit(limit).all()
        return [PolicyResponse.from_orm(policy) for policy in policies]

    def get_policy(self, db: Session, policy_id: int) -> Optional[PolicyResponse]:
        """특정 약관 조회"""
        policy = db.query(Policy).filter(Policy.policy_id == policy_id).first()
        if policy:
            return PolicyResponse.from_orm(policy)
        return None

    def delete_policy(self, db: Session, policy_id: int) -> bool:
        """약관 삭제"""
        policy = db.query(Policy).filter(Policy.policy_id == policy_id).first()
        if not policy:
            return False
        
        # 관련 임베딩 삭제
        from models import EmbeddingTextEmbedding3, EmbeddingQwen, EmbeddingMultilingualE5, EmbeddingSnowflakeArctic
        
        db.query(EmbeddingTextEmbedding3).filter(EmbeddingTextEmbedding3.policy_id == policy_id).delete()
        db.query(EmbeddingQwen).filter(EmbeddingQwen.policy_id == policy_id).delete()
        db.query(EmbeddingMultilingualE5).filter(EmbeddingMultilingualE5.policy_id == policy_id).delete()
        db.query(EmbeddingSnowflakeArctic).filter(EmbeddingSnowflakeArctic.policy_id == policy_id).delete()
        
        # 파일 삭제
        if policy.original_path and os.path.exists(policy.original_path):
            os.remove(policy.original_path)
        if policy.pdf_path and os.path.exists(policy.pdf_path):
            os.remove(policy.pdf_path)
        if policy.md_path and os.path.exists(policy.md_path):
            os.remove(policy.md_path)
        
        # 데이터베이스에서 삭제
        db.delete(policy)
        db.commit()
        return True
