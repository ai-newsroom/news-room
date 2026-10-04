---
edition: eda
decision: publish-candidate
title: "SyntheticHLS, HLS 학습 데이터를 코드 생성물에서 합성 로그가 붙은 흐름으로 바꿉니다"
date: 2026-10-05
subject: "SyntheticHLS arXiv:2610.00106v1 and sharc-lab/synthetic-hls commit e0cdc84ee5186f1864057e8b032655422036cd45"
summary: "SyntheticHLS는 LLM이 만든 high-level synthesis 설계를 그대로 모으지 않습니다. C simulation, Vitis HLS synthesis, OptDSLv2 기반 design-space 평가를 통과한 후보만 다음 반복으로 넘기는 공개 흐름입니다. 논문과 코드는 공개됐지만 Vitis HLS, model API, HLSFactory의 특정 branch가 필요해 재현성은 공개 artifact와 상용 도구 조건에 함께 걸려 있습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

HLS 연구에서 학습용 데이터는 설계 자동화의 출발점입니다. High-level synthesis, 즉 HLS는 C나 C++ 같은 높은 수준의 코드를 RTL과 FPGA 구현으로 바꾸는 흐름입니다. QoR은 quality of results의 줄임말로, 합성 뒤에 나온 latency, LUT, FF 같은 품질 지표를 뜻합니다. 문제는 HLS QoR 예측 모델이나 설계 공간 탐색 모델을 훈련할 때 쓸 다양한 HLS 설계가 많지 않다는 점입니다.

SyntheticHLS 논문과 공개 저장소가 새로 제시한 변화는 여기에 있습니다. 저자들은 LLM이 HLS 코드를 한 번 만들게 하는 데서 멈추지 않습니다. 생성된 설계를 C simulation, Vitis HLS synthesis, OptDSLv2 design-space 평가로 걸러 내고, 그 결과를 다시 LLM prompt에 넣어 다음 설계를 고칩니다. 설계 데이터셋을 "코드 묶음"이 아니라 "합성 가능성과 trade-off 평가가 붙은 실행 기록"에 가깝게 만들려는 시도입니다.

## 합성 결과를 보고 다음 설계를 다시 만듭니다

기존 HLS 데이터셋은 대체로 두 방향이었습니다. PolyBench, MachSuite, CHStone처럼 사람이 만든 benchmark를 쓰거나, 같은 설계에 pragma 조합을 많이 적용해 여러 design point를 만듭니다. pragma는 HLS compiler에 loop unroll, pipeline, array partition 같은 최적화 방식을 알려 주는 지시문입니다. 이런 방식은 같은 source design 안에서 latency와 resource trade-off를 넓게 볼 수 있습니다. 그러나 서로 다른 application 구조를 많이 확보하기는 어렵습니다.

SyntheticHLS는 먼저 LLM으로 seed design을 만듭니다. 각 seed에는 HLS kernel source, header, testbench, top function 이름, kernel 설명, OptDSLv2 optimization template가 들어갑니다. OptDSLv2는 pragma design space를 구조화해서 적는 작은 언어입니다. 예를 들어 어떤 array를 어떤 factor로 partition할지, 어떤 loop를 unroll하거나 pipeline할지를 design space로 둡니다.

그다음 흐름은 후보를 그냥 저장하지 않습니다. C simulation으로 기능 실행을 확인하고, Vitis HLS synthesis로 합성 가능성을 확인합니다. Pareto score를 목표로 삼는 단계에서는 HLSFactory로 여러 pragma 조합을 sampling하고 LUT와 latency, FF와 latency의 Pareto frontier를 계산합니다. Pareto frontier는 한 지표를 더 좋게 하려면 다른 지표가 나빠지는 경계에 있는 후보들의 집합입니다.

## LLM은 코드만 만들지 않고 평가 보고서를 읽습니다

