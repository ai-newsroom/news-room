---
edition: ai
decision: publish-candidate
title: "NVIDIA AVO 공개 - 장기 에이전트 평가는 모델보다 실행 루프를 봐야 합니다"
date: 2026-08-23
subject: "NVIDIA AVO applied to ARC-AGI-3 public set, August 21 2026"
summary: "NVIDIA는 AVO를 ARC-AGI-3 public set에 적용해 Claude Opus 5를 장기 상호작용 agent로 운용한 결과를 공개했습니다. 이 공개에서 확인되는 변화는 특정 모델의 점수 상승이 아니라, persistent memory, supervisor, 실행 피드백을 묶은 harness가 모델 호출을 여러 단계 작업으로 바꾸는 방식입니다. 100.00 RHAE와 GPU kernel 최적화 수치는 NVIDIA 자체 실행 결과이므로 독립 재현으로 다루지 않습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["NVIDIA는 AVO 연구와 2026년 8월 21일 기술 블로그의 작성 주체입니다. ARC Prize Foundation은 ARC-AGI-3 benchmark와 toolkit의 운영 주체입니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

NVIDIA가 2026년 8월 21일 AVO(Agentic Variation Operators)를 ARC-AGI-3 public set에 적용한 결과를 공개했습니다. 이 소식의 핵심은 Claude Opus 5가 갑자기 더 강해졌다는 주장이 아닙니다. 같은 모델이라도 한 번 호출해 답을 받는 방식이 아니라 기억, 감독, 도구 사용, 실행 피드백을 갖춘 장기 작업 loop 안에서 쓰면 평가 대상이 모델에서 agent system으로 바뀐다는 점입니다.

AVO는 원래 GPU kernel 최적화에서 나온 연구입니다. 논문은 고정된 mutation이나 crossover를 쓰는 대신 coding agent가 이전 후보, 실행 로그, domain 지식을 보고 다음 변형을 스스로 만들게 했다고 설명합니다. NVIDIA의 새 글은 같은 구조를 ARC-AGI-3라는 상호작용 benchmark로 옮겼습니다. agent가 규칙을 모르는 환경에서 행동하고 관찰한 뒤 다음 행동을 고르는 작업에 AVO를 썼다는 내용입니다.

이 기사의 중심 주장은 공개 논문, NVIDIA 기술 블로그, ARC-AGI-3 문서와 toolkit으로 확인할 수 있는 구조에 한정합니다. NVIDIA는 AVO가 ARC-AGI-3 public set 25개 환경 183개 level을 모두 완료해 100.00 RHAE를 기록했다고 밝혔지만, 이 수치는 NVIDIA가 실행한 결과입니다. 편집국은 같은 harness를 실행하지 않았고 AVO code도 확인하지 못했습니다. 따라서 성능 우월성을 말하기보다, 장기 agent를 설계할 때 무엇을 기록하고 제어해야 하는지를 설명합니다.

## 한 번 답하는 모델에서 계속 고치는 실행자로 바뀝니다

일반적인 LLM 평가에서는 모델이 prompt를 받고 답을 냅니다. coding agent나 업무 agent에서는 이 구조가 금방 부족해집니다. agent는 파일을 읽고, 코드를 고치고, 테스트를 돌리고, 실패 원인을 다시 찾아야 합니다. 한 번의 context 안에서 모든 것을 끝내기보다 여러 번 행동하면서, 그때마다 무엇을 배웠는지 남겨야 합니다.

AVO가 바꾸는 지점은 여기입니다. NVIDIA 블로그는 AVO의 main agent가 context를 살피고, 계획하고, 구현하고, 평가하는 loop를 반복한다고 설명합니다. persistent memory는 이전 구현, 평가 결과, compiler와 profiler output, reasoning을 다음 시도에 넘기는 저장 장치입니다. supervisor는 반복적으로 막히거나 진전이 없을 때 더 넓은 탐색 방향을 감시하고 조정합니다.

이 구조는 “더 긴 context window를 쓰면 된다”와 다릅니다. 긴 context는 더 많은 내용을 한 번에 넣는 수단입니다. AVO가 강조하는 memory는 긴 작업에서 어떤 관찰을 다음 시도에 남길지, 어떤 실패를 반복하지 않을지, 어떤 후보 lineage를 살릴지 정하는 실행 상태입니다. SW 엔지니어가 같은 작업을 다시 분석하려면 model ID만 남겨서는 부족합니다. agent loop의 state, tool 결과, supervisor 개입, 실패 판정 기준을 함께 기록해야 합니다.

## GPU kernel 최적화 방식이 ARC-AGI-3에도 쓰였습니다

