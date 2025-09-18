# 보험약관 기반 Agentic AI PRD (Product Requirements Document)

## 1. 서비스 목적 및 개요
- 생성형 AI를 활용하여 약관을 전처리, 요약, 임베딩 후 벡터DB에 저장
- 사용자의 자연어 질의에 대해 관련 약관을 검색 및 답변 제공
- 파일 업로드 지원
- 약관의 통합 관리 및 활용 편의성 극대화
    - 약관 질의 즉시 응답(예: "골절 시 보장 여부?")
    - 타 보함사 약관 비교, 설계사 교육, 계약 특약 확인 지원


## 2. 주요 기능 요건

### 2.1 약관 업로드
- 지원 파일: PDF
- 파일 업로드 → 전처리 → Markdown 변환 → 요약 → 임베딩 → 벡터DB 저장
- 원본 파일은 로컬에 저장, md 원문/요약본은 벡터DB에 저장
- 요약 결과를 업로드 시점에 사용자에게 제공

#### 2.1.1 전처리
- OCR 변환 (**Tesseract OCR**, EasyOCR, Kakao OCR, Naver OCR API)
- OCR 후 텍스트 정제 (**Python re**(정규식), textacy, custom cleaning scripts)
- 인코딩 통합/필터링 (chardet, ftfy, Python 내장 인코딩 처리)
- 목차/ 문단 구조분석 (**LlamaParse**, Camelot, Tabula)
- 불필요 텍스트 제거 (Python re)

#### 2.1.2 Markdown 변환
- 라이브러리 (**PyMuPDF**, PyPDF2, pdfminer, pdfplumber(표)) PyPDFium2Loader, PyMuPDF4LLM(표)
- 텍스트 : PyMuPDF
- 이미지 : LlamaParse
- 표 : PyMuPDF4LLM or pdfplumber

#### 2.1.3 요약
- OpenAI GPT-4o 또는 Anthropic Claude API + LangChain 워크플로우 조합

#### 2.1.4 임베딩
- chunking (**Fixed-size Chunking**, Content-aware Chunking, Semantic Chunking)
- chunk size : 200 토큰
- overlap 10~20%
- 임베딩 모델 (nomic-ai/nomic-embed-text-v1, all-MiniLM-L6-v2)
- 차원수 : 500~1000 차원

#### 2.1.5 벡터DB 저장
- DB : **FAISS** (Facebook AI Similarity Search), ChromaDB, Weaviate
- 인덱싱 : Flat (Brute Force), HNSW (Hierarchical Navigable Small World)
- 유사도 측정 방식 : Cosine Similarity
- 차원수 : 500~1000 차원

### 2.2 약관 검색
- 통합검색 및 개별 약관 지정 검색
- 유사도 순으로 결과 반환
- 검색 결과 기반 답변 생성

### 2.3 약관 관리
- 저장된 약관의 제목/요약본 목록 제공
- 원본 파일 다운로드 및 삭제 기능

### 2.4 보안조건별 모델 추천 및 자동 세팅
- 완전 폐쇄망: Qwen3 8B embedding, intfloat/multilingual-e5-large-instruct, dragonkue/snowflake-arctic-embed-l-v2.0
- 조건부 폐쇄망: Azure OpenAI(GPT-4o, GPT-4.1, text-embedding-3-large)
- 공개망: text-embedding-3-large
- 환경별 임베딩 차원에 맞는 테이블 설계 필요

## 3. 비기능 요건
- 웹 기반 UI(React, Open Web UI 스타일)
- 파일 및 데이터 보안1
- 확장성 있는 DB 설계
- 빠른 검색 및 응답 속도

## 4. 시스템 아키텍처 및 MCP 연동
- 챗 UI 기반 메인 화면(GPT 스타일)
- 사용자의 자연어 입력 → 의도 파악 → 자동 Tool 호출(MCP 기반) → 결과 응답
- 좌측 탭(사이드바)에서 수동 기능 사용 가능
- React(프론트엔드) + FastAPI/Flask(백엔드) + PostgreSQL(pgvector) + MCP 연동 구조

## 5. 데이터베이스 테이블 설계(예시)

```sql
-- 사용자 테이블
CREATE TABLE USER (
    USER_ID             SERIAL PRIMARY KEY,                   -- 사용자 고유 ID
    EMAIL               VARCHAR(255) UNIQUE NOT NULL,         -- 사용자 이메일
    PASSWORD_HASH       VARCHAR(255) NOT NULL,                -- 암호화된 비밀번호
    ROLE                VARCHAR(20) NOT NULL CHECK (ROLE IN ('ADMIN', 'USER')), -- 사용자 권한
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 생성일시
);

-- 약관 테이블
CREATE TABLE POLICY (
    POLICY_ID           SERIAL PRIMARY KEY,                   -- 약관 ID
    COMPANY             VARCHAR(100),                         -- 보험사
    CATEGORY            VARCHAR(100),                         -- 보험분류(건강보험, 자동차보험)
    PRODUCT_TYPE        VARCHAR(100),                         -- 상품 유형(정액형, 실비형)
    PRODUCT_NAME        VARCHAR(255) NOT NULL,                -- 상품명
    SALE_START_DT       VARCHAR(8),                           -- 판매시작일자
    SALE_END_DT         VARCHAR(8),                           -- 판매종료일자
    SALE_STAT           VARCHAR(10),                          -- 판매상태 (판매중, 판매종료)
    SUMMARY             TEXT,                                 -- 상품 요약
    ORIGINAL_PATH       VARCHAR(500),                         -- 원본 파일 경로
    MD_PATH             VARCHAR(500),                         -- Markdown 파일 경로
    PDF_PATH            VARCHAR(500),                         -- PDF 파일 경로
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 생성일시
    SECURITY_LEVEL      VARCHAR(20)                           -- 보안 등급
);

-- text-embedding-3 임베딩 테이블 (3072차원)
CREATE TABLE EMBEDDINGS_TEXT_EMBEDDING_3 (
    ID                  SERIAL PRIMARY KEY,                   -- 임베딩 고유 ID
    POLICY_ID           INTEGER NOT NULL REFERENCES POLICY(POLICY_ID), -- 약관 ID
    EMBEDDING           VECTOR(3072) NOT NULL,                -- 3072차원 임베딩 벡터
    MODEL               VARCHAR(100) NOT NULL,                -- 사용된 모델명
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 생성일시
);

-- Qwen 임베딩 테이블 (4096차원)
CREATE TABLE EMBEDDINGS_QWEN (
    ID                  SERIAL PRIMARY KEY,                   -- 임베딩 고유 ID
    POLICY_ID           INTEGER NOT NULL REFERENCES POLICY(POLICY_ID), -- 약관 ID
    EMBEDDING           VECTOR(4096) NOT NULL,                -- 4096차원 임베딩 벡터
    MODEL               VARCHAR(100) NOT NULL,                -- 사용된 모델명
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 생성일시
);
```

## 6. 추가 참고사항
- PoC 단계이므로 동시 사용자 수, 대규모 트래픽 등은 우선 고려하지 않음
- UI/UX는 Open Web UI의 오픈소스 스타일을 참고하여 커스터마이징
- MCP 기반 자동 Tool 호출 및 수동 기능 병행 지원

---

*본 문서는 PoC(Proof of Concept) 단계의 요구사항 정의서로, 추후 상세 설계 및 구현 단계에서 변경될 수 있습니다.*
