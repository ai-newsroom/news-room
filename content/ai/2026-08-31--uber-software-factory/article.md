---
edition: ai
decision: publish-candidate
title: "Uber 소프트웨어 팩토리 공개 - 3,600개가 넘는 AI 스킬을 관리형 에이전트로 운영"
date: 2026-08-31
publication_kind: special
subject: "Running a Software Factory Efficiently at Uber Scale, Uber Engineering, published 2026-08-27"
summary: "Uber는 3,600개가 넘는 AI 스킬을 개인용 코딩 도구 모음이 아니라 관리형 에이전트가 정해진 개발 작업을 완료하는 소프트웨어 생산 시스템으로 운영하는 방식을 공개했습니다. 도구 지연 로딩, code-mode, 작업별 모델 선택, AI Context Graph를 결합하고 token 수가 아니라 병합된 PR·review·alert처럼 끝난 작업 한 건당 드는 완료 비용으로 지출을 관리하는 것이 핵심입니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Uber Engineering 글과 Uber 소속 발표자의 공개 영상은 이 시스템을 만든 주체의 1차 자료입니다. 기사 작성에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

Uber Engineering은 8월 27일 `Running a Software Factory Efficiently at Uber Scale`을 공개했습니다. Uber가 말하는 소프트웨어 팩토리는 개발자가 질문할 때만 답하는 코딩 도구가 아닙니다. 관리형 에이전트가 정해진 절차에 따라 코드 리뷰와 CI 복구, PR 작성·검증, 장애 분류, 유지보수를 수행하는 실행 시스템입니다. Uber 내부 집계로는 이 시스템 전반에 3,600개가 넘는 에이전트 스킬이 있고, 하루 실행 횟수는 3만 회를 넘습니다.

이번 공개가 중요한 이유는 비용을 비싼 모델 하나의 가격으로만 보지 않았기 때문입니다. Uber는 실행 과정에서 모델이 필요 없는 상태 확인, 긴 중간 결과, 사용하지 않을 도구 설명, 잘못된 사내 정보 탐색을 줄였습니다. 또 병합된 PR이나 리뷰 한 건처럼 실제 결과에 든 완료 비용을 관리 단위로 삼았습니다. AI 코딩 도구를 넓게 쓰면서도 품질과 지출을 함께 관리하려면 무엇을 설계해야 하는지 보여 줍니다.

특히 도구가 많고 코드와 운영 문서가 여러 시스템에 흩어진 팀이 볼 만합니다. 도구 지연 로딩은 필요한 도구만 실행 시점에 불러오고, AI Context Graph는 서비스·팀·장애·PR·문서·배포 기록 사이의 관계를 먼저 찾아 줍니다. 두 장치를 함께 사용하면 모델을 바꾸지 않고도 한 세션에서 반복되는 request와 token을 줄일 수 있습니다.

## 개인용 세션부터 작업별 관리형 에이전트까지 네 층으로 나눴습니다

Uber가 공개한 그림은 에이전트 세션을 네 층으로 나눕니다. 맨 아래 단계인 raw session에서는 개발자가 노트북에서 프롬프트와 문맥을 직접 줍니다. 그 위 단계에서는 같은 환경에서 검토된 스킬을 불러 씁니다. 이어 Uber cloud에서 범용 에이전트가 어떤 스킬이든 실행하는 층과, 작업 경계와 평가 기준이 정해진 전문 에이전트 층이 놓입니다.

가장 위의 관리형 실행 층에서는 입력과 완료 조건이 더 좁아집니다. `Minion`은 개발 의도를 PR로 만들고, `uReview`는 PR을 코드 리뷰하며, `Conan AI`는 경보를 받아 원인을 분류합니다. 공개 글은 실패한 CI의 자동 복구, 화면 비교를 포함한 E2E PR 검증, 들어온 bug의 원인 분석, 정기 코드 유지보수도 같은 범주의 작업으로 제시합니다. 이 작업들은 Uber cloud에서 실행되며, 사람이 검토하거나 필요할 때 개입하는 경로도 포함합니다.

