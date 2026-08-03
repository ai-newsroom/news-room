# 일일 순차 발행 후 회고 턴

`prompts/conductor-role.md`와 `docs/12-continuous-improvement-loop.md`를 먼저 읽고 그대로
따라라. 이 턴은 읽기 전용 회고이며 구현 턴이 아니다.

## 절차

1. `Asia/Seoul`의 오늘 날짜를 확인한다. `git fetch origin main` 뒤 로컬 working tree가 아니라
   `origin/main`에서 `content/YYYY-MM-DD/article.md`와 선택적인
   `content/ai/YYYY-MM-DD/article.md`를 찾는다.
2. 시사판 원격 파일이 없거나 공개 `/news/YYYY-MM-DD/` URL이 HTTP 200과 기대 제목을
   만족하지 않으면 어떤 상태도 바꾸지 말고 `NO_PUBLICATION`으로 끝낸다. AI판은 원격 파일이
   있을 때만 `/ai/YYYY-MM-DD/`의 발행 ID와 공개 상태를 추가로 검증한다.
3. 다음을 필요한 만큼 읽는다.
   - 원격 시사판 article.md, debate.md, draft.md, prompt.md, run.md
   - 원격에 AI판이 있으면 article.md, evidence.json, release.json
   - `newsroom/charter.md`, `newsroom/style-exemplar.md`, `newsroom/CLAUDE.md`
   - `docs/04-article-format.md`, `docs/07-retrospectives.md`
   - 관련 Git 및 실행 증거
4. 형식 취향보다 반복 가능한 시스템 결함을 찾는다. 특히 다음을 확인한다.
   - 강령 또는 기사 불변 요소 위반
   - 초고에서 최종본으로 제거되지 않은 반복적 문체·구조 문제
   - 출처·근거·시간 감각·중복 주제·발행 실패 문제
   - 프롬프트나 절차의 충돌 때문에 생긴 문제
   - 이전 capability 실험의 지표와 새 회귀
   - 발행 전용 checkout의 clean/fast-forward/finalization 경계 위반
5. 현재 proposed/ready/running/blocked 항목을 읽고 같은 날짜·근거·수정 범위의 중복을 찾는다.
6. 실행 가치가 분명한 문제가 없거나 이미 추적 중이면 어떤 proposal도 만들지 말고
   `NO_PROPOSAL`로 끝낸다.
7. 문제가 있다면 가장 중요한 한 건만 capability proposal로 만든다.

## proposal 계약

`.coco-agents/conductor-loop.json`의 `conductor_session_id`를 `--session`에 사용한다.
제목은 `[회고 YYYY-MM-DD] <구체적인 문제>` 형식으로 한다. 설명에는 근거 파일과 관찰,
영향 범위, 제외 범위, 기대 가치를 쓴다.

반드시 다음을 모두 제공한다.

- `--kind capability`
- capability area
- 반증 가능한 hypothesis
- 해당 판의 이후 발행 3회에서 확인할 수치 또는 명확한 rubric인 measure
- 정확한 rollback plan
- 최소 두 개의 observable acceptance criterion
- 올바른 risk

위험도는 다음처럼 보수적으로 정한다.

- low: 공개 결과를 바꾸지 않는 문서, 테스트, 읽기 전용 진단 도구만
- medium: 강령 해설, 페르소나, prompt, workflow, 발행 코드, 사이트 동작
- high: 공개 기사 정정·재발행, deploy, schedule, credential, 원격 시스템

medium 항목이 저장소 변경을 요구한다면 설명에 다음을 명시한다.

`Integration: 편집자 승인과 독립 검토 통과 뒤 승인된 경로만 commit/push.`

회고 턴에서 `inbox approve`, `inbox dispatch`, 파일 수정, commit, push, publish, deploy,
routine 변경을 실행하지 마라. 마지막 응답에는 읽은 발행일, 핵심 근거, proposal 생성 여부와
생성했다면 item id만 간결하게 남겨라.
