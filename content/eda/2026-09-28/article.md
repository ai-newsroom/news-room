---
edition: eda
decision: publish-candidate
title: "OpenSTA SPICE 추출, 여러 cell subckt 파일을 직접 받습니다"
date: 2026-09-28
subject: "OpenSTA master commit ef17b3fd81404d685d33ec65e0354c122d701e4d, 2026-09-04 write_path_spice and write_gate_spice -lib_subckt_files change"
summary: "OpenSTA는 타이밍 경로나 선택한 gate를 SPICE netlist로 꺼낼 때 cell transistor-level subckt 파일을 하나가 아니라 목록으로 받을 수 있게 했습니다. 타이밍 보고서에서 의심 경로를 골라 회로 시뮬레이터로 넘기는 공개 flow에서, 여러 library와 보조 cell subckt를 미리 한 파일로 합치는 수작업을 줄이는 변화입니다. 성능이나 signoff 정확도 개선은 공개 원문만으로 확인되지 않았습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

OpenSTA의 2026년 9월 4일 changelog는 `write_path_spice`와 `write_gate_spice`의 `-lib_subckt_file` 인자가 `-lib_subckt_files`로 바뀌었고, 파일 하나 또는 파일 목록을 받을 수 있다고 적었습니다. 두 명령은 정적 타이밍 분석(static timing analysis, STA)에서 문제가 되는 경로나 gate를 골라 SPICE netlist로 꺼냅니다. SPICE netlist는 transistor와 전원·접지·모델 파일을 회로 시뮬레이터가 읽을 수 있는 형태로 적은 회로 설명입니다.

이번 변화가 바꾸는 것은 타이밍 분석의 수학 모델이 아닙니다. 바뀐 곳은 STA 결과를 더 낮은 수준의 회로 시뮬레이션으로 넘기는 연결 지점입니다. 표준셀 library 하나만 쓰는 예제에서는 cell subckt 파일이 하나일 수 있습니다. 그러나 실제 디버그에서는 기본 standard cell, level shifter, filler와 tap, 특수 cell, 별도 macro 주변 cell처럼 transistor-level subckt가 여러 파일에 흩어질 수 있습니다. 예전 인터페이스는 이름부터 단수형이어서, 이런 입력을 쓰려면 하나의 subckt 파일로 합치거나 wrapper script에서 미리 정리해야 했습니다.

공개 Tcl 구현도 이 해석을 뒷받침합니다. `write_path_spice`는 새 도움말에서 `-lib_subckt_files`를 "cell transistor level subckts filename 목록"으로 설명합니다. 기존 `-lib_subckt_file`이 들어오면 deprecation warning을 낸 뒤 같은 내부 변수로 넘깁니다. 이어서 `foreach`로 전달된 파일들을 하나씩 돌며 읽을 수 있는지 검사하고, 통과한 파일을 `lib_subckt_files` 목록에 넣습니다. `write_gate_spice`도 같은 방식으로 plural 인자를 정의하고, 단수형 인자는 경고와 함께 받아 줍니다.

## STA가 찾은 경로를 회로 시뮬레이터로 넘겨야 할 때

STA는 Liberty timing model과 parasitic 정보를 써서 setup, hold, slew, delay를 빠르게 계산합니다. 그래서 전체 chip에서 수많은 path를 훑기에 좋습니다. 하지만 특정 경로가 이상하게 느리거나, model과 실제 transistor 동작 사이의 차이를 더 자세히 보고 싶을 때는 경로 일부를 SPICE로 떼어 회로 시뮬레이션을 돌립니다. OpenSTA의 `write_path_spice`는 `-from`, `-through`, `-to` 같은 path 조건을 받아 해당 timing path의 SPICE 파일과 subckt 파일을 만들어 주는 명령입니다.

이때 엔지니어가 원하는 flow는 "경로를 찾는다"에서 끝나지 않습니다. STA가 골라 준 경로를 ngspice, HSPICE, Xyce 같은 회로 시뮬레이터가 바로 읽을 수 있어야 다음 판단으로 넘어갑니다. 여러 cell subckt 파일을 직접 넘길 수 있으면, path 추출 script는 library 파일 배치를 덜 가정해도 됩니다. PDK나 library package가 subckt를 여러 파일로 나눠 배포하는 경우에도, flow는 그 목록을 그대로 인자로 넘기는 쪽으로 단순해집니다.

## 기존 단수형 인자는 경고와 함께 당분간 받아 줍니다

OpenSTA는 단수형 인자를 바로 없애지 않았습니다. 공개 구현은 `-lib_subckt_file`을 받으면 warning을 내고, 그 값을 새 내부 처리로 넘깁니다. 따라서 기존 회귀 script는 당장 실패하지 않고, CI log나 STA log에서 deprecation warning을 보고 고칠 수 있습니다.

