# AI edition X 신호 수집 계약

이 문서는 [`x-accounts.yaml`](x-accounts.yaml)의 계정을 AI 기술판의 **발견 신호**로
수집하는 계약이다. X 글은 작성자가 그렇게 말했다는 사실을 확인하는 직접 자료일 수는
있지만, 그 안의 기술·성능 주장을 입증하지 않는다. 기존 시사판의 이념·진영 균형이나
토론 persona를 가져오지 않으며, [AI 편집 강령](../../../docs/08-ai-eda-editorial-profiles.md)의
`S2` 발견 신호 규칙을 따른다.

## 1. 레지스트리 선정과 경계

- 선정 단위는 유명세가 아니라 공개 기술 산출물로 이어지는 전문성이다. 모델 연구,
  평가, 안전, 에이전트, 추론 시스템, 오픈소스, 데이터, 학습·서빙 인프라를 모두 덮는다.
- 팔로워 수, 인증 배지, 게시물의 좋아요·조회·재게시 수는 후보 추가·정렬·유지·제외와
  evidence grade에 사용하지 않는다. 레지스트리에는 해당 필드도 두지 않는다.
- 산업 연구·엔지니어, 연구 책임자, 교수, 박사과정·초기 경력, 오픈 연구 조직,
  독립 실무자의 신호를 함께 둔다. 기업 대표나 경영자라는 이유만으로 추가하지 않는다.
- 한 조직은 active seed의 25%를 넘지 않는다. 전문 영역은 최소 한 명이 아니라 가능한
  한 서로 다른 이해관계의 두 경로로 교차 확인한다.
- 뉴스 가치가 없거나 1차 자료로 이어지지 않으면 수집량과 무관하게 발행하지 않는다.

레지스트리의 필수 account 필드는 다음과 같다.

| 필드 | 의미 |
|---|---|
| `id`, `real_name` | 변경되지 않는 내부 식별자와 실명 |
| `x_handle`, `x_url`, `x_identity_evidence` | 현재 handle, canonical URL, 신원 확인 근거 |
| `current_affiliation` | 현재 조직·역할, 근거 URL, 확인 신뢰도 |
| `role_group`, `expertise_tags` | 균형 점검용 역할군과 전문 태그 |
| `selection_reason_ko` | 팔로워 수가 아닌 기술적 선정 이유 |
| `added_at`, `last_verified_at` | 편입일과 마지막 재검증일 |
| `status`, `activity_state` | 수집 가능 상태와 관찰된 활동 상태 |
| `bias_notes_ko` | 소속·사업·연구 관점에서 예상되는 편향과 검증 주의점 |

`active`는 최근 글을 썼다는 뜻이 아니라 신원과 handle이 확인되어 수집 가능한 상태라는
뜻이다. 게시 빈도는 `activity_state`로 분리하며, X 접근 제한으로 확인하지 못한 경우
추정하지 않고 `unverified`로 남긴다.

## 2. 수집 레코드와 관계 보존

수집기는 계정별 최신 글을 기사 초안으로 복사하지 않고 아래 최소 레코드를 만든다.

```yaml
signal_id: x:<post_id>
edition: ai
registry_account_id: noam-brown
author_handle_snapshot: "@polynoamial"
post_url: https://x.com/polynoamial/status/<post_id>
post_id: "<post_id>"
posted_at: "<observed timestamp or null>"
observed_at: "<UTC timestamp>"
post_text_excerpt: "<식별·triage에 필요한 최소 인용 또는 null>"
conversation_id: "<thread id or null>"
thread_posts:
  - {position: 1, post_url: "<canonical URL>", post_id: "<id>"}
quoted_post:
  post_url: "<canonical URL or null>"
  post_id: "<id or null>"
  author_handle_snapshot: "<handle or null>"
external_links:
  - original_url: "<t.co or visible URL>"
    resolved_url: "<redirect-resolved URL>"
    relation: paper | code | system-card | model-card | release-note | benchmark | other
collection_state: discovered
collection_notes: []
```

