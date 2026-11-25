---
trigger: glob
globs:
  - src/api/**
  - src/services/flight.py
  - src/static/**
---
# API 엔드포인트 및 Stateless BYOK 규칙

FastAPI 라우터, 항공권 API 호출 서비스, 프론트엔드(`localStorage` 및 헤더 전송)를 구현·수정할 때는 SSOT(`REQ-3`, `REQ-7`, `ARCH-3`, `ARCH-4`)와 아래 상세 스펙을 반드시 따른다.
- 사용자 개인 API 키(`X-Flight-Api-Key`)는 서버 파일(`data/` 포함)·로그·`print`·에러 응답 본문에 절대 출력하거나 저장하지 않는다.
- 블로킹 `requests` 대신 `httpx.AsyncClient`와 `async/await`를 사용한다.
- 응답 JSON 필드명과 커스텀 에러 코드(`ErrorResponse`)는 `docs/03_api_and_byok.md` 스키마와 정확히 일치시킨다.

@[API 및 BYOK 상세 스펙](../../docs/03_api_and_byok.md)
