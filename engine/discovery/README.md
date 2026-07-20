# 수집 채널 발견 품질 계측 계약

> 상태: 고정 fixture로 설치를 검증한 공통 capability. 아직 실제 수집 schedule이나
> channel에 연결하지 않았으며 baseline을 관찰했다는 뜻이 아니다.

이 계층은 X, 공식 블로그, 논문 feed, 저장소 release, 표준·학회 페이지가 발견한 후보를
같은 형식으로 기록한다. 채널별 transport metric은 그대로 둔다. 예를 들어 X adapter의
`calls`, gross post reads, checkpoint, edit/delete 기록은 X adapter가 소유하고, 이 계층은
그 결과가 편집 조사에서 어떤 outcome으로 이어졌는지만 공통 집계한다.

## 1. run record와 metric 정의

한 conductor run은 edition과 시작·종료 시각, 실행한 channel 목록을 가진다. channel에는
`channel_id`, 유형, 설정 snapshot을 가리키는 `configuration_id`, collection 상태,
실행 시간, 직접 비용과 후보 목록이 필요하다. 지원 유형은 `x`, `official-blog`,
`paper-feed`, `repository-release`, `standards-conference`, `other`다.

후보마다 다음 추적 필드를 조사 결과와 연결한다.

```json
{
  "candidate_id": "x:101",
  "canonical_candidate_id": "topic:alpha",
  "source_published_at": "2026-07-20T09:55:00Z",
  "discovered_at": "2026-07-20T10:00:00Z",
  "duplicate_of": null,
  "primary_evidence_promoted": true,
  "editorial_disposition": "publish-candidate",
  "false_positive": false,
  "false_positive_reason": null
}
```

- `duplicate_of`는 channel 내부뿐 아니라 공통 canonicalization에서 먼저 발견한 관측을
  가리킨다. 중복 관측은 편집 outcome을 다시 주장할 수 없다.
- `primary_evidence_promoted`는 발견 신호 밖의 기술 1차 근거가 연결됐다는 뜻이다.
  AI판 X 글 자체나 홍보 발표만으로는 `true`가 아니다. 현재 P/E/R 계약에서 적어도
  공개 `P1` 또는 `P2` evidence가 claim에 맞게 연결된 경우에 해당한다.
- `publish-candidate` 기여는 해당 후보가 최종 candidate 판단에 추적 연결됐다는 뜻이지
  실제 publish나 인과 효과를 뜻하지 않는다.
- `false_positive`는 edition 주제와 무관하거나 알려진 중복·홍보 재포장처럼 수집 단계의
  목표에 맞지 않았다고 사람이 검토한 후보다. 근거 부족이나 가치 있는 변화 없음으로
  생긴 `no-publish`를 자동으로 오탐 처리하지 않는다. 미검토는 `null`이다.

[`metrics.py`](metrics.py)의 `build_run_record`는 각 channel에 다음 값을 만든다.

| metric | 분자 / 분모 또는 단위 |
|---|---|
| 후보 수 | channel이 반환한 raw 후보 관측 수 |
| 중복률 | `duplicate_of`가 있는 관측 / raw 후보 수 |
| 1차 근거 승격률 | `primary_evidence_promoted`인 고유 후보 / 고유 후보 수 |
| publish-candidate 기여율 | publish-candidate에 연결된 고유 후보 / 고유 후보 수 |
| 오탐률 | `false_positive: true` / `true` 또는 `false`로 검토가 끝난 고유 후보 |
| 발견 지연 | `discovered_at - source_published_at`의 count/min/median/p95/max |
| 실행 시간 | channel adapter가 측정해 전달한 초 |
| 직접 비용 | 해당 run에서 실제 또는 명시적 단가로 계산해 전달한 USD |

분모나 시간 원자료가 없으면 0으로 꾸미지 않고 `null`과 coverage count 0을 남긴다. 비용은
추정치라면 channel 원시 기록에 추정 근거가 있어야 하며, 이 공통 계층이 단가를 가정하지
않는다. 인증 header, token, API key, credential field는 계약에서 거부한다.

## 2. 저장과 실패 격리

공통 runner가 연결될 때 호출 순서는 다음과 같다.

```text
collection 완료
  -> outcome payload 조립
  -> build_run_record
  -> write_json_record(var/runs/<run-id>/<edition>/discovery/)
```

