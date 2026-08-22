---
edition: eda
decision: publish-candidate
title: "VPR-Evolve는 FPGA 배치배선 튜닝을 파라미터 선택에서 VPR 코드 수정으로 넓힙니다"
date: 2026-08-23
subject: "VPR-Evolve arXiv 2607.24998v1과 ASU-VDA-Lab/VPR-Evolve 공개 저장소"
summary: "VPR-Evolve는 LLM 에이전트가 VTR 9의 VPR 배치배선 엔진을 회로별로 고치고, 전체 빌드와 실행 결과를 보고 패치를 남기거나 되돌리는 흐름을 제안했습니다. 공개 논문과 저장소로 방법과 일부 실행 경로를 확인할 수 있지만, 편집국은 장시간 VPR 실행과 100-seed 평가를 재현하지 않았습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

FPGA 설계에서 배치배선은 합성된 회로를 실제 FPGA 구조 위에 놓고 배선을 연결하는 단계다. 이 단계는 설계자가 바로 보는 품질 지표인 critical-path delay, routed wirelength, tool runtime을 크게 흔든다. 지금까지 자동화의 일반적인 출발점은 도구가 이미 공개한 파라미터를 고르는 일이었다. `VPR-Evolve` 논문은 이 범위를 한 단계 넓힌다. 에이전트가 Verilog-to-Routing 9의 `VPR` 소스 코드를 직접 수정하고, 각 후보를 다시 빌드해 배치배선 결과로 판단하는 방식이다.

이 변화가 의미 있는 이유는 자동 튜닝의 목표가 “좋은 옵션 찾기”에서 “회로에 맞는 도구 변형 만들기”로 바뀌기 때문이다. 논문 저자들은 다섯 개 VTR 9 benchmark 회로에서 VPR-Evolve가 stock VPR보다 composite score를 최대 2.7% 낮췄고, critical-path delay는 최대 9.8%, routed wirelength는 최대 18.1%, VPR runtime은 최대 79.3% 줄였다고 보고했다. 이 수치는 저자 실험 결과이며, 편집국이 같은 장비와 seed로 재실행한 독립 검증은 아니다.

## 파라미터 튜닝만으로는 알고리즘이 그대로 남습니다

VPR은 FPGA architecture 파일과 technology-mapped circuit을 입력으로 받는다. 이후 packing, placement, routing, timing analysis를 수행한다. 여기서 packing은 LUT, flip-flop, memory 같은 원소를 FPGA의 논리 블록에 묶는 일이고, placement는 그 블록을 물리 위치에 놓는 일이다. routing은 배치된 블록 사이의 연결을 실제 배선 자원에 할당한다.

기존 자동 튜닝은 이 흐름에서 도구가 밖으로 내놓은 조정값을 바꾼다. 예를 들어 timing과 wirelength를 얼마나 강하게 볼지, simulated annealing의 내부 반복을 얼마나 늘릴지, router의 A* 탐색 가중치를 어떻게 둘지 정한다. 이런 방식은 안전하고 재현하기 쉽지만, 도구 안에 이미 구현된 행동만 고를 수 있다. 회로마다 병목이 다른데도 packing, placement, routing의 알고리즘 구조 자체는 고정된 채 남는다.

VPR-Evolve는 파라미터가 아니라 VPR 코드 자체를 바꾼다. Planner가 수정 방향을 제안하고, Coder가 VPR 코드를 고치며, Reviewer가 전체 실행 결과를 보고 유지할지 되돌릴지 판단한다. Inspiration Collector는 탐색이 막힐 때 논문이나 기존 코드에서 새 아이디어를 가져온다. 후보는 단순 컴파일이 아니라 VPR build와 target design 실행을 통과해야 한다. 평가는 critical-path delay, routed wirelength, runtime을 합친 점수로 이뤄진다.

## 도구 코드도 설계 변수로 다룹니다

