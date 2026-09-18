---
edition: eda
decision: publish-candidate
title: "SpecLens는 Verilog 생성을 정답 맞히기보다 명세 모호성 찾기로 옮깁니다"
date: 2026-09-19
subject: "SpecLens arXiv:2609.16729v1, ASP-DAC 2027 accepted paper and wenbing1216/SpecLens public code at commit e081268556802e359f860203c42123ae772453d6"
summary: "SpecLens는 자연어 명세에서 Verilog RTL을 만들 때 여러 후보의 시뮬레이션 결과가 갈라지는 지점을 찾고, 그 차이를 다시 명세 제약으로 넣는 절차를 제안합니다. 논문과 공개 코드는 방법과 benchmark 실행 경로를 확인하게 해 주지만, 성능 수치는 저자 보고 결과이고 편집국이 재실행하지는 않았습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

자연어 명세에서 Verilog RTL을 바로 생성하는 흐름은 보통 모델이 낸 코드가 benchmark testbench를 통과하는지로 평가됩니다. SpecLens는 이 순서를 한 단계 앞당깁니다. 여러 Verilog 후보를 같은 입력 자극으로 돌려 보고 출력 trace가 갈라지는 부분을 찾습니다. 그런 다음 그 차이가 원래 명세의 어떤 모호함에서 왔는지 다시 제약으로 만들어 다음 생성에 넣습니다.

이 변화의 의미는 단순히 pass@1 점수를 올렸다는 데 있지 않습니다. RTL 생성 보조 도구가 실패한 뒤 compile-repair loop로 고치는 대신, 생성 전에 명세의 취약한 문장을 찾아 보강할 수 있음을 보여 줍니다. 저자들은 SpecLens 논문을 2026년 9월 15일 arXiv에 공개했고, 논문은 ASP-DAC 2027 채택 논문이라고 밝힙니다.

## 후보 코드가 다르게 움직이면 명세를 다시 봅니다

SpecLens의 입력은 자연어로 쓴 RTL 요구사항입니다. 도구는 먼저 요구사항에서 동작을 설명하는 문장을 뽑고, 각 요구사항을 시험할 수 있는 scenario와 stimulus를 만듭니다. 여기서 stimulus는 RTL 후보에 넣는 입력 순서이고, trace는 그 입력에 대해 후보가 내는 출력 기록입니다.

기존의 self-consistency 방식은 여러 후보를 만든 뒤 다수 후보가 보이는 동작을 고르거나, testbench 통과 여부로 최종 후보를 고르는 데 가깝습니다. SpecLens는 후보가 서로 다른 trace를 만들면 그 차이를 “모델이 헷갈린 명세 지점”으로 봅니다. 예를 들어 reset 뒤 첫 입력이 들어왔을 때 출력이 같은 cycle에 바뀌어야 하는지, 한 cycle 늦게 바뀌어야 하는지를 후보 trace가 다르게 보일 수 있습니다. SpecLens는 이렇게 관찰할 수 있는 차이를 새 제약으로 정리합니다.

논문은 이 절차를 세 단계로 설명합니다. Stage I은 요구사항별 scenario와 stimulus를 만들고 후보들의 trace를 묶습니다. Stage II는 trace 묶음의 차이를 보고 제약을 만들되, 새 제약을 넣었을 때 trace의 entropy가 줄어드는지 확인합니다. Stage III는 남은 후보를 고르고, 명세가 요구한 출력 초기값을 보강합니다. entropy는 후보 출력이 여러 갈래로 흩어지는 정도를 나타내는 값입니다. 여기서는 제약이 모호성을 줄였는지 보는 신호로 쓰입니다.

## testbench 통과만으로 명세를 다 지켰다고 보기는 어렵습니다

저자들은 VerilogEval v2.0 spec-to-RTL, RTLLM v1.1, RTLLM v2.0에서 SpecLens를 평가했다고 보고했습니다. 문법 검사와 기능 검증에는 Icarus Verilog와 Verilator를 썼고, 최종 Verilog를 benchmark testbench에 대해 실행해 functional correctness를 계산했습니다. 논문은 VerilogEval v2.0에서 o3-mini-medium 설정의 SpecLens가 functional pass@1 86.2%, pass@5 92.6%, syntactic pass@1 100.0%를 냈다고 보고합니다.

다만 이 수치를 “SpecLens가 모든 RTL 생성 상황에서 우월하다”는 결론으로 읽으면 안 됩니다. RTLLM 실험에서는 흥미로운 역전이 나옵니다. 저자들은 일부 RTLLM task에서 공개 명세와 공개 testbench가 서로 맞지 않는 경우를 찾았습니다. 이때 기존 baseline은 testbench에 맞는 익숙한 RTL 패턴을 내는 반면, SpecLens는 지역 명세 문장을 더 따르려는 경향을 보였다고 설명합니다. 그래서 원래 testbench 기준만 보면 SpecLens가 불리하게 보일 수 있습니다.

이 대목이 이 논문의 실제 뉴스 가치입니다. LLM 기반 RTL 생성은 “정답 benchmark를 더 잘 맞히는가”만으로는 설계 보조 도구의 품질을 설명하기 어렵습니다. 실제 설계 현장에서는 testbench도 완전하지 않고, 명세 문장도 서로 충돌할 수 있습니다. SpecLens는 모델 후보들의 행동 차이를 이용해 이런 충돌을 표면으로 끌어내는 방법을 제시합니다.

