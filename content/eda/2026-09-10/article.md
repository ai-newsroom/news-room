---
edition: eda
decision: publish-candidate
title: "Clock gating 연구가 RTL 저전력 수정은 gate-level에서도 검증해야 한다고 보여 줍니다"
date: 2026-09-10
subject: "Clock-Gating Insertion Strategies on an Open-Source MSP430 Core, arXiv:2608.30954v1 and yanyana117/openmsp430-low-power-study-full commit c8eb1603ad1804ad9ec897862ffadd466d9fb84e"
summary: "openMSP430 clock-gating 연구는 RTL 시뮬레이션에서는 맞던 수동 latch-and-AND clock gate가 합성 뒤 gate-level simulation에서 실패할 수 있음을 공개 netlist와 evidence로 보였습니다. 같은 연구에서 synthesis-inserted integrated clock-gating cell은 32 nm 조건의 세 corner에서 total power를 25~30%, dynamic power를 74~81% 줄였다고 보고했습니다. 다만 Design Compiler, PrimeTime PX, VCS와 SAED32 EDK가 필요해 독자가 완전히 무료 flow만으로 숫자를 다시 만들 수는 없습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["없음. 공개 arXiv 원문과 GitHub 저장소만 사용했고, 사전 briefing, 제공받은 account·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

저전력 RTL을 만들 때 clock gating은 흔한 선택입니다. Clock gating은 쓰지 않는 register에 clock이 계속 들어가지 않게 해 전력을 줄이는 방법입니다. 이번 openMSP430 연구에서 중요한 대목은 “clock gating을 넣었다”는 사실이 아닙니다. RTL simulation에서는 맞던 수동 clock gate도 합성 뒤 gate-level simulation에서 깨질 수 있다는 점을 공개 netlist와 실행 증거로 남긴 데 있습니다.

논문은 2026년 8월 31일 arXiv에 올라왔습니다. 저자들은 open-source 16-bit microcontroller인 openMSP430을 32 nm SAED32 standard-cell library로 합성해 네 가지 구성을 비교했습니다. 기본 설계, RTL에 직접 쓴 behavioral clock gate, Design Compiler가 넣은 integrated clock-gating cell, 두 방법을 함께 쓴 구성을 나눴습니다. 저자들은 full flow와 증거 파일을 GitHub 저장소에 공개했습니다.

## RTL에서 맞던 clock gate가 합성 뒤 실패했습니다

RTL simulation은 register-transfer level, 즉 register와 조합논리의 동작을 기능 중심으로 확인하는 단계입니다. 이 단계에서는 이상적인 clock과 zero-delay에 가까운 모델을 쓰기 쉽습니다. 논문이 문제 삼은 수동 clock gate는 latch와 AND gate로 gated clock을 만들었습니다. 이 구성은 RTL self-checking test 10개를 통과했습니다.

문제는 합성 뒤 netlist에서 나왔습니다. 저장소의 root-cause evidence는 Opt1과 Opt3 netlist에서 multiply 결과 register가 새 값을 잡지 못해 `RESLO`가 `0x0000`으로 읽혔다고 기록합니다. CPU 전체가 멈춘 것은 아니었습니다. VCD toggle count를 보면 master clock과 여러 gated clock은 움직였습니다. 실패 범위는 gated multiply/store path로 좁혀졌습니다.

저자들은 원인을 latch-and-AND clock gate가 만든 늦은 gated clock과 ungated domain 사이의 hold race로 설명했습니다. Hold race는 data가 너무 빨리 바뀌어 register가 이전 값이나 잘못된 값을 잡는 timing 문제입니다. 같은 evidence 파일은 zero delay, unit delay, timing check off, random init, full SDF back-annotation 등 여덟 simulation 설정에서 모두 실패했다고 적었습니다. 따라서 이 결과는 단순한 simulator option 문제가 아닙니다. clock gate 구현 방식이 합성 뒤 timing 구조와 만나며 드러난 문제로 읽어야 합니다.

## tool이 넣은 ICG는 전력을 줄이고 gate-level test를 통과했습니다

Integrated clock-gating cell, 줄여서 ICG는 clock gating을 위해 library가 제공하는 특성화된 cell입니다. 저자들의 netlist evidence는 수동 gating 구성이 `LATCHX1` 12개를 만들었고, synthesis-inserted 구성은 `CGLPPRX2` 46개를 썼다고 기록합니다. 논문은 Design Compiler가 넣은 ICG 구성이 gate-level self-checking test 10개를 통과했다고 보고했습니다.

