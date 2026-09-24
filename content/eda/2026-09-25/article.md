---
edition: eda
decision: publish-candidate
title: "ChipMEM은 검증을 통과한 실행만 EDA 에이전트의 기억으로 남깁니다"
date: 2026-09-25
subject: "ChipMEM arXiv:2609.27067v1, aalrabah/ChipMEM public implementation at commit 39c22105acb5e0c18d14e0a9bf6f7ea213fc4cc3, RTLRewriter-Bench commit 96639fe67bc8f020c05978ef5028d75fcf6980f2, and CVDP benchmark commit 8e894cf74414ab1eaea1e2b4e80a02f123df07b6"
summary: "ChipMEM은 RTL 최적화와 testbench 생성 에이전트가 이전 실행에서 얻은 교훈을 곧바로 저장하지 않고, 합성·시뮬레이션·등가성 확인 같은 결정적 평가를 통과한 뒤에만 다음 작업의 기억으로 쓰는 방법을 제안합니다. 논문과 공개 구현으로 구조와 실행 인터페이스는 확인할 수 있지만, 논문 성능 수치는 저자 보고 결과입니다. raw trajectory와 상용 도구 설정은 공개 저장소에 없습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["논문 저자 중 NVIDIA와 Cadence 소속자가 포함되어 있습니다", "편집국의 사전 briefing, 제공받은 계정·라이선스·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다"]
---

LLM 기반 EDA 에이전트는 RTL을 고치고, 도구 로그를 읽은 뒤 다시 실행하기를 반복합니다. 문제는 그 과정에서 얻은 교훈이 다음 설계에도 그대로 통한다고 보기 어렵다는 점입니다. 한 설계에서 맞았던 수정 규칙은 다른 RTL에서는 틀릴 수 있습니다. 실패한 도구 명령을 계속 되풀이하면 runtime과 token 비용만 늘어납니다.

ChipMEM은 이 문제를 다룹니다. 이 논문은 에이전트가 이전 실행에서 배운 절차를 저장하되, 합성, 시뮬레이션, formal equivalence 같은 검증 절차를 통과한 경우에만 절차 기억으로 남깁니다. 동시에 도구 호출이 어떤 오류에서 성공하거나 실패했는지를 Bayesian 통계 기억으로 쌓습니다. 같은 실패를 반복할 가능성이 높아지면 이 기록을 바탕으로 회복 전략을 제안합니다.

이 변화는 “더 큰 모델로 RTL을 더 잘 만든다”는 이야기와 다릅니다. ChipMEM의 초점은 모델 가중치를 바꾸는 데 있지 않습니다. 검증된 실행 기록을 다음 작업의 입력으로 쓰는 설계 flow가 핵심입니다.

## 검증을 통과한 실행만 기억으로 남깁니다

ChipMEM에는 두 종류의 기억이 있습니다. 절차 기억은 이전 작업에서 얻은 `SKILL.md` 같은 완성된 절차를 보관합니다. 통계 기억은 도구 호출 단위의 성공과 실패를 기록합니다. 여기서 도구 호출은 synthesis, simulation, timing, equivalence check처럼 에이전트가 설계 파일을 확인하거나 고치는 과정에서 부르는 실행 단계입니다.

핵심은 저장 조건입니다. 논문은 절차 기억을 만들 때 에이전트의 자기 판단이나 LLM 채점에 맡기지 않습니다. 각 domain의 결정적 평가 harness를 통과해야 한다고 설명합니다. RTL 최적화에서는 합성 성공, 기능 등가성, 양의 개선이 필요합니다. CVDP testbench 생성에서는 숨겨진 simulation, coverage, mutation check를 모두 통과해야 합니다.

공개 구현도 같은 규칙을 전면에 둡니다. 저장소 README는 benchmark가 선언한 task artifact만 retrieval 문서로 읽고, top matching skill을 주입하며, 결정적 evaluation harness가 `PASS`를 반환한 뒤에만 immutable skill을 하나 만들도록 설명합니다. `FAIL`이나 `INVALID` 뒤에는 절차 skill을 만들지 않습니다.

이 구조가 중요한 이유는 EDA에서 “그럴듯한 설명”이 설계 품질을 보장하지 않기 때문입니다. RTL 수정은 compile만 통과해서는 부족합니다. 기존 RTL과 기능이 같은지, 합성 뒤 면적이나 timing이 실제로 좋아졌는지, testbench가 요구한 corner를 지나는지까지 확인해야 다음 단계로 넘어갈 수 있습니다. ChipMEM은 agent memory의 단위를 문장 요약이 아니라 검증 결과에 묶습니다.