`collect_with_optional_metrics`는 collector를 먼저 완료한다. 이후 payload 검증이나 sink가
실패해도 이미 얻은 collection 객체와 `instrumentation.status: failed`를 반환하고 예외를
수집 실패로 올리지 않는다. 오류 메시지 본문은 기록하지 않고 오류 type만 남긴다.

`enabled: false`면 payload builder와 sink를 전혀 호출하지 않으므로 기존 collector 동작으로
즉시 돌아간다. `write_json_record`는 run id별 JSON을 원자적으로 만들며 같은 내용의 재실행은
허용하고 다른 내용으로 기존 run 기록을 덮어쓰지 않는다. 이 hook은 network, browser,
credential, content, publish, git, deploy 기능이 없다.

계측 실패는 수집을 멈추지 않지만 보이지 않게 성공 처리하지도 않는다. conductor run은
hook 상태를 별도로 집계해 계측 누락률을 확인해야 한다. 누락된 run을 성과 분모에서 임의로
제외한 채 개선을 주장해서는 안 된다.

## 3. 관찰 창과 retrospective

기본 실험 가설은 다음과 같다.

> channel별 yield·정확도·지연·비용을 같은 형식으로 측정하면 conductor가 낮은 가치
> 수집을 줄이고 부족한 전문 영역을 더 잘 발견할 수 있다.

그러나 fixture 통과는 이 가설의 증거가 아니다. `evaluate_retrospective`는 channel 하나와
설정 snapshot 하나씩을 비교하며 다음 조건을 강제한다.

1. baseline의 `window_id`와 `configuration_id` 및 원 run 기록이 있어야 한다.
2. baseline과 experiment 각각 **최소 10 run과 14일을 모두** 채워야 한다. 이는
   “10회 또는 14일 중 늦은 시점”을 구현한 것으로, 10회를 빨리 채웠다고 끝내지 않는다.
3. 비교 전에 승격률 최소 개선폭, 오탐률 허용 퇴행, 고유 후보당 비용 상한, 발견 지연
   허용 퇴행을 policy로 고정한다.
4. 창이 부족하거나 baseline이 없으면 `comparison_ready: false`, `decision: null`,
   `improvement_claim: null`을 반환한다.
5. 창이 성숙하면 다음 셋 중 하나와 이유를 기록한다.

| 결정 | 조건 |
|---|---|
| `retain` | 1차 근거 승격률 개선폭을 넘고 오탐·비용·지연 guardrail을 모두 통과 |
| `adjust` | guardrail은 통과했지만 개선폭이 기준보다 작음 |
| `rollback` | 오탐·비용·지연 가운데 하나라도 guardrail 실패 |

`retain`도 측정한 channel·설정·기간 안의 비교만 지지한다. 전체 뉴스룸의 발견 품질이
개선됐다고 확대하지 않는다. 성숙한 회고에는 다음 bounded capability experiment를 반드시
붙인다. `capability`, 가설, 좁은 scope, 관찰 가능한 success measure, rollback plan,
최대 run 수와 최대 일수를 필수로 해 무기한 자동 변경을 막는다. 판정기는 proposal을
검증하고 보존할 뿐 channel을 자동 추가·조정·중단하지 않는다.

## 4. rollback과 다음 관찰

- rollback은 edition 설정에서 계측 hook과 자동 회고 호출만 `enabled: false`로 만든다.
- 원래 collector, checkpoint, source registry와 원시 run 기록은 보존한다.
- live 연결 전에 common runner가 계측 성공·실패·disabled 상태를 run manifest에 남기는
  후속이 필요하다.
- 그 뒤 최소 10 run과 14일을 모두 채운 baseline을 수집하고, 승인된 단일 channel 변경만
  같은 길이로 관찰해 retain/adjust/rollback을 결정한다.

현재 turn은 fixture 기반 설치와 실패 격리까지만 검증한다. 미래 관찰 창이 지났거나
가설이 입증됐다고 주장하지 않는다.

## 5. 검증

```bash
PYTHONDONTWRITEBYTECODE=1 python3 engine/discovery/test_metrics.py
```

고정 fixture에는 X, 공식 블로그, 논문 feed, 저장소 release, 표준·학회 channel과 0건
channel, 중복, no-publish와 오탐 구분, 직접 비용·지연이 있다. retrospective fixture는
baseline 부재, 10 run이지만 14일 미만인 창, retain, adjust, rollback과 bounded proposal을
검증한다.
