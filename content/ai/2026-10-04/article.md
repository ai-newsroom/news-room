---
edition: ai
decision: publish-candidate
title: "DeepSeek-V4.1-Flash 공개 - 긴 agent 입력의 KV cache 부담을 줄이는 공개 모델"
date: 2026-10-04
subject: "DeepSeek-V4.1-Flash, Hugging Face repository last modified 2026-10-01"
summary: "DeepSeek가 공개한 V4.1-Flash는 1M token context를 쓰는 agent에서 KV cache가 커지는 문제를 줄이려는 모델입니다. 이를 위해 Causal Encoder-Decoder, compressed sparse attention, FP4 KV cache를 결합했습니다. weight, config, inference code, DeepSWE 재현 절차는 공개됐지만, 성능 비교는 아직 DeepSeek 자체 평가가 중심입니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

DeepSeek가 `DeepSeek-V4.1-Flash`를 공개했습니다. 이 모델의 핵심은 더 긴 입력을 받는다는 사실만이 아닙니다. 코드 agent나 문서 agent가 1M token까지 문맥을 들고 갈 때 KV cache 부담이 커집니다. DeepSeek는 이 부담을 줄이기 위해 모델 구조와 cache 저장 방식을 함께 바꿨다고 설명합니다.

SW 엔지니어에게 이 변화가 중요한 이유는 분명합니다. 긴 context 모델은 입력을 많이 넣을수록 attention에 필요한 중간 상태를 오래 보관해야 합니다. 이 메모리 비용은 serving 비용과 동시 처리량의 병목이 됩니다. DeepSeek는 V4.1-Flash의 global KV cache가 token당 890 byte라고 설명합니다. 같은 계열의 V4-Flash보다 약 4분의 1로 줄였다는 주장입니다.

다만 이 글의 결론은 좁습니다. V4.1-Flash가 모든 agent benchmark에서 경쟁 모델을 독립적으로 이겼다는 뜻은 아닙니다. 공개 원문으로 확인할 수 있는 것은 DeepSeek가 긴 입력 agent를 겨냥한 cache 압축 중심의 공개 weight 모델을 냈다는 사실입니다. model card, technical report, config, inference code, 일부 benchmark 재현 절차도 같은 저장소에 공개했습니다.

## 긴 입력에서 문제는 답변보다 중간 상태입니다

LLM serving에서 긴 입력은 단순히 prompt가 길다는 뜻으로 끝나지 않습니다. 모델은 이전 token을 다시 계산하지 않기 위해 key와 value를 cache에 저장합니다. context가 길어지고 batch가 커질수록 이 cache는 GPU memory를 빠르게 차지합니다. agent가 repository, issue, test log, 웹 문서, 이미지까지 한 번에 들고 움직이면 이 비용은 더 커집니다.

DeepSeek-V4.1-Flash는 이 병목을 모델 구조에서 줄이려 합니다. 저장소의 README와 technical report는 이 모델을 552B backbone parameter를 가진 multimodal MoE 모델로 설명합니다. 모든 token이 모든 parameter를 쓰는 방식은 아닙니다. prefill에서는 8B, decode에서는 16B parameter를 활성화한다고 적었습니다.

여기서 prefill은 긴 입력을 처음 읽는 단계이고, decode는 답변 token을 하나씩 만드는 단계입니다. agent 제품에서는 prefill 비용이 특히 중요합니다. 사용자가 codebase 전체, 설계 문서, 긴 대화 이력을 넣으면 모델은 답하기 전에 그 입력을 먼저 처리해야 하기 때문입니다.

## decoder마다 cache를 만들지 않게 했습니다

V4.1-Flash의 큰 구조 변화는 Causal Encoder-Decoder입니다. DeepSeek는 40-layer Transformer를 20-layer causal encoder와 20-layer decoder로 나눴다고 설명합니다. 일반적인 decoder-only 모델에서는 decoder layer마다 자기 hidden state에서 KV cache를 만들고 보관합니다.

V4.1-Flash에서는 decoder의 global KV cache를 각 decoder layer가 따로 만든 값이 아니라 encoder의 마지막 hidden state에서 projection합니다. 이렇게 하면 decoder 쪽에서 layer마다 같은 규모의 전역 cache를 계속 들고 있을 필요가 줄어듭니다. DeepSeek가 긴 입력 agent workload에서 비용 효율을 말하는 이유가 여기에 있습니다.

