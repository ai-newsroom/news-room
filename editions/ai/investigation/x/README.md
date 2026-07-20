# AI edition X 신호 조사·promotion 계약

이 계약은 [수집 계약](../../sources/x-signal-contract.md)과
[공식 API adapter](../../acquisition/x/README.md)가 만든 X 신호를 논문·코드·릴리스 노트·
시스템 카드·공식 문서로 추적하는 조사 단계다. X 글은 끝까지 `S2` 발견 신호로 남는다.
**승격되는 것은 X 문구가 아니라 claim에 연결된 외부 evidence bundle**이다.

기존 시사판의 이념·진영 토론 구조를 사용하지 않으며,
[AI 기술판의 P/E/R rubric](../../../../docs/08-ai-eda-editorial-profiles.md)을 그대로 적용한다.
이 단계는 publish를 실행하지 않고 `review-ready` 또는 `no-publish` 조사 결론만 만든다.

## 1. 조사 record

판정이 끝난 모든 signal은 최소한 다음 구조를 가진다.

```yaml
signal_id: x:123
edition: ai
author:
  registry_account_id: fixture-author
  real_name: Example Researcher
  x_handle: "@example"
  affiliation_snapshot: Example Lab
  conflicts: ["Example Lab employee"]
post:
  post_id: "123"
  url: https://x.com/example/status/123
  posted_at: 2026-07-20T09:00:00Z
  text_excerpt: "triage에 필요한 최소 인용"
observed_at: 2026-07-20T09:05:00Z
edit_state:
  canonical_post_id: "123"
  current_post_id: "123"
  version_ids: ["123"]
  is_deleted: false
  material_change: false
  latest_version_verified_at: 2026-07-20T09:05:00Z
thread_context:
  conversation_id: "123"
  reply_to_post_id: null
  quoted_post_id: null
  thread_post_ids: ["123"]
  completeness: complete
outbound_links:
  - link_id: L1
    original_url: https://t.co/example
    resolved_url: https://example.org/paper
    artifact_kind: paper
    status: accessible
    accessed_at: 2026-07-20
    version: v1
    published_at: 2026-07-20
source_evidence:
  - source_id: S1
    url: https://example.org/paper
    source_type: P1
    discovered_via: outbound
    relation: supports
    accessible: true
    public: true
    version: v1
    published_at: 2026-07-20
    conditions_complete: true
    reproduction_state: R1
extracted_claims:
  - claim_id: C1
    claim_kind: technical
    claim_text_ko: "검증 가능한 한 문장"
    material: true
    subject_version: v1
    claim_date: 2026-07-20
    source_refs: [S1]
    promotion_status: primary-source-linked
promotion_status: primary-source-linked
promotion_mapping:
  signal_source_type: S2
  evidence_source_types: [P1]
  evidence_grade: E2
  reproducibility: R1
editorial_disposition: review-ready
reason_codes: []
```

필수 필드는 `promotion.py`가 검사한다. author는 수집 당시 소속과 이해상충을 snapshot으로
남기고, 현재 레지스트리가 바뀌어도 과거 조사 기록을 덮어쓰지 않는다. Post 본문 전체가
아니라 정책상 허용되는 최소 excerpt, canonical URL과 ID를 기본으로 한다.

## 2. 조사 단계

1. **현재 상태 확인:** Post ID·URL을 rehydrate해 삭제, edit chain, 최신 version을
   확인한다. 삭제됐거나 material edit 뒤 최신본을 확인하지 못하면 이전 문구를 쓰지 않는다.
2. **문맥 복원:** self-thread의 순서, reply 대상, quoted Post와 작성자를 분리한다.
   `thread_context.completeness`가 `partial`이면 빠진 문맥을 limitation으로 남긴다.
3. **link 해제:** `t.co` 원 URL과 redirect 최종 URL을 모두 보존하고 paper, code,
   release-note, system-card, model-card, official-doc, benchmark로 분류한다.
4. **claim 추출:** 발언 사실(`speech-act`), 출시 사실(`announcement`), 방법·기능
   (`technical`), 정량 결과(`performance`), 개인 평가(`opinion`)를 원자 문장으로 나눈다.
   각 claim에는 정확한 version과 date를 붙이고 모르면 `null`로 둔다.
5. **원문 조사:** outbound link가 없어도 제목·artifact·저자를 단서로 공식 원문을 찾을
   수 있지만 `discovered_via: research`로 구분한다. 검색 요약·재인용은 원문이 아니다.
6. **교차 검증:** source가 claim을 지지하는지, 반박하는지, 공개 접근 가능한지,
   version·비교 조건·실행 artifact·독립성을 claim 단위로 기록한다. `P0/P1/P2`의
   `published_at`은 claim date와 일치해야 한다. 나중에 나온 `I1`은 자체 공개일을
   보존하되 같은 subject version을 검증해야 한다.
7. **판정:** claim별 promotion을 계산한 뒤 material claim 가운데 가장 낮은 안전 상태를
   signal 상태로 사용한다. 하나라도 반박·삭제·제한 자료 위험으로 `rejected`이면 signal도
   `rejected`다.

자연어 claim 추출은 사람 또는 별도 extractor의 책임이다. 이 최소 구현은 이미 추출된
record의 완전성과 evidence promotion을 결정적으로 판정하며, 문구를 추측해 채우지 않는다.