전력 결과도 이 구성을 중심으로 봐야 합니다. 저장소의 PPA evidence는 worst corner 조건에서 baseline total power가 1.4840 mW, Opt2 synthesis gating이 1.0500 mW였다고 기록합니다. 같은 표에서 dynamic power는 49.64 uW에서 12.58 uW로 줄었습니다. multi-corner evidence는 Opt2의 total power 감소가 ss에서 29.2%, tt에서 30.1%, ff에서 24.6%였고, dynamic power 감소가 각각 74.7%, 73.6%, 81.1%였다고 보고했습니다.

이 수치를 제품 일반론으로 넓히면 안 됩니다. 대상은 openMSP430, 32 nm SAED32 library, 저자들이 고른 workload와 corner입니다. 또 평균 total power에서는 leakage가 96~99%를 차지했습니다. 그래서 dynamic power 절감률이 전체 전력 절감률과 같지는 않았습니다. 그래도 설계 flow 관점의 메시지는 분명합니다. 저전력 수정은 RTL 기능 통과만으로 끝나지 않습니다. 합성된 clock structure와 gate-level 검증 결과를 함께 봐야 합니다.

## 공개 파일이 있어 실패 원인과 재현 한계를 따져볼 수 있습니다

이 연구는 보도자료나 주장만 남기지 않았습니다. GitHub 저장소에는 RTL, synthesis script, PrimeTime PX power script, gate-level netlist, raw evidence, offline reproduction bundle이 들어 있습니다. `repro/REPRODUCE.md`는 VCS `W-2024.09-SP2-5`, Design Compiler `W-2024.09-SP5-4`, PrimeTime PX `V-2023.12-SP5-4`, SAED32 EDK와 corner library 이름을 적었습니다. upstream openMSP430 commit도 `92c883abb4518dbc35b027e6cad5ffef5b2fbb81`로 고정했습니다.

다만 재현성은 제한적입니다. netlist와 script는 공개돼 있지만, 주요 flow를 다시 돌리려면 Synopsys 상용 tool과 SAED32 EDK가 필요합니다. 저장소는 netlist를 제공하므로 일부 timing, power, gate-level simulation은 re-synthesis 없이 다시 확인할 수 있다고 설명합니다. 하지만 독자가 일반적인 open-source 환경만으로 논문 표 전체를 재현할 수 있다는 뜻은 아닙니다.

저장소에는 OpenROAD와 sky130hd로 baseline RTL-to-GDSII physical design을 닫은 확장 결과도 있습니다. 최종 run은 30% target core utilization, 0.40 placement density, one-site padding에서 detailed-route DRC 0개와 antenna violation 0개를 기록했습니다. 그러나 그 문서는 clock-gated variant의 post-route 비교는 future work로 남겼다고 명시합니다. 따라서 이 기사는 clock gating의 post-route 전력 결론을 새로 만들지 않습니다.

## 지금은 coding guideline과 GLS 항목부터 확인해야 합니다

지금 할 일은 low-power coding guideline에서 hand-written latch-and-AND clock gate를 허용하는지 확인하는 것입니다. 허용하고 있다면 synthesis tool의 ICG inference rule, clock-gating check, gate-level simulation, SDF back-annotation regression을 같은 review 항목에 넣어야 합니다. 특히 “RTL test가 통과했으니 clock gating은 안전하다”는 판단은 이 연구의 실패 사례와 맞지 않습니다.

아직 하지 말아야 할 일은 이 논문의 수치를 그대로 자기 공정과 core에 적용하는 것입니다. 32 nm 교육용 library, openMSP430, 특정 workload에서 나온 PPA 결과는 advanced-node SoC나 다른 clock tree, 다른 retention·power-gating strategy를 대표하지 않습니다. 수동 gating을 전부 금지한다는 조직 규칙도 이 논문 하나로 만들기에는 근거가 좁습니다.

