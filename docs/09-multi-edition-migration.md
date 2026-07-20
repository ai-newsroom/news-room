# 다중 edition 구조와 무중단 마이그레이션 계획

> 상태: 구현 전 설계 계약
>
> 범위: 시사판·AI판·EDA판이 공통 실행·콘텐츠·사이트·발행 도구를 공유하되,
> 편집 설정과 쓰기 경계를 분리하는 최소 구조를 정한다. 이 문서 자체는 현재 배치,
> URL, 콘텐츠, 스케줄을 바꾸지 않는다.

관련 편집 계약은 [AI·EDA 기술판 독립 편집 프로필](08-ai-eda-editorial-profiles.md)에
있다. 이 문서는 그 계약을 실행 구조로 옮기는 순서만 다룬다.

## 1. 먼저 고정할 불변 조건

1. 현재 `content/<legacy-id>/article.md`는 이동하거나 다시 쓰지 않는다.
2. 현재 공개 주소 `/news/<legacy-id>/`와 GitHub Pages의 `/news-room` base를 유지한다.
   특히 `/news/2026-06-11/` 같은 기존 주소에 redirect를 요구하지 않는다.
   비교 실험 content는 `publication: experiment`로 보존하되 홈과 정적 기사 route에서
   제외한다. 단계 0 legacy manifest는 2026-06-16까지의 URL anchor를 고정하고,
   이후 정상 일일 발행은 날짜형 ID와 published frontmatter 계약으로 회귀 검증한다.
3. 시사판의 기존 cron과 `scripts/publish-daily.sh`는 새 runner의 시사판 회귀 검증이
   끝나기 전까지 유일한 운영 배치다. 전환 중 두 runner를 같은 날짜에 함께 쓰지 않는다.
4. AI·EDA는 누락된 설정을 `newsroom/`에서 찾지 않는다. 기술 공통 계약 외에 서로의
   prompt, role, source, validator도 fallback으로 사용하지 않는다.
5. `no-publish`는 정상적인 편집 결정이지만 공개 기사나 휴간 공지가 아니다. 실행 실패와
   구분해 공개 content tree 밖에 둔다.
6. 새 공통 runner의 기본 모드는 `prepare-only`다. 사람의 명시적 승인 전에는 content
   승격, `git add`, commit, push, deploy를 하지 않는다.
7. migration은 각 단계가 독립적으로 되돌릴 수 있어야 한다. 기존 파일 이동이나 일괄
   frontmatter 변환은 이 계획의 필수 단계가 아니다.

## 2. 현재 구조와 결합 지점

현재 실행 경로는 다음과 같다.

```text
external cron
  -> scripts/publish-daily.sh
     -> prompts/daily-newsroom-single-claude.md
     -> workflows/daily-newsroom.json + newsroom/**
     -> newsroom/artifacts/**
     -> content/YYYY-MM-DD/**
     -> git add/commit/push

site/src/content.config.ts
  -> content/*/article.md
  -> site/src/pages/news/[id].astro
  -> /news/<content-directory>/
```

따라서 다음은 설정만 추가한다고 분리되지 않는다.

- `publish-daily.sh`가 workspace, prompt, artifacts, 날짜형 output, 휴간 처리, git 작업을
  모두 소유한다.
- `content.config.ts`, 홈, `/news/[id]`가 depth 1 디렉터리를 모두 시사판 기사로 본다.
- workflow와 prompt가 `newsroom/` 및 시사판 역할을 직접 가리킨다.
- 시사판의 `holiday: true`와 기술판의 `decision: no-publish`는 의미가 다르다.

새 구조는 이 결합을 한 번에 뜯지 않고 설정 해석, 실행, 사이트, 운영 배치를 차례로
분리한다.

## 3. 목표 디렉터리

아래는 migration 완료 시의 최소 목표다. 기존 경로는 호환 계층으로 남긴다.