그렇다고 새 이름이 단순한 철자 수정만은 아닙니다. 구현은 `lib_subckt_arg`를 리스트로 보고 각 파일을 순회합니다. 빈 목록이면 에러를 내고, 읽을 수 없는 파일도 파일별로 에러 처리합니다. 이 구조는 명령의 기준을 "한 파일을 요구한다"에서 "여러 입력 파일을 검증해 SPICE writer로 넘긴다"로 바꿉니다.

## 호출부는 고치되 signoff 판단은 그대로 둬야 합니다

OpenSTA나 OpenROAD flow에서 경로 SPICE 추출을 자동화하는 팀은 `write_path_spice`와 `write_gate_spice` 호출부를 찾아 `-lib_subckt_files`로 바꾸는 것이 좋습니다. subckt가 여러 파일로 나뉜 library라면, 지금까지 쓰던 merge script를 유지해야 하는지 다시 볼 만합니다. 다만 이 변경만으로 STA와 SPICE의 correlation이 좋아졌다고 말할 수는 없습니다. 공개 원문은 인터페이스와 파일 처리 방식을 보여 줄 뿐, PPA, runtime, signoff 일치도, simulator별 결과 비교를 제시하지 않습니다.

아직 미뤄야 할 일도 분명합니다. 타이밍 signoff 기준을 바꾸거나, OpenSTA의 SPICE 추출 결과를 상용 signoff flow와 동등하게 보는 판단은 이 근거로 할 수 없습니다. 다음에 확인할 신호는 세 가지입니다. 첫째, OpenSTA 명령 문서와 OpenROAD 문서가 plural 인자로 갱신되는지입니다. 둘째, OpenROAD-flow-scripts나 공개 PDK 예제가 여러 subckt 파일을 넘기는 방식으로 바뀌는지입니다. 셋째, 실제 design에서 생성된 SPICE deck과 simulator log가 공개되어 기존 merge 방식과 같은 결과를 내는지입니다.

## 이해상충과 취재 조건

이 기사는 공개 changelog와 공개 source code만 확인해 작성했습니다. OpenSTA나 OpenROAD 프로젝트, EDA 벤더, foundry, PDK 배포자로부터 계정·라이선스·브리핑·자료를 제공받지 않았습니다. 편집국은 OpenSTA를 빌드하거나 예제 design으로 SPICE 추출을 재실행하지 않았습니다.

## 근거 원장

| claim_id | 주장 | 근거 | 등급 | 한계 |
| --- | --- | --- | --- | --- |
| C1 | OpenSTA changelog는 2026년 9월 4일 `write_path_spice`와 `write_gate_spice`의 `-lib_subckt_file`이 `-lib_subckt_files`로 바뀌었고 파일 하나 또는 목록을 받을 수 있다고 적었다. | OpenSTA `doc/ChangeLog.md`, commit `ef17b3fd81404d685d33ec65e0354c122d701e4d` | E2 | changelog는 사용자-visible 변경 설명이며, 성능 결과를 담지 않는다. |
| C2 | `write_path_spice` 구현은 plural 인자를 정의하고, 단수형 인자가 들어오면 deprecation warning을 낸 뒤 전달된 파일들을 순회해 readable 여부를 검사한다. | OpenSTA `spice/WriteSpice.tcl`, commit `ef17b3fd81404d685d33ec65e0354c122d701e4d` | E2 | 편집국은 실제 명령 실행과 simulator 출력을 재현하지 않았다. |
| C3 | `write_gate_spice` 구현도 plural 인자를 정의하고, 단수형 인자는 warning과 함께 같은 목록 처리로 넘긴다. | OpenSTA `spice/WriteSpice.tcl`, commit `ef17b3fd81404d685d33ec65e0354c122d701e4d` | E2 | gate SPICE 추출 결과 deck의 완전성은 공개 design으로 재실행해야 확인할 수 있다. |
| C4 | 이번 변경은 타이밍 경로나 gate를 SPICE로 넘기는 script의 입력 처리 부담을 줄일 수 있지만, timing signoff 정확도나 PPA 개선을 입증하지는 않는다. | C1-C3에서 파생한 편집 판단 | E2 | 실제 flow 효과는 library 구성, PDK, simulator, design script에 따라 달라진다. |

## 출처

- OpenSTA `doc/ChangeLog.md`, commit `ef17b3fd81404d685d33ec65e0354c122d701e4d`: https://raw.githubusercontent.com/The-OpenROAD-Project/OpenSTA/ef17b3fd81404d685d33ec65e0354c122d701e4d/doc/ChangeLog.md
- OpenSTA `spice/WriteSpice.tcl`, commit `ef17b3fd81404d685d33ec65e0354c122d701e4d`: https://raw.githubusercontent.com/The-OpenROAD-Project/OpenSTA/ef17b3fd81404d685d33ec65e0354c122d701e4d/spice/WriteSpice.tcl
