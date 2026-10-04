---
edition: ai
decision: publish-candidate
title: "DeepSeek-V4.1-Flash 공개 - 긴 에이전트 입력의 KV cache를 줄이는 공개 가중치 모델"
date: 2026-10-05
subject: "deepseek-ai/DeepSeek-V4.1-Flash, Hugging Face revision 2cba9e42aa026125f3ed06c6d98c1db82f7ca027, updated 2026-10-01"
summary: "DeepSeek가 V4.1-Flash를 공개 가중치 모델로 내놨습니다. 이 모델은 긴 에이전트 입력에서 cache 저장량을 줄이기 위해 Causal Encoder-Decoder 구조와 sparse attention, FP4 main KV cache를 결합했습니다. 가중치, config, inference code, 평가 재현 안내가 공개돼 구조와 실행 조건은 E2로 확인할 수 있지만, 성능 비교는 DeepSeek가 작성한 결과입니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["DeepSeek는 DeepSeek-V4.1-Flash의 개발·공개 주체이며 모델 카드, 기술 보고서, 평가 안내와 deepseek-recipe를 작성·운영합니다. Hugging Face는 model registry와 artifact hosting을 제공합니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

DeepSeek가 `DeepSeek-V4.1-Flash`를 공개했습니다. 이 모델은 텍스트와 이미지를 함께 입력받고, 최대 1M token 문맥을 목표로 하는 공개 가중치 모델입니다. Hugging Face 모델 저장소에는 모델 카드와 기술 보고서, config, safetensors 가중치 shard, prompt encoding, inference code, DeepSWE 평가 재현 안내가 함께 올라와 있습니다.

이번 공개에서 중요한 변화는 benchmark 점수보다 긴 입력을 처리하는 방식에 있습니다. 에이전트(agent)가 긴 repository, 브라우저 상태, 도구 호출 결과, 이미지를 한 작업 안에서 계속 들고 가면 입력이 길어질수록 KV cache와 prefill 비용이 커집니다. DeepSeek는 V4.1-Flash에서 decoder가 자기 layer별 hidden state에서만 KV를 만들지 않고, causal encoder의 마지막 hidden state에서 global KV cache를 투영하는 Causal Encoder-Decoder 구조를 썼다고 설명합니다.

따라서 이 글의 중심은 “더 높은 순위의 모델”이 아닙니다. 공개 문서와 artifact로 확인할 수 있는 변화는 긴 에이전트 작업에서 큰 문맥을 열어 두면서 cache 저장량과 decode 비용을 줄이려는 구조입니다. 이 구조가 공개 가중치, 실행 code, 평가 재현 절차와 함께 나왔다는 점이 이번 공개의 핵심입니다.

## 긴 입력을 계속 들고 가는 비용을 줄이려 합니다

일반적인 decoder-only transformer에서는 긴 입력을 한 번 읽은 뒤에도 각 layer의 key와 value를 계속 저장해야 합니다. 에이전트가 긴 코드베이스와 tool 결과를 한 대화 안에서 오래 끌고 가면 이 cache가 메모리 비용으로 돌아옵니다. 입력이 긴 작업에서는 새 token을 생성하는 계산만큼이나, 이전 문맥을 저장하고 다시 참조하는 방식이 운영 비용을 크게 좌우합니다.

DeepSeek-V4.1-Flash는 이 문제를 Causal Encoder-Decoder 구조로 다룹니다. 모델 카드는 40개 Transformer layer를 20개 causal encoder와 20개 decoder로 나누고, decoder의 global KV cache를 encoder의 마지막 hidden state에서 투영한다고 설명합니다. DeepSeek는 이 구조 때문에 prefill에서는 token당 8B parameter, decode에서는 token당 16B parameter만 활성화한다고 적었습니다.

여기에 SWA Bounded Replay, Compressed Sparse Attention 2, FP4 main KV caching이 붙습니다. 모델 카드는 이 조합으로 global KV cache가 token당 890 bytes가 되며, DeepSeek-V4-Flash보다 약 4분의 1 수준이라고 설명합니다. 이 수치는 DeepSeek의 자체 설명이지만, 어떤 병목을 줄이려는지는 공개 구조와 config로 확인할 수 있습니다.

## 전체 parameter와 실제 실행 비용은 다릅니다

Hugging Face API는 이 모델을 `image-text-to-text` pipeline으로 표시하고, 공개 저장소의 latest revision을 `2cba9e42aa026125f3ed06c6d98c1db82f7ca027`로 보여 줍니다. 저장소는 비공개나 gated 상태가 아니며, MIT license tag와 48개 safetensors shard, config, inference code를 포함합니다. Hugging Face UI에 표시된 model size는 763B parameter입니다.

