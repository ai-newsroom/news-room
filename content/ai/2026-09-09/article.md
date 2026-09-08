---
edition: ai
decision: publish-candidate
title: "MiniCPM5-2B 공개 - 로컬 에이전트 실험용 2B 장문 모델"
date: 2026-09-09
subject: "OpenBMB MiniCPM5-2B open-weight model, Hugging Face revision a063f08de1bd09dfc9ae4cf3da35e6064949e533, September 2026"
summary: "OpenBMB가 MiniCPM5-2B를 Apache-2.0 공개 가중치 모델로 내놨습니다. 25억 parameter급 Llama 구조에 131K token context, tool-calling template, vLLM·SGLang·Transformers 실행 경로를 제공해 노트북과 단일 GPU급 환경에서 로컬 agent 실험을 시작하기 쉽게 했습니다. 성능 우위는 개발 주체가 쓴 benchmark 표에 머물지만, 모델 파일과 config, 공개 데이터셋 연결, 실행 예제는 확인할 수 있습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["OpenBMB는 MiniCPM5-2B의 개발·공개 주체이며 Hugging Face model card와 GitHub repository를 작성·운영합니다. Hugging Face는 model registry와 artifact hosting을 제공합니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

OpenBMB가 MiniCPM5-2B를 공개했습니다. 이 모델은 대형 frontier 모델의 API를 대체하겠다는 발표가 아닙니다. 로컬 assistant, coding agent, tool-use workflow처럼 작은 모델을 직접 올려 시험해야 하는 개발 환경을 겨냥합니다. 공개 config와 Hub metadata로 확인되는 핵심은 2,516,756,480개 parameter, 42개 layer, 131,072 token context, Apache-2.0 license, 그리고 vLLM·SGLang·Transformers 실행 경로입니다.

작은 모델에서 중요한 변화는 “조금 더 똑똑하다”는 순위가 아닙니다. 제품팀이 prompt routing, offline mode, edge device, 사내 문서 보안, agent tool loop를 실험하려면 모델을 직접 내려받아 고칠 수 있어야 합니다. 같은 runtime에서 반복 실행할 수 있는지도 중요합니다. MiniCPM5-2B는 그 조건을 맞추기 위해 표준 `LlamaForCausalLM` 구조를 택하고, tool calling과 장문 context를 model card 안에 실행 예제로 묶었습니다.

## 작은 모델은 바로 띄워 볼 수 있어야 합니다

2B급 모델은 parameter 수만 보면 이미 흔합니다. MiniCPM5-2B가 기사 후보가 되는 이유는 공개 범위가 비교적 넓기 때문입니다. Hugging Face API는 model revision `a063f08de1bd09dfc9ae4cf3da35e6064949e533`, public·ungated 상태, `safetensors`, `transformers`, `license:apache-2.0`, 그리고 단일 `model-00000-of-00001.safetensors` 파일을 보여 줍니다. raw config는 architecture를 `LlamaForCausalLM`으로 적고, `max_position_embeddings`를 131,072로 둡니다.

이 선택은 운영팀이 확인해야 할 불확실성을 줄입니다. custom model code나 vendor endpoint에 묶이지 않고, Hugging Face Transformers의 `AutoModelForCausalLM`으로 불러오거나 vLLM, SGLang server로 띄울 수 있습니다. 물론 5GB 안팎의 BF16 weight와 131K context를 실제로 쓰려면 GPU memory, KV cache, batch size를 따로 잡아야 합니다. 그래도 모델 파일과 설정이 열려 있으면 자기 workload로 비용·latency 실험을 다시 할 수 있습니다.

## 긴 입력과 tool calling을 함께 시험할 수 있습니다

OpenBMB는 MiniCPM5-2B를 local assistant, coding agent, tool-use workflow, reasoning scenario를 위한 모델이라고 설명합니다. 공개 config의 131K context는 긴 code file, 문서 묶음, 이전 tool 결과를 한 번에 넣는 실험에 의미가 있습니다. 긴 문맥을 항상 잘 쓴다는 뜻은 아니지만, 작은 모델을 4K나 8K context에 가둬 두던 실험보다는 agent harness 설계 폭이 넓어집니다.