## 3. promotion 상태와 P/E/R 매핑

| promotion 상태 | 필요한 evidence bundle | P/E/R ceiling | 허용되는 서술 |
|---|---|---|---|
| `signal-only` | X `S2`뿐이거나 원문 없음, 개인 의견, 조건 불충분 | `S2 / E0 / R0` | 조사 질문으로만 보존. 기술·성능 사실로 쓰지 않음 |
| `announcement-confirmed` | 공개된 `P0` 또는 `P1`이 주체·날짜·version의 발표 사실을 확인 | bundle `P0/P1`, `E1`, `R0~R1`; X는 `S2` | “발표했다”, “문서에 적었다”까지만 허용 |
| `primary-source-linked` | claim과 같은 version·date의 공개 `P1`; 성능 claim은 조건이 완전한 `P1`과 검사 가능한 `P2` 모두 필요 | bundle `P1(+P2) / E2 / R1~R2`; X는 `S2` | 공개 조건 안의 저자·벤더 결과. 한계와 이해상충 병기 |
| `independently-verified` | primary bundle에 독립 `I1`이 같은 claim을 확인 | `P1/P2+I1 / E3 / R1~R2`; 공개 로그로 독립 재현하면 `E4/R3` | 확인된 범위와 차이를 밝혀 독립 확인으로 서술 |
| `rejected` | 삭제, 미확인 material edit, 공개 불가 NDA/embargo 근거, 직접 반박, claim-source 불일치 | `S2 또는 unavailable / E0 / R0` | 발행 근거에서 제외하고 사유와 재검토 조건만 보존 |

상태가 높아져도 `promotion_mapping.signal_source_type`은 언제나 `S2`다. P/E/R은 별도
`source_evidence` 묶음의 ceiling이며, 링크가 있다는 사실만으로 `E2`가 되지 않는다.

signal에 여러 material claim이 있으면 `rejected`를 최우선으로 하고, 그 밖에는
`signal-only < announcement-confirmed < primary-source-linked < independently-verified`
순서의 최솟값을 쓴다. 예를 들어 출시 사실이 `announcement-confirmed`여도 “20% 향상”이
`signal-only`면 signal 전체는 `signal-only`다.

## 4. 경계·미발행 규칙

| 상황 | 판정 | 보존·미발행 동작 |
|---|---|---|
| outbound/source link 없음 | `signal-only` | `PRIMARY_SOURCE_MISSING`; 원문 공개 전까지 `no-publish` |
| source가 접근 불가 또는 version/date 불일치 | `signal-only` | `PRIMARY_SOURCE_UNAVAILABLE` 또는 `VERSION_OR_DATE_MISMATCH`; 추측 보완 금지 |
| Post 삭제 | `rejected` | `POST_DELETED`; excerpt를 비우고 ID·URL·tombstone만 보존 |
| material edit 후 최신본 미확인 | `rejected` | `EDIT_NOT_REVERIFIED`; 최신 version rehydrate 전 미발행 |
| 개인 의견·전망뿐 | `signal-only` | `OPINION_ONLY`; 발언 사실 이외 기술 결론 금지 |
| embargo·NDA·비공개 briefing 암시 | `rejected` | `SECURITY_OR_LICENSE_RISK`; 공개 자료로 대체되기 전 사용 금지 |
| 작성자·근거의 고용·투자·후원 이해상충 | 현재 근거 상태 유지 | 독립 `I1` 전에는 `CONFLICT_UNRESOLVED`로 `no-publish`; 관계 공개 |
| 독립 자료가 claim을 반박 | `rejected` | `CLAIM_CONTRADICTED`; 양쪽 원문과 조건 차이를 기록 |
| 성능 claim의 benchmark·baseline·version·조건 또는 `P2` 누락 | `signal-only` | `PERFORMANCE_CONDITIONS_MISSING`; X 수치를 성능 사실로 사용 금지 |

`no-publish`는 오류가 아니라 정상 편집 결과다. `recheck_triggers`에는 최신 Post 재확인,
공식 릴리스/논문/시스템 카드 공개, benchmark script 공개, 독립 재현처럼 관찰 가능한
조건만 적는다. “관계자가 맞다고 했다”나 비공개 확인은 trigger 충족이 아니다.

## 5. 판정기와 fixture

[`promotion.py`](promotion.py)는 network·browser·LLM 호출 없이 JSON record를 검증하고
promotion을 계산한다. 입력과 출력에서 thread·reply·quote 문맥, 원 URL·resolved URL,
version·date를 그대로 보존한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 editions/ai/investigation/x/test_promotion.py
```

고정 fixture는 다섯 상태를 모두 포함하고 다음 경계를 별도로 확인한다.

- 출처 없는 기술 claim과 개인 의견
- 공식 발표, 공개 paper/code, 독립 재현
- 삭제된 Post와 material edit 미재검증
- embargo/NDA 암시
- 이해상충이 있는 벤더 성능 claim

fixture의 `review-ready`는 기술 조사 자료가 다음 편집 gate로 갈 수 있다는 뜻일 뿐 자동
기사·발행 승인이 아니다. 실제 publish는 중요성, 새 국면, 기사 품질과 사람 승인을 다시
통과해야 한다.
