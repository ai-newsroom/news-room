---
edition: eda
decision: publish-candidate
title: "EZ130 8T 공개로 표준셀 수업이 실제 tapeout flow와 이어졌습니다"
date: 2026-09-27
subject: "ETH Zurich EZ130 8T v1.1 open standard-cell library for IHP SG13G2, arXiv:2609.29965v1 and public library archive dated 2026-09-25"
summary: "ETH Zurich 연구진과 학생들이 IHP 130nm SG13G2 공정용 8-track 표준셀 라이브러리 EZ130 8T v1.1을 Apache 2.0으로 공개했습니다. 중요한 점은 표준셀 layout을 만들고 LIB·LEF·GDSII·Verilog 파일로 묶어 합성·배치배선 flow에 넣는 과정을 공개 artifact로 남겼다는 데 있습니다. 면적과 에너지 개선 수치는 저자들이 상용 도구와 제한된 benchmark에서 보고한 결과이며, 편집국이 재실행하지는 않았습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["논문과 배포물은 Cadence가 설계와 characterization에 필요한 라이선스를 제공했다고 밝힙니다", "편집국의 사전 briefing, 제공받은 계정·라이선스·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다"]
---

표준셀 라이브러리는 트랜지스터 수준 회로와 자동 디지털 설계 flow를 이어 주는 파일 묶음입니다. RTL 설계자는 보통 AND, NAND, flip-flop 같은 셀을 추상 부품처럼 씁니다. 하지만 합성 도구와 배치배선 도구는 각 셀의 지연, 면적, 전력, 핀 위치, layout 데이터를 필요로 합니다. 이 정보가 닫혀 있으면 학생이나 연구자는 RTL 설계를 GDS까지 보내는 flow는 배울 수 있어도, 그 아래 표준셀이 왜 그런 timing과 면적을 갖는지는 직접 확인하거나 고치기 어렵습니다.

ETH Zurich의 Integrated Information Processing 그룹은 IHP의 공개 130nm SG13G2 공정에 맞춘 표준셀 라이브러리 EZ130 8T v1.1을 공개했습니다. 논문은 2026년 9월 24일 arXiv에 올라왔고, ETH 배포 페이지의 v1.1 zip 파일은 2026년 9월 25일 갱신된 공개 archive입니다. 배포물에는 CDL, GDS, Verilog, LEF, LIB, datasheet와 release note가 들어 있습니다.

이번 공개의 의미는 새 cell 묶음이 하나 더 나왔다는 데 그치지 않습니다. 학생들이 표준셀을 그리고, 특성화 파일을 만들고, 합성·배치배선·물리 검증에 넣는 전체 경로가 공개 공정과 공개 배포물 위에 놓였습니다. 상용 EDA 도구가 평가 flow에 쓰였고 성능 결과는 저자 보고에 머물지만, 적어도 라이브러리 자체는 NDA 없이 내려받아 구조를 살펴볼 수 있습니다.

## 표준셀 파일이 합성과 배치배선의 입력이 됩니다

표준셀은 자동 합성이 실제 공정에서 쓸 수 있는 가장 작은 물리 단위입니다. RTL 합성 도구는 `assign y = a & b` 같은 논리를 공정에 맞는 AND cell과 buffer, flip-flop으로 바꿉니다. 배치배선 도구는 그 cell의 폭, 높이, 핀 위치, 배선 layer 정보를 보고 chip 안에 놓습니다. timing 분석기는 `.lib` 파일의 지연과 전력 table을 읽고 clock 주기를 맞출 수 있는지 계산합니다.

EZ130 8T는 이 경계에 들어가는 데이터를 공개합니다. 배포 zip 안에는 layout 교환 형식인 GDS, 물리 추상화 파일인 LEF, timing과 전력 특성화를 담은 LIB, simulation용 Verilog, 회로 netlist인 CDL이 들어 있습니다. 즉 독자는 논문 수치를 믿는 데서 멈추지 않고, 어떤 cell 이름과 어떤 corner 파일이 제공되는지 직접 볼 수 있습니다.

