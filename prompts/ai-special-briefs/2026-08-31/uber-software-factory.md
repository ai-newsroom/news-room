# Uber 소프트웨어 팩토리 특별판 브리프

## 편집자 요청

Uber Engineering이 2026년 8월 27일 공개한 `Running a Software Factory Efficiently at Uber Scale`을 AI 특별 기사로 다룬다.

제목은 기술·시스템 이름을 먼저 놓고 핵심 변화를 짧게 잇는 뉴스형으로 쓴다. 우선 제목안은 다음과 같다.

> Uber 소프트웨어 팩토리 공개 - 3,600개 AI 스킬을 비용 효율적으로 운영하는 방법

더 정확하고 자연스러운 제목이 근거 조사 중 확인되면 뜻을 유지한 채 다듬을 수 있다.

## 중심 질문

Uber는 AI 코딩 에이전트를 개인 개발 도구가 아니라 대규모 소프트웨어 생산 시스템으로 어떻게 운영하고 있으며, 비용을 낮추면서 품질과 사용량을 함께 관리하기 위해 실행 구조를 어떻게 바꿨는가.

## 반드시 설명할 내용

1. `Software Factory`가 무엇인지 구체적인 개발 장면으로 설명한다. 코드 리뷰, CI 복구, PR 작성·검증, 장애 분류 같은 관리형 에이전트가 어떤 위치에 있는지 보여 준다.
2. 비용식을 쉬운 한국어로 풀어 쓴다. 사용자를 줄이는 것이 아니라 세션 안의 불필요한 turn, request, token을 줄이는 접근임을 설명한다.
3. 표준 MCP 방식에서 도구 schema를 모두 문맥에 넣을 때 생기는 부담과, CLI tool resolution·tool search·code-mode가 이를 어떻게 바꾸는지 단계별로 설명한다.
4. code-mode는 반복 polling과 중간 결과 처리를 script/subprocess에 맡기고 모델에는 필요한 요약만 돌려주는 구조라는 점을 설명한다. 특정 제품과 동일 구현이라고 단정하지 않는다.
5. 작업별 실제 benchmark, 주 모델과 더 저렴한 하위 agent의 역할 분리, Pareto-optimal model routing을 설명한다. 한 모델이 모든 작업에서 최고라는 결론으로 쓰지 않는다.
6. AI Context Graph가 서비스·팀·장애·PR·문서·배포 기록을 연결해 에이전트의 정보 탐색 turn을 줄이는 방식을 설명한다.
7. 비용 단위를 token이나 model call에만 두지 않고 병합된 PR, review, alert 처리처럼 완료된 결과로 바꾼 의미를 판단한다.
8. Uber가 앞으로 추진한다고 밝힌 Continuous Skill Improvement는 현재 완성된 자율 자기개선 시스템이 아니라 향후 계획임을 구분한다.

## 수치와 표현의 경계

- `PR의 70% 이상이 local 또는 cloud agent에 attributed`됐다는 Uber의 표현을 정확히 옮긴다. 이를 `AI가 Uber 코드의 70%를 작성했다`거나 `PR의 70%를 자율 생성했다`고 바꾸지 않는다. attribution 산정 방법이 공개되지 않았다는 점을 가까이에서 밝힌다.
- 3,600개 이상 agent skill, 하루 3만 회 이상 skill 실행, 2026년 2월부터 8월까지 주간 사용자 7배와 agentic request 9.4배 증가는 Uber 내부 집계다.
- 모델을 고정한 비교에서 request 1,000건당 비용이 peak 대비 약 34%, session당 비용이 6월 peak 대비 52% 줄었다는 주장은 Uber 내부 측정이며 독립 재현이 없다.
- SQL 비교의 `1,431,594 tokens -> 900 tokens`는 매우 큰 응답을 code-mode 밖에서 모델 문맥에 넣은 극단 사례다. 대표 평균처럼 제목이나 요약에 쓰지 않는다. 단순 query에서도 50%대 절감이 관찰됐다는 표의 전체 조건을 함께 설명한다.
- Context Graph를 사용한 38초 정답 대 20분 9초 오답 비교는 같은 모델에 같은 질문을 넣은 Uber 내부 단일 사례이지 일반 benchmark가 아니다.
- 비용 총액, raw trace, benchmark dataset, model/vendor 구성, PR attribution 방법은 공개되지 않았다. before-after 수치에는 adoption, workload, model 변화가 섞일 수 있으며 Uber는 일부 unit-cost 비교에서만 모델을 고정했다고 설명한다.

## 독자를 위한 기술적 의미

이 기사는 AI 에이전트 운영의 최소 단위가 `좋은 모델 한 번 호출`에서 `실제 작업을 끝내는 관리형 실행 시스템`으로 이동하고 있다는 점을 설명해야 한다. 특히 다음 판단을 독자가 가져갈 수 있게 한다.

- 필요한 도구만 늦게 불러오고, 반복 제어는 코드가 맡으면 모델 문맥을 크게 줄일 수 있다.
- 모델 선택은 작업별 benchmark와 완료 비용을 기준으로 해야 한다.
- 큰 코드베이스에서는 모델 교체보다 올바른 사내 문맥을 빠르게 찾게 하는 구조가 더 중요할 수 있다.
- 비용 절감은 작은 모델 사용만의 문제가 아니라 불필요한 검색, tool schema, polling, 긴 중간 결과를 제거하는 시스템 설계 문제다.
- 관리형 에이전트는 자동화 범위를 넓히지만 사람 검토·승격, 권한, 정책, 실패 복구 설계가 함께 필요하다.

## 문체

기술을 처음 접하는 엔지니어가 따라갈 수 있는 자연스러운 한국어 설명형 기사로 쓴다. 낯선 용어는 처음 나올 때 풀고, 소제목은 그 절에서 알게 될 내용을 평범하고 구체적인 문장으로 쓴다. 검증 면책이나 주의사항을 제목·요약·여러 절에서 반복하지 않는다. Uber의 홍보 문구를 그대로 옮기기보다 실제 실행 흐름과 인과관계를 먼저 설명한다.

## 우선 확인할 원문

- Uber Engineering 글: https://www.uber.com/us/en/blog/efficient-software-factory/
- Uber Engineering X 게시물: https://x.com/ubereng/status/2093444169037762840
- 글에서 연결한 Uber의 AI Engineer 2026 발표 영상: https://www.youtube.com/watch?v=17-YSUHo6Lk

X나 YouTube 본문에 접근할 수 없으면 검색 요약을 사실 근거로 승격하지 않는다. 중심 기술 주장과 수치는 Uber Engineering 글에서 직접 확인한다. 원문 두 개 조건을 채우기 위해 서로 복제된 지역별 Uber 블로그 URL을 별도 출처처럼 세지 않는다.
