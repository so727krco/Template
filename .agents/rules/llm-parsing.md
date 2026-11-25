---
trigger: model_decision
description: 자연어 여행 조건 파싱, Gemini 2.5 Flash 프롬프트 작성, IATA 공항 코드 매핑, Pydantic 출력 스키마, 결과 브리핑 로직 작업 시 적용
---
# LLM 자연어 파싱 및 브리핑 규칙

자연어 입력을 구조화된 검색 조건으로 변환하거나 최종 항공권 결과를 요약할 때는 SSOT(`REQ-1`, `REQ-2`, `ARCH-6`)와 아래 상세 스펙을 반드시 따른다.
- 시스템 프롬프트에 매 요청 시점의 KST 현재 날짜(`YYYY-MM-DD`, 요일 포함)를 주입한다.
- 1회 검색당 SerpApi 호출은 최대 4회(1단계 탐색 1회 + 2단계 상세 병렬 조회 최대 3회) 상한을 지킨다.
- 테스트 작성 시 실제 Gemini API 및 SerpApi를 호출하지 않고 반드시 Mock 응답을 사용한다.

@[LLM 파싱 상세 스펙](../../docs/02_llm_spec.md)
