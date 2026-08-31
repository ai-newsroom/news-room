---
edition: eda
decision: publish-candidate
title: "RTL repair framework는 LLM이 고친 RTL을 formal proof로 다시 검증합니다"
date: 2026-09-01
subject: "Open-Source LLM-Driven Formal Verification: A Multi-Agent Pipeline for RTL Repair, arXiv:2607.28877v1 and rtl-repair-framework commit 539301395aad8dc558faae737d33063c0b2bcf98"
summary: "RTL repair framework는 LLM이 고친 Verilog를 곧바로 성공 사례로 보지 않습니다. Yosys·SymbiYosys·Z3 formal verification 결과와 counterexample를 다음 수정 입력으로 되돌립니다. 논문과 공개 저장소는 여섯 benchmark, 실행 스크립트, raw log, 실패 유형을 공개했습니다. 다만 저자 실험에서 5회 모두 고친 benchmark는 `alu` 하나뿐이고, 편집국은 OpenAI API와 formal toolchain이 필요한 전체 평가를 재실행하지 않았습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["논문과 저장소 저자는 방법과 결과의 당사자입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

LLM으로 RTL 코드를 고칠 때 가장 위험한 지점은 “그럴듯한 패치”와 “검증된 패치”가 쉽게 섞인다는 점입니다. `RTL Repair Framework`는 이 둘을 formal verification으로 나눕니다. Formal verification은 설계가 주어진 성질을 만족하는지 수학적으로 증명하는 검증 단계입니다. LLM은 Verilog RTL을 수정하지만, 성공 여부는 Yosys, SymbiYosys, Z3가 만든 proof와 counterexample로 판단합니다.

이 흐름은 RTL repair를 프롬프트 실험이 아니라 검증 flow 실험으로 다룹니다. 입력은 buggy RTL과 자연어 specification입니다. framework는 port와 reset 같은 구조 정보를 뽑고, SystemVerilog Assertion 형태의 property를 만듭니다. 그런 다음 solver가 찾은 반례를 LLM에게 다시 줍니다. 그래서 agent의 다음 행동은 “문장을 다시 생성한다”보다 “formal tool이 낸 실패 흔적을 보고 RTL을 다시 고친다”에 가깝습니다.

발행 근거는 논문과 저장소가 함께 공개됐다는 점입니다. arXiv 논문 `2607.28877v1`은 방법과 여섯 benchmark 결과를 설명합니다. GitHub 저장소는 MIT license로 code, buggy benchmark, 실행 스크립트, `multi_run_b11.csv` raw result, log 일부, Python dependency를 공개했습니다. 편집국은 저장소 `main`의 HEAD가 `539301395aad8dc558faae737d33063c0b2bcf98`임을 확인했습니다.

## RTL을 고치기 전에 검증 조건부터 만듭니다

일반적인 LLM RTL repair demo는 compiler error, testbench failure, waveform 해석을 feedback으로 쓰는 경우가 많습니다. 이 framework는 repair loop 앞에 property 작성 단계를 둡니다. property는 설계가 지켜야 할 조건을 assertion으로 적은 것입니다. 예를 들어 ALU라면 opcode에 따라 ADD, SUB, AND, OR 결과가 맞는지와 zero flag가 결과와 일치하는지를 확인할 수 있습니다.

저장소의 orchestrator는 LangGraph state graph로 여섯 node를 연결합니다. `contract` node가 interface를 읽고, `architect` node가 property를 만들며, `verifier` node가 Yosys와 SymbiYosys, Z3를 실행합니다. 실패하면 `cex_analyzer`가 VCD counterexample를 해석하고, `coder`가 RTL을 고친 뒤, `reviewer`가 specification과 수정 방향을 다시 점검합니다.

이 구조에서 counterexample는 단순한 오류 메시지가 아닙니다. Counterexample는 assertion이 깨지는 입력과 시간 흐름을 보여 주는 반례입니다. RTL 엔지니어가 waveform을 보고 원인을 좁히듯, agent도 반례를 보고 다음 patch를 정합니다. 이 framework는 LLM을 코드 생성기로만 쓰지 않습니다. Formal verifier가 만든 실패 증거를 해석해 반복 수정하는 보조자로 둡니다.

## 빈 검증 통과를 막는 guard가 중요합니다

