# news-room

하루에 단 하나의 뉴스를, 깊게 다루는 AI 편집국.

지금의 뉴스는 자극적이고 클릭에 종속되어 있다. news-room은 그 반대를 지향한다 —
그날 가장 중요한 하나의 소식을 골라, 서로 다른 철학적 스탠스를 가진 AI 에이전트들이
토론을 거쳐 깊이 있는 기사 한 편을 만든다. HBO 드라마 〈The Newsroom〉에서 영감을 받았다.

**이 매체는 렌즈를 숨기지 않는다.** 편집 강령, 모든 에이전트의 페르소나(프롬프트),
취재 소스 목록, 그리고 매일의 토론 전문까지 — 전부 이 레포에 공개되어 있다.
독자는 기사가 어떤 시각으로, 어떤 과정을 거쳐 만들어졌는지 직접 확인할 수 있다.

## 구조

```
docs/        구상·설계 문서 (비전, 강령, 편집국, 기사 형태, 아키텍처, 소스)
newsroom/    편집국 실행 워크스페이스 — 강령·페르소나·소스의 정본 (전부 공개)
workflows/   coco-agents 워크플로 정의 (매일의 편집 회의 절차)
scripts/     발행 래퍼 스크립트 (cron이 호출)
content/     발행된 기사 아카이브 (날짜별: 기사 + 토론 전문 + 객원 프롬프트 + 초고 + 실행 프롬프트 + 실행 정보)
site/        Astro 정적 사이트 → GitHub Pages
```

## 동작 방식

```
[홈서버 단일 timer, 매일 07:00 Asia/Seoul]
  └→ scripts/publish-sequential-daily.sh (발행 전용 clean checkout)
       ├→ 시사판 생성·검증 → 공통 finalizer → push → 공개 URL 확인
       └→ 시사판 공개 확인 뒤 AI판 생성·검증
            └→ 공통 finalizer → push → 공개 URL 확인

[별도 개선 checkout]
  └→ 승인된 capability 작업만 구현·독립 검토·finalization

[시사판 지속 개선, 매일 발행 뒤]
  └→ coco-agents routine이 지속 개선 컨덕터 세션을 깨움
       ├→ 최신 시사판 결과를 읽기 전용으로 회고
       ├→ 실행 가치가 있는 개선을 inbox proposal로 최대 한 건 기록
       ├→ 편집자가 승인한 항목만 별도 작업 세션에 배정
       └→ 독립 검토와 제한된 finalization 뒤 완료 처리
```

발행 checkout은 순차 발행기만 수정한다. 컨덕터와 개선 worker는 별도 checkout을 사용하며,
검토되지 않은 변경을 발행 checkout에 남길 수 없다. 컨덕터는 같은 턴에서 기사 작성·자기
평가·자기 수정을 모두 수행하지 않는다.

`prompts/daily-newsroom-single-codex.md`와
`prompts/daily-newsroom-single-claude.md`는 시사판 서버 배치용 진입 프롬프트다.
이 프롬프트는 `workflows/daily-newsroom.json`을 읽고 시사판 절차를 단일 세션 안에서
수행하며, AI판의 `content/ai/`나 편집 계약을 사용하지 않는다.
`workflows/daily-newsroom.json`은 여러 AgentTask로 편집국을 모델링한 정본 절차이며,
coco-agents 자체 개발과 multi-agent workflow 실험은 로컬 개발 머신에서 수행한다.

발행 후 지속 개선의 운영 계약과 승인 경계는
[`docs/12-continuous-improvement-loop.md`](docs/12-continuous-improvement-loop.md)에 있다.

## 편집국 사람들

| 필명 | 역할 |
|------|------|
| 파수꾼 | 취재기자 — 스탠스 없이 사실과 여론 지형만 수집 |
| 느티나무 | 논설위원 (중도 보수) |
| 물길 | 논설위원 (중도 진보) |
| 등에 | 철학 — 소크라테스의 쇠파리 |
| 청진기 | 심리 — 사건에 대한 사람들의 반응을 진찰 |
| 씨줄 | 사회 — 개인의 선택처럼 보이는 것에서 구조를 본다 |
| 저울 | 경제 — 모든 선택의 보이지 않는 반대편 접시 |
| 등대 | 데스크 — 편집 강령의 구현체 |
| (객원) | 매일 주제에 맞춰 소집되는 도메인 전문가 |

각 페르소나의 전문은 [`newsroom/personas/`](newsroom/personas/)에, 편집 강령은
[`newsroom/charter.md`](newsroom/charter.md)에 있다.
