# AI edition X 공식 API 수집 계약

> 상태: mock/dry-run 전용. X 개발자 계정, credential, credit를 만들거나 사용하지 않는다.
>
> 확인일: 2026-07-20. 가격·접근 등급·정책은 live 승인 직전에 공식 문서와 Developer
> Console에서 다시 확인한다.

이 디렉터리는 [`x-accounts.yaml`](../../sources/x-accounts.yaml)의 작은 watchlist를
무단 scraping이나 browser automation 없이 수집하기 위한 최소 계약과 fixture를 둔다.
X 글은 계속 `S2` 발견 신호이며 이 adapter가 기술 주장의 근거 등급을 올리지는 않는다.

## 1. 공식 경로 비교

| 경로 | 인증·접근 | 범위와 checkpoint | 누락 가능성 | 운영 복잡도와 현재 과금 |
|---|---|---|---|---|
| User Posts timeline `GET /2/users/{id}/tweets` | 승인된 App의 app-only Bearer 또는 user context. 다른 공개 계정 감시에는 owned-read 할인이 적용되지 않는다. | 계정별 최근 3,200개, 페이지당 최대 100개, `since_id`·`pagination_token` 지원. reply를 제외하면 검색 가능 범위가 최근 800개로 줄어드므로 이 계약은 repost만 제외한다. | 3,200개 경계를 넘은 글, polling 사이 삭제·보호·정지, 30분 edit window 안의 이전 응답은 놓칠 수 있다. | 13개 계정을 각각 호출해야 하지만 일간 newsroom에는 가장 단순하고 결정적이다. 반환된 Post resource 기준 과금이다. |
| Recent Search `GET /2/tweets/search/recent` | 승인된 App과 Bearer token. 모든 개발자가 사용할 수 있는 7일 검색 경로다. | 최근 7일, 페이지당 최대 100개, 표준 query 512자, `since_id`·`next_token` 지원. 여러 `from:` 조건을 묶되 길이 한도를 넘으면 고정 shard로 나눈다. | 7일보다 오래 중단되면 복구할 수 없고, 잘못된 query·shard·인덱싱 경계는 누락을 만든다. 검색 결과만으로 삭제 event를 보장하지 않는다. | timeline 누락을 하루 한 번 대조하는 보조 경로로 쓴다. 같은 날 같은 Post의 중복 반환은 X 과금상 일일 dedupe 대상이지만 로컬 예산은 보수적으로 모두 센다. |
| Filtered Stream / Webhook | persistent stream은 app-only Bearer로 pay-per-use에서 1 connection·1,000 rules를 지원한다. webhook delivery는 Enterprise 전용이며 공개 HTTPS endpoint, CRC 검증, 동시 delivery 처리가 필요하다. | rule과 일치하는 글을 near-real-time으로 받는다. 표준 stream은 `since_id` pagination이 없고, Enterprise backfill도 연결 단절 후 최대 5분이며 중복을 보낼 수 있다. | 연결 단절, rule 교체 구간, 5분 초과 장애, 처리 지연에서 누락 가능성이 있다. webhook도 rule 밖 글과 별도 compliance event를 대신하지 않는다. | 일간 발행·13계정 규모에는 상시 연결 및 webhook 운영 비용이 과하다. webhook·redundancy·compliance stream은 Enterprise custom 가격이다. |

근거:

