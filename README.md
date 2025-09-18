# ISPL Insurance Policy AI

보험약관 기반 Agentic AI 시스템으로, PDF 약관 파일을 업로드하고 자연어 질의를 통해 관련 약관을 검색하고 답변을 제공합니다.

## 🚀 주요 기능

- **약관 업로드**: PDF 파일을 업로드하여 자동으로 텍스트 추출, 요약, 임베딩 생성
- **자연어 검색**: 자연어 질의를 통한 관련 약관 검색 및 답변 생성
- **워크플로우 모니터링**: LangGraph를 활용한 시스템 워크플로우 실시간 모니터링
- **보안 등급별 모델 지원**: 공개망, 조건부 폐쇄망, 완전 폐쇄망 환경별 최적화된 모델 사용

## 🏗️ 시스템 아키텍처

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL + pgvector
- **AI/ML**: LangChain + LangGraph + OpenAI/Anthropic API
- **Monitoring**: LangGraph 워크플로우 모니터링

## 📋 사전 요구사항

- Docker & Docker Compose
- Node.js 18+ (로컬 개발시)
- Python 3.11+ (로컬 개발시)

## 🛠️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ISPL
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 등 설정
```

### 3. Docker Compose로 실행
```bash
docker-compose up -d
```

### 4. 로컬 개발 환경 설정

#### 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

## 🔧 설정

### 데이터베이스 설정
- PostgreSQL 16 + pgvector 확장
- 기본 계정: admin / admin123
- 데이터베이스: ISPLDB

### API 키 설정
`.env` 파일에서 다음 API 키들을 설정하세요:
- `OPENAI_API_KEY`: OpenAI API 키
- `ANTHROPIC_API_KEY`: Anthropic API 키 (선택사항)

### 보안 등급별 모델 설정
- **공개망**: text-embedding-3-large, GPT-4o
- **조건부 폐쇄망**: Azure OpenAI
- **완전 폐쇄망**: Qwen3 8B, 다국어 E5, Snowflake Arctic

## 📖 사용법

### 1. 로그인
- 기본 관리자 계정: admin@ispl.com / admin123

### 2. 약관 업로드
1. "약관 관리" 탭으로 이동
2. "약관 업로드" 버튼 클릭
3. PDF 파일과 메타데이터 입력
4. 보안 등급 선택

### 3. 약관 검색
1. "채팅" 탭으로 이동
2. 자연어로 질문 입력
3. 관련 약관 정보 확인

### 4. 워크플로우 모니터링
1. "워크플로우" 탭으로 이동
2. 실시간 워크플로우 실행 상태 확인
3. 오류 발생시 상세 로그 확인

## 🔍 API 엔드포인트

### 인증
- `POST /auth/login` - 로그인
- `POST /auth/register` - 회원가입

### 약관 관리
- `POST /policies/upload` - 약관 업로드
- `GET /policies` - 약관 목록 조회
- `GET /policies/{id}` - 특정 약관 조회
- `DELETE /policies/{id}` - 약관 삭제

### 검색
- `POST /search` - 약관 검색

### 워크플로우
- `GET /workflow/logs` - 워크플로우 로그 조회

## 🗄️ 데이터베이스 스키마

### 주요 테이블
- `users`: 사용자 정보
- `policies`: 약관 정보
- `embeddings_*`: 임베딩 벡터 (모델별)
- `workflow_logs`: 워크플로우 실행 로그

## 🔒 보안 고려사항

- JWT 토큰 기반 인증
- 비밀번호 bcrypt 해싱
- CORS 설정
- 환경별 API 키 분리

## 🚀 배포

### Docker Compose 배포
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 개별 서비스 배포
각 서비스별 Dockerfile을 사용하여 개별 배포 가능

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**ISPL Insurance Policy AI** - 보험약관의 미래를 만들어갑니다.