하지만 실제 비용을 판단할 때는 전체 parameter 수만 보면 부족합니다. 공개 config는 text model에 40개 hidden layer, 384 routed expert, 1 shared expert가 있고 token당 6 routed expert를 쓴다고 적고 있습니다. 또 `max_position_embeddings`는 1,048,576으로 설정되어 있고, `index_topk`, `candidate_topk_blocks`, `engram_layer_ids`, `dspark_target_layer_ids` 같은 긴 문맥과 speculative decoding 관련 설정도 들어 있습니다.

따라서 공개 가중치라고 해서 바로 작은 GPU 한 장에 올릴 수 있다는 뜻은 아닙니다. 저장소 전체 크기는 510GB로 표시되고, 가중치 shard만 48개입니다. self-hosting을 검토하는 팀은 “공개됐는가”를 확인한 뒤 weight memory, KV cache memory, vision input 비율, prefill과 decode 분리, runtime 지원 여부를 따로 계산해야 합니다.

## prompt 변환과 평가 재현 절차도 공개됐습니다

DeepSeek는 이 모델에 Jinja chat template만 제공하고 끝내지 않았습니다. 모델 저장소에는 `encoding/encoding.py`와 test case가 있습니다. 별도 `deepseek-recipe` 저장소는 Messages, Chat Completions, Responses 형식의 요청을 DeepSeek V4와 V4.1 prompt나 token ID로 바꾸고, 출력도 streaming response와 complete response로 파싱한다고 설명합니다. thinking, tool call, image, generation setting도 변환 범위에 들어갑니다.

이 부분은 에이전트 제품을 만드는 팀에 중요합니다. 같은 모델이라도 prompt encoding, tool namespace, thinking mode, reasoning effort, image placeholder 처리가 달라지면 평가 결과와 운영 결과가 달라집니다. DeepSeek가 모델과 함께 protocol 변환 도구를 공개했기 때문에 검토는 “가중치를 받았다”에서 끝나지 않습니다. 기존 API와 agent harness에 어떻게 연결할 것인지까지 확인해야 합니다.

평가 재현 안내도 같은 맥락입니다. `evaluation/README.md`는 DeepSWE를 `mini-swe-agent`와 `dsh-minimal`로 실행하는 절차를 적고, Pier와 DeepSWE의 특정 commit, Docker, Python 3.12, `uv`, API endpoint, patch 적용 방법을 제시합니다. 이 글은 해당 benchmark를 재실행하지 않았습니다. 다만 공개 절차가 있으므로 재현성은 R2로 볼 수 있습니다.

## 성능 표는 목표 작업을 보여 주는 자료입니다

모델 카드는 GPQA, Terminal-Bench, DeepSWE, CyberGym, SEC-Bench Pro 같은 결과를 함께 실었습니다. 예를 들어 DeepSeek는 DeepSWE v1.1에서 `reasoning_effort=100`, 1M token context, 특정 agent scaffold 조건을 두고 V4.1-Flash가 74.2를 기록했다고 적었습니다. Terminal-Bench 2.1과 DeepSWE의 scaffold별 비교도 공개했습니다.

이 수치는 모델의 목표를 이해하는 데 도움이 됩니다. DeepSeek가 노리는 작업은 짧은 질의응답보다 긴 agent 실행, 소프트웨어 수정, 보안·자동화 과제에 가깝습니다. 그러나 benchmark 표는 DeepSeek가 작성한 자체 결과입니다. 경쟁 모델의 조건, API 상태, harness 차이, 비용, 실패 사례를 편집국이 독립적으로 맞춰 재실행하지 않았기 때문에, 이 기사에서는 독립 순위나 우월성 결론으로 쓰지 않습니다.

한국의 개발팀이 바로 확인할 질문은 더 구체적입니다. 자기 업무에서 1M token 문맥이 실제로 필요한지, 이미지 입력과 tool call이 어느 정도 섞이는지, reasoning effort를 높일 때 지연시간과 비용이 얼마나 늘어나는지, 공개 inference code와 deepseek-recipe가 현재 serving stack에 맞는지 먼저 봐야 합니다. 공개 가중치와 MIT license는 검토를 시작할 조건입니다. 다만 510GB급 저장소와 대형 MoE 구조까지 공개된 만큼, 운영 비용 검토를 건너뛰기는 어렵습니다.

## 확인된 범위와 남은 검증

이 후보의 근거 수준은 E2입니다. 모델 카드와 기술 보고서는 구조, cache 설계, 학습·후처리 설명, 평가 조건을 제공합니다. Hugging Face API와 파일 목록으로는 공개 상태, revision, license tag, config, safetensors shard, inference code, evaluation 안내를 확인할 수 있습니다. `deepseek-recipe`는 prompt encoding과 API 변환 경로를 별도 공개 code로 제공합니다.

