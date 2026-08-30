---
edition: eda
decision: publish-candidate
title: "ReviewDSE는 OpenROAD 튜닝을 옵션 조합에서 보호된 소스 수정으로 넓힙니다"
date: 2026-08-31
subject: "ReviewDSE protected white-box DSE for OpenROAD detailed placement, arXiv:2607.11294v4 and DPLEvolve-AE artifact at commit fca145292478431412aff93bbae9f011f0387508"
summary: "ReviewDSE는 공개 EDA 도구의 설계 공간 탐색을 command option과 flow script 조합에서 소스 코드 수준의 mechanism 탐색으로 넓힙니다. 이때 검증 경로는 보호된 평가기 안에 고정합니다. 논문은 OpenROAD detailed placement에서 HPWL과 strict legality 결과를 보고했고, DPLEvolve-AE artifact는 고정 tool revision과 재현 스크립트를 공개했습니다. 다만 편집국은 긴 실행과 모델 비용이 필요한 실험을 재현하지 않았고, timing·congestion·power·signoff까지 확인된 결과로 보지는 않습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["ReviewDSE 논문과 DPLEvolve-AE artifact 저자는 방법과 결과의 당사자입니다. 논문은 AI for Science Program, Shanghai Municipal Commission of Economy and Informatization, Fudan Kunpeng&Ascend Center of Cultivation의 지원을 받았다고 밝힙니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

EDA 도구 튜닝은 보통 이미 노출된 option, seed, script 순서를 바꾸는 일로 시작합니다. `ReviewDSE`는 이 경계를 한 단계 안쪽으로 옮깁니다. OpenROAD처럼 소스 코드가 공개된 도구라면, 상세 배치 엔진의 내부 정책도 설계별 탐색 대상이 될 수 있다는 주장입니다. 단, 아무 코드나 바꾸는 방식은 아닙니다. benchmark 입력, 실행 순서, metric parser, legality check를 보호된 평가기 안에 고정합니다. 후보 소스가 이 경계를 건드리면 탈락합니다.

이 변화가 중요한 이유는 설계 공간 탐색, 즉 DSE의 단위가 달라지기 때문입니다. 기존 black-box DSE는 도구를 고정된 실행 파일로 보고 public knob을 조합합니다. ReviewDSE가 말하는 white-box DSE는 도구 내부의 합법화 정책, local repair, move scoring, rollback, stage handoff 같은 source-level mechanism을 후보로 다룹니다. 한국어로 풀면, 도구 사용법만 고르는 것이 아니라 도구 안의 작은 의사결정 방식을 설계별로 바꿔 본다는 뜻입니다.

논문과 artifact가 함께 공개된 점도 발행 근거입니다. arXiv 논문 `2607.11294v4`는 MLCAD 2026 논문으로 표시되며, OpenROAD detailed placement를 대상으로 한 방법과 저자 보고 결과를 담고 있습니다. `DPLEvolve-AE` 저장소와 Zenodo record는 재현 workflow, selected source program, Table 4와 Table 6 실행 경로, 고정 OpenROAD·ORFS·Yosys revision을 공개합니다. 그래서 이 기사는 단순 발표가 아니라 논문과 실행 artifact가 맞물린 공개 연구로 다룹니다.

## 도구 내부의 선택지를 설계별로 바꿉니다

칩 구현 flow에서 detailed placement는 global placement 뒤의 cell 위치를 더 촘촘하게 다듬는 단계입니다. 이때 도구는 cell overlap을 없애는 strict legality, wirelength, displacement, runtime 사이에서 계속 절충합니다. 기존 DSE는 `detailed_placement` 명령의 option, flow script, seed처럼 바깥에 드러난 제어 항목을 바꾸며 더 나은 점을 찾습니다.

ReviewDSE는 같은 문제를 다르게 자릅니다. OpenROAD의 detailed placement 구현을 대상으로 삼고, candidate source tree를 새로 빌드한 뒤 같은 flow에서 평가합니다. 후보는 stage가 상태를 초기화하는 방식, move를 고르는 방식, repair를 적용하는 방식, 다음 stage로 넘기는 handoff state를 바꿀 수 있습니다. 여기서 mechanism은 stage 이름 자체가 아니라 source-level logic chain입니다.

이 접근은 실무적으로 매력적이지만 위험합니다. 소스 코드를 바꾸면 metric parser를 우회하거나, legality check를 약하게 만들거나, stale binary로 잘못된 결과를 낼 수 있습니다. 논문이 protected evaluator를 앞세운 이유가 여기에 있습니다. 평가기는 입력, top-level command sequence, baseline harness, checker, metric parser, runtime gate, 관련 없는 tool component를 고정합니다. 후보가 build에 실패하거나, strict legality를 깨거나, canonical metric을 빠뜨리거나, runtime gate를 넘으면 promotion되지 않습니다. 주장한 mechanism의 liveness evidence를 남기지 못해도 탈락합니다.

## agent가 코드를 만들고 평가기가 걸러 냅니다