## 공개 코드는 재실행을 시작할 수 있게 합니다

공개 저장소에는 논문 실험에 쓴 실행 가능한 pipeline 두 개가 들어 있습니다. 하나는 Evalhuman 또는 HDLBits 스타일 benchmark용이고, 다른 하나는 RTLLM benchmark용입니다. 저장소 README는 `data_Evalhuman`, `RTLLMv1.1`, `RTLLM2.0` 같은 bundled benchmark 폴더와 `safe_pipeline_156.py`, `safe_pipeline_RTLLM.py` 실행 방법을 설명합니다.

실행 조건도 일부 공개됐습니다. README는 Python 3.10 이상, Python 3.11 권장, Icarus Verilog 12.0 stable, 로컬에서 확인한 Verilator 5.046을 적고 있습니다. 이 pipeline은 OpenAI API key 같은 provider 설정을 `.env`에 두고, 실행별 dataset root와 trace root를 CLI 인자로 받습니다.

하지만 편집국은 이번 턴에서 저장소를 clone해 benchmark를 재실행하지 않았습니다. 공개 코드와 데이터 묶음이 있으므로 재실행 가능성은 R2로 볼 수 있지만, 저자 수치를 독립적으로 재현한 것은 아닙니다. 또 공개 패키지는 machine-specific retest result artifact를 포함하지 않는다고 README가 밝힙니다. 따라서 독자는 결과 파일을 그대로 대조하기보다 같은 환경에서 새로 실행해야 합니다.

## 지금은 명세 점검기로 볼 때입니다

지금 할 일은 SpecLens를 RTL 생성 agent의 “최종 생성기”보다 “명세 점검기”로 먼저 보는 것입니다. 자연어 명세가 benchmark보다 자주 바뀌는 팀이라면, 여러 후보의 trace가 어디서 갈라지는지 보고 명세 문장을 보강하는 절차를 review checklist로 쓸 수 있는지 검토할 만합니다. 특히 testbench가 충분하지 않은 초기 설계 단계에서는 통과율보다 후보들이 어디서 갈라지는지가 더 유용한 피드백일 수 있습니다.

아직 미룰 일은 논문 수치를 근거로 기존 RTL 생성 flow를 바로 교체하는 결정입니다. 비교 결과는 VerilogEval과 RTLLM 계열 benchmark, 특정 모델 설정, 저자 실행 환경 안에서 보고된 값입니다. 상용 IP, 복잡한 protocol, 사내 coding rule, formal signoff flow까지 같은 효과가 난다고 볼 근거는 아직 없습니다.

다음에 확인할 신호는 세 가지입니다. 첫째, 공개 저장소로 VerilogEval v2.0과 RTLLM 결과가 제3자 환경에서 얼마나 가깝게 재현되는지입니다. 둘째, mismatch가 있는 testbench를 사람이 고쳤을 때 SpecLens의 이점이 실제 bug 발견이나 review 시간 절감으로 이어지는지입니다. 셋째, derived constraint가 더 큰 SoC block이나 protocol-heavy RTL에서 오히려 잘못된 제약을 강화하지 않는지입니다.

## 이해상충과 취재 조건

이 기사는 공개 arXiv 원문, arXiv HTML, 공개 GitHub 저장소와 GitHub API metadata만 확인해 작성했습니다. 사전 briefing, 제공받은 계정·라이선스·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 논문의 성능 결과는 저자 보고 결과이며, 편집국이 benchmark를 재실행하거나 독립 로그를 확보하지는 않았습니다.

## 근거 원장

| claim_id | 주장 | 근거 수준 | 원문 |
|---|---|---|---|
| C1 | SpecLens는 자연어 RTL 명세에서 행동 요구사항을 뽑고, 후보 Verilog의 trace divergence를 이용해 명세 제약을 보강하는 flow를 제안합니다. | E2 | arXiv 논문, 공개 code README |
| C2 | 논문은 VerilogEval v2.0에서 o3-mini-medium 설정 SpecLens가 functional pass@1 86.2%, pass@5 92.6%, syntactic pass@1 100.0%를 냈다고 보고합니다. | E2 | arXiv 논문 |
| C3 | RTLLM 평가에서는 일부 task의 specification-testbench mismatch를 지적했고, benchmark testbench 통과와 명세 충실성이 다를 수 있음을 보여 줍니다. | E2 | arXiv 논문 |
| C4 | 공개 저장소는 Evalhuman/HDLBits 스타일 pipeline과 RTLLM pipeline, bundled benchmark 폴더, 실행 안내와 environment 조건을 제공합니다. | E2 | GitHub README, GitHub API |

## 출처

- https://arxiv.org/abs/2609.16729
- https://arxiv.org/html/2609.16729
- https://github.com/wenbing1216/SpecLens
- https://raw.githubusercontent.com/wenbing1216/SpecLens/main/README.md
- https://api.github.com/repos/wenbing1216/SpecLens
- https://api.github.com/repos/wenbing1216/SpecLens/commits/main