```text
editions/
  _schema/
    edition.schema.json          # 모든 edition 설정의 구조 검증
  _shared/
    technical-common/            # AI·EDA가 명시적으로만 상속하는 rubric/template
  current-affairs/
    edition.yaml
    prompts/
    validators/
  ai/
    edition.yaml                 # 기존 sources/, acquisition/, investigation/과 공존
    prompts/
    validators/
  eda/
    edition.yaml
    prompts/
    validators/

engine/
  edition/                       # 설정 load·경로 검증·phase 조립
  content/                       # publish candidate/no-publish artifact 조립
  site/                          # 정규화된 content manifest 생성
  publish/                       # 승인된 candidate만 승격; git/배포는 별도 adapter

scripts/
  run-edition.sh                 # 공통 진입점: --edition, --mode, --run-id
  publish-daily.sh               # 시사판 전환 완료 전까지 유지하는 legacy 진입점

var/runs/<run-id>/<edition>/     # 실행 중간물; gitignore 대상, 다른 edition과 쓰기 공유 금지
decisions/<edition>/<date>/      # 추적 가능한 no-publish 결정; 사이트 loader 대상 아님

content/
  YYYY-MM-DD/                    # 시사판 legacy 및 앞으로도 같은 URL을 쓰는 일일 발행
  ai/<publication-id>/           # AI 공개 기사만
  eda/<publication-id>/          # EDA 공개 기사만

tests/
  edition/                       # schema, isolation, routing fixture
  fixtures/legacy-routes.json    # 보존할 운영 URL과 title snapshot
  fixtures/excluded-content.json # 공개하지 않을 실험·내부 content 목록
```

`engine/`은 공통 phase와 산출물 계약만 가진다. 수집 대상, prompt, 편집 역할, 선정 기준,
검증 규칙은 `editions/<id>/`가 가진다. `editions/ai/`에 이미 있는 X registry와 adapter는
옮기지 않고 AI 설정에서 명시적으로 참조한다.

## 4. edition 설정 계약

### 4.1 최소 스키마

모든 값은 저장소 root 기준 상대 경로다. 누락 값을 다른 edition에서 보충하지 않는다.

```yaml
schema_version: 1
id: ai                         # ^[a-z][a-z0-9-]*$
profile_class: technical       # current-affairs | technical
inherits:
  - technical-common          # current-affairs는 []

paths:
  workspace: editions/ai/workspace
  prompt: editions/ai/prompts/run.md
  workflow: editions/ai/workflow.yaml
  charter: editions/ai/editorial/charter.md
  roles: editions/ai/editorial/roles.yaml
  sources: editions/ai/sources
  validators: editions/ai/validators
  run_root: var/runs
  decision_root: decisions/ai
  content_root: content/ai

schedule:
  enabled: false
  managed_by: none             # none | external-cron | engine
  timezone: Asia/Seoul
  cadence: on-demand           # cron이면 표현식을 edition별로 명시

decision:
  allowed:
    - publish-candidate
    - no-publish
  failure_is_no_publish: false

site:
  route_prefix: /ai
  include_in_legacy_home: false

release:
  mode: prepare-only
  requires_human_approval: true
  git_write: false
  deploy: false

validation:
  common:
    - schema
    - path-isolation
    - content-contract
  edition:
    - editions/ai/validators/release-gates.yaml

forbidden_fallbacks:
  - newsroom/charter.md
  - newsroom/personas
  - newsroom/sources.md
  - editions/eda
```

시사판의 1단계 설정은 파일을 옮기지 않고 현재 경로를 가리킨다.

| 키 | `current-affairs` | `ai` | `eda` |
|---|---|---|---|
| `profile_class` | `current-affairs` | `technical` | `technical` |
| `inherits` | `[]` | `[technical-common]` | `[technical-common]` |
| workspace | `newsroom` | `editions/ai/workspace` | `editions/eda/workspace` |
| prompt | 현재 `prompts/daily-newsroom-single-claude.md` | AI 전용 | EDA 전용 |
| content root | `content`의 depth 1 legacy 경로 | `content/ai` | `content/eda` |
| route prefix | `/news` | `/ai` | `/eda` |
| 최초 schedule | 현재 external cron만 `enabled` | `false` | `false` |
| 최초 release mode | legacy wrapper 유지 | `prepare-only` | `prepare-only` |