이 라이브러리는 IHP SG13G2 공정용 8-track cell입니다. 여기서 track은 표준셀 높이를 배선 pitch 몇 줄로 잡는지 나타내는 물리 설계 단위입니다. 논문과 release note는 v1.1에 220개 cell이 들어 있고, TT 1.20V 25도, FF 1.32V -40도, SS 1.08V 125도 corner의 LIB와 datasheet를 제공한다고 설명합니다.

## 수업 결과물이 tapeout 재료가 됐습니다

논문이 흥미로운 이유는 라이브러리 제작 과정을 교육 과정과 연결해 공개했다는 점입니다. ETH Zurich의 VLSI 5 수업에서 학생들은 schematic과 layout을 그렸습니다. 이어 Cadence Liberate로 LIB와 Verilog를 만들고 LEF·CDL·GDSII를 생성한 뒤, 새 표준셀이 실제 디지털 설계 flow 안에 들어가는지 확인했습니다.

검증 flow에는 Synopsys Design Compiler, Cadence Innovus, Siemens Calibre, Siemens QuestaSim이 쓰였다고 논문은 밝힙니다. 이 부분은 재현성의 한계이기도 합니다. 라이브러리 파일은 공개됐지만, 논문과 같은 도구 조합과 license를 갖춘 독자만 같은 방식으로 특성화와 배치배선 평가를 반복할 수 있습니다.

그래도 공개 범위는 실무적으로 유용합니다. 기존 open PDK 수업이나 연구 flow에서 표준셀은 이미 만들어진 library로 주어지는 경우가 많습니다. ETH 페이지와 논문은 학생들이 만든 EZ130 8T cell이 단순 과제에 그치지 않고, 2026년 VLSI 2 수업의 chip tapeout에도 쓰였다고 설명합니다. 논문은 EZ130 8T cell을 쓴 두 chip이 fabrication에서 돌아왔고 초기 test를 통과했지만, 전체 characterization은 진행 중이라고 적었습니다.

## 성능 수치는 공개 조건 안에서만 읽어야 합니다

저자들은 EZ130 8T v1.1을 SG13G2 PDK에 포함된 기본 표준셀 라이브러리 revision 0.1.4와 비교했습니다. 합성 평가는 32-bit adder, 32-bit multiplier, counter, LUT, shift register, latch array, 64-point FFT, 8x8 matrix-vector multiplier로 구성됐습니다. 합성은 Synopsys Design Compiler의 TT 1.20V 25도 조건에서 clock constraint를 바꾸며 진행했고, 비교 대상 SG13G2 library는 같은 Cadence Liberate flow로 다시 characterization했다고 논문은 설명합니다.

가장 자세한 배치배선 결과는 8x8 complex matrix-vector multiplier입니다. 저자들은 Cadence Innovus로 lowest area-delay product netlist를 배치배선하고, 50% density, 100ps 단위 clock sweep, TT·FF·SS 세 corner 분석을 적용했습니다. 이 조건에서 EZ130 8T v1.1은 cell area 0.92mm2, clock period 5.05ns, energy 0.77nJ/MVP를 보고했습니다. SG13G2 R0.1.4의 1.42mm2, 4.89ns, 1.27nJ/MVP와 비교하면 면적은 35% 작고 에너지는 39% 낮으며 clock period는 3% 큽니다.

이 수치는 저자 보고 결과입니다. 편집국은 상용 도구 license와 원 benchmark script를 갖고 같은 flow를 재실행하지 않았습니다. 또 이 결과를 최신 고성능 공정이나 다른 PDK의 표준셀 품질로 확대할 수 없습니다. 이 기사에서 확인한 것은 논문이 평가 조건을 공개했고, 배포 archive가 실제 LIB·LEF·GDS·Verilog 파일을 제공한다는 점입니다.

## 먼저 자기 flow에 맞는 파일인지 확인해야 합니다

