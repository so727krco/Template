# GitHub Issue 초안 참고 템플릿

> **양식 원본:** `.github/ISSUE_TEMPLATE/maintenance.yml` (이 파일과 다르면 원본을 따른다.)
> GitHub `Issues` → `New issue` → **"유지보수 작업"**에 옮겨 적기 전, 초안을 작성하거나 AI에게 초안을 요청할 때 참고한다.

---

## 복붙용 6항목 템플릿

```markdown
### 1. 배경
- 현상: <무엇이 문제인가 / 왜 필요한가>
- 재현: <재현 절차 (버그일 때)>
- 관련 규칙: <REQ-* / ARCH-* / docs/ 절>

### 2. 변경할 내용
- <바꿀 동작 요약>
- 대상: <수정할 파일 또는 모듈 경로>

### 3. 종료 조건
- [ ] C1. <조건> 상태에서 <동작>을 실행하면 <기대 결과>가 성립한다
- [ ] C2. <조건> 상태에서 <동작>을 실행하면 <기대 결과>가 성립한다
- [ ] C3. <브라우저에서 눈으로 확인할 조건> (수동)

### 4-1. 테스트 기능명
<영문_소문자_snake_case>

### 4-2. 기계 검증
- 테스트 파일: `tests/issues/test_issue_{번호}_{기능명}.py`
- 조건 ↔ 테스트
  - C1 → `test_c1_...`
  - C2 → `test_c2_...`
- 수동 확인: <C3 확인 방법 | 없으면 "없음">
- [ ] 변경 전 코드에서 위 테스트가 실패하는 것을 확인
- [ ] `python scripts/verify.py` 통과 (VER-1)

### 5. 건드리면 안 되는 것
- 기본 보호 영역 (`docs/`, `AGENTS.md`, `.agents/`, `scripts/`, `.github/workflows/`, `.env`, `requirements.txt`, 기존 테스트 기대값)
- 이 작업에서 추가로 막을 것: <파일/모듈 경로 | 없으면 "없음">

### 6. 구현 루프 최대 횟수
3회
```

---

## 작성 완료 예시 (Flight Finder)

- **제목:** `[유지보수] BYOK 헤더 전달 시 공용 일일 횟수 차감 우회`
- **1. 배경:**
  - 현상: `X-Flight-Api-Key` 헤더를 전달해 BYOK 모드로 검색했는데도 공용 키 일일 횟수가 차감된다.
  - 재현: 유효한 `X-Invite-Code`와 `X-Flight-Api-Key` 헤더로 `POST /api/search` 호출 후 `GET /api/quota` 확인.
  - 관련 규칙: `REQ-3`, `REQ-5`, `docs/03_api_and_byok.md` §2
- **2. 변경할 내용:**
  - `X-Flight-Api-Key` 헤더가 존재하면 일일 횟수 확인·차감을 우회하고 `used_byok=true`를 반환한다.
  - 대상: `src/api/search.py`, `src/services/limiter.py`
- **3. 종료 조건:**
  - `[ ]` C1. `X-Flight-Api-Key` 헤더가 있으면 공용 일일 한도를 소진한 IP에서도 `POST /api/search`가 성공하고 `used_byok=true`를 반환한다
  - `[ ]` C2. BYOK 요청 전후로 `GET /api/quota`의 `used` 값이 변하지 않는다
  - `[ ]` C3. 브라우저 설정 모달에 개인 키를 입력해 검색하면 새로고침 후에도 `localStorage`에서 키가 유지된다 `(수동)`
- **4-1. 테스트 기능명:** `byok_bypass_limit`
- **4-2. 기계 검증:**
  - 테스트 파일: `tests/issues/test_issue_{번호}_byok_bypass_limit.py`
  - `C1 → test_c1_byok_allows_over_limit`, `C2 → test_c2_byok_keeps_quota_unchanged`
- **5. 건드리면 안 되는 것:** 기본 보호 영역 + `src/services/llm.py`, `src/services/cache.py`
- **6. 구현 루프 최대 횟수:** `3회`