이 설계만으로 끝나지는 않습니다. 모델은 sliding-window attention에서 빠진 KV 상태를 모두 저장하지 않고, 최근 window만 다시 replay하는 SWA Bounded Replay를 씁니다. 또 Compressed Sparse Attention 2는 attention layer를 Full, Reindex, Reuse 세 mode로 나눕니다. 이 방식은 KV와 sparse index를 layer 사이에서 공유하거나 재사용합니다. 여기에 FP4 main KV cache를 결합해 global KV cache를 token당 890 byte로 줄였다는 것이 DeepSeek의 중심 설명입니다.

## weight와 실행 절차를 함께 공개했습니다

Hugging Face 모델 저장소에는 MIT license, `transformers` library metadata, `image-text-to-text` pipeline tag가 있습니다. API로 확인한 `main` revision은 `2cba9e42aa026125f3ed06c6d98c1db82f7ca027`이고, 저장소의 `lastModified`는 2026년 10월 1일입니다. 같은 저장소에는 48개 safetensors shard, tokenizer, config, technical report PDF, inference 폴더, evaluation 폴더가 있습니다.

`config.json`은 `max_position_embeddings`를 1,048,576으로 둡니다. 이는 model card가 말한 1M token context와 맞습니다. config에는 FP8 quantization, FP4 expert dtype, 384 routed experts, token당 6 routed experts, DSpark draft 경로, vision encoder 설정도 들어 있습니다. 이런 값은 성능 결론을 증명하지는 않지만, 공개 weight가 어떤 구조로 실행되도록 설계됐는지 확인하게 해 줍니다.

`inference/README.md`는 production serving engine이 아니라 읽을 수 있는 reference implementation이라고 설명합니다. weight 변환, tensor parallel rank별 checkpoint 생성, 예제 실행, interactive chat, 작은 self-test 절차도 적었습니다. `evaluation/README.md`는 DeepSWE v1.1 재현 절차를 제공합니다. 이 절차는 Pier와 DeepSWE를 특정 commit으로 checkout하고, DeepSeek 호환 endpoint와 API key를 써서 `mini-swe-agent`와 `dsh-minimal` agent를 실행합니다.

이 공개 범위 때문에 재현성은 R2로 볼 수 있습니다. 코드와 weight, 절차는 열려 있습니다. 하지만 이 기사 작성 턴에서는 510GB가 넘는 weight, API key, GPU 환경이 필요해 benchmark를 직접 다시 실행하지 않았습니다. 따라서 benchmark 수치는 DeepSeek 자체 평가로만 다룹니다.

## benchmark 수치는 순위보다 조건이 중요합니다

DeepSeek는 V4.1-Flash가 DeepSWE v1.1에서 74.2, Terminal-Bench 2.1에서 90.6을 냈다고 제시합니다. 또 DeepSWE와 Terminal-Bench의 agent scaffold별 비교에서 sample 수, container 조건, temperature, context limit, max steps를 함께 적었습니다. 이런 조건 공개는 단순한 leaderboard 이미지보다 낫습니다.

그래도 이 수치는 독립 평가가 아닙니다. model card 자체가 base model은 내부 framework에서 평가했다고 밝힙니다. agent benchmark도 DeepSeek가 제공한 harness와 endpoint 조건에 묶여 있습니다. 다른 팀이 같은 commit, 같은 API behavior, 같은 hardware와 container 조건에서 결과를 다시 확인해야 "동일 조건에서 재현됐다"고 말할 수 있습니다.

vLLM 0.30.0 release note가 V4.1-Flash 지원을 넣은 점은 실무적으로 중요합니다. vLLM은 이 모델을 새 지원 모델로 적고, FlashMLA V4.1, Mega-mHC, Engram prefetch 같은 serving 관련 변경을 함께 설명합니다. 다만 이것도 vLLM에서 지원 경로가 생겼다는 근거입니다. 모든 배포 환경에서 비용이 줄어든다는 독립 성능 검증은 아닙니다.

## 도입 전에는 memory와 도구 호출을 봐야 합니다

이 모델은 공개 weight 모델을 자체 serving하거나 third-party inference provider로 쓰려는 팀에 더 직접적인 의미가 있습니다. API만 호출하는 팀도 `reasoning_effort`를 1부터 100까지 조절하는 interface와 tool call template를 확인해야 합니다. 저장소의 chat template는 `low`, `medium`, `high`, `max` 같은 문자열을 내부 budget 값으로 바꾸고, image block과 tool schema를 별도로 다룹니다.