ReviewDSE workflow는 두 단계입니다. Level 1은 calibration design에서 method evidence와 source-start branch를 만듭니다. Level 2는 target design마다 이 frozen evidence를 초기 힌트로 삼고, Teacher-Student agent loop를 돌립니다. Teacher는 전체 flow 결과와 mechanism evidence를 검토합니다. Student는 source start를 고치거나, 다른 후보의 mechanism을 참고하거나, 실패한 edit를 수리합니다.

핵심은 agent가 직접 점수를 결정하지 않는다는 점입니다. agent는 candidate source를 만들고 설명합니다. 하지만 후보가 승격되려면 보호된 평가기의 build, full-flow run, metric, legality, runtime, liveness 기록을 통과해야 합니다. 이 구조가 없으면 “LLM이 도구를 고쳤다”는 말은 재현 가능한 EDA 결과가 아니라 코드 생성 demo에 머물기 쉽습니다.

DPLEvolve-AE artifact는 이 구조를 재현 대상으로 묶었습니다. README는 Table 4의 QoR와 runtime 비교, Table 5의 stage composability, Table 6의 hard cut-row legality repair, ReviewDSE search, figure 재생성 절차를 나눠 적습니다. Table 4 경로는 OpenROAD default, 400-trial Optuna-TPE baseline, ReviewDSE-HPWL, runtime-aware ReviewDSE-GHR을 아홉 design/platform target에서 비교합니다. Table 6 경로는 Diamond, Negotiation, frozen ReviewDSE repair program을 아홉 cut-row pattern에서 실행합니다.

재현성은 `R2`로 봅니다. 공개 code, script, expected output, provenance가 있고, Zenodo에는 약 213 MB archive가 올라와 있습니다. 저장소는 BSD-3-Clause license이고 Zenodo record는 open access입니다. 다만 전체 paper-scale search에는 인증된 Codex/API access와 큰 token budget이 필요합니다. reference system은 Rocky Linux 8.10, Xeon Platinum 8462Y+ 두 개, 314 GiB RAM, 22 TiB home filesystem로 적혀 있습니다. 논문 appendix와 requirements 문서는 GPU, 상용 EDA license, proprietary PDK가 필요하지 않다고 설명합니다. 그러나 완전 실행은 작은 노트북 작업으로 보기 어렵습니다.

## HPWL은 줄었지만 signoff를 뜻하지는 않습니다

논문은 아홉 target task에서 ReviewDSE가 final post-DPL HPWL을 평균 1.78% 줄였다고 보고했습니다. 같은 2배 runtime gate 안에서 public-knob black-box DSE는 평균 0.38% 개선으로 제시됐습니다. runtime-aware 선택은 평균 HPWL 개선 1.68%를 유지하면서 평균 runtime을 1.34배에서 1.11배로 낮췄다고 적었습니다. HPWL은 half-perimeter wirelength의 약자이며, 배선될 net의 bounding box 둘레를 이용해 배선 길이를 근사하는 배치 단계 지표입니다.

이 수치는 저자 보고 결과입니다. 편집국은 Table 4와 Table 6을 재실행하지 않았고, 독립 연구팀의 재현 로그도 확인하지 못했습니다. 그래서 이 기사는 ReviewDSE가 OpenROAD detailed placement 전체에서 항상 더 낫다고 쓰지 않습니다. 확인된 중심 변화는 source-level mechanism을 보호된 평가기 아래에서 탐색하고, 그 절차와 일부 결과를 실행 가능한 artifact로 공개했다는 점입니다.

한계도 분명합니다. 논문은 현재 결과가 HPWL, runtime, displacement, strict legality를 다룬다고 밝힙니다. timing, congestion, power, signoff는 추가 metric이 필요합니다. physical design 실무에서는 HPWL이 좋아져도 timing closure나 congestion, DRC, IR drop이 나빠질 수 있습니다. ReviewDSE가 stage-local winner를 바로 채택하지 않고 full-flow review를 강조하는 이유도 이와 맞닿아 있습니다. 한 단계에서 좋아 보이는 legalizer가 downstream detailed-placement optimization을 거치면 final HPWL을 악화시킬 수 있기 때문입니다.

## 실패하던 배치를 고친 사례가 더 실무에 가깝습니다

Table 6의 hard cut-row repair는 평균 HPWL보다 실무 판단에 더 가까운 신호를 줍니다. cut-row pattern은 row topology를 일부 끊어 기존 route가 strict legal solution을 찾기 어렵게 만든 stress test입니다. 논문은 Ariane133, SWERV dense, BPQUAD의 아홉 pattern에서 ReviewDSE가 모두 strict legal placement를 만들었다고 보고했습니다. BPQUAD에서는 fixed reference가 실패하거나 7200초 cap에 걸렸고, ReviewDSE는 563.6초에서 1085.0초 사이에 strict repair를 냈다고 적었습니다.

