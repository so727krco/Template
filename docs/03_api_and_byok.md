# 03. 웹 API 명세 및 Stateless BYOK 스펙

## 1. 엔드포인트 목록

| Method | Path | 설명 |
| :--- | :--- | :--- |
| `GET` | `/` | 정적 웹페이지(`src/static/index.html`) 반환. 진입 시 만료 파일 정리 백그라운드 태스크 트리거 |
| `GET` | `/api/health` | 서버 상태 확인 (`{"status": "ok"}`) |
| `POST` | `/api/search` | 자연어 조건 파싱 + 항공권 조회 + 브리핑 결과 반환 |
| `GET` | `/api/quota` | 현재 클라이언트 기준 공용 키 일일 잔여 횟수 조회 |

## 2. 요청 헤더 및 BYOK 분기 (`POST /api/search`)

### 요청 헤더
- `X-Invite-Code` (필수): `.env`의 `INVITE_CODE`와 일치해야 함. **공용 키·BYOK 여부와 관계없이 모든 요청에 필수 적용**한다.
- `X-Flight-Api-Key` (선택): 사용자 개인 SerpApi 키.

### 요청 본문 (`SearchRequest`)
```json
{
  "query": "다음 달 금요일 출발 2박 3일 도쿄 직항 30만 원 이하"
}
```

### 백엔드 키 분기 로직
1. `X-Invite-Code` 검증 → 불일치 시 `401 Unauthorized` 반환.
2. `X-Flight-Api-Key` 존재 여부 확인:
   - **존재 시 (BYOK 모드):** 일일 횟수 제한(`DAILY_FREE_LIMIT`) 우회 → 사용자 키로 항공권 API 호출.
   - **미존재 시 (공용 모드):** 일일 횟수 제한 확인 → 초과 시 `429 Too Many Requests` 반환 → 캐시 확인 후 미스 시 `FLIGHT_API_KEY`로 호출 및 횟수 차감.
3. **Stateless 보안 원칙:** `X-Flight-Api-Key`는 함수 인자로만 전달해 메모리에서 일회성 사용하고, 파일(`data/`)·로그·`print`·에러 응답 본문에 절대 남기지 않는다.

## 3. 성공 응답 스키마 (프론트엔드 연동 계약)

### 3-1. `POST /api/search` 응답 (`SearchResponse`, `200 OK`)

#### 필드 정의 (`SearchResponse`)
| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `parsed_query` | `FlightSearchQuery` | LLM이 자연어에서 추출한 구조화 검색 조건 (`docs/02_llm_spec.md` 참조) |
| `flights` | `list[FlightOption]` | 예산·조건에 맞는 상위 3~5개 항공권 옵션 목록 |
| `briefing` | `str` | 전체 검색 결과에 대한 한국어 핵심 요약 브리핑 |
| `cached` | `bool` | 4시간 TTL 로컬 캐시 적중 여부 |
| `used_byok` | `bool` | 사용자 개인 API 키(`X-Flight-Api-Key`) 사용 여부 |

#### 항공편 항목 정의 (`FlightOption`)
| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `airline` | `str` | 항공사명 |
| `price_krw` | `int` | 항공권 총액 (원화 정수) |
| `origin` | `str` | 출발 공항 IATA 코드 |
| `destination` | `str` | 도착 공항 IATA 코드 |
| `departure_time` | `str` | 가는 편 출발 시각 (`YYYY-MM-DDTHH:MM`) |
| `arrival_time` | `str` | 가는 편 도착 시각 (`YYYY-MM-DDTHH:MM`) |
| `return_departure_time` | `str \| None` | 오는 편 출발 시각 (편도일 경우 `null`) |
| `return_arrival_time` | `str \| None` | 오는 편 도착 시각 (편도일 경우 `null`) |
| `is_direct` | `bool` | 직항 여부 |
| `booking_url` | `str` | 구글 플라이트 또는 예약 이동 링크 |
| `pros_cons` | `str` | 해당 항공편의 시간대·가성비 한 줄 장단점 |