이 연구에서 눈에 띄는 부분은 성공률보다 실패를 다루는 방식입니다. README와 code는 빈 assertion이나 `bind` 처리 문제 때문에 SymbiYosys가 의미 없는 PASS를 낼 수 있는 경로를 명시합니다. `main_graph.py`에는 property text가 비어 있거나 `assert`와 `module`을 갖지 않으면 verifier로 넘기지 않는 guard가 들어 있습니다. README도 Yosys 0.61 SystemVerilog frontend가 `bind`로 참조된 module을 조용히 버려 false PASS가 생길 수 있었다고 설명합니다.

EDA flow에서는 이런 방어가 중요합니다. LLM이 만든 RTL이 testbench 몇 개를 통과해도, property 자체가 비어 있거나 환경 가정이 너무 강하면 검증은 설계를 확인하지 못합니다. 논문과 저장소는 이 문제를 “성공률을 높이는 요령”이 아니라 repair flow의 신뢰도 조건으로 다룹니다. 그래서 이 기사의 중심 판단은 framework가 더 많은 RTL을 고쳤다는 데 있지 않습니다. 성공과 실패를 formal proof, vacuity, quota crash, temporal logic failure처럼 구분해 기록한 공개 repair flow라는 점입니다.

## 여섯 benchmark 중 하나만 안정적으로 고쳤습니다

저장소의 결과는 신중하게 읽어야 합니다. 저자는 여섯 benchmark를 각 5회씩 돌렸고, `alu`는 5회 모두 PASS로 보고했습니다. 평균 반복 횟수는 2.0회, 평균 시간은 16.5초로 적었습니다. 반면 `counter`, `arbiter`, `axi_lite_slave`, `uart_tx`, `fifo`는 성공하지 못했습니다. `fifo`는 다섯 run 가운데 두 번이 OpenAI API quota error로 중단되어 통계에서 제외됐다고 기록했습니다.

실패 유형도 서로 다릅니다. `counter`는 bounded-cover vacuity, `arbiter`는 specification ambiguity, `axi_lite_slave`는 multi-property, `uart_tx`와 `fifo`는 temporal logic 문제로 분류됐습니다. Temporal logic은 시간에 따른 순서와 지속 조건을 다루는 논리입니다. UART 송신이나 FIFO처럼 여러 cycle에 걸쳐 상태가 바뀌는 회로에서는 조합 논리 ALU보다 property 작성과 반례 해석이 훨씬 어렵습니다.

이 결과는 실무자에게 두 가지를 동시에 말합니다. 하나는 formal feedback을 LLM repair loop에 넣는 구조가 공개 code와 log로 확인된다는 점입니다. 다른 하나는 그 구조가 아직 일반 RTL repair 도구라고 부를 만큼 넓게 성공하지 못했다는 점입니다. 특히 multi-cycle protocol과 복수 property가 있는 설계에서는 specification 작성, environment constraint, vacuity check가 repair 성공률을 좌우합니다.

## 지금은 검증 flow 실험으로 봐야 합니다

재현성은 `R2`로 봅니다. 저장소에는 `run_n_times.py`, benchmark, requirements, raw CSV, log가 있습니다. README는 Python 3.12.3, LangGraph 1.0.6, OpenAI client 2.15.0, GPT-4o temperature 0, Yosys 0.61+39, SymbiYosys 0.61, Z3 4.15.5 조건을 적었습니다. MIT license라 code 검토와 fork도 가능합니다.

다만 편집국은 전체 평가를 실행하지 않았습니다. OpenAI API key와 비용, Yosys·SymbiYosys·Z3 설치, LLM의 비결정성, quota error가 결과에 영향을 줍니다. 논문과 저장소의 raw log는 저자가 보고한 artifact이며, 독립 연구팀의 재현이나 silicon 결과는 아닙니다. 이 framework의 결과를 상용 formal signoff 품질이나 모든 RTL bug class의 repair 성공률로 확대하면 안 됩니다.

지금 할 일은 작습니다. 팀이 LLM RTL repair를 검토한다면 `alu`처럼 작은 조합 논리부터 clone, dependency 설치, tool version 확인, 단일 benchmark run, CSV 비교를 순서대로 확인하는 것이 맞습니다. 아직 미뤄야 할 일은 복잡한 bus protocol이나 FIFO repair를 자동화된 production flow로 넣는 결정입니다. 다음에 확인할 신호는 독립 재현 로그, `bind`와 vacuity guard를 포함한 regression test, SystemVerilog frontend 변화 뒤의 false-pass 재검증, 여러 LLM과 여러 seed에서의 pass/fail 분포입니다.