- self-thread는 `conversation_id`와 글별 canonical URL·ID·순서를 보존한다. 삭제되거나
  접근할 수 없는 중간 글은 순서를 당겨 합치지 않고 `missing`으로 표시한다.
- 인용 글은 인용한 사람의 해석과 인용된 사람의 원문을 합치지 않는다. `quoted_post`를
  별도 객체로 보존하고 양쪽 작성자·URL·시각을 각각 기록한다.
- 외부 링크는 리디렉션 전 URL과 최종 URL을 모두 보존하고, 논문·코드·시스템 카드 등
  자료 유형을 기록한다. 기술 검증은 반드시 최종 원문을 열어 수행한다.
- 원문 삭제 대비는 이용 조건과 저작권이 허용하는 범위의 최소 인용, URL·ID·관찰 시각,
  외부 자료의 콘텐츠 해시로 제한한다. X 글 전문이나 미디어를 무단 복제하지 않는다.
- 수집 오류, 로그인 제한, 삭제 추정은 사실로 확정하지 않고 `collection_notes`에 관찰
  상태로 기록한다.

## 3. claim 분리 규칙

한 글에서 최소한 다음 세 종류를 별개 claim으로 만든다.

| claim kind | 질문 | X 글의 역할 | 출고 전 필요한 근거 |
|---|---|---|---|
| `speech-act` | 누가 언제 무엇을 게시했나 | 그 발언 사실에만 직접 근거 | canonical 글 URL, 신원·시각 확인 |
| `technical` | 방법·기능·인과 주장이 맞나 | `S2` 발견 신호 | 논문, 코드, 시스템/모델 카드, 표준 등 1차 자료 |
| `performance` | 어떤 조건에서 얼마나 나아졌나 | `S2` 발견 신호 | 원 benchmark, 데이터·버전·하드웨어·비교군·분산/오차 |

예를 들어 “Model A를 공개했고 benchmark B에서 20% 향상했다”는 글은 다음처럼 쪼갠다.

1. `speech-act`: 해당 계정이 그 문장을 게시했다. X URL은 이 사실만 지지한다.
2. `technical`: Model A가 공개되었다. 공식 릴리스 노트·저장소·모델 카드로 확인한다.
3. `performance`: B에서 20% 향상했다. benchmark 정의, baseline, 데이터 오염, 실행 설정,
   반복 횟수와 독립 평가를 확인하기 전에는 기사 본문의 확정 표현으로 쓰지 않는다.

인용 글도 같은 원칙을 적용한다. 인용한 사람의 평가는 별도 `speech-act`이고, 인용된
원문의 기술 주장은 다시 1차 자료를 찾아야 한다. “연구자가 말했다”를 “기술적으로
입증됐다”로 축약하지 않는다.

각 claim 레코드는 최소한 아래 필드를 갖는다.

```yaml
claim_id: <stable id>
signal_id: x:<post_id>
claim_kind: speech-act | technical | performance
claim_text_ko: <원자적 문장>
source_class: S2
evidence_scope: speech-only | discovery-only
primary_source_urls: []
verification_state: unverified | primary-found | corroborated | contradicted
limitations: []
```

`speech-act`는 `evidence_scope: speech-only`, 기술·성능 claim은 최초에
`discovery-only`다. 외부 1차 자료를 확인하면 그 자료를 별도 source로 등록하며 X의
source class 자체를 올리지 않는다.

## 4. triage에서 출고까지

1. **발견:** 등록된 active 계정의 글에서 AI edition 전문 태그와 외부 원문 링크를
   찾는다. engagement 수치는 사용하지 않는다.
2. **관계 복원:** thread, quoted post, 외부 링크를 빠짐없이 기록하고 서로 다른 작성자의
   claim을 분리한다.
3. **원문 승격:** 논문·코드·시스템 카드·모델 카드·릴리스 노트·표준·benchmark로
   이동한다. 링크가 없으면 제목·저자·artifact 이름으로 찾되 추측 링크는 만들지 않는다.