이 구분은 자동완성 기능을 여러 개 모았다는 뜻과 다릅니다. 위층으로 갈수록 시스템이 작업의 입력, 실행 환경, 허용된 도구, 성공 기준, 사용할 모델을 정합니다. 개발자는 turn마다 다음 동작을 계속 지시하는 대신 결과를 검토하고 예외를 처리합니다.

Uber는 PR의 70% 이상이 local 또는 cloud agent에 `attributed`됐다고 적었습니다. 이는 Uber가 사용한 귀속 표현입니다. AI가 코드의 70%를 작성했다거나 PR의 70%를 자율 생성했다는 뜻은 아닙니다. attribution 산정 방법도 공개되지 않았으므로 이 수치는 사용 확산을 보여 주는 내부 지표로만 읽어야 합니다.

## 전체 비용을 사용자 수부터 token 가격까지 여섯 항으로 나눕니다

Uber의 비용식은 다음 여섯 항을 곱합니다.

`전체 비용 = 사용자 수 × 사용자당 session 수 × session당 turn 수 × turn당 request 수 × request당 token 수 × token당 가격`

사용자와 session은 얼마나 많은 사람이 얼마나 자주 쓰는지를 나타냅니다. turn은 에이전트가 결과를 보고 다음 행동을 정하는 단계입니다. request는 그 단계에서 실제 모델을 다시 부른 횟수입니다. request마다 대화 이력, 프로젝트 문맥, 도구 결과가 다시 들어갈 수 있으므로 앞 단계에서 생긴 낭비가 뒤의 token 비용까지 키웁니다.

따라서 비용을 줄인다고 해서 사용을 제한해야 하는 것은 아닙니다. Uber의 내부 집계에서 2026년 2월부터 8월 중순까지 주간 사용자는 7배, 주간 agentic request는 9.4배 늘었습니다. Uber는 같은 기간 전체 AI 지출이 4월 이후 비교적 안정됐다고 설명하지만 총액은 공개하지 않았습니다.

사용량과 모델이 동시에 바뀌는 영향을 구분하기 위해 Uber는 모델을 고정한 단위 비용도 비교했습니다. request 1,000건당 비용은 정점보다 약 34%, session당 비용은 6월 정점보다 52% 낮아졌다는 내부 측정입니다. session 자료는 5월 말부터 시작합니다. 원본 trace와 작업 구성, 모델·vendor 조합이 공개되지 않아 독립 재현은 할 수 없고, 이 두 비율을 다른 조직의 예상 절감률로 옮길 수도 없습니다.

## 필요한 도구 설명만 실행할 때 불러옵니다

도구가 많아지면 모델이 답을 만들기 전부터 프롬프트가 커집니다. Uber가 비교한 표준 MCP 운용에서는 설치한 도구의 schema, 즉 이름과 입출력 설명을 세션 문맥에 미리 넣습니다. 설치 도구가 100개를 넘는 예에서는 이 설명만 약 5만~7만 token이었고, 이후 turn마다 다시 전송됐습니다.

Uber는 이 부담을 세 단계로 줄였습니다.

1. 모델이 shell command를 내리면 CLI가 실행 시점에 필요한 도구를 MCP gateway에서 찾아 호출합니다. 이를 **CLI tool resolution**이라고 합니다. Uber 내부 gateway의 1,000개가 넘는 MCP 도구를 CLI command로 보이게 해 전체 schema를 세션에 넣지 않습니다.
2. 모델이 목록을 검색한 뒤 필요한 도구 정의만 불러오는 방식은 **Tool search**입니다. 도구 수가 늘어도 모든 정의를 처음부터 싣지 않는 지연 로딩입니다.
3. 여러 tool call과 반복 제어를 한 script로 묶는 방식은 **Code-mode**입니다. 모델은 script를 만들고 요약 결과를 받으며, polling과 큰 중간 응답은 subprocess 안에서 처리됩니다.