SyntheticHLS의 중요한 차이는 feedback의 형식입니다. 반복 mutation 단계에서 LLM은 현재 design 파일뿐 아니라 `call_graph.json`과 `pareto_scores_summary.json` 같은 평가 산출물을 함께 받습니다. `call_graph.json`은 함수 수, 최대 호출 깊이, 함수당 평균 코드 줄 수처럼 구조 복잡도를 요약합니다. `pareto_scores_summary.json`은 design space가 latency-resource trade-off를 얼마나 넓고 고르게 덮는지 보여 줍니다.

이 구조는 EDA agent나 LLM 기반 설계 자동화에서 흔한 실패를 줄이려는 장치입니다. LLM은 더 복잡해 보이는 코드를 만들 수 있습니다. 그러나 HLS에서 중요한 것은 그 코드가 testbench를 통과하고 합성되는지, 또 pragma 조합으로 의미 있는 trade-off를 만드는지입니다. SyntheticHLS는 목표 지표를 prompt에 넣습니다. 실패하면 compiler error나 synthesis error를 바탕으로 repair prompt를 만들어 다시 시도합니다.

저자들은 논문에서 mutation 후보가 여러 개 통과하면 목표 metric이 가장 좋은 후보를 다음 seed로 고른다고 설명합니다. 모두 실패하면 repair 단계를 실행합니다. 이는 HLS 데이터 생성에서 LLM의 "첫 답"보다 합성 도구의 feedback이 더 중요해진다는 뜻입니다.

## 저자 결과는 데이터 다양성 개선으로 읽어야 합니다

논문은 SyntheticHLS가 만든 최종 mutated design이 zero-shot synthetic design이나 기존 benchmark만으로 만든 학습 세트보다 HLS QoR 모델의 cross-dataset generalization에 더 도움이 된다고 보고했습니다. 또한 mutation을 거친 design이 seed design보다 더 넓고 고른 design space로 이동했다고 설명합니다.

다만 이 수치는 저자 보고 결과입니다. 논문은 Vitis HLS를 써서 후보의 C simulation과 synthesis를 확인하고, HLSFactory와 OptDSLv2로 design-space 평가를 구성했다고 밝힙니다. 공개 저장소도 그 경로를 담고 있습니다. 그러나 편집국은 Vitis HLS license와 model API key가 없어 전체 실험을 재실행하지 않았습니다. 따라서 이 기사의 중심 결론은 "SyntheticHLS가 HLS 학습용 데이터 생성을 synthesis feedback loop로 공개했다"입니다. "특정 QoR 모델에서 항상 더 좋은 데이터셋"이라는 결론은 아직 저자 실험 범위 안에 둬야 합니다.

저장소 상태도 실무 판단에 중요합니다. `sharc-lab/synthetic-hls`는 2026년 10월 4일 확인한 기본 branch commit `e0cdc84ee5186f1864057e8b032655422036cd45`에서 공개되어 있습니다. README는 Vitis HLS 2023.1로 테스트했다고 적고, OptDSLv2 frontend와 validation logic을 갖춘 HLSFactory가 필요하다고 밝힙니다. `pyproject.toml`은 `sharc-lab/HLSFactory`의 `mzhou_OptDSLv2` branch를 의존성으로 고정합니다. 이 branch의 관측 commit은 `b063823948c6d633224bdbd6d421a9a2baa1cf51`입니다.

## 설계팀은 데이터가 어떻게 만들어졌는지 봐야 합니다

SyntheticHLS가 실무 EDA flow에 바로 들어간다고 보기는 이릅니다. 상용 FPGA HLS 환경, LLM 호출 비용, 합성 병렬 실행 자원, AGPL-3.0 license 조건을 모두 봐야 합니다. 그래도 HLS QoR 예측이나 pragma 추천 모델을 연구하는 팀에는 중요한 신호입니다. 데이터셋을 평가할 때 source code 개수만 보면 부족합니다. 각 design이 어떤 testbench를 통과했는지, 어떤 synthesis report와 연결되는지, 어떤 design-space sampling으로 Pareto frontier를 만들었는지도 함께 봐야 합니다.