### 4.2 loader가 거부해야 할 상태

- 모르는 key, 지원하지 않는 `schema_version`, 중복 edition id 또는 route prefix
- 절대 경로, `..`, root 밖을 가리키는 symlink, 다른 edition의 쓰기 root
- `technical` profile이 `newsroom/` 또는 다른 edition의 editorial 경로를 참조하는 설정
- `schedule.enabled: true`인데 manager, timezone, cadence가 없는 설정
- `requires_human_approval: false`, `git_write: true`, `deploy: true`인 AI·EDA 초기 설정
- content root와 decision root가 같거나, no-publish artifact가 site manifest에 들어가는 설정

환경 변수는 credential 값만 주입할 수 있다. edition id, source path, route, gate, release
mode는 실행 때 환경 변수로 덮어쓸 수 없게 해 실행 기록과 실제 판단이 달라지는 일을 막는다.

## 5. 공통 실행 계약과 쓰기 경계

공통 진입점은 다음 형태로 제한한다.

```text
scripts/run-edition.sh \
  --edition ai \
  --mode dry-run|prepare \
  --run-id <caller-supplied-unique-id> \
  [--fixture <repo-relative-path>]
```

runner는 `resolve -> acquire -> analyze -> decide -> validate -> stage` phase를 실행하고
각 phase에 edition 설정과 그 edition의 run directory만 전달한다.

| 결과 | 저장 위치 | 공개·git 동작 |
|---|---|---|
| 실행 실패 | `var/runs/.../run.json`의 failed 상태 | 기사·no-publish로 변환하지 않음 |
| `no-publish` | `decisions/<edition>/<date>/...` 후보 | 사이트 제외, 자동 git 없음 |
| `publish-candidate` | `var/runs/.../staged-content/` | 사람 승인 전 `content/` 복사 금지 |
| 승인된 publish | config가 정한 content root | 별도 publish adapter가 승인 증거를 확인 |

한 run은 자기 `var/runs/<run-id>/<edition>`만 쓸 수 있다. 공통 engine은 다른 edition의
workspace나 decisions를 검색하지 않는다. 동일 publication id 재실행은 임시 디렉터리에
완전한 candidate를 만든 뒤 승인 단계에서만 원자적으로 승격하며, 기존 공개 디렉터리에
부분 파일을 섞지 않는다.

스케줄러는 edition마다 공통 runner를 별도로 호출할 뿐 판단을 공유하지 않는다. AI 또는
EDA에 가치 있는 후보가 없으면 정상 `no-publish`로 끝나며 시사판 휴간 기사나 다른
edition 기사로 대체하지 않는다.

## 6. content와 edition 라우팅

### 6.1 정규화 키

사이트 입력 manifest의 주 키는 `(edition, publication_id)`다.

```json
{
  "edition": "ai",
  "publication_id": "2026-07-20-example",
  "source_directory": "content/ai/2026-07-20-example",
  "route": "/ai/2026-07-20-example/",
  "decision": "publish"
}
```

frontmatter, source directory, 설정의 content root가 가리키는 edition이 다르면 build를
실패시킨다. 기술판은 `edition`과 `decision: publish`를 필수로 한다.

### 6.2 legacy 호환 규칙

기존 문서를 일괄 수정하지 않기 위해 compatibility loader만 다음 예외를 가진다.

1. `content/YYYY-MM-DD/article.md`처럼 root 바로 아래의 정확한 날짜 디렉터리는
   frontmatter에 edition이 없으면 `current-affairs`로 해석한다.
2. 날짜 형식이 아닌 기존 공개 id는 migration 시작 때 만든
   `tests/fixtures/legacy-routes.json` allowlist에 있을 때만 시사판으로 해석한다.
   현재의 `2026-06-11-prep` 같은 주소는 이 방식으로 보존한다.