세 번째 단계는 요청과 응답이 자주 오가는 프로토콜에서 차이가 큽니다. 예를 들어 데이터웨어하우스 질의 한 번에도 요청, 상태 polling 2~5회, 결과 가져오기가 이어질 수 있습니다. 표준 흐름에서는 모델이 매번 다음 call을 만들고 응답을 문맥에 쌓습니다. code-mode에서는 Python loop가 이 과정을 진행하고 필요한 요약만 모델에 돌려줍니다. 이 설명은 Uber가 공개한 실행 방식에 관한 것이며, 이름이 비슷한 다른 제품도 같은 방식으로 구현했다는 뜻은 아닙니다.

Uber가 같은 Claude Code session에서 측정했다고 밝힌 SQL 비교는 다음과 같습니다.

| 질의 | 일반 tool-use token | code-mode token | 절감률 |
|---|---:|---:|---:|
| `SELECT 1`, 1행 | 903 | 402 | 55% |
| `COUNT(*)`, 1행 | 954 | 403 | 58% |
| `GROUP BY LIMIT 20`, 20행 | 1,600 | 457 | 71% |
| `SHOW COLUMNS`, 175행 | 2,200 | 900 | 59% |
| 넓은 table에서 `SELECT *`, 50행 | 1,431,594 | 900 | 약 100% |

마지막 행은 code-mode 밖에서 매우 큰 응답이 모델 문맥으로 들어간 극단 사례이므로 평균값처럼 해석해서는 안 됩니다. 다만 결과가 작은 첫 두 질의에서도 55%와 58%가 줄었습니다. 이는 schema를 처음 불러오는 작업, 반복 polling, 단계별 판단 자체가 비용을 만든다는 Uber의 설명과 맞습니다. 이 표 역시 내부 단일 session 측정이며 공개 script나 raw log는 없습니다.

## 작업마다 모델의 비용과 품질을 함께 평가합니다

관리형 에이전트는 작업 범위가 좁아서 실제 업무를 기준으로 benchmark를 만들 수 있습니다. Uber는 `uReview`를 평가할 때 이미 bug가 알려진 실제 PR을 쉬움·보통·어려움으로 나눴습니다. 그 bug를 찾는 정밀도(precision)·재현율(recall)·F1뿐 아니라 리뷰당 비용, latency, timeout, 불필요한 지적도 함께 측정했다고 설명합니다.

공개한 산점도에는 이름을 가린 비공개 frontier 모델과 가중치를 공개한 모델을 포함한 10개 설정이 있습니다. Uber가 운영에 고른 설정은 리뷰당 0.47달러와 F1 0.50으로 표시됐습니다. 더 싼 공개 가중치 설정은 0.28달러와 F1 0.48이었고, 0.06달러 설정의 F1은 0.31이었습니다. Uber는 점 하나만 보고 승자를 고르지 않습니다. 더 싸면서 품질도 높은 다른 선택지가 없는 경계인 파레토 최적선(Pareto frontier)에서 요구 품질과 안정성에 맞는 설정을 택합니다.

하나의 모델 계열이 모든 일을 맡지도 않습니다. Uber의 대화형 환경에서는 주 모델이 작업 분해와 결과 평가를 담당합니다. 입력과 출력이 분명한 하위 agent는 더 저렴하고 약한 모델을 기본값으로 쓰며, 필요하면 사람이 설정을 바꿀 수 있습니다. 이 역할 분리는 작은 모델이 언제나 충분하다는 결론이 아닙니다. 작업별 benchmark가 허용하는 곳에서만 싼 모델을 쓴다는 뜻입니다.

`uReview` 평가에 쓴 dataset, 사람 리뷰어의 판정 절차, 표본 수, 모델·vendor 이름과 전체 분포는 공개되지 않았습니다. 따라서 산점도는 Uber가 어떤 측정축으로 모델을 배분하는지는 보여 주지만, 어느 모델이 일반적인 코드 리뷰에서 가장 낫다는 독립 benchmark는 아닙니다.

## AI Context Graph로 사내 정보 탐색 turn을 줄입니다