재현성은 R2입니다. 코드와 평가 절차가 공개되어 qualified third party가 실행을 시도할 수 있습니다. 다만 이 turn에서는 가중치를 내려받거나 benchmark를 실행하지 않았고, 독립 검증 결과도 중심 근거로 확보하지 못했습니다. 그러므로 이 글은 DeepSeek의 성능표를 검증된 성능 순위로 쓰지 않고, 긴 에이전트 입력을 위한 구조와 공개 artifact가 무엇인지 설명하는 데 한정합니다.

## 이해상충과 취재 조건

DeepSeek는 DeepSeek-V4.1-Flash의 개발·공개 주체이며 모델 카드, 기술 보고서, 평가 안내와 deepseek-recipe를 작성·운영합니다. Hugging Face는 model registry와 artifact hosting을 제공합니다. 성능 비교와 비용 효율 표현은 발표 주체의 주장으로 보고, 공개 artifact와 설정값으로 확인되는 구조·라이선스·실행 조건만 중심 결론에 사용했습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 X, 커뮤니티 글, 2차 블로그는 후보 발견에만 사용할 수 있지만, 이 기사 사실은 열린 공식 모델 저장소, model card, raw config, evaluation README, DeepSeek GitHub 저장소로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. DeepSeek는 `DeepSeek-V4.1-Flash`를 공개했고, Hugging Face 저장소는 비공개나 gated 상태가 아니며 revision `2cba9e42aa026125f3ed06c6d98c1db82f7ca027`, lastModified `2026-10-01T05:56:24.000Z`, MIT license tag를 표시합니다. | E2 · P1/P2 | Hugging Face API와 모델 카드로 확인했습니다. 모델 공개와 artifact 존재를 확인한 것이며 성능 우월성을 확인한 것은 아닙니다. |
| C2. 모델 카드는 DeepSeek-V4.1-Flash를 552B backbone parameter의 multimodal MoE로 설명하고, Causal Encoder-Decoder 구조, 1M token context, prefill 8B active parameter, decode 16B active parameter를 적습니다. | E2 · P1/P2 | 모델 카드와 기술 보고서 링크로 확인했습니다. 활성 parameter와 성능 효과는 DeepSeek가 공개한 설명입니다. |
| C3. 모델 카드는 SWA Bounded Replay, CSA2, FP4 main KV caching을 통해 global KV cache footprint를 token당 890 bytes로 줄였다고 설명합니다. | E2 · P1 | 수치는 DeepSeek가 작성한 기술 설명입니다. 편집국은 KV cache 측정을 재현하지 않았습니다. |
| C4. 공개 config는 `DeepseekV41ForCausalLM`, `deepseek_v41`, `max_position_embeddings` 1,048,576, 40 hidden layer, 384 routed expert, token당 6 routed expert, FP8 quantization config와 vision config를 포함합니다. | E2 · P2 | raw config.json으로 확인했습니다. 실제 latency, memory 사용량, 품질은 실행하지 않았습니다. |
| C5. 모델 저장소에는 safetensors shard, inference code, prompt encoding code, evaluation README가 있으며, evaluation README는 DeepSWE 재현 절차와 Pier·DeepSWE commit을 제시합니다. | E2 · P2 | Hugging Face 파일 목록과 `evaluation/README.md`로 확인했습니다. API key와 대형 실행 환경이 필요하며 이 기사에서는 재실행하지 않았습니다. |
| C6. deepseek-recipe는 Messages, Chat Completions, Responses 요청을 DeepSeek V4/V4.1 prompt 또는 token ID로 바꾸고, thinking, tool call, image, generation setting과 streaming response parsing을 지원한다고 설명합니다. | E2 · P2 | DeepSeek GitHub 저장소 README로 확인했습니다. 실제 제품 통합은 각 팀의 serving backend와 tool execution 구현에 달려 있습니다. |

## 출처

1. Hugging Face, `deepseek-ai/DeepSeek-V4.1-Flash` model card: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash
2. Hugging Face API, `deepseek-ai/DeepSeek-V4.1-Flash`: https://huggingface.co/api/models/deepseek-ai/DeepSeek-V4.1-Flash
3. Raw config, `deepseek-ai/DeepSeek-V4.1-Flash`: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/config.json
4. Evaluation README, `deepseek-ai/DeepSeek-V4.1-Flash`: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/evaluation/README.md
5. DeepSeek GitHub, `deepseek-recipe`: https://github.com/deepseek-ai/deepseek-recipe
6. DeepSeek GitHub organization: https://github.com/deepseek-ai