## 이해상충과 취재 조건

논문과 저장소 저자는 방법과 결과의 당사자입니다. 이 기사는 저자 보고 성공률을 독립 검증으로 쓰지 않았고, 편집국 재현으로 표현하지 않았습니다.

이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 웹 원문, GitHub raw file, GitHub API 응답만 사용했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. RTL Repair Framework는 buggy RTL과 자연어 specification을 입력으로 받고, property 생성, formal verification, counterexample 분석, RTL patch, review, 재검증을 반복합니다. | E2 · P1/P2 · R2 | arXiv 논문과 저장소 README·`main_graph.py`를 확인했습니다. 편집국은 실행하지 않았습니다. |
| C2. framework는 Yosys, SymbiYosys, Z3를 formal backend로 쓰고, k-induction 또는 iteration budget 종료까지 loop를 돌립니다. | E2 · P1/P2 · R2 | 논문과 README, requirements를 대조했습니다. toolchain 설치와 solver 결과 재생성은 확인하지 않았습니다. |
| C3. 저장소는 여섯 benchmark multi-run 결과를 공개했고, `alu`는 5/5 PASS, 나머지 다섯 benchmark는 실패 또는 quota crash를 보고했습니다. | E2 · P2 · R2 | `multi_run_b11.csv`와 README 결과 요약을 확인했습니다. 저자 실행 로그이며 독립 재현은 아닙니다. |
| C4. false PASS를 줄이기 위해 assertion이 비었거나 구조적으로 부족하면 verifier로 넘기지 않는 guard가 있습니다. | E2 · P2 · R2 | `main_graph.py`의 `_has_real_assertions`와 `route_after_architect`를 확인했습니다. guard의 충분성은 별도 보안 감사 대상입니다. |
| C5. 저장소는 MIT license로 공개됐고, `main` HEAD는 `539301395aad8dc558faae737d33063c0b2bcf98`입니다. | E2 · P2 · R2 | GitHub API, `git ls-remote`, LICENSE 파일을 확인했습니다. 이후 branch가 바뀔 수 있어 commit 기준으로 기록했습니다. |

## 출처

1. arXiv, `Open-Source LLM-Driven Formal Verification: A Multi-Agent Pipeline for RTL Repair`: https://arxiv.org/abs/2607.28877
2. arXiv HTML, `2607.28877v1`: https://arxiv.org/html/2607.28877v1
3. GitHub, `trunghafromvietnam/rtl-repair-framework`: https://github.com/trunghafromvietnam/rtl-repair-framework
4. RTL Repair Framework README at commit `539301395aad8dc558faae737d33063c0b2bcf98`: https://raw.githubusercontent.com/trunghafromvietnam/rtl-repair-framework/539301395aad8dc558faae737d33063c0b2bcf98/README.md
5. RTL Repair Framework `main_graph.py` at commit `539301395aad8dc558faae737d33063c0b2bcf98`: https://raw.githubusercontent.com/trunghafromvietnam/rtl-repair-framework/539301395aad8dc558faae737d33063c0b2bcf98/main_graph.py
6. RTL Repair Framework raw CSV result: https://raw.githubusercontent.com/trunghafromvietnam/rtl-repair-framework/539301395aad8dc558faae737d33063c0b2bcf98/logs/sprint1/multi_run_b11.csv
7. RTL Repair Framework `run_n_times.py`: https://raw.githubusercontent.com/trunghafromvietnam/rtl-repair-framework/539301395aad8dc558faae737d33063c0b2bcf98/run_n_times.py
8. RTL Repair Framework LICENSE: https://raw.githubusercontent.com/trunghafromvietnam/rtl-repair-framework/539301395aad8dc558faae737d33063c0b2bcf98/LICENSE
9. GitHub API, commit `539301395aad8dc558faae737d33063c0b2bcf98`: https://api.github.com/repos/trunghafromvietnam/rtl-repair-framework/commits/539301395aad8dc558faae737d33063c0b2bcf98