AVO 논문의 첫 실험은 attention kernel 최적화입니다. NVIDIA 연구진은 AVO가 NVIDIA Blackwell B200 GPU에서 7일 동안 multi-head attention kernel을 자동으로 탐색했고, 500개가 넘는 최적화 방향과 40개의 commit된 kernel version을 만들었다고 보고했습니다. 논문과 블로그는 이 실험에서 cuDNN과 FlashAttention-4 대비 개선 수치를 제시하지만, 이 기사는 그 수치를 독립 성능 결론으로 쓰지 않습니다.

중요한 것은 task의 모양입니다. kernel 최적화에서는 작은 code change가 correctness, memory access, scheduling, throughput을 바꿉니다. agent는 가설을 세우고, 코드를 바꾸고, benchmark를 실행하고, profiler 결과를 읽고, 실패하면 되돌아가야 합니다. 이 흐름은 사람이 성능을 튜닝할 때 반복하는 작업 단위와 닮았습니다.

ARC-AGI-3는 겉보기에는 전혀 다른 문제입니다. agent는 명시적인 규칙이나 목표 설명 없이 낯선 game-like environment에 들어갑니다. 그 안에서 행동을 시도하고, 환경이 어떻게 바뀌는지 관찰하며, 목표를 추론해야 합니다. 하지만 계산 패턴은 비슷합니다. 불완전한 증거에서 가설을 만들고, 외부 환경에 행동을 보내고, 결과를 관찰하고, 유용한 상태를 보존하고, 잘못된 가정을 고친 뒤 계속 진행합니다.

## ARC-AGI-3 점수는 완주와 행동 효율을 함께 봅니다

ARC Prize Foundation 문서는 ARC-AGI-3를 정적 puzzle이 아니라 interactive reasoning benchmark로 설명합니다. agent는 각 환경에서 level을 풀어야 하고, score는 completion과 efficiency를 함께 봅니다. 공식 scoring 문서의 RHAE(Relative Human Action Efficiency)는 각 level에서 human baseline action 수와 AI action 수를 비교해 계산합니다. 그런 다음 game별로 aggregate하고 전체 평균으로 score를 냅니다.

이 방식에서는 “답을 맞혔다”만으로 충분하지 않습니다. 너무 많은 action을 써서 겨우 완료하면 효율이 낮습니다. 반대로 일부 level만 잘하면 전체 game score의 상한이 낮아집니다. 문서는 100%가 모든 game과 level을 완료하면서 human efficiency에 맞추거나 그보다 나은 상태라고 설명합니다.

NVIDIA는 AVO가 public set의 25개 environment, 183개 level을 모두 완료했고 6,624 environment action으로 100.00 RHAE를 얻었다고 밝혔습니다. 또한 같은 public set을 Claude Opus 5로 완료한 VISTA 결과와 비교해 action 수가 약 12% 적었다고 설명합니다. 다만 NVIDIA도 이 비교를 controlled ablation으로 보지 말라고 선을 그었습니다. agent backend, observation representation, memory, context management가 모두 다르기 때문입니다.

## 모델 선택보다 harness 기록이 먼저입니다

이 공개가 개발팀에 주는 실무적 의미는 agent 평가표를 다시 짜야 한다는 점입니다. “어느 모델이 ARC-AGI-3에서 몇 점인가”만 보면 실제 제품 agent의 문제를 놓칩니다. 같은 모델이라도 observation을 이미지로 주는지 text grid로 주는지에 따라 결과가 달라질 수 있습니다. memory를 어떻게 압축하는지, tool 실패를 어떻게 회복하는지, supervisor가 언제 개입하는지도 결과에 영향을 줍니다.

따라서 장기 agent를 평가할 때는 model version, reasoning effort, temperature 같은 model parameter만으로 부족합니다. task interface, action schema, tool 권한, state 저장 방식, memory pruning 기준, retry policy, supervisor rule, 종료 조건, 평가 script version을 함께 고정해야 합니다. 특히 코드 수정 agent나 사내 문서 agent처럼 여러 tool을 오래 쓰는 시스템은 이 기록 없이는 성능 회귀의 원인을 분리하기 어렵습니다.

한국 독자에게도 이 지점은 직접적입니다. 국내 기업이 coding agent, 문서 처리 agent, 보안 분석 agent를 도입할 때 vendor benchmark만 보고 모델을 고르면 운영 환경에서 실패할 수 있습니다. 사내 repository 구조, 보안 정책, 테스트 속도, 승인 절차, 로그 보존 정책이 모두 harness의 일부가 됩니다. AVO 사례는 frontier model을 들여오는 일보다 agent 실행 환경의 관측성과 재현성을 먼저 설계해야 한다는 신호로 읽는 편이 정확합니다.

## 재현에는 AVO 구현과 실행 기록이 더 필요합니다