3. allowlist에 없고 `content/` root에 놓인 suffix 실험 디렉터리는 공개 목록에서 제외하고
   검증을 실패시킨다. 이름이 날짜로 시작한다는 이유만으로 공개하지 않는다.
4. 새 시사판 기사는 기존 배치 호환을 위해 계속 `content/YYYY-MM-DD/`에 쓸 수 있다.
   AI·EDA는 반드시 자기 하위 root에 쓴다.

라우팅 결과는 다음과 같다.

| source | canonical route | migration 처리 |
|---|---|---|
| `content/2026-06-16/article.md` | `/news/2026-06-16/` | 현재와 byte-for-byte 동일한 URL |
| allowlist의 `content/2026-06-11-prep/article.md` | `/news/2026-06-11-prep/` | 기존 URL 유지 |
| `content/ai/<id>/article.md` | `/ai/<id>/` | 새 route, AI index만 포함 |
| `content/eda/<id>/article.md` | `/eda/<id>/` | 새 route, EDA index만 포함 |
| `decisions/**` | 없음 | build input에서 제외 |

기존 `/` 홈은 시사판 feed만 보여 주는 현재 동작을 먼저 보존한다. AI·EDA landing과 통합
feed는 별도 후속이며, migration을 위해 통합 feed를 만들 필요는 없다.

## 7. 단계적 migration

각 단계는 앞 단계의 검증을 통과한 뒤 별도 통합 단위로 진행한다.

### 단계 0 — 기준선 고정

- 현재 build가 만드는 모든 `/news/*/` route, title, home link를 먼저 inventory한다.
- inventory에서 production content는 `legacy-routes.json`, 비교 실험 content는
  `excluded-content.json`으로 분류한다. 전자는 URL 보존 allowlist이고 후자는 현재 노출을
  발견하는 회귀 fixture이지 호환 대상으로 승격되지 않는다.
- 현재 cron 명령, timezone, 실행 주기, wrapper exit 상태를 기록한다.
- 운영 코드와 content는 바꾸지 않는다.

**통과 조건:** 보존할 운영 URL, 제거할 실험 route, 배치 진입점이 서로 섞이지 않고
기계적으로 비교 가능하다.

### 단계 1 — 설정 schema와 resolver

- 세 `edition.yaml`, JSON Schema, read-only resolver만 추가한다.
- 시사판 설정은 현재 `newsroom/`, prompt, workflow를 그대로 가리킨다.
- AI·EDA schedule과 release는 disabled/prepare-only다.
- resolver는 최종 경로와 phase plan을 JSON으로 출력하지만 workflow를 실행하지 않는다.

**통과 조건:** 세 설정이 독립적으로 통과하고 forbidden fallback fixture는 모두 실패한다.

### 단계 2 — fixture 기반 공통 runner

- network와 LLM이 없는 고정 candidate bundle로 공통 phase를 실행한다.
- 시사·AI·EDA 각각 publish-candidate 또는 no-publish를 만들되 content나 git을 쓰지 않는다.
- 같은 fixture를 넣어도 edition별 gate가 독립적으로 다른 결정을 낼 수 있음을 확인한다.

**통과 조건:** path isolation, 결정 구분, 실패 fail-closed, 재실행 idempotency가 통과한다.

### 단계 3 — 사이트의 병렬 content 읽기

- 현재 `articles` collection과 `/news/[id]`를 유지한 채 AI·EDA collection과 route를 추가한다.
- legacy manifest snapshot을 새 build와 비교한다.
- no-publish와 allowlist 밖 실험 content가 route에 나타나지 않음을 확인한다.

**통과 조건:** `legacy-routes.json`의 route·title·home link 차이 0,
`excluded-content.json`의 route 0, 새 fixture route만 기대한 prefix에 생긴다.

### 단계 4 — 시사판 shadow와 단일 전환

