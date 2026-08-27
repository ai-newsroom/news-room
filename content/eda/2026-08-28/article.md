---
edition: eda
decision: publish-candidate
title: "TaiWei-Pin-3D는 3D IC 물리설계 연구를 실행 가능한 flow로 공개합니다"
date: 2026-08-28
subject: "CODA-Team TaiWei-Pin-3D public 3D physical-design flow at commit c85b79352eefc31a588da3ef873e4fd68a3df3f2 and RosettaStone 2.0 ISPD 2026 paper"
summary: "TaiWei-Pin-3D는 face-to-face 3D IC 구현 절차를 공개 저장소로 내놓았습니다. OpenROAD 계열 flow와 Cadence flow에 3D stage, tier별 library view, split-net, staged CTS, 결과 JSON을 붙인 형태입니다. 논문과 코드가 함께 공개돼 연구자는 실행 경로를 확인할 수 있지만, 일부 평가는 Cadence 도구와 상용 도구 허가가 필요해 완전한 공개 재현은 제한됩니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["TaiWei-Pin-3D와 RosettaStone 2.0 논문 저자는 flow와 결과의 당사자입니다. 저장소는 Cadence와 Synopsys가 학술 연구 범위에서 일부 저작권 자료 발췌 사용을 허용했다고 밝힙니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

3D IC 물리설계 연구에서 어려운 일은 새 알고리즘을 제안하는 것만이 아닙니다. 같은 설계, 같은 공정 가정, 같은 clock constraint, 같은 배치·배선 뒤처리를 놓고 비교할 수 있어야 합니다. `TaiWei-Pin-3D`는 이 문제를 풀기 위해 face-to-face 3D IC 구현 과정을 실행 가능한 flow로 공개했습니다.

face-to-face 3D IC는 두 개의 die를 서로 마주 보게 붙이고, hybrid bonding terminal, 즉 HBT로 위아래 tier를 연결하는 구조입니다. 이 구조는 배선 길이와 집적도를 바꿀 수 있지만, 기존 2D 물리설계 도구가 바로 이해하는 평면 layout은 아닙니다. TaiWei-Pin-3D의 핵심은 완전히 새 3D router를 만드는 대신 기존 2D 엔진이 다룰 수 있는 표현과 stage를 더한 데 있습니다. 그렇게 해서 3D 문제를 실험 가능한 형태로 낮춥니다.

이 사안을 새 기사로 볼 만한 이유는 논문과 저장소가 서로 다른 역할을 하기 때문입니다. ISPD 2026 논문은 RosettaStone 2.0을 `OpenROAD-Research`와 `ORFS-Research` 위의 benchmark backplane으로 설명했습니다. 또 2D와 Pin-3D 스타일 face-to-face 3D 설계를 같은 평가 계약 아래 비교하려 했다고 보고했습니다. 공개 저장소는 그 설명을 README, 실행 스크립트, stage 문서, platform, design, known issue로 이어 줍니다.

## 3D 구현 절차를 기존 flow 안에 넣습니다

기존 2D RTL-to-GDS flow는 RTL, SDC constraint, Liberty, LEF, DEF, RC rule 같은 입력을 받습니다. 이후 floorplan, place, clock tree synthesis, route, final report로 이어집니다. 3D IC에서는 여기에 tier assignment, 위아래 tier의 library view, HBT 연결, tier별 power delivery network가 추가됩니다. tier를 넘는 clock과 data net을 어떻게 처리할지도 정해야 합니다.

TaiWei-Pin-3D는 3D를 하나의 거대한 black-box 최적화로 밀어 넣지 않습니다. 먼저 2D synthesis와 partition으로 시작한 뒤, partition 결과를 3D floorplan과 IO로 바꿉니다. 그다음 mixed-fanout net을 나누고, 위 tier와 아래 tier를 번갈아 배치·합법화합니다. PDN은 tier별로 만들고, clock tree synthesis는 owner tier와 receive tier 단계로 나눕니다. 마지막 route와 final report는 합쳐진 3D metal stack 위에서 수행합니다.