AVO의 공개 정보는 구조를 이해하기에는 충분하지만, 독자가 같은 결과를 바로 재현하기에는 부족합니다. 논문과 블로그는 agent loop, GPU kernel 최적화 실험, ARC-AGI-3 적용 결과를 설명합니다. ARC-AGI-3는 공식 문서, API, open-source Python toolkit을 제공합니다. 그러나 AVO 자체의 구현, ARC-AGI-3 실행 로그, scorecard ID, 전체 replay, 실패 사례 분포는 이 기사 작성 시점에 확인하지 못했습니다.

따라서 이 기사의 재현성 상태는 R1입니다. 방법과 조건은 설명할 수 있지만, 편집국은 AVO를 실행하지 않았고 public set score를 독립적으로 재현하지 않았습니다. NVIDIA가 제시한 100.00 RHAE, 6,624 action, GPU kernel 개선 폭은 모두 NVIDIA 자체 실행 결과로 귀속합니다.

## 이해상충과 취재 조건

NVIDIA는 AVO 연구와 2026년 8월 21일 기술 블로그의 작성 주체입니다. ARC Prize Foundation은 ARC-AGI-3 benchmark, scoring 방법, docs, toolkit의 운영 주체입니다. 각 자료는 자기 연구나 benchmark를 설명하는 1차 자료이며, NVIDIA의 AVO 성능 우월성을 독립적으로 증명하지는 않습니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 이전 AI판 산출물은 후보 발견과 중복 확인에만 사용했고, 기사 사실은 열린 공식 원문과 공개 문서로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. NVIDIA는 2026년 8월 21일 AVO를 ARC-AGI-3 public set에 적용한 결과를 공개했고, AVO를 persistent memory, supervisor, tool use를 갖춘 장기 agent architecture로 설명했습니다. | E1 · P1 | NVIDIA 기술 블로그로 확인했습니다. 발표 사실과 구조 설명의 근거이며 독립 재현은 아닙니다. |
| C2. AVO 논문은 고정 mutation이나 hand-designed heuristic 대신 autonomous coding agent가 실행 피드백과 lineage를 보고 다음 후보를 만드는 evolutionary search 방법을 설명합니다. | E2 · P1 | arXiv 논문으로 방법, 실험 범위, GPU kernel 최적화 조건을 확인했습니다. AVO 구현 code는 확인하지 못했습니다. |
| C3. ARC-AGI-3는 agent가 낯선 환경에서 행동하고 관찰하며 목표와 규칙을 추론하는 interactive reasoning benchmark입니다. | E2 · P1/P2 | ARC Prize의 benchmark 설명, docs, open-source toolkit 경로로 확인했습니다. 전체 public set을 실행하지는 않았습니다. |
| C4. ARC-AGI-3의 RHAE는 completion과 human baseline 대비 action efficiency를 함께 반영하며, 100%는 모든 game과 level을 완료하면서 human efficiency에 맞추거나 넘어서는 상태를 뜻합니다. | E2 · P1 | ARC-AGI-3 scoring methodology 문서로 확인했습니다. NVIDIA의 실제 scorecard 원장은 확인하지 못했습니다. |
| C5. NVIDIA는 AVO가 ARC-AGI-3 public set 25개 environment 183개 level을 6,624 action으로 완료해 100.00 RHAE를 기록했다고 밝혔습니다. | E2 · P1 | NVIDIA 기술 블로그로 확인했습니다. public set 결과라는 범위는 명시됐지만, 편집국의 독립 실행이나 공개 scorecard 확인은 없습니다. |
| C6. ARC-AGI Toolkit은 ARC-AGI-3 환경을 local 또는 API로 다룰 수 있는 open-source Python interface입니다. | E2 · P2 | ARC Prize GitHub, PyPI, toolkit docs로 확인했습니다. AVO가 이 toolkit만으로 그대로 재현된다는 뜻은 아닙니다. |

## 출처

1. NVIDIA Technical Blog, "NVIDIA AVO Reaches 100% on ARC-AGI-3, Demonstrating a Frontier-Level General-Purpose Architecture for Long-Horizon Autonomous Agents": https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/
2. arXiv, "AVO: Agentic Variation Operators for Autonomous Evolutionary Search": https://arxiv.org/abs/2603.24517
3. ARC Prize, "ARC-AGI-3": https://arcprize.org/arc-agi/3
4. ARC-AGI-3 Docs, "ARC-AGI-3 Scoring Methodology": https://docs.arcprize.org/methodology
5. ARC Prize GitHub, `arcprize/ARC-AGI`: https://github.com/arcprize/arc-agi
6. PyPI, `arc-agi`: https://pypi.org/project/arc-agi/