- 현재 배치는 계속 legacy wrapper를 사용한다.
- 격리된 fixture에서 legacy 조립 결과와 공통 runner의 정규화 결과를 비교한다.
- 성공·세션 실패·prompt 누락·재실행 fixture가 통과한 뒤, external cron 명령만 한 번에
  current-affairs edition 진입점으로 바꾼다. 같은 시각에 두 schedule을 두지 않는다.
- 기존 wrapper는 한 rollback window 동안 호출되지 않는 상태로 보존한다.

**통과 조건:** 한 scheduler만 enabled이고 기존 날짜 output 및 URL 계약이 유지된다.

### 단계 5 — AI, 그 다음 EDA 수동 pilot

- AI를 먼저 `dry-run`, 다음 `prepare`로 실행해 미발행 결정과 candidate를 검토한다.
- EDA도 같은 순서를 별도로 밟는다. EDA fixture와 gate가 없으면 시작하지 않는다.
- schedule이나 실제 publish는 edition별 사람 승인과 별도 inbox가 있을 때만 켠다.

**통과 조건:** 양 edition이 시사판 파일을 읽지 않고 자기 설정만으로 결정 artifact를 만든다.

## 8. 회귀 테스트 matrix

| 영역 | fixture/명령 | 필수 관찰값 |
|---|---|---|
| 문서·shell 정적 검사 | `git diff --check`, `bash -n scripts/publish-daily.sh` | whitespace 오류 0, legacy wrapper 구문 유지 |
| 현재 사이트 | `npm --prefix site run build` | build 성공 |
| legacy URL snapshot | build output과 `tests/fixtures/legacy-routes.json` 비교 | 보존 대상 route, title, home href 차이 0 |
| 실험 content 제외 | build output과 `tests/fixtures/excluded-content.json` 비교 | 제외 대상 route와 home link 0 |
| config schema | 세 config + invalid fixture validator | valid 3개 통과, unknown key·누락·경로 탈출 실패 |
| edition isolation | 다른 edition 경로를 넣은 fixture | resolve 단계에서 실패하고 파일 쓰기 0 |
| technical fallback | AI·EDA에서 `newsroom/**`를 참조하는 fixture | 명시적 실패 |
| routing | current/AI/EDA/no-publish/실험 fixture | `/news`, `/ai`, `/eda`, route 없음으로 정확히 분리 |
| route collision | 같은 edition/id 및 중복 prefix fixture | build 전 실패 |
| 결정 의미 | no change, vendor-only, runner failure fixture | no-publish, no-publish, failed로 서로 다르게 기록 |
| current batch 조립 | 임시 저장소 + fake `coco-agents` 성공/실패 | 운영 git·network 없이 기존 content 계약 비교 |
| 재실행 | 같은 run id와 publication id 두 번 실행 | 부분 overwrite 없이 같은 결과 또는 명시적 충돌 |
| schedule | 세 설정을 합친 검사 | current 하나만 enabled, AI·EDA disabled |
| release gate | 승인 없음 fixture | content·git·deploy 쓰기 0 |
| worktree 보존 | 실행 전후 `git status --porcelain=v1 -uall` 비교 | 허용된 test output 외 기존 변경 차이 0 |

LLM 결과의 문장 일치는 회귀 기준으로 삼지 않는다. 공통 runner는 고정 fixture에서 phase,
입력·출력 schema, 결정 코드, 경로, 쓰기 집합을 비교한다. 실제 취재 품질 평가는 edition별
별도 평가다.

## 9. rollback 경계

| 단계 | 바뀌는 권위 | rollback |
|---|---|---|
| 0 | test fixture뿐 | fixture 제거; 운영 영향 없음 |
| 1 | config resolver뿐 | resolver 호출 제거; legacy 배치·사이트 그대로 |
| 2 | fixture runner뿐 | runner 비활성화; config와 평가 기록만 보존 |
| 3 | site loader와 새 route | AI·EDA loader/route만 feature flag로 끄고 기존 `articles`, `/news/[id]`, 홈으로 복귀 |
| 4 | 시사판 cron 진입점 | cron을 보존된 legacy wrapper 한 곳으로 되돌림; 새 runner 동시 실행 금지 |
| 5 | edition별 수동 pilot | 해당 edition schedule/release를 disabled로 바꾸고 decisions·fixture만 보존 |