이 구조에서는 feedback이 stage 단위로 남습니다. 연구자가 새 placer나 split 정책을 제안했을 때 전체 flow가 무너졌는지, 특정 tier 배치에서만 나빠졌는지, HBT 수와 DRC 위반이 어디서 늘었는지 나눠 볼 수 있습니다. 논문 속 PPA 표만으로는 이런 판단을 하기 어렵습니다.

## HBT를 via처럼 모델링해 2D router를 재사용합니다

저장소의 README는 이 flow가 mature 2D engine을 재사용한다고 설명합니다. 핵심 장치는 unified 2D abstraction입니다. HBT를 확장된 metal stack 안의 special via처럼 모델링하면 2D router가 cross-tier connection을 만들 수 있습니다. 여기서 HBT는 두 tier 사이를 잇는 물리적 접점입니다.

이 방식은 새 3D router를 기다리지 않고 실험을 시작하게 해 줍니다. 그렇다고 공정 관점에서 완전한 signoff 모델이라는 뜻은 아닙니다. 연구 flow에서는 HBT와 tier-local metal, RC rule, library view를 어떻게 추상화했는지가 결과의 범위를 정합니다. TaiWei-Pin-3D도 2026년 8월 11일 commit에서 3D routing layer 정렬을 고치며 ASAP7과 NanGate45 기반 3D platform의 routing layer, RCX rule, LEF layer 정의를 조정했습니다.

저장소는 세 가지 대표 3D stack을 공개합니다. NanGate45-NanGate45, ASAP7-ASAP7, NanGate45-ASAP7입니다. 같은 library를 위아래로 복제한 homogeneous stack과 서로 다른 node를 붙인 heterogeneous stack을 모두 둔 점이 중요합니다. 두 경우는 buffer tier 선택, routing resource, timing closure에서 다른 실패 양상을 보일 수 있기 때문입니다.

## 위아래 tier로 흩어진 net을 먼저 쪼갭니다

3D flow에서 까다로운 net은 driver와 sink가 같은 tier에만 있는 net이 아닙니다. sink가 위아래 tier에 흩어진 mixed-fanout net이 더 까다롭습니다. 그냥 두면 하나의 fanout tree가 tier 경계와 tier-local 최적화를 계속 끌고 다닙니다. TaiWei-Pin-3D는 이를 structural `cross-tier` net과 functional `mixed_fanout` net으로 나누어 봅니다.

`cross-tier` net은 실제 물리 view에서 위아래 tier를 잇는 net입니다. HBT 압력을 보는 지표입니다. `mixed_fanout` net은 실제 sink가 위아래 tier에 흩어진 net이며, split-net stage가 줄이려는 대상입니다. 둘을 구분하지 않으면 HBT가 얼마나 필요한지와 fanout 구조가 얼마나 tier-local하게 바뀌었는지를 섞어 보게 됩니다.

split-net stage는 mixed data net에 tier-local buffer를 넣어 한쪽 sink 묶음을 branch net 뒤로 옮깁니다. 이렇게 하면 통제되지 않은 mixed fanout이 하나의 tier 경계와 tier-local branch로 바뀝니다. 저장소의 known issue 문서는 예전 정책이 heavy fanout이나 driver 반대편 배치만 보면서 heterogeneous stack에서 비싼 tier를 과하게 쓸 수 있었다고 적습니다. 현재 정책은 tier utilization, extra HBT proxy, buffer area를 함께 보는 가벼운 비용식을 씁니다.

여기서도 한계는 분명합니다. 이 비용식은 final routed HBT count나 routing congestion을 예측하지 않습니다. global utilization도 근사치입니다. 따라서 이 기사는 split 정책이 HBT 수를 최적으로 낮춘다고 쓰지 않습니다. 확인된 변화는 mixed-fanout 문제를 flow의 공개 stage로 꺼내고, 그 stage가 어떤 cost proxy를 쓰는지 설명했다는 점입니다.

## 실행 경로는 공개됐지만 일부 평가는 상용 도구가 필요합니다

TaiWei-Pin-3D는 공개 저장소라는 점에서 많은 EDA 연구 발표보다 한 단계 나아갑니다. README는 테스트한 ORFS-Research commit을 `568eb04da9173695d6bfc1b10ba868e0b6b8a9fa`, bundled OpenROAD commit을 `305d3ba2ddfd00591924cc586ad408179f566afe`로 고정합니다. GCD 예제를 OpenROAD flow와 Cadence flow에서 실행하는 명령도 제공합니다.

