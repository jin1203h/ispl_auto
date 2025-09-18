#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

from database import get_db
from models import Policy
from sqlalchemy.orm import Session

def check_policies():
    try:
        db = next(get_db())
        policies = db.query(Policy).all()
        print(f'총 약관 수: {len(policies)}')
        
        if len(policies) == 0:
            print("데이터베이스에 약관이 없습니다.")
            return
            
        for policy in policies:
            print(f'ID: {policy.policy_id}')
            print(f'  회사: {policy.company}')
            print(f'  상품명: {policy.product_name}')
            print(f'  생성일: {policy.created_at}')
            print(f'  파일경로: {policy.file_path}')
            print(f'  원본경로: {policy.original_path}')
            print('---')
            
    except Exception as e:
        print(f'오류 발생: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_policies()



