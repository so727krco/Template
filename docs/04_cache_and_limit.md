# 04. 캐싱, 초대 코드 및 횟수 제한 스펙

## 1. 저장소 원칙 (No-DB)
외부 DB를 두지 않고 프로젝트 내부 `data/` 폴더의 JSON 파일로 관리한다. 서버 시작 시 `data/cache/`와 `data/limits/` 폴더가 없으면 자동 생성한다.

## 2. 검색 결과 파일 캐시 (`data/cache/`)

### 캐시 키 생성
- LLM이 파싱한 정규화 조건(`origin`, `destinations`, `departure_dates`, `stay_nights`, `trip_type`, `direct_only`, `passengers`)을 정렬된 JSON 문자열로 만든 뒤 `SHA-256` 해시 앞 16자리를 파일명으로 사용한다.
- 예: `data/cache/{cache_key}.json`

### 저장 포맷
```json
{
  "created_at": "2026-11-24T15:00:00+09:00",
  "query_params": {},
  "flight_results": []
}
```

### 캐시 유효기간(TTL) vs 물리 삭제 주기 (엄격 분리)
1. **캐시 적중 유효기간 (TTL: 4시간, 3~6시간 범위 내 설정):**
   - 조회 시 파일의 `created_at` 기준 **4시간 이내**인 경우에만 API 호출을 생략하고 캐시 데이터를 반환한다.
   - 4시간이 지난 파일은 캐시 미스(Miss)로 처리하고 새 API 결과로 덮어쓴다.
   - **공용 키 횟수 보호:** 캐시 적중(Hit) 시에는 공용 API를 호출하지 않았으므로 일일 횟수를 차감하지 않는다.
2. **디스크 물리 삭제 주기 및 스캔 빈도 제어:**
   - **실행 시점:** 사용자가 메인 웹페이지(`GET /`)를 열 때 백그라운드 태스크(`BackgroundTasks`)로 실행해 페이지 로딩을 지연시키지 않는다.
   - **스캔 빈도 가드:** 새로고침마다 불필요한 디스크 I/O가 발생하지 않도록 모듈 전역 메모리 타임스탬프(`last_cleanup_at`)를 두고, **마지막 정리 후 최소 1시간이 지났을 때만** 폴더를 스캔한다.
   - **삭제 기준:**
     - `data/cache/`: 수정 시각(`mtime`) 기준 **365일(86400 * 365초) 이상 경과**한 `.json` 파일 삭제
     - `data/limits/`: 수정 시각(`mtime`) 기준 **30일 이상 경과**한 오래된 일일 기록 `.json` 파일 함께 삭제

## 3. 일일 검색 횟수 제한 및 호출 상한선 (`data/limits/`)
- **파일 단위:** 날짜별 개별 파일로 저장한다. 예: `data/limits/2026-11-24.json`
- **식별자:** 클라이언트 IP 주소(프록시 환경 시 `X-Forwarded-For` 첫 번째 IP 우선) 기준으로 카운트한다.
- **일일 제한값:** `.env`의 `DAILY_FREE_LIMIT` (기본값 5).
- **1회 검색당 API 호출 상한선 (Cost Cap):**
  - LLM이 다수의 목적지·날짜 조합을 추출하더라도, **1회 검색당 SerpApi 호출은 최대 4회(1단계 탐색 1회 + 2단계 상세 병렬 조회 최대 3회)**로 하드 리미트를 걸어 공용 키 할당량 폭발을 원천 차단한다.
- **초대 코드 검증:** 모든 요청에서 `X-Invite-Code`가 `INVITE_CODE`와 일치하는지 상수 시간 비교(`hmac.compare_digest`)로 검증한다.

## 4. 비동기 동시성 보호 및 크로스 플랫폼 파일 안전성 (Windows · Ubuntu 공통)
동일 JSON 파일(`data/limits/{date}.json` 및 캐시 파일)에 여러 비동기 요청이 동시에 쓸 때 파일 손상과 OS 간 차이를 막기 위해 다음 3가지를 반드시 적용한다.
1. 모듈 전역 `asyncio.Lock()`으로 쓰기 임계 구역 보호
2. **Atomic Write (파일 닫힘 후 교체):** 같은 폴더에 임시 파일(`.tmp`)로 기록한 뒤 **`with` 블록이 완전히 종료되어 파일 핸들이 닫힌 다음** `os.replace()`로 원본 파일을 원자적으로 교체한다 (Windows `PermissionError` 방지).
3. **경로 · UTF-8 명시:** 모든 파일 입출력은 `pathlib.Path`와 명시적 `encoding="utf-8"`을 사용해 Windows(`cp949`)와 Ubuntu CI(`UTF-8`) 간 한글 인코딩 오류를 차단한다.