test 문서는 더 구체적입니다. `run_case.sh`로 한 case 전체를 돌리고, `run_stage.sh`로 route나 final 같은 한 stage만 다시 실행하며, `eval_case.sh`로 기존 결과를 평가할 수 있습니다. 내부 CI는 OpenROAD-origin 결과와 Cadence 평가 JSON, Cadence-origin 결과와 Cadence restore JSON을 비교하는 계약을 둡니다. 이 정도면 논문 방법을 읽는 데서 그치지 않고 실행 경로를 검사할 수 있습니다.

다만 완전한 공개 재현이라고 부르기는 어렵습니다. 저장소는 Open-source PD tools와 함께 Cadence Innovus `v21.39`, Genus `v21.39`를 지원 도구로 적습니다. test 문서도 OpenROAD-origin 결과에 Cadence `cds-final` 평가를 붙이는 비대칭 평가 계약을 설명합니다. 상용 도구가 없는 연구자는 OpenROAD 경로 일부를 볼 수 있지만, 논문·저장소가 의도한 모든 비교와 평가를 같은 조건으로 반복하기 어렵습니다.

라이선스와 저작권 경계도 남습니다. README는 commercial EDA tool을 호출하는 TCL script의 header notice를 확인하라고 안내합니다. 또 Cadence와 Synopsys가 학술 연구 맥락에서 일부 저작권 자료 발췌 사용을 허용했다고 밝힙니다. 따라서 기업 flow에 바로 가져다 쓰기 전에는 도구 라이선스, PDK 사용권, script 재배포 조건을 따로 확인해야 합니다.

## 연구자는 어느 stage를 바꿨는지 보여 줄 수 있습니다

이 공개의 의미는 3D IC가 곧바로 쉬워졌다는 데 있지 않습니다. 비교 단위가 바뀐 데 있습니다. 이제 연구자는 placer 하나, router 하나, tier partition 정책 하나를 논문 안의 독립 실험으로만 제시하지 않아도 됩니다. stage-managed RTL-to-GDS flow 안에서 어느 handoff와 어느 metric을 바꿨는지 보여 줄 수 있습니다.

실무 팀에도 신호가 있습니다. 3D IC 도입을 검토하는 조직은 전체 signoff 가능성만 물으면 답을 얻기 어렵습니다. 먼저 어떤 tier abstraction을 쓰는지, mixed fanout을 언제 쪼개는지, clock tree를 owner와 receive 단계로 나누는지 봐야 합니다. final report가 HBT와 DRC를 어떻게 분리해 보여 주는지도 확인해야 합니다. TaiWei-Pin-3D는 이런 질문 목록을 구체적인 stage 이름으로 바꿔 줍니다.

지금은 공개 flow를 benchmark와 교육용 기준선으로 보는 편이 맞습니다. OpenROAD 경로의 GCD나 IBEX 같은 작은 design부터 실행 가능성을 확인하고, 결과 JSON과 handoff 파일이 어느 stage에서 만들어지는지 살필 수 있습니다. 논문이나 README만 보고 commercial signoff flow를 대체한다고 판단할 단계는 아닙니다. 다음에 확인할 신호는 독립 연구팀의 재실행 로그, 상용 도구 없이 닫히는 평가 경로, ariane133 같은 macro-heavy design blocker의 해소, HBT·thermal·IR drop을 더 깊게 포함한 signoff 조건입니다.

## 이해상충과 취재 조건

TaiWei-Pin-3D 저장소와 RosettaStone 2.0 논문의 저자는 이 flow와 평가 방식의 당사자입니다. 논문은 physical design research benchmark의 재현성을 높이려는 방법과 초기 결과를 보고하는 1차 자료이고, 저장소는 코드와 문서를 제공하는 실행 가능한 1차 자료입니다. 이 기사는 저자 보고 결과를 독립 재현으로 바꾸어 쓰지 않았습니다.

