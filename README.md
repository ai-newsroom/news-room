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
content/     발행된 기사 아카이브 (날짜별: 기사 + 토론 전문 + 객원 프롬프트)
site/        Astro 정적 사이트 → GitHub Pages
```

## 동작 방식

```
[홈서버 cron, 매일 1회]
  └→ scripts/publish-daily.sh
       └→ coco-agents workflow run workflows/daily-newsroom-single-claude.json --workspace newsroom/
            ① 단일 Claude Code 세션 실행
            ② 뉴스 지형 수집, 주제 선정, 토론 artifacts 작성
            ③ 기사 초고와 최종 기사 작성
       └→ content/YYYY-MM-DD/ 에 기사·토론 전문 저장 (실패 시 휴간 공지)
       └→ git commit & push → GitHub Actions가 사이트 빌드·배포
```

`workflows/daily-newsroom.json`은 여러 AgentTask로 편집국을 모델링한 개발/실험용
워크플로다. Proxmox 서버 배치에서는 사양과 운영 안정성을 고려해
`daily-newsroom-single-claude.json`을 기본값으로 사용한다. coco-agents 자체 개발과
multi-agent workflow 실험은 로컬 개발 머신에서 수행한다.

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