이 결과가 곧 signoff 성공은 아닙니다. 그래도 source-level DSE가 왜 필요한지 보여 주는 장면입니다. public knob만 조합해도 되는 경우라면 굳이 optimizer 내부를 건드릴 이유가 약합니다. 반대로 특정 design과 topology에서 fixed source가 legality를 회복하지 못한다면, 합법화와 local repair의 내부 mechanism을 바꾸는 탐색이 의미를 가질 수 있습니다.

실무 팀은 이 기술을 production flow 교체 후보가 아니라 open-source EDA 최적화 연구의 검증 방식으로 보는 편이 맞습니다. 지금 할 일은 작은 target 하나에서 `make doctor`, pinned tool build, default run, selected-source replay를 순서대로 확인하는 것입니다. 저자 보고 HPWL 수치를 tapeout 의사결정의 근거로 쓰는 일은 아직 미뤄야 합니다. 다음에 확인할 신호는 독립 재현 로그, timing·congestion·power를 포함한 protected metric 확장, OpenROAD upstream에 들어간 mechanism, paper-scale search 비용을 줄인 반복 실험입니다.

## 이해상충과 취재 조건

ReviewDSE 논문과 DPLEvolve-AE artifact 저자는 방법과 결과의 당사자입니다. 논문은 AI for Science Program, Shanghai Municipal Commission of Economy and Informatization, Fudan Kunpeng&Ascend Center of Cultivation의 지원을 받았다고 밝힙니다. 이 기사는 저자 보고 수치를 독립 검증으로 바꾸어 쓰지 않았습니다.

이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 웹 원문과 API 응답만 사용했습니다. 편집국은 OpenROAD flow와 agent search를 실행하지 않았습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. ReviewDSE는 OpenROAD detailed placement의 DSE를 public knob 탐색에서 protected evaluator 아래의 source-level mechanism 탐색으로 확장합니다. | E2 · P1/P2 · R2 | arXiv 논문과 DPLEvolve-AE README·provenance를 함께 확인했습니다. 방법과 결과는 저자 보고이며 편집국 재실행은 없습니다. |
| C2. protected evaluator는 입력, command sequence, checker, metric parser, runtime gate를 고정하고, 후보가 평가 경로를 바꾸거나 canonical metric·legality·liveness 조건을 놓치면 탈락시키는 경계입니다. | E2 · P1/P2 · R2 | 논문의 방법 설명과 artifact의 실행·acceptance 문서를 대조했습니다. 실제 로그 검증은 수행하지 않았습니다. |
| C3. 논문은 아홉 target에서 ReviewDSE가 평균 post-DPL HPWL 1.78% 개선, runtime-aware 선택 1.68% 개선과 1.11배 평균 runtime을 보고했습니다. | E2 · P1/P2 · R2 | arXiv HTML의 Table 4 설명과 artifact의 Table 4 재현 README를 확인했습니다. 독립 재현이나 편집국 재현은 아닙니다. |
| C4. 논문은 hard cut-row stress test 아홉 pattern에서 ReviewDSE가 strict legal placement를 모두 만들었다고 보고했고, artifact는 Table 6의 27-run 실행 경로와 data package 조건을 공개합니다. | E2 · P1/P2 · R2 | 논문의 Table 6 설명과 artifact README를 확인했습니다. timing·congestion·power·signoff 성공으로 확대하지 않습니다. |
| C5. DPLEvolve-AE는 공개 GitHub 저장소와 Zenodo archive로 배포되며, OpenROAD·ORFS·Yosys 등 주요 source revision을 고정합니다. | E2 · P2 · R2 | GitHub API, README, provenance/source-commits.json, Zenodo API를 확인했습니다. paper-scale agent search에는 인증된 모델/API 접근과 큰 계산·token 비용이 필요합니다. |

## 출처

1. arXiv, `From Tool Invocation to Source-Mechanism Exploration: Protected White-Box DSE for Open-Source EDA`: https://arxiv.org/abs/2607.11294
2. arXiv HTML, `2607.11294v4`: https://arxiv.org/html/2607.11294v4
3. GitHub, `yuan-fd/DPLEvolve-AE`: https://github.com/yuan-fd/DPLEvolve-AE
4. DPLEvolve-AE README: https://raw.githubusercontent.com/yuan-fd/DPLEvolve-AE/main/README.md
5. DPLEvolve-AE source provenance: https://raw.githubusercontent.com/yuan-fd/DPLEvolve-AE/main/provenance/source-commits.json
6. DPLEvolve-AE requirements: https://raw.githubusercontent.com/yuan-fd/DPLEvolve-AE/main/docs/requirements.md
7. DPLEvolve-AE Table 4 README: https://raw.githubusercontent.com/yuan-fd/DPLEvolve-AE/main/artifacts/01-table4-qor/README.md
8. DPLEvolve-AE Table 6 README: https://raw.githubusercontent.com/yuan-fd/DPLEvolve-AE/main/artifacts/03-table6-cutrow/README.md
9. Zenodo API, `DPLEvolve-AE`: https://zenodo.org/api/records/21629308
10. GitHub API, latest `DPLEvolve-AE` commit: https://api.github.com/repos/yuan-fd/DPLEvolve-AE/commits/main
