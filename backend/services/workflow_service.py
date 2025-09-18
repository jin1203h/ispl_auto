import uuid
import time
from typing import List, Optional
from sqlalchemy.orm import Session
from models import WorkflowLog
from schemas import WorkflowLogResponse

class WorkflowService:
    def start_workflow(self, workflow_type: str) -> str:
        """워크플로우 시작"""
        workflow_id = f"{workflow_type}_{uuid.uuid4().hex[:8]}"
        return workflow_id

    def log_step(
        self, 
        workflow_id: str, 
        step_name: str, 
        status: str, 
        input_data: dict = None, 
        output_data: dict = None,
        execution_time: int = None,
        db: Session = None
    ):
        """워크플로우 단계 로깅"""
        print(f"[{workflow_id}] {step_name}: {status}")
        if input_data:
            print(f"  Input: {input_data}")
        if output_data:
            print(f"  Output: {output_data}")
        if execution_time:
            print(f"  Execution time: {execution_time}ms")
        
        # 데이터베이스에 저장
        if db:
            try:
                workflow_log = WorkflowLog(
                    workflow_id=workflow_id,
                    step_name=step_name,
                    status=status,
                    input_data=input_data,
                    output_data=output_data,
                    execution_time=execution_time
                )
                db.add(workflow_log)
                db.commit()
            except Exception as e:
                print(f"워크플로우 로그 저장 실패: {e}")
                db.rollback()

    def log_error(self, workflow_id: str, error_message: str, db: Session = None):
        """워크플로우 오류 로깅"""
        print(f"[{workflow_id}] ERROR: {error_message}")
        
        # 데이터베이스에 저장
        if db:
            try:
                workflow_log = WorkflowLog(
                    workflow_id=workflow_id,
                    step_name="error",
                    status="error",
                    error_message=error_message
                )
                db.add(workflow_log)
                db.commit()
            except Exception as e:
                print(f"워크플로우 오류 로그 저장 실패: {e}")
                db.rollback()

    def get_workflow_logs(self, db: Session, workflow_id: Optional[str] = None, limit: int = 100) -> List[WorkflowLogResponse]:
        """워크플로우 로그 조회"""
        query = db.query(WorkflowLog)
        if workflow_id:
            query = query.filter(WorkflowLog.workflow_id == workflow_id)
        
        logs = query.order_by(WorkflowLog.created_at.desc()).limit(limit).all()
        return [WorkflowLogResponse.from_orm(log) for log in logs]
    

    def log_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        status: str,
        db: Session,
        input_data: dict = None,
        output_data: dict = None,
        error_message: str = None,
        execution_time: int = None
    ):
        """워크플로우 단계를 데이터베이스에 로깅"""
        log_entry = WorkflowLog(
            workflow_id=workflow_id,
            step_name=step_name,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
            execution_time=execution_time
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return log_entry
