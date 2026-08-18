---
edition: eda
decision: publish-candidate
title: "HighTide는 VLSI benchmark를 정적 RTL 묶음에서 실행 가능한 RTL-to-GDS flow로 바꿉니다"
date: 2026-08-19
subject: "VLSIDA HighTide open-source VLSI benchmark suite와 Bazel 기반 OpenROAD RTL-to-GDS 실행 경로"
summary: "HighTide는 공개 하드웨어 설계를 ASAP7, NanGate45, SkyWater 130nm에서 OpenROAD RTL-to-GDS flow로 돌릴 수 있게 묶은 benchmark suite입니다. 논문과 GitHub artifact는 실행 구조와 조건을 공개하지만, 편집국은 전체 빌드를 재현하지 않았고 공개 결과 사이트 DNS도 확인하지 못했습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

ML for EDA와 agentic EDA의 병목은 더 많은 RTL 예제를 모으는 일만이 아닙니다. 실제 설계 흐름에서 중요한 질문은 같은 RTL이 synthesis, floorplan, placement, clock tree synthesis, routing, GDSII 출력까지 지나가며 어떤 quality of results, 즉 QoR을 내는지입니다. HighTide는 이 지점을 겨냥해 공개 하드웨어 설계를 OpenROAD 기반 RTL-to-GDS flow에서 실행 가능한 benchmark로 묶었습니다.

HighTide 논문은 이 suite가 여러 하드웨어 기술 언어와 세 technology platform을 포함하고, Bazel 기반 incremental RTL-to-GDS compilation과 remote cache, agent 보조 설계 큐레이션, RTL compilation check를 제공한다고 설명합니다. GitHub 저장소는 이 설명을 실행 경로로 뒷받침합니다. 설계 RTL을 고정된 upstream commit에서 가져오고, 필요한 변환과 patch를 Bazel 안에서 처리한 뒤, Yosys와 OpenROAD-flow-scripts를 거쳐 최종 layout과 report를 만듭니다.

## 정적 benchmark가 놓치는 것은 flow에서의 실패입니다

기존 공개 benchmark는 종종 RTL, netlist, 배치 문제, routing 문제처럼 한 단계 입력으로 고정됩니다. 이런 자료는 특정 알고리즘을 비교하기에는 좋지만, 실제 물리설계 flow의 단계 간 상호작용을 충분히 보여 주지 못합니다. Local placement가 좋아 보여도 clock tree synthesis 뒤에 timing repair가 커질 수 있고, 한 node에서 무난한 macro 배치가 다른 metal stack에서는 congestion을 만들 수 있습니다.

HighTide가 다른 점은 benchmark의 단위를 "설계 파일"이 아니라 "돌아가는 flow"로 잡는 데 있습니다. 저장소 문서는 각 설계가 `MODULE.bazel`의 hermetic `http_archive`로 고정된 upstream source에서 오고, native HDL을 Verilog로 낮춘 뒤, platform별 `constraint.sdc`, utilization, density, SRAM macro model과 함께 OpenROAD-flow-scripts를 실행한다고 설명합니다. Hermetic은 빌드가 외부 환경의 우연한 상태에 덜 의존하도록 source, version, integrity hash를 고정한다는 뜻입니다.

이 구조는 EDA 연구자가 비교 대상을 바꾸는 방식을 바꿉니다. 알고리즘 하나를 평가하려면 작은 toy design에 한 번 넣어 보는 대신, 같은 설계와 같은 platform 조건에서 stage별 output, timing slack, area, power, DRC count 같은 report를 다시 만들 수 있어야 합니다. HighTide는 그 반복의 최소 단위를 Bazel target으로 노출합니다.

## 입력에서 GDS까지 이어지는 실행 단위입니다

HighTide의 기본 flow는 여섯 단계로 나뉩니다. 먼저 Yosys가 RTL을 gate-level netlist로 합성합니다. 그다음 OpenROAD가 die 크기, I/O placement, power grid를 잡고, cell placement, clock tree synthesis, global/detailed routing, metal fill과 최종 GDSII 생성을 수행합니다. GDSII는 mask layout을 표현하는 물리설계 결과 형식입니다.