큰 코드베이스에서는 에이전트가 코드를 쓰는 시간보다 필요한 사내 정보를 찾는 시간이 더 길 수 있습니다. 어느 서비스가 어느 팀 소유인지, 장애와 배포가 어떤 PR과 연결되는지부터 확인해야 하기 때문입니다. Uber의 AI Context Graph는 이런 관계를 하나의 graph로 연결합니다. 공개 글에 따르면 개체를 나타내는 2,400만 node와 그 관계를 나타내는 8,000만 edge로 구성되며, edge 유형은 117개입니다. 서비스·개발팀·장애 기록·PR·설계 문서·배포·dataset·과거 query 사용 기록 등 30개가 넘는 내부 시스템에서 정보를 가져옵니다.

모델이 자연어로 질문하면 graph에서 관련 개체와 경로를 받습니다. 서로 다른 문서 저장소와 데이터 시스템을 차례로 뒤지는 turn을 줄일 수 있습니다. 모델을 바꾸지 않고 더 정확한 사내 문맥을 먼저 제공해 request 수와 실패를 함께 줄이는 방식입니다.

Uber는 같은 모델과 같은 질문, 같은 비용 조건으로 graph 사용 여부를 비교한 사례도 공개했습니다. graph를 쓴 실행은 tool call 4회와 38초 만에 정답을 냈고, 쓰지 않은 실행은 tool call 5회, error 3회, 하위 agent 2개를 거쳐 20분 9초 뒤 오답을 냈습니다. 평가는 30점 만점에 30점과 19점으로 표시됐습니다. 하나의 내부 질문을 고른 비교이므로 일반적인 속도·정확도 benchmark가 아니라, 잘못된 정보 탐색이 어떻게 turn을 늘리는지 보여 주는 사례입니다.

## token이 아니라 끝낸 작업 한 건을 비용 단위로 삼습니다

Software Factory가 비용을 관리할 때는 청구 단위보다 실제 작업 결과를 나타내는 운영 지표를 더 중요하게 봅니다. raw session과 skill session은 session당 비용을 보기 쉽습니다. 전문 에이전트에는 병합된 PR당 비용, 리뷰당 비용, alert당 비용, cleanup당 비용을 붙입니다. 품질은 되돌린 변경의 비율, F1, 평균 복구 시간 같은 신호로 함께 봅니다.

이렇게 해야 token을 줄였지만 재시도와 사람 수정이 늘어난 경우를 절감으로 잘못 계산하지 않습니다. 작업 하나를 끝내는 데 든 전체 비용과 품질을 보면 모델 배분, 도구 경로, 문맥 설계를 같은 기준으로 비교할 수 있습니다. 즉, 모델 한 번의 호출이 아니라 검증을 거쳐 끝낸 작업을 에이전트 운영의 최소 단위로 봅니다.

자동화 범위가 넓어질수록 통제도 작업 단위로 설계해야 합니다. Uber의 공개 자료는 MCP gateway의 중앙 인증·정책 집행과 사람의 검토·개입 경로를 밝히지만, 세부 권한표와 승격 절차, 실패 복구 정책은 공개하지 않았습니다. 다른 조직이 이 구조를 도입하려면 최소 권한, 격리 환경, 변경 승인, 감사 기록, 되돌리기, 사람에게 넘길 조건을 각 에이전트의 완료 정의와 함께 설계해야 합니다.

## 스킬 자동 개선은 아직 향후 과제입니다

Uber가 `Continuous Skill Improvement`라고 부른 항목은 현재 완성된 자율 자기개선 시스템이 아닙니다. 공개 글의 향후 과제 목록에는 스킬을 실행할 때 생기는 작은 불편을 trace, 즉 실행 기록에 남기고, 모은 trace로 skill update를 자동 생성하는 방법을 개발 중이라고 적혀 있습니다.

현재 확인할 수 있는 것은 계획의 방향뿐입니다. 자동으로 만든 update가 어떤 평가를 통과해야 배포되는지, 사람이 어디서 승인하는지, 잘못된 변경을 어떻게 되돌리는지에 관한 공개 구현과 결과는 없습니다. 따라서 이 기사에서 확인한 변화는 실행 trace를 바탕으로 skill을 자동 개선한 성과가 아닙니다. 작업별 benchmark와 완료 지표를 갖춘 관리형 실행 구조입니다.

## 이해상충과 취재 조건

