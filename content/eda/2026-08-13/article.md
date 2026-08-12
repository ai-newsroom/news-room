---
edition: eda
decision: publish-candidate
title: "EDA 에이전트의 승부처는 더 큰 모델보다 ‘검증 가능한 피드백’일 수 있습니다"
date: 2026-08-13
subject: "Cadence의 EDA agent feedback loop 전략과 공개 연구"
summary: "Cadence가 말한 ‘피드백 루프의 moat’를 쉽게 풀고, 공개 논문이 뒷받침하는 범위와 아직 확인되지 않은 경쟁 우위를 나눠 봅니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["중심 자료 중 하나는 Cadence가 자사 제품과 전략을 설명한 벤더 블로그입니다.", "인용한 연구 결과는 저자들이 선택한 과제와 평가 조건에서 보고한 수치이며 독립 재현이 아닙니다.", "편집국은 JasperGold·Verisium SimAI 라이선스와 동일 실험 환경이 없어 도구 결과를 재실행하지 못했습니다."]
---

칩 설계를 돕는 AI가 좋은 답을 한 번 내놓는 것보다 더 중요한 일이 있습니다. 틀렸을 때
**어디가 왜 틀렸는지 도구가 알려 주고, AI가 그 정보를 받아 다음 답을 고치는 일**입니다.
Cadence는 이 반복 구조를 앞으로 EDA 에이전트의 핵심 경쟁력이라고 주장합니다.

## 세 줄 요약

- Cadence는 칩 설계 AI의 한계가 언어 모델 자체보다 simulation·formal 도구가 돌려주는
  피드백의 속도와 정보량에서 결정될 수 있다고 봅니다.
- 공개 연구는 formal 도구의 오류·구조 정보를 다시 AI에 넣으면 RTL 명세나 assertion을
  만드는 특정 과제에서 결과가 좋아질 수 있음을 보여 줍니다.
- 다만 Cadence의 통합이 다른 EDA 환경보다 우월하거나 쉽게 따라 하기 어려운 ‘moat’라는
  점을 증명한 독립 비교는 아직 확인하지 못했습니다.

## EDA 엔지니어를 위한 판단

- **지금 할 일:** 에이전트 demo의 말솜씨보다 어떤 tool API, counterexample, coverage·설계
  구조 정보를 읽고 다음 시도를 바꾸는지 확인할 만합니다.
- **아직 미룰 일:** 벤더가 소개한 한두 workflow만 보고 verification 전체의 생산성이나
  제품 간 우열을 결론 내리는 일입니다.
- **다음에 확인할 신호:** 같은 RTL·property·예산으로 여러 모델과 도구 조합을 비교하고,
  성공뿐 아니라 반복 횟수·실패·runtime·검증 누락까지 공개하는 benchmark입니다.

### 피드백은 ‘정답/오답’보다 ‘어디를 고칠지’가 중요합니다

간단한 예를 들어 보겠습니다. AI가 FIFO라는 작은 데이터 버퍼의 동작을 검사하는
assertion을 만들었다고 합시다. Assertion은 설계가 반드시 지켜야 할 규칙을 적은 문장입니다.

formal 도구가 `실패`만 돌려주면 AI는 거의 눈을 감고 다시 써야 합니다. 반면 어느 상태에서
규칙이 깨졌는지 보여 주는 counterexample, 신호가 어디에서 영향을 받는지 나타내는
cone of influence, 도달할 수 있는 상태를 함께 돌려주면 수정 범위가 작아집니다. 즉 좋은
피드백은 점수 한 개가 아니라 **다음 행동을 고를 수 있는 진단 정보**입니다.

Cadence의 2026년 6월 30일 글은 이를 두 종류로 나눕니다. Compile 성공, proof 성공,
coverage 백분율 같은 값은 결과를 알려 주는 낮은 정보량의 피드백입니다. Testbench 설정과
coverage의 관계, FSM의 도달 상태, 신호 사이의 구조 같은 정보는 원인을 찾게 하는 높은
정보량의 피드백입니다. FSM은 설계가 가질 수 있는 상태와 이동 규칙을 나타내는 유한 상태
기계입니다.