## 작업을 넘겨도 검증된 절차를 다시 씁니다

기존 RTL 생성·수정 에이전트의 흔한 흐름은 현재 작업 안에서만 배웁니다. 에이전트가 오류 로그를 보고 코드를 고치고, 다시 도구를 돌리고, 마지막 결과를 제출합니다. 다음 설계로 넘어가면 같은 종류의 오류를 다시 만날 수 있지만, 앞선 실행의 경험은 prompt에 사람이 넣어 주거나 모델이 우연히 기억하는 범위에 머뭅니다.

ChipMEM은 작업 사이의 경계를 넘기는 별도 layer를 둡니다. 새 RTL 최적화 작업이 들어오면 top RTL 파일 같은 task artifact를 embedding으로 바꾸고, 그와 비슷한 과거 작업에서 검증을 통과한 skill을 찾아 agent context에 넣습니다. CVDP testbench 생성 작업에서는 task의 `PROMPT.md` 같은 정의 파일이 retrieval 기준이 됩니다. 이렇게 하면 agent가 “이 설계와 비슷한 구조에서 어떤 절차가 실제로 통과했는가”를 먼저 볼 수 있습니다.

통계 기억은 더 좁은 문제를 맡습니다. 에이전트가 같은 종류의 도구 호출에 여러 번 실패하면, ChipMEM은 retry 성공 확률을 Beta 모델로 갱신합니다. 논문과 README는 기본 nudge threshold를 0.20으로 둡니다. 예측한 retry 성공 가능성이 이 값 아래로 내려가면, 이전 실패 회복 기록을 보고 어떤 전략이 더 나았는지 순위를 만들어 agent에게 조언합니다.

따라서 엔지니어가 받는 feedback도 달라집니다. 단순히 “이번 RTL이 testbench를 통과했다”에서 끝나지 않습니다. 어떤 종류의 설계에서 어떤 수정을 저장해도 되는지, 어떤 오류에서는 같은 명령을 반복하지 말고 log 확인이나 다른 recovery로 넘어가야 하는지를 기록할 수 있습니다.

## 저자들은 다른 작업에도 통하는지 실험했습니다

논문은 RTL-OPT, RTLRewriter-Bench, CVDP, OpenTitan과 custom design set에서 ChipMEM을 평가했다고 보고합니다. 특히 RTLRewriter-Bench에서는 같은 모델과 도구 설정에서 equivalence-passing output이 memory off 35/54에서 ChipMEM 39/54로 늘었고, 49개 short suite의 평균 area improvement가 5.66%에서 8.69%로 올랐다고 보고했습니다. CVDP held-out task에서는 frozen procedural library로 18/20에서 20/20으로 올라갔다고 적었습니다.

이 수치는 저자 보고 결과입니다. 편집국이 benchmark를 재실행하거나 raw trajectory를 감사하지는 않았습니다. 또 공개 ChipMEM 저장소는 구현과 일반 experiment runner를 담지만, 논문 결과, raw trajectory, trained memory state, proprietary agent, private prompt, commercial dataset, commercial tool configuration은 담지 않는다고 명시합니다. 따라서 성능 결론은 “논문 조건에서 저자들이 보고한 결과”로 읽어야 합니다.

그래도 분석할 가치는 있습니다. 논문이 측정하려 한 질문이 기존 논문들과 다르기 때문입니다. 이전 EDA 에이전트 연구 상당수는 한 benchmark 안에서 agent가 얼마나 많이 통과하는지를 봅니다. ChipMEM은 저장한 경험을 frozen 상태로 둔 뒤 unseen task에서 쓰는 실험을 별도로 뒀습니다. 같은 문제를 외운 것인지, 다른 작업에도 옮겨 쓸 수 있는지를 구분하려 한 것입니다.

## 공개 구현만으로 논문 수치를 모두 재현하기는 어렵습니다

공개 저장소의 장점은 interface가 비교적 분명하다는 점입니다. `main.py`는 `memory_off`, `procedural_only`, `statistical_only`, `chipmem` 네 mode를 받습니다. adapter는 embedding, agent, harness, distill callable을 외부에서 연결합니다. harness는 `pass`, `fail`, `invalid` verdict를 내기 때문에, agent의 성공 주장만으로 skill을 만들 수 없습니다.

하지만 이 공개 범위만으로 논문 수치를 바로 재현할 수 있다고 말하기는 어렵습니다. repository는 privacy-safe synthetic task와 generic runner를 제공합니다. 논문에 쓰인 agent, raw trajectory, trained memory state와 상용 도구 설정은 공개되지 않았습니다. CVDP 자체도 공개 no-commercial flow와 commercial EDA tool이 필요한 범위를 구분합니다.