저장소의 quick start는 `bazel build //designs/asap7/lfsr:lfsr_final` 같은 target으로 LFSR 설계를 ASAP7 7nm academic predictive PDK에서 끝까지 빌드한다고 안내합니다. 출력은 `1_synth.odb`부터 `6_final.odb/.gds`, timing·area·DRC report, stage별 log로 나뉩니다. ODB는 OpenROAD Database로, 각 stage의 물리설계 상태를 담는 내부 database입니다.

지원 platform도 단일 조건이 아닙니다. 문서는 ASAP7 7nm, NanGate45 45nm, SkyWater 130nm high-density를 제시합니다. 세 node는 실제 상용 signoff PDK를 대체하지 않지만, advanced FinFET 성격, 중간 node baseline, routing layer가 제한적인 fabricable open PDK라는 서로 다른 압력을 줍니다. 논문은 초기 suite가 cell count 2만 미만부터 150만 초과까지의 설계를 포함한다고 보고했습니다.

## Agent는 benchmark를 쓰는 대상이면서 관리 도구이기도 합니다

HighTide 논문에서 흥미로운 부분은 agentic EDA를 평가 대상으로만 보지 않는다는 점입니다. 논문은 design lifecycle, flow optimization, tool reference, meta-maintenance를 다루는 12개 Claude Code skill과 per-design decision log를 설명합니다. 여기서 decision log는 특정 설계를 porting하거나 timing closure를 맞추며 왜 어떤 constraint와 workaround를 택했는지 남기는 장기 기록입니다.

이 방식의 실무적 의미는 큽니다. Benchmark suite는 시간이 지나면 설계 upstream이 바뀌고, tool이 바뀌고, PDK와 rule deck의 가정이 바뀝니다. 변경 때마다 사람이 같은 실패를 다시 분석하면 suite는 빠르게 낡습니다. HighTide는 agent skill과 decision memory를 사용해 설계 발견, cross-platform porting, bug tracking, flow tuning의 근거를 남기고 재사용하려 합니다.

다만 이것은 agent가 PPA를 자동으로 개선한다는 독립 검증이 아닙니다. 논문과 저장소가 공개한 것은 suite 관리와 실행 구조입니다. 개별 설계에서 어떤 agent 수정이 더 나은 timing, power, area를 만들었는지는 design, node, tool commit, constraint, seed, 반복 횟수별로 따로 검증해야 합니다.

## 지금 할 일 / 아직 미룰 일 / 다음에 확인할 신호

지금 할 일은 HighTide를 OpenROAD 기반 물리설계 연구의 재현성 기준 후보로 검토하는 것입니다. 특히 새 placer, resizer, CTS, routing pass를 평가하는 팀이라면 `bazel_to_orfs.sh`나 `bazel_to_config_mk.sh`로 HighTide design을 일반 OpenROAD-flow-scripts 실험으로 빼내는 경로가 중요합니다. 이렇게 하면 HighTide의 고정 입력을 유지하면서 custom OpenROAD binary나 flow Tcl 변경을 시험할 수 있습니다.

아직 미룰 일은 HighTide 결과를 상용 signoff 또는 silicon 결과로 읽는 것입니다. 논문도 post-flow verification과 silicon validation의 한계를 적고, memory-bearing design에는 FakeRAM macro를 사용한다고 설명합니다. FakeRAM은 SRAM compiler 없이 placement와 routing을 가능하게 하는 LEF/LIB black-box입니다. 실제 memory timing, bitcell layout, foundry signoff를 대체하지는 않습니다.

다음에 확인할 신호는 세 가지입니다. 첫째, 공개 결과 사이트와 remote cache가 안정적으로 접근되어 baseline report와 log를 독립적으로 받을 수 있는지입니다. 둘째, 외부 연구팀이 같은 commit과 cache 없이 주요 design을 재실행해 QoR 차이를 보고하는지입니다. 셋째, OpenROAD나 ML-for-EDA 논문이 HighTide target을 명시해 비교 조건을 고정하기 시작하는지입니다.

## 설계 조직에 주는 의미