EZ130 8T는 먼저 교육용 공개 표준셀 라이브러리로 보는 편이 맞습니다. IHP SG13G2로 수업, 연구 prototype, Tiny Tapeout류 실험을 준비하는 팀이라면 자기 flow에 필요한 인터페이스 파일이 맞는지 확인해야 합니다. cell list, LEF site와 pin grid, LIB corner, Verilog model, GDS/CDL 구성이 첫 확인 대상입니다. 배포물은 Apache 2.0 license를 명시하지만, 함께 쓰는 PDK와 EDA 도구의 license는 별도로 확인해야 합니다.

아직 미룰 일은 논문 수치만 보고 기존 library를 곧바로 바꾸는 결정입니다. 표준셀 교체는 합성 결과뿐 아니라 hold, DRC, LVS, antenna, clock tree, filler·tap insertion, power rail 연결까지 영향을 줍니다. 논문은 8개 benchmark와 한 개 post-layout 사례를 제공하지만, 사용자가 가진 SoC block이나 mixed-signal 주변 회로에서 같은 trade-off가 나온다는 뜻은 아닙니다.

다음에 확인할 신호는 세 가지입니다. 첫째, 공개 script나 독립 재현 로그가 나와 논문 표의 합성·배치배선 결과를 다시 만들 수 있는지입니다. 둘째, fabrication에서 돌아온 chip의 전체 silicon characterization이 공개되는지입니다. 셋째, OpenROAD나 다른 공개 flow에서 EZ130 8T를 IHP SG13G2 PDK와 함께 안정적으로 쓰는 사례가 쌓이는지입니다.

## 이해상충과 취재 조건

이 기사는 공개 arXiv 논문, ETH Zurich 공개 배포 페이지, 배포 zip archive, IHP Open PDK 저장소를 확인해 작성했습니다. 사전 briefing, 제공받은 계정·라이선스·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 논문과 README는 Cadence가 EZ130 8T의 설계와 characterization에 필요한 license를 제공했다고 밝힙니다. 따라서 상용 도구 사용 결과는 저자 환경의 보고로만 다뤘습니다.

## 근거 원장

| claim_id | 주장 | 근거 수준 | 원문 |
|---|---|---|---|
| C1 | EZ130 8T v1.1은 IHP SG13G2용 8-track 공개 표준셀 라이브러리이며 220개 cell과 LIB·LEF·GDS·Verilog·CDL 파일을 제공합니다. | E2 | arXiv HTML, ETH 배포 페이지, 배포 archive |
| C2 | 논문은 VLSI 5 수업에서 학생들이 표준셀을 만들고 상용 EDA flow로 characterization·합성·배치배선·검증에 연결했다고 설명합니다. | E2 | arXiv HTML, 배포 archive README |
| C3 | 저자들은 8x8 matrix-vector multiplier post-layout 조건에서 EZ130 8T v1.1이 SG13G2 R0.1.4보다 면적 35%, 에너지 39%를 줄이고 clock period는 3% 컸다고 보고했습니다. | E2 | arXiv HTML, ETH 배포 페이지 |
| C4 | 배포물은 Apache 2.0 license를 담고, IHP Open PDK 파일과 Cadence Liberate characterization 사용 사실을 NOTICE에 적었습니다. | E2 | 배포 archive LICENSE·NOTICE, IHP Open PDK 저장소 |

## 출처

- https://arxiv.org/abs/2609.29965
- https://arxiv.org/html/2609.29965
- https://iip.ethz.ch/ez-library/ihp130-8t.html
- https://iis-people.ee.ethz.ch/~iisdatasets/iip/ezlib/ihp130_8t/v1p1/ez130_8t_v1p1.zip
- https://iis-people.ee.ethz.ch/~iisdatasets/iip/ezlib/ihp130_8t/v1p1/ez130_8t_tt_1p20v_25c.pdf
- https://github.com/IHP-GmbH/IHP-Open-PDK