논문이 보여 주는 핵심은 에이전트가 RTL이나 constraint만 고치지 않는다는 점이다. 이 방식은 CAD 도구의 내부 알고리즘까지 설계자가 탐색할 대상으로 둔다. 출력도 하나의 옵션 파일이 아니다. 최종 결과는 특정 회로에 맞게 바뀐 VPR 구현, hyperparameter 설정, 그리고 어떤 패치를 시도했고 왜 남겼는지 보여 주는 git history다.

공개 저장소에서도 이 구조를 확인할 수 있다. `ASU-VDA-Lab/VPR-Evolve` 저장소는 `launch_experiments.sh`, `.vpr-evolve/scripts/loop-driver.sh`, `.vpr-evolve/agents/`, VTR submodule, 회로별 tournament 파일과 일부 transfer evaluation 결과를 포함한다. 저장소의 `.vpr-evolve/README.md`는 Codex, Claude Code, OpenCode, Pi 같은 coding agent가 실행 주체라고 설명한다. 이 agent들은 회로별 worktree에서 한 phase씩 VPR 수정과 평가를 반복한다.

이 설계는 EDA agent 평가에도 다른 질문을 던진다. 에이전트가 Verilog를 잘 쓰는지만 보는 대신, 비싼 place-and-route 실행을 몇 번 써야 하는지, 어떤 실패 패치를 되돌렸는지, 회로가 바뀌었을 때 패치가 옮겨 가는지를 볼 수 있다. VPR-Evolve가 남기는 작은 source patch와 annotated evolution trail은 사람이 이런 판단을 검토할 수 있게 해 주는 기록이다.

## 성능 숫자는 저자 실험 조건 안에서 읽어야 합니다

저자들은 VTR 9 benchmark 다섯 개를 썼고, 후보 평가에는 seed 여러 개를 사용했다. 논문 표에는 `LU8`, `bgm`, `sv2`, `LU32`, `mcml`의 critical-path delay, routed wirelength, runtime이 stock VTR 9 VPR, VPR-Evolve, AutoTuner baseline으로 나뉘어 나온다. VPR-Evolve는 모든 회로에서 geometric-mean critical-path delay가 가장 낮았다고 보고됐다.

다만 이것을 “모든 FPGA flow에서 LLM이 VPR을 더 좋게 고친다”로 읽으면 과하다. composite score는 CPD 0.5, wirelength 0.2, runtime 0.3의 가중치로 정의됐다. 이 수치는 선택한 회로와 architecture, fixed channel width, seed 정책 안에서 나온 결과다. 저장소에 공개된 일부 transfer evaluation 결과는 한 branch를 다른 회로에 옮겼을 때 모두 개선되지는 않는다는 점도 보여 준다. 즉 이 연구의 강점은 일반 승자 선언이 아니라, 도구 코드 수정과 실행 로그를 한 흐름 안에 묶은 점이다.

재현성도 조건이 붙는다. 논문과 저장소는 실행 스크립트, VTR submodule, agent prompt와 평가 파일 일부를 공개했다. 반면 setup 문서는 Lmod cluster, GCC 12.5.0, Eigen, oneTBB, scratch storage, 장시간 실행 예산을 전제로 한다. 편집국은 저장소 구조와 원문 수치를 확인했지만, VPR build와 multi-seed place-and-route를 기사 작성 과정에서 재실행하지 않았다.

## 설계팀은 평가 기록부터 점검할 수 있습니다

지금 할 일은 이 방법을 tapeout flow에 바로 넣는 것이 아니다. 내부 CAD 연구와 flow 자동화 실험에서 무엇을 평가 기록으로 남길지부터 바꿔 볼 수 있다. 이미 VTR, OpenROAD, Yosys 같은 공개 도구로 실험하는 팀이라면 agent가 남긴 source patch, 되돌린 patch, seed별 QoR 분산, 실행 비용을 함께 저장하는 평가 harness를 먼저 점검할 만하다.

