---
trigger: model_decision
description: 초대 코드 인증, 일일 검색 횟수 제한, data/cache 파일 캐싱(TTL 4시간), 웹페이지 진입 시 1년(365일) 경과 캐시 자동 삭제, asyncio.Lock 동시성 제어 작업 시 적용
---
# 캐싱, 초대 코드 및 횟수 제한 규칙

로컬 JSON 기반 캐시·횟수 제한·만료 파일 정리를 구현할 때는 SSOT(`REQ-4`, `REQ-5`, `REQ-6`, `ARCH-2`, `ARCH-5`)와 아래 상세 스펙을 반드시 따른다.
- 캐시 적중 유효기간(TTL 4시간, 3~6시간 범위)과 디스크 물리 삭제 주기(365일, `limits` 30일)를 절대 혼동하지 않는다.
- 캐시 적중(Hit) 시에는 공용 키 일일 횟수를 차감하지 않는다.
- 공유 JSON 파일 쓰기 시 모듈 전역 `asyncio.Lock`과 Atomic Write(`.tmp` 쓰기 `with` 블록 종료 후 `os.replace`)를 적용한다.
- 모든 파일 입출력에는 `pathlib.Path`와 `encoding="utf-8"`을 명시한다 (Windows 로컬 · Ubuntu CI 크로스 플랫폼 안전성).
- 초대 코드는 `hmac.compare_digest`로 상수 시간 비교한다.

@[캐싱 및 횟수 제한 상세 스펙](../../docs/04_cache_and_limit.md)