HighTide의 가치는 "가장 큰 공개 benchmark"라는 식의 순위가 아닙니다. 더 중요한 변화는 EDA benchmark가 RTL 파일 모음에서 stage별 report와 실패 로그를 남기는 실행 환경으로 이동한다는 점입니다. 설계 조직이 새로운 optimization pass나 agent를 검토할 때, demo design 하나가 아니라 여러 언어, 여러 구조, 여러 node에서 같은 flow를 돌려 보는 기준점이 생깁니다.

그 기준점은 완전하지 않습니다. 상용 PDK, 상용 IP, foundry rule deck, signoff extraction, power integrity, 실제 SRAM compiler가 빠진 조건에서는 양산 chip의 최종 판단까지 갈 수 없습니다. 그러나 공개 연구와 open-source EDA에서는 이 한계가 오히려 분명한 장점입니다. 누구나 볼 수 있는 source, target, constraint, report 구조 안에서 주장을 좁혀 검증할 수 있기 때문입니다.

## 이해상충과 취재 조건

중심 근거는 HighTide arXiv 논문, VLSIDA GitHub 저장소, 저장소의 architecture·quick start·design catalog·Kubernetes build 문서입니다. 편집국은 저자, VLSIDA, OpenROAD 프로젝트, 관련 벤더에게서 사전 브리핑, 계정, compute credit, 비공개 benchmark, 도구 license를 제공받지 않았습니다.

편집국은 이번 턴에서 HighTide 전체 build를 실행하지 않았습니다. `hightide-benchmarks.dev` 결과 도메인은 DNS가 확인되지 않아 결과 페이지를 근거로 쓰지 않았습니다. 따라서 QoR 수치와 suite 규모 중 논문 본문에 의존한 항목은 저자 보고로 제한하고, 실행 가능성은 공개 GitHub artifact와 문서로 판단했습니다.

## 근거 원장

| Claim | 근거 | 판정 |
|---|---|---|
| C1. HighTide는 공개 VLSI design을 OpenROAD RTL-to-GDSII flow로 실행하는 benchmark suite다. | arXiv 논문, GitHub README | `E2`: 논문 설명과 공개 저장소 실행 구조가 일치 |
| C2. HighTide는 ASAP7, NanGate45, SkyWater 130nm platform을 대상으로 한다. | GitHub README, design catalog, architecture 문서 | `E2`: platform 목록과 node 설명을 공개 문서에서 확인 |
| C3. Bazel은 upstream RTL source, tool commit, ORFS/OpenROAD archive, build target을 고정하고 stage별 재실행과 cache를 제공한다. | GitHub README, architecture 문서, MODULE.bazel | `E2`: source와 build 규칙을 공개 code로 확인 |
| C4. Quick start는 LFSR 예제를 synthesis부터 final GDS/report/log까지 빌드하는 절차와 출력 위치를 제시한다. | quickstart.md | `E2`: 실행 절차와 output tree가 공개되어 있음. 편집국 미실행 |
| C5. HighTide가 상용 signoff 또는 silicon 결과를 보장한다. | 공개 근거 없음 | 미확인: 기사 결론으로 채택하지 않음 |

근거 수준의 상한은 `E2`, 재현성은 `R2`입니다. 공개 code, build target, script, license, 문서가 있어 재실행 가능한 artifact가 있지만, 편집국은 로컬에서 전체 flow를 실행하지 않았습니다.

## 출처

1. [arXiv, HighTide: An Agent-Curated Open-Source VLSI Benchmark Suite](https://arxiv.org/abs/2606.04126)
2. [VLSIDA/HighTide GitHub repository](https://github.com/VLSIDA/HighTide)
3. [HighTide architecture.md](https://github.com/VLSIDA/HighTide/blob/main/docs/architecture.md)
4. [HighTide quickstart.md](https://github.com/VLSIDA/HighTide/blob/main/docs/quickstart.md)
5. [HighTide design catalog](https://github.com/VLSIDA/HighTide/blob/main/docs/designs.md)
6. [HighTide k8s build documentation](https://github.com/VLSIDA/HighTide/blob/main/k8s/README.md)
7. [HighTide LICENSE](https://github.com/VLSIDA/HighTide/blob/main/LICENSE)