지금 할 일은 공개 저장소의 작은 experiment를 읽고 자기 환경에서 필요한 의존성을 분리하는 것입니다. Vitis HLS version, HLSFactory branch, model provider, `OPENROUTER_API_KEY`, include path, 병렬 job 수를 먼저 고정해야 합니다. 이미 HLS QoR 모델을 쓰는 팀이라면 기존 PolyBench나 MachSuite 중심 학습 세트와 SyntheticHLS식 mutated design을 섞을 때 test set을 어떻게 나눌지도 미리 정해야 합니다.

아직 미룰 일은 이 데이터로 훈련한 모델을 signoff 판단에 쓰는 것입니다. HLS synthesis report는 RTL implementation과 measured silicon을 대신하지 않습니다. 또 SyntheticHLS는 생성된 설계가 특정 Vitis HLS 조건에서 합성된다는 사실을 확인하지만, 그 설계가 실제 제품 workload를 대표한다는 뜻은 아닙니다.

다음에 확인할 신호는 명확합니다. HLSFactory의 OptDSLv2 지원이 main branch로 들어오는지, 논문 결과를 재현할 수 있는 고정 release와 dataset archive가 나오는지, Vitis HLS 외에 Catapult, Intel HLS, Google XLS 같은 다른 flow에서 같은 mutation 구조가 유지되는지입니다. 이 셋이 확인되면 SyntheticHLS는 HLS 데이터 생성 도구를 넘어, EDA 학습 데이터의 provenance를 따지는 기준으로 커질 수 있습니다.

## 이해상충과 취재 조건

이 기사는 공개 arXiv 원문과 공개 GitHub 저장소만 읽어 작성했습니다. 저자, 소속 기관, 도구 공급사로부터 브리핑, 계정, license, hardware, cloud credit을 제공받지 않았습니다. Vitis HLS와 model API가 필요한 전체 실험은 실행하지 않았고, 논문 수치는 저자 보고 결과로만 다뤘습니다.

## 근거 원장

| claim | 근거 | 등급 | 한계 |
|---|---|---|---|
| SyntheticHLS는 LLM으로 만든 HLS 설계를 iterative feedback-guided mutation으로 개선하고, C simulation과 Vitis HLS synthesis를 통과한 후보를 다음 반복에 사용합니다. | arXiv:2610.00106v1, SyntheticHLS repository | E2 | 전체 실험을 재실행하지 않았습니다. |
| SyntheticHLS는 `call_graph.json`과 `pareto_scores_summary.json` 같은 평가 산출물을 prompt feedback으로 사용합니다. | arXiv HTML, repository code | E2 | 산출물 형식과 code path 확인이며 결과 수치는 저자 보고입니다. |
| 논문은 mutated synthetic design이 HLS QoR 모델의 cross-dataset generalization에 더 도움이 된다고 보고했습니다. | arXiv:2610.00106v1 | E2 | 저자 실험입니다. 독립 재현은 확인하지 않았습니다. |
| 공개 저장소는 Vitis HLS 2023.1 테스트, HLSFactory `mzhou_OptDSLv2` branch 의존성, AGPL-3.0 license를 밝힙니다. | GitHub README, pyproject.toml, LICENSE | E2 | 상용 Vitis HLS와 model API 접근이 필요합니다. |

## 출처

- Stefan Abi-Karam, Miaoyan Zhou, Callie Hao, "SyntheticHLS: Building Diverse Synthetic High-Level Synthesis Datasets using LLMs," arXiv:2610.00106v1, submitted 2026-09-09. https://arxiv.org/abs/2610.00106
- arXiv HTML version of SyntheticHLS, accessed 2026-10-04. https://arxiv.org/html/2610.00106
- sharc-lab/synthetic-hls public repository, main commit `e0cdc84ee5186f1864057e8b032655422036cd45`, accessed 2026-10-04. https://github.com/sharc-lab/synthetic-hls
- sharc-lab/HLSFactory public repository, `mzhou_OptDSLv2` branch commit `b063823948c6d633224bdbd6d421a9a2baa1cf51`, accessed 2026-10-04. https://github.com/sharc-lab/HLSFactory