상용 signoff flow에 같은 방식을 그대로 적용한다는 판단은 아직 이르다. VPR-Evolve는 FPGA 연구용 CAD flow인 VTR 9의 VPR을 대상으로 했고, 논문 수치는 저자 환경의 benchmark 결과다. foundry rule, signoff DRC/LVS, timing closure, 전력 분석이 걸린 ASIC production flow에서는 source-code evolution의 권한, 검증 책임, 라이선스 경계가 훨씬 무겁다.

다음에 확인할 신호는 세 가지다. 첫째, 같은 저장소 commit과 seed로 외부 팀이 VPR-Evolve 결과를 재실행했는지다. 둘째, 회로별로 특화된 패치와 여러 회로에 옮겨도 이득이 남는 패치가 어떻게 갈리는지다. 셋째, LLM token 비용과 place-and-route 실행 비용을 합친 총비용이 사람이 기존 튜닝을 하는 비용보다 낮아지는 조건이다.

## 이해상충과 취재 조건

이해상충은 확인된 것이 없다. 중심 근거는 논문 저자들이 공개한 arXiv 원문과 ASU-VDA-Lab의 GitHub 저장소, 그리고 VTR 프로젝트의 공식 문서다. 편집국은 저자나 프로젝트로부터 계정, 장비, 라이선스, 사전 브리핑을 제공받지 않았다.

## 근거 원장

| claim id | 기사 속 주장 | 근거 | 등급 | 한계 |
|---|---|---|---|---|
| C1 | VPR-Evolve는 VPR의 packing, placement, routing 소스 코드를 회로별로 수정하고 전체 VPR build/run으로 후보를 평가한다. | arXiv 2607.24998v1, ASU-VDA-Lab/VPR-Evolve 저장소 | E2 | 논문과 공개 저장소 기반 확인이며, 편집국 실행 재현은 아니다. |
| C2 | 논문 저자들은 다섯 개 VTR 9 benchmark에서 stock VPR 대비 composite score 최대 2.7%, CPD 최대 9.8%, wirelength 최대 18.1%, runtime 최대 79.3% 개선을 보고했다. | arXiv 2607.24998v1 | E2 | 저자 보고 수치다. 독립 재현이나 상용 FPGA flow 일반화 근거는 아니다. |
| C3 | VTR/VPR은 Verilog circuit과 FPGA architecture를 입력으로 받아 synthesis 이후 packing, placement, routing, timing analysis를 수행하는 공개 FPGA CAD flow다. | VTR GitHub README, VTR VPR documentation | E2 | VTR 공식 문서의 일반 설명이며 VPR-Evolve 성능을 입증하지는 않는다. |
| C4 | 공개 저장소에는 실행 스크립트, agent 설정, VTR submodule, 회로별 결과 문서와 일부 transfer evaluation 결과가 있다. | ASU-VDA-Lab/VPR-Evolve GitHub repository, `.vpr-evolve/README.md`, `docs/vpr_committed_changes.md` | E2 | 최상위 README는 매우 짧고, 실행에는 별도 cluster toolchain과 긴 runtime이 필요하다. |

## 출처

- VPR-Evolve 논문: https://arxiv.org/abs/2607.24998
- VPR-Evolve HTML 원문: https://arxiv.org/html/2607.24998
- VPR-Evolve 공개 저장소: https://github.com/ASU-VDA-Lab/VPR-Evolve
- VPR-Evolve 실행 문서: https://github.com/ASU-VDA-Lab/VPR-Evolve/blob/main/.vpr-evolve/README.md
- VPR-Evolve code-change 문서: https://github.com/ASU-VDA-Lab/VPR-Evolve/blob/main/docs/vpr_committed_changes.md
- VTR 공식 저장소: https://github.com/verilog-to-routing/vtr-verilog-to-routing
- VPR 공식 문서: https://docs.verilogtorouting.org/en/latest/vpr/