다음에 확인할 대목은 post-route 비교입니다. 저자 저장소는 OpenROAD baseline closure까지 공개했지만 clock-gated variant의 배치배선 뒤 전력과 timing 비교는 future work로 남겼습니다. 실제 signoff flow에서는 clock tree synthesis, skew, hold fixing, placement density, leakage optimization이 함께 움직입니다. synthesis-level 결과와 post-route 결과가 같은 방향으로 남는지 확인돼야 더 강한 결론을 쓸 수 있습니다.

## 이해상충과 취재 조건

이 기사에는 이해상충이 없습니다. 공개 arXiv 원문과 GitHub 저장소만 사용했고, 사전 briefing, 제공받은 account·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다.

저자들의 재현 flow는 Synopsys VCS, Design Compiler, PrimeTime PX와 SAED32 EDK에 의존합니다. 이 도구와 library는 공개 저장소에 포함되지 않으며, 기사는 이를 재현성의 한계로 봅니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. 논문은 openMSP430에서 RTL behavioral clock gating, synthesis-inserted ICG, 두 방법의 조합, baseline을 비교했습니다. | E2 · P1/P2 · R1 | arXiv 원문이 연구 대상과 구성, GitHub artifact를 명시하고, 저장소가 RTL·script·netlist·evidence를 공개합니다. |
| C2. 수동 latch-and-AND clock gate는 RTL simulation 10개를 통과했지만 gate-level simulation에서 multiply 결과 capture 실패를 보였습니다. | E2 · P1/P2 · R1 | 논문 초록과 저장소 root-cause evidence가 실패 현상, 여덟 simulation 설정, hold race 설명을 제시합니다. 편집국은 tool을 직접 재실행하지 않았습니다. |
| C3. synthesis-inserted ICG는 gate-level test를 통과했고, 세 corner에서 total power를 25~30%, dynamic power를 74~81% 줄였다고 저자들이 보고했습니다. | E2 · P1/P2 · R1 | arXiv 원문과 raw evidence 파일의 PPA·multi-corner 표가 같은 방향의 결과를 제시합니다. 조건은 32 nm SAED32, openMSP430, 저자 workload입니다. |
| C4. 저장소는 offline reproduction bundle, tool version, upstream openMSP430 commit, netlist, script, raw evidence를 공개했습니다. | E2 · P2 · R1 | `repro/REPRODUCE.md`와 repository tree에서 확인했습니다. Synopsys tool과 SAED32 EDK가 필요해 완전한 무료 재현은 아닙니다. |
| C5. OpenROAD physical-design extension은 baseline closure를 공개했지만 clock-gated post-route 비교는 future work입니다. | E2 · P2 · R1 | `PHYSICAL_DESIGN_PLAN.md`와 `physical-design/results/summary.md`가 baseline closure와 future-work 항목을 명시합니다. 이 기사는 post-route clock-gating 결론을 내리지 않습니다. |

## 출처

1. arXiv, `Clock-Gating Insertion Strategies on an Open-Source MSP430 Core: A Reproducible PPA Study and a Gate-Level Simulation Caveat`: https://arxiv.org/abs/2608.30954
2. GitHub, `yanyana117/openmsp430-low-power-study-full`: https://github.com/yanyana117/openmsp430-low-power-study-full
3. GitHub raw, `repro/REPRODUCE.md`: https://raw.githubusercontent.com/yanyana117/openmsp430-low-power-study-full/main/repro/REPRODUCE.md
4. GitHub raw, `repro/evidence/part2_netlist_analysis.txt`: https://raw.githubusercontent.com/yanyana117/openmsp430-low-power-study-full/main/repro/evidence/part2_netlist_analysis.txt
5. GitHub raw, `repro/evidence/part3_ppa_comparison.txt`: https://raw.githubusercontent.com/yanyana117/openmsp430-low-power-study-full/main/repro/evidence/part3_ppa_comparison.txt
6. GitHub raw, `repro/evidence/part6_multicorner_power.txt`: https://raw.githubusercontent.com/yanyana117/openmsp430-low-power-study-full/main/repro/evidence/part6_multicorner_power.txt
7. GitHub raw, `PHYSICAL_DESIGN_PLAN.md`: https://raw.githubusercontent.com/yanyana117/openmsp430-low-power-study-full/main/PHYSICAL_DESIGN_PLAN.md
8. GitHub raw, `physical-design/results/summary.md`: https://raw.githubusercontent.com/yanyana117/openmsp430-low-power-study-full/main/physical-design/results/summary.md