### Cadence가 그리는 구조는 빠른 안쪽 루프와 정확한 바깥쪽 루프입니다

Cadence는 coverage closure 사례에 Verisium SimAI를, formal 사례에 Jasper의 설계 구조
정보를 연결합니다. Coverage closure는 아직 실행되지 않은 기능 조건을 찾고 testbench를
조정해 검증 빈틈을 줄이는 작업입니다.

이 글이 제안하는 구조는 다음과 같습니다.

1. 안쪽 루프에서는 빠른 예측기나 구조 정보가 다음 입력·property 후보를 좁힙니다.
2. 바깥쪽 루프에서는 simulation 또는 formal 엔진이 그 후보를 정확하게 다시 검사합니다.
3. 통과하지 못하면 진단 결과를 받아 후보를 고치고 반복합니다.

빠른 도구만 쓰면 틀린 예측이 쌓일 수 있고, 정확하지만 무거운 도구만 매번 돌리면 시간이
많이 듭니다. 두 루프를 나눈다는 생각은 이 속도와 정확성의 균형을 잡으려는 것입니다.

### 공개 논문도 ‘도구를 다시 부르는 루프’의 효과를 보고합니다

2026년 4월 공개된 ProofLoop 연구는 RTL에서 SystemVerilog assertion을 만드는 과제를
다뤘습니다. 연구팀은 먼저 RTL의 구조를 검색하고 JasperGold 질의를 사용한 뒤, 생성한
assertion을 formal 도구로 검사하고 최대 세 차례 고쳤습니다. 저자들은 FVEval의
Design2SVA 평가에서 문법 정확도 93.7%, 기능 정확도 82.0%를 보고했습니다. 이 수치는
해당 연구의 설정에서 나온 **저자 보고 결과**이며, 모든 설계와 제품에 그대로 적용되는
성능표가 아닙니다.

SpecLoop 연구도 비슷한 방향입니다. RTL에서 형식 명세를 만들고 formal equivalence가 내놓는
counterexample을 받아 명세를 다시 고칩니다. 저자들은 LLM이 한 번만 답하는 방식보다 여러
모델과 benchmark에서 결과가 좋아졌다고 보고했습니다.

ISQED 2026의 관련 논문은 이 흐름을 더 넓게 정리합니다. EDA 도구 피드백이 없는 open-loop
방식은 신뢰하기 어렵고 simulation·synthesis를 다시 부르는 closed-loop가 필요하다고
설명합니다. 동시에 잘못 설계된 반복은 hardware Trojan을 심거나 실제로 아무것도 확인하지
않는 vacuous verification 같은 실패를 키울 수 있다고 경고합니다. 루프가 있다는 사실만으로
안전해지는 것은 아니라는 뜻입니다.

## 확인된 것과 확인되지 않은 것

| 구분 | 지금 말할 수 있는 것 | 아직 말할 수 없는 것 |
|---|---|---|
| 기술 방향 | 구조·오류·coverage 정보를 다시 AI에 넣는 폐쇄형 루프가 특정 formal·assertion 과제의 결과를 개선할 수 있습니다. | 이 효과가 대규모 SoC의 모든 verification·implementation 단계에 같은 크기로 이어지는지는 모릅니다. |
| Cadence 사례 | Cadence는 Verisium SimAI와 Jasper를 이용한 구체적인 연결 방식을 공개 글에서 설명했습니다. | 동일 과제에서 Cadence와 Siemens·Synopsys·오픈소스 조합을 비교한 독립 결과는 확인하지 못했습니다. |
| 생산성 | 실패 원인과 다음 행동을 직접 연결하면 무작위 재시도를 줄일 가능성이 있습니다. | 라이선스·서버 비용을 포함한 전체 runtime, 엔지니어 검토 시간, 놓친 bug 수는 공개 자료만으로 계산할 수 없습니다. |
| 경쟁력 | 풍부한 machine-readable 피드백과 도구 통합은 agent 제품을 평가할 중요한 기준입니다. | 이것이 장기간 복제하기 어려운 사업적 ‘moat’인지는 기술 논문만으로 증명할 수 없습니다. |

