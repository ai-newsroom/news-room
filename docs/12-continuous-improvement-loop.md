# 발행 후 지속 개선 루프

> 상태: 1단계 반자동 운영. 회고와 작업 제안은 자동화하되, 모든 제안의 실행 승격은
> 편집자가 명시적으로 승인한다.

## 목적

강령 7의 "발행하고, 읽고, 개선한다"를 역사적 회고 기록에 머물지 않는 일일 운영
루프로 만든다. 최종적으로 하나의 지속 컨덕터 역할이 발행 결과 확인, 회고,
개선 작업, 다음 발행의 효과 관찰까지 하루 사이클 전체를 소유한다. 각 단계는 별도 턴과
역할 세션으로 나누며 `coco-agents`의 관리 세션, routine, inbox, message를 사용한다.
폐기된 campaign 실행 정책은 되살리지 않는다.

```text
단일 결정적 실행기가 시사판 발행·공개 확인
  -> 같은 checkout에서 AI판 발행·공개 확인
  -> 컨덕터가 원격·공개 증거 확인
  -> 읽기 전용 회고
  -> inbox 개선 제안
  -> 편집자 승인
  -> 작업 세션 구현
  -> 독립 검토
  -> 승인된 범위만 최종 반영
  -> 이후 발행에서 효과 관찰
```

## 역할과 책임

### 발행 파이프라인

결정적 상위 실행기인 `scripts/publish-sequential-daily.sh`가 맡는다. 시사판의
`scripts/publish-daily.sh`를 먼저 실행해 기사와 토론, 초고, 실행 프롬프트, 실행 정보를
`content/YYYY-MM-DD/`에 보존하고 공개 URL을 확인한다. 그 뒤에만
`scripts/publish-ai-daily.sh`를 실행한다. 두 판의 Git 외부 동작은 공통 finalizer가 맡는다.
발행 세션은 자기 결과의 회고나 시스템 변경을 수행하지 않는다.

systemd의 `news-room-daily.timer` 하나만 이 상위 실행기를 시작한다. 기존 별도 AI Codex
automation은 중복 실행을 막기 위해 비활성화한다. 발행기는 전용 clean checkout을 독점하고,
컨덕터와 개선 worker는 별도 checkout을 사용한다.

### 컨덕터 세션

- 최종 운영에서는 오늘의 발행 작업을 시작하거나 발행 세션에 배정한다.
- 발행 종료, Git 반영, 사이트 배포 증거를 확인한 뒤 다음 단계로 넘어간다.
- 최신 시사판 발행 결과와 관련 아티팩트를 읽는다.
- 회고에서 근거가 있는 개선 후보를 하루 최대 한 건 제안한다.
- 제안을 직접 승인하거나 구현하지 않는다.
- 편집자가 `ready`로 승격한 작업만 작업 세션에 배정한다.
- 작업 결과를 곧바로 완료로 처리하지 않고 독립 검토를 요청한다.
- 검토 결과와 원래 승인 범위를 확인한 뒤 수정, 최종 반영, 완료를 결정한다.

### 작업 세션

- 배정받은 inbox 항목 하나만 구현한다.
- 발행 전용 checkout이 아닌 개선 작업 checkout에서만 파일을 수정한다.
- 시작 전 기존 worktree 변경을 보존한다.
- 구현과 검증 결과를 메시지로 보고한다.
- 첫 결과 전에는 commit, push, publish, deploy를 하지 않는다.
- 독립 검토 통과 뒤 컨덕터가 보낸 최종 반영 요청에만 승인된 경로를 commit/push한다.

### 검토 세션

- 원래 항목의 완료 조건, 실제 diff, 테스트 증거를 읽기 전용으로 검사한다.
- 각 완료 조건을 `verified`, `unmet`, `blocked`로 판정한다.
- 파일 수정, commit, push, publish, deploy를 하지 않는다.

### 편집자

- 모든 session-origin 제안을 실행 전에 확인한다.
- `inbox approve`는 항목에 적힌 범위의 구현을 허가한다.
- 중위험 항목의 설명에 최종 Git 반영이 명시돼 있다면, 독립 검토 통과 뒤 승인된
  경로만 한 번 commit/push하는 것까지 허가한다.
- 공개 기사 수정, 재발행, 배포 설정, 스케줄, 비밀정보, 강령의 가치 판단은 별도의
  구체적인 사람 지시 없이는 허가된 것으로 보지 않는다.

## 일일 순서

기본 시각은 `Asia/Seoul` 기준이다.

1. 07:00: 단일 timer가 시사판 → AI판 순차 발행과 각 공개 URL 검증 실행
2. 09:30: `news-room-post-publish-retrospective` routine이 원격·공개 증거를 확인한 뒤 컨덕터를 깨움
3. 10:00: `news-room-inbox-reconcile` routine이 이미 승인된 작업을 최대 한 건 배정
4. 결과 메시지 도착 시: 컨덕터가 검토 세션과 작업 세션을 메시지로 조정

09:30까지 오늘 시사판의 원격 commit과 공개 URL 결과가 없으면 회고는 저장소와 외부 상태를 바꾸지 않고
종료한다. routine에는 backfill이 없으므로 운영자가 원인을 확인한 뒤 필요하면
`run-now`로 다시 실행한다.

## 운영 경계

