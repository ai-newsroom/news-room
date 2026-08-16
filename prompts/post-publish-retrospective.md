# 발행 후 회고 턴

`prompts/conductor-role.md`와 `docs/12-continuous-improvement-loop.md`를 먼저 읽고 그대로
따라라. 이 턴은 읽기 전용 회고이며 구현 턴이 아니다.

## 절차

1. `Asia/Seoul`의 오늘 날짜를 확인한다. `git fetch origin main` 뒤 로컬 working tree가 아니라
   `origin/main`에서 `content/YYYY-MM-DD/article.md`, 선택적인 정규 AI·EDA 기사와 함께
   `content/ai/YYYY-MM-DD--*/article.md` 형태의 편집자 요청 AI 특별판을 모두 찾는다. 정규
   AI 기사가 없으면 `decisions/ai/YYYY-MM-DD/no-publish.json`의 명시적 미발행 결정도 찾는다.
2. 오늘 발행된 후보의 공개 상태를 각각 검증한다. 시사판은 `/news/YYYY-MM-DD/`, AI·EDA판은
   release JSON의 routes에 기록된 URL에서 HTTP 200, 기대 제목과 발행 ID를 확인한다.
   특별판은 `/ai/YYYY-MM-DD/<slug>/`이고 정규판의 날짜 URL을 대신하지 않는다. 공개 검증에
   성공한 AI `no-publish` 결정은 `/ai/`에서 `오늘 AI판은 휴간입니다`, 상태 날짜, 휴간 기록을
   확인하고 `/ai/YYYY-MM-DD/` 기사 route가 없음을 확인한다. 이는 기사가 아니라 운영 상태다.
   공개 검증에 성공한 기사와 AI 상태 기록이 하나도 없을 때만 어떤 상태도 바꾸지 않고
   `NO_PUBLICATION`으로 끝낸다.
3. 아래 tracked 자료는 local working tree가 아니라 `git show origin/main:<path>`로 필요한 만큼
   읽는다. Conductor workspace의 오래되거나 미커밋된 파일을 발행 정본으로 사용하지 않는다.
   - 원격 시사판 article.md, debate.md, draft.md, prompt.md, run.md
   - 정규 AI판 `content/ai/YYYY-MM-DD/article.md`와
     `decisions/ai/YYYY-MM-DD/{evidence,release}.json`
   - 정규 AI판이 미발행이면 `decisions/ai/YYYY-MM-DD/no-publish.json`
   - 특별 AI판 `content/ai/YYYY-MM-DD--<slug>/article.md`와
     `decisions/ai/YYYY-MM-DD--<slug>/{evidence,release}.json`
   - EDA판 `content/eda/YYYY-MM-DD/article.md`와
     `decisions/eda/YYYY-MM-DD/{evidence,release}.json`
   - `editions/eda/editorial/article-prompt.md`, `editions/eda/editorial/style-contract.md`
   - `docs/14-eda-auto-publishing.md`
   - `newsroom/charter.md`, `newsroom/style-exemplar.md`, `newsroom/CLAUDE.md`
   - `docs/04-article-format.md`, `docs/07-retrospectives.md`
   - 관련 Git 및 실행 증거
4. 형식 취향보다 반복 가능한 시스템 결함을 찾는다. 특히 다음을 확인한다.
   - 강령 또는 기사 불변 요소 위반
   - 초고에서 최종본으로 제거되지 않은 반복적 문체·구조 문제
   - 출처·근거·시간 감각·중복 주제·발행 실패 문제
   - EDA 벤더 주장의 과장, 원문 두 개의 역할 중복, 전문 용어 설명 누락
   - 주요 EDA 벤더·학회·논문 신호의 반복적인 coverage 누락
   - 프롬프트나 절차의 충돌 때문에 생긴 문제
   - 이전 capability 실험의 지표와 새 회귀
   - 발행 전용 checkout의 clean/fast-forward/finalization 경계 위반
   - 명시적 AI `no-publish`, 공개 휴간 상태, 실행 실패를 서로 잘못 표시한 문제
   - 비보류 done 항목의 prompt, validator, workflow, 발행 코드, runtime config, site, 발행 docs
     변경이 `origin/main`에 반영되지 않아 새 발행이 이전 contract로 승인된 문제
5. 현재 proposed/ready/running/blocked 항목을 읽고 같은 날짜·근거·수정 범위의 중복을 찾는다.
6. 실행 가치가 분명한 문제가 없거나 이미 추적 중이면 어떤 proposal도 만들지 말고
   `NO_PROPOSAL`로 끝낸다.
7. 문제가 있다면 가장 중요한 한 건만 capability proposal로 만든다.

## proposal 계약

`.coco-agents/conductor-loop.json`의 `conductor_session_id`를 `--session`에 사용한다.
제목은 `[회고 <publication-id>] <구체적인 문제>` 형식으로 한다. 설명에는 근거 파일과 관찰,
영향 범위, 제외 범위, 기대 가치를 쓴다.

반드시 다음을 모두 제공한다.

- `--kind capability`
- capability area
- 반증 가능한 hypothesis
- 문제가 발견된 해당 판의 이후 발행 3회에서 확인할 수치 또는 명확한 rubric인 measure
- 정확한 rollback plan
- 최소 두 개의 observable acceptance criterion
- 올바른 risk

위험도는 다음처럼 보수적으로 정한다.

- low: 공개 결과를 바꾸지 않는 문서, 테스트, 읽기 전용 진단 도구만
- medium: 강령 해설, 페르소나, prompt, workflow, 발행 코드, 사이트 동작
- high: 공개 기사 정정·재발행, deploy, schedule, credential, 원격 시스템

medium 항목이 저장소 변경을 요구한다면 설명에 다음을 명시한다.

`Integration: 편집자 승인과 독립 검토 통과 뒤 승인된 경로만 commit/push.`

회고에서 새 발행의 release metadata가 비보류 done capability 항목보다 오래된 contract를
사용한 사실을 발견하면, worker result와 review가 passed였다는 이유만으로 통합 성공으로
보지 않는다. 이는 finalization/reconciliation system defect이며 proposal에는 landed,
editor-deferred, no-publication-effect 중 하나를 accept 전에 기록하게 하는 완료 조건을 넣는다.

회고 턴에서 `inbox approve`, `inbox dispatch`, 파일 수정, commit, push, publish, deploy,
routine 변경을 실행하지 마라. 마지막 응답에는 읽은 발행일, 핵심 근거, proposal 생성 여부와
생성했다면 item id만 간결하게 남겨라.
