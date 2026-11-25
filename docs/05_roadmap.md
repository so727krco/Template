# 05. MVP 개발 로드맵 및 체크리스트

새 기능을 구현하기 전 현재 진행 단계를 확인하고, 단계 완료 시 `python scripts/verify.py` 통과 후 체크박스를 갱신한다.

## Phase 1: 프로젝트 초기화 및 검증 파이프라인 구축
- [ ] `requirements.txt`, `.env.example`, `.gitignore` 생성
- [ ] `scripts/verify.py` 배치 및 검증 도구(`ruff`, `mypy`, `pytest`) 동작 확인
- [ ] `tests/conftest.py` 외부 호스트 실연결 차단 픽스처(`autouse=True`) 작성 (`ARCH-6`)
- [ ] `src/config.py`, `src/main.py` 기본 뼈대 및 `/api/health` 엔드포인트 구현

## Phase 2: 핵심 파싱 및 항공권 조회 서비스 (Mock 우선)
- [ ] `src/schemas/` Pydantic v2 모델 정의 (`FlightSearchQuery`, `SearchRequest`, `SearchResponse`)
- [ ] `src/services/llm.py` Gemini 2.5 Flash 자연어 파싱 및 결과 브리핑 구현
- [ ] `src/services/flight.py` SerpApi Google Flights 2단계 비동기 조회 구현
- [ ] `tests/` LLM 및 항공권 API Mock 단위 테스트 작성

## Phase 3: 보안, 캐싱 및 횟수 제한 연동
- [ ] `src/services/limiter.py` 초대 코드 검증 및 일일 횟수 제한 (`asyncio.Lock` + Atomic Write) 구현
- [ ] `src/services/cache.py` 4시간 TTL 파일 캐싱 및 365일 경과 파일 삭제 로직 구현
- [ ] `src/api/` `/api/search`, `/api/quota` 엔드포인트, BYOK 헤더 분기, 커스텀 에러 핸들러 연동
- [ ] BYOK 우회, 초대 코드 오류, 한도 초과, 캐시 적중/만료 삭제 통합 테스트 작성
- [ ] `tests/test_invariants.py` 공통 불변식 테스트 작성 (BYOK 키 비유출 `ARCH-4` · 1회 검색당 SerpApi `<= 4`회 `REQ-2` · 동시 쓰기 무결성 및 한글 UTF-8/`.tmp` 잔여 없음 `ARCH-2`)

## Phase 4: 단순 웹페이지 UI 및 최종 점검
- [ ] `src/static/index.html`, `style.css`, `app.js` 구현 (검색 폼, 결과 카드, 설정 모달)
- [ ] `localStorage` 연동 (초대 코드, 개인 BYOK 키, 최근 검색값 최대 10건)
- [ ] `tests/test_static_contract.py` 정적 계약 테스트 작성 (정적 서빙 `200 OK` · `index.html` ID ↔ `app.js` 참조 교차 · 백엔드 응답 스키마 필드 ↔ `app.js` 교차 · 필수 헤더/`localStorage` 키/API 경로)
- [ ] `GET /` 진입 시 365일 경과 캐시 정리 백그라운드 태스크 연결 및 `TestClient` 검증
- [ ] 전체 `python scripts/verify.py` PASS 및 로컬 실테스트 완료