여기서 가장 중요한 구분은 **작동 가능성**과 **제품 우위**입니다. 공개 연구는 전자를 어느
정도 지지합니다. 후자는 같은 조건의 독립 비교가 있어야 판단할 수 있습니다.

## 이 공개의 의의와 편집 판단

**편집 판단:** 이 글은 Cadence의 제품 우위 선언이 아니라, EDA 에이전트를 평가하는 질문을
`어떤 LLM인가`에서 `어떤 검증 도구가 무엇을 되돌려 주는가`로 옮겨 놓았다는 점에서 기사
가치가 있습니다. 공개 연구도 피드백 루프의 기술적 가능성을 E2 수준으로 지지합니다. 다만
Cadence가 말한 ‘moat’는 독립 비교가 없는 벤더의 전략적 주장으로 남겨 둡니다.

앞으로 EDA 에이전트 발표를 볼 때는 다음 네 가지를 함께 묻겠습니다. 도구가 돌려주는 정보가
단순 점수인지 진단 가능한 구조인지, golden engine으로 최종 확인하는지, 실패 사례와 반복
비용을 공개하는지, 다른 도구와 같은 조건에서 비교했는지입니다.

## 이해상충과 취재 조건

중심 자료 중 하나는 Cadence의 AI 담당 블로그로, 자사 Verisium SimAI와 Jasper 통합의
가치를 설명합니다. 인용한 ProofLoop·SpecLoop·ISQED 결과도 각 저자가 선택한 과제와
환경에서 보고한 결과입니다. 편집국은 기사 작성에 Cadence나 논문 저자의 지원을 받지
않았으며, 상용 도구와 동일한 benchmark 환경이 없어 결과를 재실행하지 않았습니다.

## 근거 원장

| Claim | 근거 | 판정 |
|---|---|---|
| C1. Cadence는 빠르고 풍부한 EDA 피드백을 agent 신뢰성과 경쟁력의 핵심으로 제시했다. | Cadence 원문, 제품 예시 | `E1`: 벤더가 자기 전략을 설명한 사실 |
| C2. Formal·구조 피드백을 반복 입력하면 특정 RTL 명세·assertion 생성 과제의 결과가 좋아질 수 있다. | ProofLoop, SpecLoop, ISQED 논문 | `E2`: 방법과 실험이 공개된 저자 보고, 독립 재현 없음 |
| C3. Cadence 통합이 경쟁 제품보다 우월하고 지속 가능한 moat다. | 독립 head-to-head 없음 | 미확인: 기사 결론으로 채택하지 않음 |

근거 수준의 상한은 `E2`, 재현성은 `R1`입니다. 논문 방법과 일부 수치는 공개됐지만 편집국이
상용 도구를 이용해 다시 실행하지 않았습니다.

## 출처

1. [Cadence, *The Feedback Loop Is the Moat* (2026-06-30)](https://community.cadence.com/cadence_blogs_8/b/artificial-intelligence/posts/the-feedback-loop-is-the-moat-480749506)
2. [Mashnoor 외, *From Language to Logic: Bridging LLMs & Formal Representations for RTL Assertion Generation*](https://arxiv.org/abs/2604.23100)
3. [*SpecLoop: Agentic RTL-to-Specification Generation with Formal Equivalence Feedback*](https://arxiv.org/abs/2603.02895)
4. [*Closing the Loop: Overcoming the Tool-Feedback Gap in Agentic Hardware Design*](https://doi.org/10.1109/ISQED69900.2026.11534671)
5. [DVCon Proceedings, Verisium SimAI를 이용한 coverage closure 사례](https://dvcon-proceedings.org/wp-content/uploads/1100.pdf)