4. **검증:** AI 편집 강령의 source/evidence rubric으로 근거 등급과 한계를 기록한다.
   벤더 소속 인물의 주장은 이해상충을 표시하고 독립 자료를 우선 추가한다.
5. **결정:** 1차 자료 부재, 조건 누락, 중복, 낮은 중요도면 `hold` 또는 `no-publish`로
   남긴다. X 신호만으로 심층 기사 출고 게이트를 통과할 수 없다.

우선순위는 전문 적합성, 변화의 새로움, 영향 범위, 1차 artifact 도달 가능성,
서로 다른 출처의 교차 확인 가능성으로 정한다. “바이럴”은 뉴스 가치나 진실성의 대리
변수가 아니다.

## 5. 재검증·추가·제외 절차

정기 검증 주기는 90일이며, 소속 변경·handle 변경·장기 무응답·삭제 정황을 발견하면
즉시 event-driven 검증을 시작한다.

### 재검증 체크리스트

1. 공식 고용주·학술기관 페이지 또는 당사자가 관리하는 최신 프로필에서 실명,
   조직, 역할을 확인한다. 검색 결과 요약만으로 확정하지 않는다.
2. X canonical URL과 handle 연결을 확인한다. rename이면 이전 URL·handle을 지우지
   않고 `renamed` 이력을 추가한다.
3. 최근 180일의 원문 기술 글을 확인할 수 있으면 `recent`, 없으면 `quiet`, 접근 제한이면
   `unverified`로 기록한다. 재게시·답글만으로 활동을 부풀리지 않는다.
4. 퇴사만 확인되고 새 소속을 확인하지 못하면 `departed`로 두고 수집을 보류한다.
   새 역할을 추정하지 않는다.
5. 삭제·정지·휴면 계정도 행을 삭제하지 않는다. 상태, 확인일, 근거, 대체 handle 여부를
   `change_log`에 남긴다.

90일이 지난 계정은 자동으로 `verification_due`로 간주해 신규 수집을 보류한다. 자동
삭제나 자동 대체는 하지 않는다.

### 후보 변경 기록

후보 추가·제외·보류는 레지스트리 `change_log`에 아래 정보를 append한다.

```yaml
- changed_at: "YYYY-MM-DD"
  action: candidate-added | candidate-held | candidate-excluded | role-updated | handle-renamed
  account_ids: [<id>]
  reason_ko: <전문 공백, 중복, 휴면, 신원 불명확 등 구체적 이유>
  evidence_urls: [<확인 가능한 URL>]
  reviewer: <사람 또는 승인 주체>
```

추가 후보는 현재 조직·역할과 handle을 두 개의 독립 필드로 확인하고, 필수 전문 영역의
공백을 메우거나 기존 신호를 실질적으로 교차 검증해야 한다. 제외는 팔로워 감소나
비우호적 견해가 아니라 신원 불명확, 지속적 무관 신호, 중복, 삭제, 재검증 실패처럼
관찰 가능한 이유를 요구한다. 모든 변경은 원 기록을 보존하며 편집자 승인 후 적용한다.

## 6. no-publish 예시

- 유명 연구자가 “새 모델이 최고”라고 썼지만 model card와 benchmark 설정이 없다:
  `no-publish — performance claim primary evidence missing`.
- 긴 thread가 논문을 링크했으나 실험은 단일 seed·비공개 데이터이고 비교군 버전이
  다르다: `hold — reproducibility and comparison conditions unresolved`.
- 여러 계정이 같은 보도자료를 재게시했다: 독립 확인 여러 건으로 세지 않고 하나의
  벤더 신호로 병합한 뒤 새 기술 변화가 없으면 `no-publish — duplicate promotion`.

이 결정들은 “발행하지 못한 실패”가 아니라 강령에 따른 편집 산출물이며, 신호 URL,
검토한 1차 자료, 미충족 게이트와 재검토 조건을 함께 남긴다.