tool calling도 별도 fine-tuning 설명에 그치지 않습니다. model card의 chat template는 `<tools>` 안에 function signature를 넣고, 모델이 XML 형태의 `<function name="...">` 호출을 내도록 짜여 있습니다. SGLang 예제는 `--tool-call-parser minicpm5`를 써서 이 XML 호출을 OpenAI-compatible `tool_calls`로 바꾸는 경로를 제시합니다. 여러 모델을 같은 agent harness에서 비교하려는 팀에는 이 정보가 benchmark 평균보다 더 실용적입니다.

## 여러 RL 교사 모델을 하나의 release model로 합쳤습니다

MiniCPM5-2B의 post-training 설명에서 눈에 띄는 부분은 RL과 OPD입니다. OPD는 On-Policy Distillation의 약자입니다. OpenBMB 설명에 따르면 개발팀은 math, code, agentic task, writing 등 여러 영역의 RL teacher를 학습했습니다. 그런 뒤 16개 expert model의 능력을 하나의 release model로 증류했습니다. 각 응답 위치에서 student와 teacher의 전체 vocabulary logit 차이를 reverse KL divergence로 계산해 advantage estimate로 쓴다는 설명도 함께 공개했습니다.

이 방식이 중요한 이유는 작은 모델의 용도와 맞닿아 있습니다. 2B 모델 하나가 모든 영역에서 큰 모델을 이길 필요는 없습니다. 대신 local agent가 code reasoning, math reasoning, long-context reading, tool use를 고르게 처리해야 한다면, 여러 특화 teacher의 행동을 작은 release model 안으로 압축하는 post-training이 의미를 갖습니다. 모델 카드의 성능 표는 RL+OPD가 reasoning·general capability 평균을 10.96점, agentic capability 평균을 6.96점 높였다고 주장합니다. 다만 이 수치는 OpenBMB가 작성한 결과입니다. 이 글은 그 수치를 독립 성능 검증으로 쓰지 않습니다.

## 공개 데이터셋은 재현성 판단에 도움이 됩니다

OpenBMB는 모델과 함께 Ultra-FineWeb, UltraX-Preview, Ultra-FineWeb-L3, UltraData-Math, UltraData-Code, UltraData-SFT-2605, UltraData-SFT-Agent-2609, UltraData-RL-2609를 연결했습니다. 특히 Agent SFT data와 RL data가 공개되어 있다는 점은 작은 agent model을 다시 만들거나 domain adaptation을 해 보려는 연구·제품팀에 중요합니다.

다만 이것이 학습 전체를 그대로 재현할 수 있다는 뜻은 아닙니다. base training, mid-training, post-training의 절차와 일부 데이터셋 링크는 있지만, 전체 training log, compute budget, filtering decision, evaluation harness의 모든 설정이 열린 것은 아닙니다. 따라서 재현성은 R2입니다. 모델을 내려받아 실행할 수 있고 일부 입력과 학습 자료를 살펴볼 수 있지만, 발표된 benchmark 우위를 편집국이 재실행한 상태는 아닙니다.

## 지금 고를 때 봐야 할 조건

MiniCPM5-2B는 한국의 개발팀에도 실용적인 후보입니다. cloud API에 보내기 어려운 사내 문서, 폐쇄망 demo, 온디바이스 기능, tool-call parser를 포함한 agent loop를 시험할 때 공개 가중치 모델은 의사결정 시간을 줄입니다. Apache-2.0 license도 상업적 검토의 출발점을 단순하게 만듭니다.

하지만 선택 기준은 분명해야 합니다. 먼저 자기 workload의 입력 길이가 131K context를 실제로 필요로 하는지 봐야 합니다. 다음으로 tool call이 XML template와 SGLang parser 경로에서 충분히 안정적인지, vLLM serving에서 latency와 memory가 감당 가능한지 확인해야 합니다. 마지막으로 OpenBMB의 benchmark 평균 53.9와 “2B-class open-source SOTA” 주장은 같은 조건에서 직접 재실행하거나 독립 평가가 나올 때까지 vendor-authored claim으로 남겨야 합니다.