긴 입력 agent에서 중요한 질문은 "가장 높은 점수를 냈는가"보다 "내 workload에서 memory 병목이 실제로 줄어드는가"입니다. 문서에 따르면 V4.1-Flash는 긴 context, image-text 입력, tool call, DSpark speculative decoding, Engram memory를 함께 다룹니다. 이 조합은 agent serving의 병목을 줄이려는 방향과 맞지만, 효과는 각 팀의 GPU, vLLM 또는 SGLang 버전, concurrency, prompt 길이, cache hit rate에 따라 달라질 수 있습니다.

한국 독자에게도 의미가 있습니다. 국내 팀이 자체 GPU나 국내외 inference provider 위에 긴 문서 분석, code review, 테스트 agent를 올릴 때 open-weight 모델은 비용과 데이터 통제의 선택지를 넓힙니다. 다만 MIT license라고 해서 운영 리스크가 사라지는 것은 아닙니다. 모델 출력 안전성, 보안 prompt, 개인정보 처리, benchmark 재현 비용은 별도로 검토해야 합니다.

## 이해상충과 취재 조건

이 기사는 공개 웹 원문만 사용했습니다. 벤더 briefing, embargo, 유료 계정, 제공받은 credit, 비공개 문서는 사용하지 않았습니다. 작성자와 검토자의 관련 이해상충은 없습니다.

DeepSeek가 자기 모델 구조와 benchmark를 설명한 원문은 P1/P2 근거입니다. 그러나 경쟁 모델 대비 우월성은 독립 평가가 아니므로 편집국 결론으로 쓰지 않았습니다. vLLM release note는 serving 지원과 구현 경로를 확인하는 공개 project 근거로만 사용했습니다.

## 근거 원장

| claim id | 주장 | 근거 | 등급 | 한계 |
| --- | --- | --- | --- | --- |
| C1 | DeepSeek-V4.1-Flash는 552B backbone parameter, 1M token context, image-text 입력을 지원하는 multimodal MoE 모델로 공개됐다. | Hugging Face model card, README, config | E2 | 모델 개발 주체가 작성한 문서이며 실제 운영 가능성은 환경에 따라 다릅니다. |
| C2 | CED, SWA Bounded Replay, CSA2, FP4 main KV cache는 긴 입력에서 KV cache footprint를 줄이기 위한 핵심 설계입니다. | README, technical report, config | E2 | 구조 설명과 수치는 DeepSeek 자체 보고입니다. |
| C3 | 저장소에는 MIT license, 공개 safetensors shard, tokenizer, config, inference code, evaluation 절차가 있다. | Hugging Face API, file tree, LICENSE, inference/evaluation README | E2 | 직접 benchmark를 재실행하지 않았고 weight 규모가 큽니다. |
| C4 | DeepSWE와 Terminal-Bench 수치는 DeepSeek가 공개한 조건에서는 agent 성능 방향을 보여 주지만 독립 우월성 근거는 아닙니다. | model card evaluation section, evaluation README | E2 | 내부 또는 벤더 제공 조건이며 독립 재현 로그를 확인하지 못했습니다. |
| C5 | vLLM 0.30.0은 DeepSeek-V4.1-Flash 지원과 관련 serving kernel 변경을 release note에 포함했습니다. | vLLM v0.30.0 release note | E2 | serving support 확인이며 실제 throughput 개선을 이 기사에서 재현하지 않았습니다. |

## 출처

- DeepSeek-V4.1-Flash model card: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash
- DeepSeek-V4.1-Flash README raw: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/README.md
- DeepSeek_V41_Tech_Report.pdf: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf
- DeepSeek-V4.1-Flash config: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/config.json
- DeepSeek-V4.1-Flash inference README: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/inference/README.md
- DeepSeek-V4.1-Flash evaluation README: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/evaluation/README.md
- DeepSeek-V4.1-Flash license: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/LICENSE
- Hugging Face model API: https://huggingface.co/api/models/deepseek-ai/DeepSeek-V4.1-Flash
- vLLM v0.30.0 release: https://github.com/vllm-project/vllm/releases/tag/v0.30.0