따라서 재현성은 R1로 봅니다. 방법과 구현 구조는 설명할 수 있고 일부 코드는 실행할 수 있습니다. 다만 논문 결과 전체를 같은 조건으로 재실행할 artifact가 충분히 공개됐다고 보기는 어렵습니다. RTLRewriter-Bench와 CVDP는 공개되어 있어 독립 팀이 별도 adapter와 agent를 붙여 비슷한 질문을 다시 검증할 수는 있습니다.

## 내부 도입보다 통과 기준을 먼저 정해야 합니다

지금 할 일은 ChipMEM을 특정 제품의 성능 주장보다 EDA agent 운영 방식의 설계안으로 보는 것입니다. 내부 RTL agent를 실험하는 팀이라면, 먼저 “어떤 결과를 통과로 인정할 것인가”를 정해야 합니다. 예를 들어 compile 성공, simulation pass, equivalence pass, timing closure, area improvement를 각각 다른 gate로 두고, gate를 통과한 실행만 다음 작업의 skill 후보로 저장해야 합니다.

또 하나 할 일은 memory retrieval의 입력을 좁게 정하는 것입니다. ChipMEM은 agent instruction이나 tool history 전체가 아니라 benchmark가 선언한 task artifact를 retrieval key로 삼습니다. 실제 팀에서도 top RTL, failing assertion, protocol requirement처럼 비교 가능한 입력을 고정해야 합니다. 그렇지 않으면 기억 검색이 설계 유사성이 아니라 prompt 잡음에 끌릴 수 있습니다.

아직 미룰 일은 논문 수치를 근거로 기존 RTL 생성·검증 flow를 바로 교체하는 결정입니다. 공개 구현은 논문 결과를 모두 담지 않고, reported PPA와 CVDP 결과는 저자 환경에 묶여 있습니다. 특히 상용 simulator, signoff tool, 사내 IP, coding rule이 들어가는 flow에서는 같은 memory policy가 도움이 되는지 별도 검증해야 합니다.

다음에 확인할 신호는 세 가지입니다. 첫째, 제3자가 공개 ChipMEM 구현과 공개 benchmark로 memory off 대비 개선을 재현하는지입니다. 둘째, raw trajectory와 trained memory state가 공개되는지입니다. 적어도 논문 표의 각 design별 실패·성공 로그가 감사 가능한 형태로 나오는지도 봐야 합니다. 셋째, retrieval된 skill이 다른 설계에서 성능을 떨어뜨리는 경우를 얼마나 잘 막는지입니다.

## 이해상충과 취재 조건

이 기사는 공개 arXiv 원문, 공개 GitHub 저장소, 공개 benchmark 저장소, Git 원격 HEAD만 확인해 작성했습니다. 사전 briefing, 제공받은 계정·라이선스·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 논문 저자에는 NVIDIA와 Cadence 소속자가 포함되어 있어 EDA agent와 상용 설계 도구 생태계에 이해관계가 있을 수 있습니다.

## 근거 원장

| claim_id | 주장 | 근거 수준 | 원문 |
|---|---|---|---|
| C1 | ChipMEM은 검증 통과 실행에서만 절차 기억을 만들고, 도구 호출 성공·실패를 통계 기억으로 갱신하는 EDA agent memory layer를 제안합니다. | E2 | arXiv HTML, ChipMEM README |
| C2 | 논문은 RTLRewriter-Bench에서 ChipMEM이 memory off보다 equivalence-passing output과 평균 area improvement를 높였다고 보고합니다. | E2 | arXiv HTML, RTLRewriter-Bench README |
| C3 | 논문은 CVDP held-out task에서 frozen procedural library가 18/20에서 20/20으로 올라갔다고 보고합니다. | E2 | arXiv HTML, CVDP README |
| C4 | 공개 ChipMEM 저장소는 구현과 generic runner를 담지만, 논문 결과, raw trajectory, trained memory state, proprietary agent, private prompt, commercial dataset, commercial tool configuration은 담지 않는다고 밝힙니다. | E2 | ChipMEM README |

## 출처

- https://arxiv.org/abs/2609.27067
- https://arxiv.org/html/2609.27067v1
- https://github.com/aalrabah/ChipMEM
- https://raw.githubusercontent.com/aalrabah/ChipMEM/main/README.md
- https://github.com/yaoxufeng/RTLRewriter-Bench
- https://raw.githubusercontent.com/yaoxufeng/RTLRewriter-Bench/master/README.md
- https://github.com/NVlabs/cvdp_benchmark
- https://raw.githubusercontent.com/NVlabs/cvdp_benchmark/main/README.md