## 이해상충과 취재 조건

OpenBMB는 MiniCPM5-2B의 개발·공개 주체이며 Hugging Face model card와 GitHub repository를 작성·운영합니다. Hugging Face는 model registry와 artifact hosting을 제공합니다. 성능 비교는 OpenBMB가 고른 benchmark와 baseline에 의존하므로, 구조·license·공개 artifact·실행 경로 확인과 분리해 다뤘습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 2차 글은 후보 발견에만 사용했고, 기사 사실은 열린 공식 model card, GitHub repository, Hugging Face API metadata, raw config와 공개 실행 예제로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. OpenBMB는 MiniCPM5-2B를 MiniCPM5 series의 두 번째 모델로 공개했고, local assistant, coding agent, tool-use workflow, reasoning scenario를 목표로 설명했습니다. | E2 · P1/P2 | Hugging Face model card와 GitHub README로 확인했습니다. 제품 포지셔닝은 개발 주체 설명입니다. |
| C2. Hugging Face API는 MiniCPM5-2B가 public, ungated model이며 revision `a063f08de1bd09dfc9ae4cf3da35e6064949e533`, lastModified `2026-09-08T09:08:22.000Z`, license tag `apache-2.0`, `safetensors` artifact를 가진다고 반환했습니다. | E2 · P2 | 공개 API metadata로 확인했습니다. 이 turn에서는 weight를 내려받아 hash를 별도로 계산하지 않았습니다. |
| C3. raw config는 architecture `LlamaForCausalLM`, 42 layers, 16 Q heads, 2 KV heads, hidden size 2048, BF16 dtype, context length 131,072를 적고 있습니다. | E2 · P2 | raw config.json으로 확인했습니다. 긴 문맥의 품질과 latency는 직접 재실행하지 않았습니다. |
| C4. model card와 GitHub README는 vLLM, SGLang, Transformers 실행 예제를 제공하며 SGLang의 `minicpm5` tool-call parser를 권합니다. | E2 · P1/P2 | 공개 문서와 예제로 확인했습니다. parser 안정성은 이 turn에서 테스트하지 않았습니다. |
| C5. OpenBMB는 base training, mid-training, SFT, RL, OPD 절차와 공개 데이터셋 링크를 설명하고, 16개 RL expert model을 release model로 distill했다고 적었습니다. | E2 · P1/P2 | model card와 GitHub README로 확인했습니다. 전체 training log와 compute 조건은 공개되지 않았습니다. |
| C6. 평균 53.9, RL+OPD 개선 폭, 2B-class SOTA 같은 benchmark 수치는 OpenBMB가 작성한 표에 근거하므로 독립 성능 순위로 쓰지 않습니다. | E2 · P1 | 비교 대상과 일부 평가 조건은 문서에 있지만, 편집국이나 독립 주체가 같은 조건으로 재현하지 않았습니다. |

## 출처

1. Hugging Face, `openbmb/MiniCPM5-2B` model card: https://huggingface.co/openbmb/MiniCPM5-2B
2. Hugging Face API, `openbmb/MiniCPM5-2B`: https://huggingface.co/api/models/openbmb/MiniCPM5-2B
3. Raw config, `openbmb/MiniCPM5-2B`: https://huggingface.co/openbmb/MiniCPM5-2B/raw/main/config.json
4. OpenBMB GitHub repository, `MiniCPM`: https://github.com/OpenBMB/MiniCPM
5. UltraData-Code dataset: https://huggingface.co/datasets/openbmb/UltraData-Code
6. UltraData-SFT-Agent-2609 dataset: https://huggingface.co/datasets/openbmb/UltraData-SFT-Agent-2609
7. UltraData-RL-2609 dataset: https://huggingface.co/datasets/openbmb/UltraData-RL-2609