- systemd timer 하나가 결정적 순차 발행기를 시작한다.
- 발행 checkout은 시작 전 clean 상태와 `origin/main` fast-forward 동기화를 강제한다.
- 시사판 push와 공개 검증이 끝나기 전에는 AI판을 시작하지 않는다.
- 모델 턴은 commit, push, deploy를 직접 수행하지 않는다. 공통 finalizer만 허용된 경로를 반영한다.
- 발행·배포 증거가 확인된 뒤 별도 회고 턴을 연다.
- 한 번의 conductor turn이 기사 작성, 자기 평가, 자기 수정까지 모두 수행하지 않는다.

## 회고 입력

회고는 기본적으로 다음 자료만 읽는다.

- `content/YYYY-MM-DD/article.md`
- `content/YYYY-MM-DD/debate.md`
- `content/YYYY-MM-DD/draft.md`
- `content/YYYY-MM-DD/prompt.md`
- `content/YYYY-MM-DD/run.md`
- `newsroom/charter.md`
- `newsroom/style-exemplar.md`
- `newsroom/CLAUDE.md`
- `docs/04-article-format.md`
- `docs/07-retrospectives.md`
- 관련 Git diff와 실행·테스트 기록

회고는 기사 취향을 매일 흔드는 문체 투표가 아니다. 반복되는 문제, 강령 위반,
발행 실패, 검증 가능한 구조적 결함처럼 시스템 수준에서 다시 나타날 가능성이 있는
문제만 작업 후보로 만든다.

## 제안 계약

실행 가치가 있는 문제가 하나 있을 때만 `inbox propose`로 capability 항목을 만든다.
제안은 다음을 모두 포함한다.

- 문제와 발행 아티팩트 근거
- 영향받는 범위와 제외 범위
- 검증 가능한 완료 조건
- 가설
- 이후 3회 시사판 발행에서 확인할 성공 지표
- 정확한 rollback 방법
- 위험도

같은 날짜와 같은 근거에서 중복 제안을 만들지 않는다. 실행할 문제가 없으면
`NO_PROPOSAL`로 끝낸다. 회고 문서, 프롬프트, 기사, Git, 스케줄 또는 외부 시스템은
회고 턴에서 수정하지 않는다.

## 위험도

| 위험도 | 예시 | 1단계 처리 |
| --- | --- | --- |
| low | 공개 결과를 바꾸지 않는 문서, 테스트, 읽기 전용 진단 도구 | 편집자 승인 후 실행 |
| medium | 강령 해설, 페르소나, 프롬프트, 워크플로, 발행 코드, 사이트 동작 | 편집자 승인 + 독립 검토 |
| high | 공개 기사 정정·재발행, 배포·스케줄 변경, 비밀정보·외부 시스템 | 자동 최종 반영 금지 |

1단계에서는 low도 자동 승격하지 않는다. 충분한 운영 증거가 쌓인 뒤에만 별도 결정으로
저위험 자동 승격을 검토한다.

## 작업과 검토 프로토콜

1. 컨덕터는 `ready` 항목을 하나 선택해 `inbox dispatch`로 작업 세션에 배정한다.
2. 작업 세션은 구현·테스트 후 `result` 또는 `blocked` 메시지를 보낸다.
3. 컨덕터는 첫 `result`를 곧바로 accept하지 않고 검토 세션에 같은 task id로 검토를 요청한다.
4. `changes_requested`이면 컨덕터가 원래 작업 세션에 수정 요청을 보낸다.
5. `passed`이고 승인 범위에 Git 최종 반영이 포함되면 컨덕터가 작업 세션에 좁은
   finalization 요청을 보낸다.
6. 컨덕터는 최종 commit, push 결과, clean/preserved worktree를 확인한 뒤 해당 결과
   메시지로 `inbox accept`한다.
7. high-risk 외부 동작은 완료 조건이 충족돼도 사람의 별도 지시 전까지 대기한다.

## 효과 관찰

현재 capability experiment에는 여러 발행을 아우르는 first-class 관찰 상태와 자동
retain/rollback 판정이 없다. 따라서 제안의 `measure`와 `rollback`을 정본으로 삼고,
이후 회고가 지난 실험과 연결된 후속 항목을 만들 수 있게 한다.

기본 관찰 기간은 이후 시사판 3회다.

- retain: 지표가 충족되고 새 회귀가 없음
- adjust: 방향은 맞지만 좁은 수정이 필요함
- rollback: 같은 결함이 지속되거나 새 강령·품질 회귀가 생김

## 운영 명령

```bash
coco-agents routine list --workspace /home/pys/repositories/news-room
coco-agents routine runs news-room-post-publish-retrospective --workspace /home/pys/repositories/news-room
coco-agents inbox list --status proposed --workspace /home/pys/repositories/news-room
coco-agents inbox show <item-id> --workspace /home/pys/repositories/news-room
coco-agents inbox approve <item-id> --workspace /home/pys/repositories/news-room
coco-agents routine run-now news-room-inbox-reconcile --workspace /home/pys/repositories/news-room
```

배포별 세션 ID는 공개 저장소에 커밋하지 않고 ignored 상태인
`.coco-agents/conductor-loop.json`에 둔다.

상주 control plane의 user service 정본은
`ops/systemd/coco-agents-news-room.service`다. 설치할 때 사용자 systemd 디렉터리에
복사한 뒤 daemon reload와 enable을 수행한다.