#### 응답 JSON 예시
```json
{
  "parsed_query": {
    "origin": "ICN",
    "destinations": ["NRT", "HND"],
    "departure_dates": ["2026-12-04"],
    "stay_nights": 2,
    "trip_type": "round_trip",
    "direct_only": true,
    "max_budget_krw": 300000,
    "passengers": 1
  },
  "flights": [
    {
      "airline": "에어서울",
      "price_krw": 248000,
      "origin": "ICN",
      "destination": "NRT",
      "departure_time": "2026-12-04T07:30",
      "arrival_time": "2026-12-04T10:00",
      "return_departure_time": "2026-12-06T11:30",
      "return_arrival_time": "2026-12-06T14:15",
      "is_direct": true,
      "booking_url": "https://www.google.com/travel/flights/...",
      "pros_cons": "예산 내 최저가 직항이나 출발이 다소 이름"
    }
  ],
  "briefing": "도쿄 직항 2박 3일 기준 24~29만 원대 옵션 3건을 찾았습니다. 가성비는 에어서울 오전편이 가장 좋습니다.",
  "cached": false,
  "used_byok": false
}
```

### 3-2. `GET /api/quota` 응답 (`QuotaResponse`, `200 OK`)

#### 필드 정의 (`QuotaResponse`)
| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `daily_limit` | `int` | 일일 공용 키 최대 무료 검색 횟수 (`DAILY_FREE_LIMIT`) |
| `used` | `int` | 오늘 사용한 공용 키 검색 횟수 |
| `remaining` | `int` | 오늘 남은 공용 키 검색 횟수 (`max(0, daily_limit - used)`) |

#### 응답 JSON 예시
```json
{
  "daily_limit": 5,
  "used": 2,
  "remaining": 3
}
```

## 4. 커스텀 에러 응답 규격 (`ErrorResponse`)

외부 API 오류나 사용자 입력 오류 시 `500` 에러를 그대로 노출하지 않고 아래 JSON 포맷으로 통일해 반환한다. 에러 본문에는 사용자 API 키나 내부 스택 트레이스를 절대 포함하지 않는다.

### 필드 정의 (`ErrorResponse`)
| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `error_code` | `str` | 프론트엔드 분기 처리용 대문자 스네이크 케이스 에러 코드 |
| `message` | `str` | 사용자 화면에 그대로 표시할 친절한 한국어 안내 문구 |

### 응답 JSON 예시
```json
{
  "error_code": "INVALID_USER_API_KEY",
  "message": "입력하신 항공권 API 키가 유효하지 않거나 한도가 초과되었습니다. 키를 다시 확인해 주세요."
}
```

### 상태 코드 및 에러 코드 매핑표
| HTTP 상태 | `error_code` | 한국어 안내 메시지 기준 |
| :--- | :--- | :--- |
| `401` | `INVALID_INVITE_CODE` | 초대 코드가 올바르지 않습니다. |
| `429` | `DAILY_LIMIT_EXCEEDED` | 오늘의 무료 검색 횟수를 모두 사용했습니다. 설정에서 본인 API 키를 입력하면 계속 이용할 수 있습니다. |
| `400` | `INVALID_USER_API_KEY` | 입력하신 항공권 API 키가 유효하지 않거나 한도가 초과되었습니다. |
| `422` | `QUERY_PARSE_FAILED` | 여행 조건을 이해하지 못했습니다. 목적지와 대략적인 일정을 포함해 다시 입력해 주세요. |
| `502` | `UPSTREAM_API_ERROR` | 항공권 조회 서비스 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요. |

## 5. 프론트엔드 `localStorage` 키 규약
로그인 없이 개인별 데이터를 유지하기 위해 브라우저 `localStorage`에 아래 항목만 저장한다.
- `ff_invite_code`: 사용자가 입력한 초대 코드
- `ff_flight_api_key`: 사용자 개인 BYOK 키 (선택)
- `ff_recent_searches`: 최근 검색 조건 및 결과 요약 목록 (최대 10건 보관, 오래된 항목부터 교체)