- [User Posts timeline 개요와 3,200개 한도](https://docs.x.com/x-api/posts/timelines/introduction),
  [인증·pagination·edit 동작](https://docs.x.com/x-api/posts/timelines/integrate),
  [User Posts endpoint](https://docs.x.com/x-api/users/get-posts)
- [Recent Search의 7일·100개·query 한도](https://docs.x.com/x-api/posts/search/introduction),
  [Recent Search endpoint의 `since_id`](https://docs.x.com/x-api/posts/search-recent-posts)
- [Filtered Stream 접근 등급·연결·rules](https://docs.x.com/x-api/posts/filtered-stream/introduction),
  [연결 복구와 5분 backfill의 중복](https://docs.x.com/x-api/fundamentals/recovery-and-redundancy),
  [Enterprise webhook 조건](https://docs.x.com/x-api/webhooks/stream/introduction)
- [endpoint별 rate limit](https://docs.x.com/x-api/fundamentals/rate-limits),
  [pagination token과 `since_id` 권고](https://docs.x.com/x-api/fundamentals/pagination)

### 현재 가격 모델

[공식 가격표](https://docs.x.com/x-api/getting-started/pricing)는 선불 credit을 차감하는
pay-per-use 모델이며 2026-07-20 현재 일반 Post read를 **resource당 USD 0.005**로
표시한다. 앱 소유자의 자기 데이터에만 해당하는 owned read는 USD 0.001이므로 watchlist의
다른 계정 timeline 예산에는 적용하지 않는다. [usage 문서](https://docs.x.com/x-api/fundamentals/post-cap)는
pay-per-use 월 Post read 상한을 2,000,000으로 두고, 같은 Post를 같은 날 여러 경로에서
받으면 과금량을 한 번으로 dedupe한다고 설명한다. Enterprise webhook 가격은
[별도 custom 계약](https://docs.x.com/enterprise-api/getting-started/pricing)이다.

가격은 바뀔 수 있고 최종 청구는 Console이 정본이다. 따라서 adapter는 단가를 상수로
숨기지 않고 run config로 받는다. fixture의 `0.005`는 확인일의 snapshot이며 live 전
재확인 실패 시 circuit을 연다.

## 2. 선택한 최소 경로

가설을 검증할 초기 조합은 다음과 같으며 아직 실행 schedule이 아니다.

1. **기본:** 계정별 User Posts timeline을 `since_id`로 polling한다. thread reply를
   보존해야 하므로 repost만 제외한다.
2. **보조:** Recent Search를 watchlist handle의 고정 shard로 하루 한 번 대조한다.
   timeline과 search의 중복은 edit chain root와 Post ID로 제거한다.
3. **보류:** Filtered Stream은 초 단위 lead time이 실제 필요하다는 관찰 전에는 켜지
   않는다. Webhook과 compliance stream은 Enterprise 견적·운영 승인이 별도로 필요하다.

초기 live pilot 후보 주기는 timeline 하루 2회, recent search 하루 1회다. 그러나 실제
주기와 `max_results`는 사용자가 정한 월 비용 상한에서 역산하며, 상한 결정 전에는
fixture 외 호출을 계획하지 않는다.

## 3. adapter interface

[`adapter.py`](adapter.py)는 HTTP client가 아니라 credential 없는 순수 정규화 경계다.

```text
AdapterConfig + Checkpoint + BudgetPolicy
        -> plan_request()       # method/path/query만 반환, header/token 없음
API transport outside adapter  # 향후 승인 시 runtime secret provider가 인증 주입
        -> ingest_fixture()     # page/event를 정규화
        -> events + checkpoint + records + metrics
```

- `FetchRequest`에는 method, path, params만 있고 header·token·secret 필드가 없다.
- credential은 파일, fixture, checkpoint, log, metrics에 저장하지 않는다. live transport가
  생기더라도 runtime secret provider에서 요청 순간에만 주입하고 adapter에는
  `credential_available: bool`만 전달한다.
- 현재 구현에는 network import와 live transport가 없다. 모든 테스트는 고정 JSON을
  메모리에서 처리한다.
- webhook은 push 경로라 `plan_request()` 대상이 아니다. 동일한 ingest event 계약만
  공유한다.

### Checkpoint와 pagination

checkpoint는 `route`, `scope_key`, `since_id`, opaque `pagination_token`, 현재 run의
`high_watermark_id`, `complete`를 가진다.

1. 첫 page는 저장된 `since_id`를 사용한다.
2. `next_token`이 있으면 `since_id`를 올리지 않고 token을 저장한다.
3. 모든 page를 끝낸 경우에만 `since_id`를 이번 run의 가장 큰 Post ID로 원자적으로
   올린다.
4. 예산·429·오류로 멈추면 기존 `since_id`와 다음 `pagination_token`을 남겨 재개한다.
5. token은 opaque 값으로 취급하며 해석하거나 합성하지 않는다.

이 순서로 page 중간 실패가 새 `since_id` 뒤의 오래된 page를 영구히 건너뛰는 일을 막는다.

### Dedupe, edit, delete

- 동일 Post ID가 timeline, search, backfill에 다시 나오면 저장 event를 만들지 않되
  `duplicate_reads`에는 센다.
- edit마다 새 Post ID가 생기므로 `edit_history_tweet_ids[0]`을 canonical ID로 쓰고,
  가장 최신 ID와 전체 version IDs를 보존한다. 더 긴 chain이 오면 `edit` event와
  `supersedes_post_id`를 만든다. 근거는 [Edit Posts](https://docs.x.com/x-api/fundamentals/edit-posts)다.
- delete event나 rehydration의 not-found가 오면 chain의 어느 version ID라도 canonical
  tombstone으로 합치고 저장 text를 즉시 `null`로 만든다. 이미 삭제한 event는 idempotent다.
- standard timeline/search/stream은 완전한 delete feed가 아니다. Enterprise
  [compliance stream](https://docs.x.com/x-api/compliance/streams/introduction)을 쓰지 않는
  pilot은 공개 표시 전 rehydration과 최대 24시간 주기의 저비용 batch lookup을 예산에
  포함해야 한다. 그 절차가 승인되지 않으면 X 본문을 공개 저장·표시하지 않고 ID,
  canonical URL, 최소 triage 메모만 보존한다.

[X Developer Policy](https://docs.x.com/developer-terms/policy)는 저장한 X Content가 X에서
삭제·수정·보호·정지되면 현재 상태에 맞게 삭제 또는 수정하고, X나 계정 소유자의 요청은
가능한 빨리 또는 24시간 안에 반영하도록 요구한다. credential 비공개, 승인 use case
준수, rate limit 비우회도 live hard gate다.

## 4. 비용 예산과 circuit breaker

모든 값은 live 승인 때 명시적으로 입력하며 무제한 기본값은 없다.

| 값 | 역할 |
|---|---|
| `max_calls_per_run` | pagination 폭주와 rate-limit 접근을 막는다. |
| `max_post_reads_per_run` | 한 run에서 반환받을 Post resource의 gross 상한이다. |
| `monthly_post_read_limit` | newsroom 내부 월 read 상한이며 X의 200만 cap보다 작아야 한다. |
| `monthly_cost_limit_usd` | 사용자가 결정하는 월 현금 상한이다. |
| `post_read_unit_cost_usd` | live 직전 공식 가격/Console에서 복사한 단가다. |

요청 전 남은 call·read·cost로 `max_results`를 줄인다. 하나라도 0이면 호출하지 않고
checkpoint를 보존한 채 circuit을 연다. 반환 resource가 계획값을 넘거나 429, credit
부족, 가격 snapshot 만료, checkpoint 불일치가 발생해도 즉시 중단한다. 로컬 비용은
`gross reads × unit cost`로 잡아 X의 일일 dedupe 할인을 미리 가정하지 않는다. Developer
Console에도 같은 월 spending limit을 설정하고 auto-recharge는 별도 승인 없이는 끈다.

호출 수는 현재 read 가격표상 별도 금액이 아니라 rate/운영 예산이지만, metrics에는
post read와 함께 남긴다.

## 5. live 전 사용자 결정 두 가지

다음 결정은 서로 대체할 수 없다.

1. **월 비용 상한:** `monthly_cost_limit_usd`와 Console spending limit의 구체적 금액.
2. **credential 제공:** 승인된 X App credential을 runtime secret provider로 제공할지.

`live_gate()`는 두 결정을 별도 blocker로 반환한다. 비용 상한만 있어도 credential이
없으면 막히고, credential만 있어도 비용 상한이 없으면 막힌다. 둘 다 있기 전에는
mock/dry-run만 허용한다. 이 항목은 계정 생성, token 구매·저장, credit 구매, 유료 호출을
수행하지 않는다.

## 6. fixture와 14일 관찰 instrumentation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 editions/ai/acquisition/x/test_adapter.py
```

고정 fixture는 pagination 중간 checkpoint, `since_id`의 완료 후 갱신, 경로 간 중복,
edit chain, delete tombstone, call budget circuit breaker를 검증한다. 결과 metrics에는
`calls`, `post_reads_gross`, `estimated_cost_usd`, `duplicate_reads`, `duplicate_rate`,
`edits`, `deletes`, `lead_time_seconds`, 표본 `recall`과 circuit 사유가 있다.

fixture 통과는 가설의 설치 검증일 뿐 live 수집 성공이 아니다. 승인된 별도 pilot에서만
14일 동안 사람이 확인한 표본 계정의 기대 Post ID와 비교해 recall, 중복률, gross/Console
post reads, 실제 비용, lead time을 일별 기록한다. 14일이 지나기 전에는 retain 결론을
내리지 않는다.

rollback은 schedule/adapter를 `disabled`로 두고 API 호출을 멈춘 뒤 레지스트리,
fixture, 검증 기록만 보존하고 수동 canonical URL 확인으로 돌아가는 것이다.