rollback은 공개 content 삭제나 git history rewrite를 요구해서는 안 된다. 이미 승인되어 공개된
기사는 기존 URL에 남기고, 잘못된 새 edition index만 비활성화한다. credential은 config나 run
artifact에 저장하지 않으므로 adapter 비활성화만으로 외부 호출을 멈출 수 있어야 한다.

## 10. 현재 dirty worktree와 충돌 지도

이 설계 시점의 변경은 모두 기존 작업으로 간주하며 이동·수정·제외하지 않는다.

| 현재 경로 | 향후 충돌 지점 | 이번 항목의 처리 |
|---|---|---|
| `README.md`, `docs/04-article-format.md`, `docs/05-architecture.md` | 현재 발행·렌더링 설명과 최종 다중 edition 문서 연결 | 수정하지 않음. 실제 단계 1~4 구현 뒤 사실에 맞춰 마지막에 정렬 |
| `scripts/publish-daily.sh` | workspace/prompt/output/git 결합을 공통 runner로 분리할 핵심 경계 | 수정하지 않음. 단계 4 전까지 운영 정본으로 취급 |
| `site/src/pages/news/[id].astro` | legacy artifact 렌더링과 새 edition route 분리 | 수정하지 않음. 현재 변경을 먼저 fixture로 고정한 뒤 단계 3 수행 |
| `content/2026-06-16/article.md` | legacy schema·렌더링 회귀 입력 | 수정하지 않음. 사실 퇴고와 migration을 별도 통합 단위로 유지 |
| `newsroom/AGENTS.md`, `newsroom/CLAUDE.md`, `newsroom/personas/lighthouse.md` | 시사판 profile 경로와 문체 계약 | 이동·복사하지 않음. 단계 1 설정이 현 위치를 참조 |
| `content/2026-06-14-codex-high-test/`, `content/2026-06-14-codex-high-workflow-test/` | 현재 glob에 잡히는 비교 실험 content | 삭제·이동하지 않음. 단계 0 allowlist 밖 fixture로 분류하고 production route 제외를 검증 |
| `docs/08-ai-eda-editorial-profiles.md` | 설정 schema의 편집 계약 원본 | 수정하지 않고 참조만 함 |
| `editions/ai/**`의 X registry·adapter·promotion 작업 | 목표 `editions/ai/`와 같은 디렉터리 | 덮어쓰거나 재구성하지 않음. 단계 1에서 새 설정 파일만 충돌 검사 후 추가 |

이 때문에 이번 설계는 `docs/09-multi-edition-migration.md` 한 파일만 추가한다. README나
기존 architecture 문서를 지금 맞추면 아직 구현되지 않은 route와 runner를 현재 동작처럼
보이게 하고, 기존 dirty 변경과 섞이므로 보류한다.

## 11. 완료 판정과 남은 objective gap

이 항목의 설계 완료 조건은 다음과 같다.

- 목표 디렉터리와 required config key가 정해져 있다.
- 시사판 URL·배치를 유지하는 compatibility loader와 단일 scheduler 전환 순서가 있다.
- edition별 route, content, prompt, schedule, validator, 쓰기 root가 분리돼 있다.
- 각 단계에 실행 가능한 test와 rollback 경계가 있다.
- 현재 dirty 경로와 직접 충돌하는 후속 변경이 식별돼 있다.

그러나 장기 objective는 아직 완료가 아니다. schema/resolver와 공통 runner가 구현되지
않았고, EDA fixture·결정 경로와 시사판 회귀 snapshot도 아직 없다. 다음 구현 단위는 단계
0과 1만 묶어 **운영 동작을 바꾸지 않는 schema·read-only resolver·legacy route fixture**를
만드는 것이다.