저장소는 Cadence와 Synopsys가 학술 연구 맥락에서 일부 저작권 자료 발췌 사용을 허용했다고 밝힙니다. 이 관계는 flow의 공개 범위와 사용 조건을 읽을 때 중요한 이해상충이자 접근 조건입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. RosettaStone 2.0 논문은 2D와 Pin-3D face-to-face 3D 설계를 같은 OpenROAD-Research·ORFS-Research 기반 평가 backplane에서 비교하려는 방법을 제시했습니다. | E2 · P1/P2 · R2 | arXiv/ACM 논문과 TaiWei-Pin-3D 저장소를 함께 확인했습니다. 논문의 모든 실험 로그를 직접 재실행하지는 않았습니다. |
| C2. TaiWei-Pin-3D는 OpenROAD 계열 flow와 Cadence flow를 대상으로 3D floorplan, IO, split-net, tier별 placement, staged CTS, route, final report를 공개 stage로 둡니다. | E2 · P2 · R2 | README와 OpenROAD 3D strategy 문서의 stage graph, test entry point를 확인했습니다. 일부 Cadence 경로는 상용 라이선스가 필요합니다. |
| C3. 이 flow는 HBT를 확장된 metal stack의 via처럼 모델링하고, tier-specific library view와 COVER view로 기존 2D 엔진을 3D-aware하게 사용합니다. | E2 · P2 · R2 | README와 strategy 문서의 3D enablement 설명을 확인했습니다. 이 추상화가 실제 공정 signoff와 같은 정확도를 낸다는 독립 근거는 없습니다. |
| C4. 저장소는 mixed-fanout net과 cross-tier net을 구분하고, split-net stage에서 tier utilization, HBT proxy, buffer area를 함께 보는 비용식을 사용합니다. | E2 · P2 · R2 | README, strategy 문서, issue 문서의 split-net 설명과 한계를 확인했습니다. 비용식은 final routed HBT count나 congestion 예측기가 아닙니다. |
| C5. 2026년 8월 11일 최신 commit은 3D routing layer 정렬을 위해 ASAP7/Nangate45 기반 platform의 routing layer, RCX rule, LEF layer 정의를 조정했습니다. | E2 · P2 · R2 | GitHub commit API와 commit diff를 확인했습니다. 이 commit의 QoR 효과나 DRC 개선은 별도로 재현하지 않았습니다. |
| C6. 공개 재현성은 논문만 있는 경우보다 높지만, Cadence Innovus/Genus와 일부 저작권 자료 사용 조건 때문에 모든 평가를 완전 공개 환경에서 반복할 수는 없습니다. | E2 · P2 · R2 | README의 supported tools, test README의 평가 계약, README의 저작권 허가 고지를 확인했습니다. 라이선스 세부 조건은 각 도구 계약에 따릅니다. |

## 출처

1. arXiv, `Invited: Toward Sustainable and Transparent Benchmarking for Academic Physical Design Research`: https://arxiv.org/abs/2601.17520
2. ACM Digital Library, `Invited: Toward Sustainable and Transparent Benchmarking for Academic Physical Design Research`: https://dl.acm.org/doi/10.1145/3764386.3779611
3. CODA-Team, `TaiWei-Pin-3D` 저장소: https://github.com/CODA-Team/TaiWei-Pin-3D
4. CODA-Team, `TaiWei-Pin-3D` README: https://raw.githubusercontent.com/CODA-Team/TaiWei-Pin-3D/main/README.md
5. CODA-Team, OpenROAD 3D Co-Optimization Strategy: https://raw.githubusercontent.com/CODA-Team/TaiWei-Pin-3D/main/DOC/openroad_3d_cooptimization_strategy.md
6. CODA-Team, Test Script Guide: https://raw.githubusercontent.com/CODA-Team/TaiWei-Pin-3D/main/test/README.md
7. CODA-Team, Known issues and limitations: https://raw.githubusercontent.com/CODA-Team/TaiWei-Pin-3D/main/DOC/issue.md
8. GitHub API, latest TaiWei-Pin-3D commit `c85b79352eefc31a588da3ef873e4fd68a3df3f2`: https://api.github.com/repos/CODA-Team/TaiWei-Pin-3D/commits/main