Uber Engineering 글과 Uber 소속 발표자의 공개 영상은 이 시스템을 만든 주체의 1차 자료입니다. 사용량, 비용, benchmark와 Context Graph 비교는 Uber 내부 측정이며 독립 검증이 아닙니다. 기사 작성에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다.

공식 X 게시물은 Uber Engineering 글을 배포한 같은 내용의 원문 복제본으로 확인했으며, 두 번째 독립 URL 요건을 채우는 별도 기술 근거로 세지 않았습니다. 원문 두 개 요건에는 2026년 8월 27일 Uber Engineering 글과 8월 21일 공개된 Uber 소속 발표자 두 명의 AI Engineer 2026 발표 영상을 사용했습니다.

## 근거 원장

- **C1 · E1 · P1:** Uber Engineering은 2026년 8월 27일 비용 효율적인 Software Factory 운영 글을 공개했으며, 3,600개가 넘는 skill, 하루 3만 회가 넘는 실행, 주간 사용자 7배와 request 9.4배를 Uber 내부 집계로 제시했습니다.
- **C2 · E2 · P1:** Software Factory는 raw interactive session, skill session, general cloud agent와 specialized managed agent를 한 실행 체계에 놓고 code review·CI 복구·PR 검증·alert 분류·maintenance를 사람 review와 escalation 경로 안에서 수행합니다. Uber Engineering 글과 공개 발표 영상이 구조의 서로 다른 시점을 설명합니다.
- **C3 · E2 · P1:** Uber는 전체 비용을 사용자, session, turn, request, token과 token 가격으로 나누고, specialized agent는 병합된 PR·review·alert·cleanup 같은 완료 결과당 비용과 품질을 함께 측정합니다.
- **C4 · E1 · P1:** 모델을 고정한 Uber 내부 비교에서 request 1,000건당 비용은 peak보다 약 34%, session당 비용은 6월 peak보다 52% 낮아졌습니다. 원자료와 총비용은 공개되지 않았습니다.
- **C5 · E2 · P1:** CLI resolution과 tool search는 필요한 MCP 도구만 실행 시점에 찾고, code-mode는 polling과 중간 결과 처리를 subprocess에 맡겨 모델 context에 들어가는 schema·request·token을 줄입니다.
- **C6 · E1 · P1:** SQL token 표와 uReview 산점도, Context Graph 비교는 Uber가 공개한 내부 측정입니다. 조건과 지표 일부는 설명됐지만 dataset, raw trace, model 이름과 반복 분포는 공개되지 않았습니다.
- **C7 · E2 · P1:** 실제 작업으로 만든 benchmark와 cost·quality·reliability의 Pareto frontier를 함께 보면 한 모델을 모든 agent에 고정하지 않고 작업별 model routing을 할 수 있습니다. 주 모델과 더 저렴한 하위 agent의 역할 분리도 이 원칙을 따릅니다.
- **C8 · E2 · P1:** AI Context Graph는 서비스·팀·장애·PR·문서·배포·dataset 기록의 관계를 미리 연결해 agent가 올바른 사내 정보를 찾는 turn을 줄이도록 설계됐습니다.
- **C9 · E1 · P1:** Continuous Skill Improvement는 trace에서 불편을 모아 skill update를 자동 생성하려는 향후 과제이며, 현재 완성된 자율 자기개선 구현으로 공개되지 않았습니다.

## 출처

- [Uber Engineering, Running a Software Factory Efficiently at Uber Scale](https://www.uber.com/us/en/blog/efficient-software-factory/) — 2026년 8월 27일 공개된 중심 기술 원문입니다.
- [AI Engineer, Agentic SDLC at Uber — Uday Kiran Medisetty & Adam Huda, Uber](https://www.youtube.com/watch?v=17-YSUHo6Lk) — Uber 소속 발표자가 Software Factory의 기반 요소와 관리형 개발 흐름을 설명한 2026년 8월 21일 공개 영상입니다.
- [Uber Engineering 공식 X 게시물](https://x.com/ubereng/status/2093444169037762840) — 같은 Uber Engineering 글의 공식 배포·복제본이며 별도 원문 수로 세지 않았습니다.
