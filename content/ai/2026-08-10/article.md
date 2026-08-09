---
edition: ai
decision: publish-candidate
title: "LFM2.5-2.6B는 로컬 agent 후보지만 라이선스부터 확인해야 합니다"
date: 2026-08-10
subject: "Liquid AI LFM2.5-2.6B"
summary: "Liquid AI는 2026년 8월 4일 2.69B parameter, 128K context, tool calling 지원을 내세운 LFM2.5-2.6B와 base checkpoint를 공개했습니다. Hugging Face에는 native, GGUF, ONNX, MLX 경로가 있어 실행 검토가 가능하지만, lfm1.0 license는 연 매출 1천만 달러 이상 법인의 상업 사용을 별도 허가 밖에 두므로 일반적인 permissive open source로 보면 안 됩니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["Liquid AI는 LFM2.5-2.6B의 개발·배포 주체이며 blog, docs, Hugging Face model card와 license를 작성했습니다. 이 기사에는 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

Liquid AI가 2026년 8월 4일 공개한 LFM2.5-2.6B는 RAG, ticket triage, data extraction, local file workflow처럼 개인정보와 내부 문서를 장치 밖으로 보내기 어려운 agent 작업을 맡기는 SW 엔지니어에게 중요합니다. 바뀐 점은 2.69B parameter급 text model이 128K context, tool calling, agent harness post-training을 내세우고, native checkpoint뿐 아니라 GGUF, ONNX, MLX 형식까지 Hugging Face에 올라왔다는 점입니다. 다만 이 모델을 "제약 없는 open source"로 받아들이면 안 됩니다. Hugging Face model card의 license는 `lfm1.0`이고, license 원문은 연 매출 1천만 달러 이상 법인의 상업 사용을 이 계약의 허가 밖에 둡니다.

## 세 줄 요약

- Liquid AI는 LFM2.5-2.6B와 LFM2.5-2.6B-Base를 공개했고, model card는 2.69B parameter, 30 layers, 131,072 token context, 한국어를 포함한 16개 언어, tool use 절차를 적고 있습니다.
- Hugging Face API 기준 `LiquidAI/LFM2.5-2.6B`는 공개·비게이트 repository이며 revision은 `ab00687315bc1298e9d54e9c4b611dde9867ccc2`입니다. native safetensors, GGUF, ONNX, MLX 경로가 분리되어 있습니다.
- 성능 수치는 Liquid AI가 구성한 benchmark와 hardware 조건의 벤더 평가입니다. 도입 판단은 자체 workload, latency, tool-call 정확도, license threshold 확인 뒤에 해야 합니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** model ID, checkpoint 파일, config, chat template, tool-call 형식, Transformers·vLLM·SGLang·llama.cpp·ONNX·MLX 사용 경로, lfm1.0 license 원문은 공개되어 있습니다.
- **도입 전에 확인할 것:** 회사의 연 매출과 사용 목적이 lfm1.0의 Commercial Use Limitation에 걸리는지, 한국어 agent workload에서 tool call schema가 안정적인지, 긴 context에서 실제 memory와 latency가 맞는지 확인해야 합니다.
- **아직 결론 내릴 수 없는 것:** Liquid AI의 benchmark만으로 이 모델이 모든 로컬 agent 작업에서 Qwen, Gemma, 다른 sub-10B 모델보다 낫다고 결론낼 수 없습니다. 편집국은 checkpoint를 실행하지 않았습니다.

## 무엇이 실제로 바뀌었나

LFM2.5-2.6B의 공개 단위는 제품 API가 아니라 실행 가능한 model artifact입니다. Liquid AI blog는 post-trained model인 `LFM2.5-2.6B`와 pre-trained base model인 `LFM2.5-2.6B-Base`가 Hugging Face에 공개됐다고 설명합니다. Hugging Face model card와 API metadata는 repository가 private도 gated도 아니며, safetensors model shard, tokenizer, config, generation config, chat template이 올라와 있음을 확인시켜 줍니다.

모델 자체는 text-only general-purpose model입니다. model card는 총 2.69B parameter, 30 layers, 22 double-gated short convolution blocks와 8 GQA blocks, 128,000 vocabulary, 131,072 token context를 적고 있습니다. 지원 언어 목록에는 한국어도 들어갑니다. Liquid docs도 같은 모델을 2.6B dense model, 128K context, native tool calling, on-device agent용 모델로 설명합니다.

중요한 배포 변화는 format입니다. native checkpoint는 Transformers, vLLM, SGLang 용도로 안내되고, GGUF는 llama.cpp와 로컬 앱, ONNX는 WebGPU와 server runtime, MLX는 Apple Silicon 경로로 분리되어 있습니다. 즉 "로컬 agent 후보를 테스트한다"는 작업이 한 vendor playground가 아니라 여러 runtime 선택지로 시작될 수 있습니다.

## 입력에서 출력까지의 동작

LFM2.5의 chat template은 ChatML과 비슷한 구조를 씁니다. system, user, assistant message를 template으로 감싸고, model card는 `tokenizer.apply_chat_template()` 사용을 권합니다. post-trained LFM2.5-2.6B는 assistant answer를 시작할 때 `<think>` tag를 넣는 pure reasoning model이라고 model card가 설명합니다.

tool use는 네 단계로 제시됩니다. system prompt나 tokenizer helper에 tool 목록을 넣고, 모델은 기본적으로 `<|tool_call_start|>`와 `<|tool_call_end|>` 사이에 Pythonic function call 형태를 씁니다. 호출 결과는 `tool` role로 다시 넣고, 모델이 최종 자연어 답을 만듭니다. JSON function call도 system prompt로 요구할 수 있지만, 기본 계약은 OpenAI-style JSON schema만 고정한 방식과 다릅니다.

이 점은 agent framework 연동에서 바로 확인해야 할 부분입니다. 기존 harness가 Pythonic call list를 그대로 받을 수 있는지, JSON만 받는 tool router라면 prompt override가 일관적으로 작동하는지, 실패한 tool call을 재시도하거나 취소하는 정책이 있는지 봐야 합니다. "tool calling 지원"은 제품 통합에서 곧바로 안전한 function execution을 뜻하지 않습니다.

## API·runtime·배포에 미치는 영향

로컬 실행 경로는 넓습니다. Hugging Face model card는 Transformers quick start를 `transformers>=5.0.0`과 `AutoModelForCausalLM`, `AutoTokenizer` 기반으로 제시합니다. vLLM과 SGLang은 OpenAI-compatible endpoint로 serve하는 경로를 안내하고, GGUF repository는 llama.cpp 예제와 quantization 파일 크기를 제공합니다. ONNX repository는 WebGPU와 server에서 쓸 precision variant를 구분합니다.

deployment 관점에서 가장 먼저 볼 것은 memory입니다. Liquid AI는 blog와 model card에서 CPU decode 220 tokens/s on Apple M5 Max, 113 tokens/s on AMD Ryzen AI Max+ 395, phone 30 tokens/s, under 2.5GB memory를 주장합니다. GGUF repository의 `Q4_K_M` 파일은 1.67GB, `Q8_0`은 2.87GB로 표시됩니다. 다만 이 수치는 vendor 측 조건과 Hugging Face listing 기준입니다. 한국어 tool-heavy prompt, 긴 trace, mobile thermal throttling, WebGPU backend에서는 별도로 측정해야 합니다.

라이선스는 기술 성능만큼 중요합니다. Hugging Face metadata는 `license: other`, `license_name: lfm1.0`으로 표시합니다. license 원문은 상업 사용 권리가 사용 주체의 연 매출 1천만 달러 미만 조건에 걸린다고 적고, 그 이상 법인의 상업 사용은 이 계약으로 허가되지 않는다고 밝힙니다. 따라서 대기업, 매출 threshold를 넘는 스타트업, 고객사에 재배포하는 SI 조직은 모델 실행 가능성과 법적 사용 가능성을 분리해 검토해야 합니다.

## 이 공개의 의의와 편집 판단

확인된 사실은 LFM2.5-2.6B가 작은 로컬 agent 후보로 필요한 여러 요소를 한 번에 공개했다는 점입니다. 공개 checkpoint, base checkpoint, long-context config, tool-use template, 여러 runtime format, 한국어 포함 언어 목록, license 원문이 함께 있습니다. 이 조합은 "edge agent를 검토하려면 API provider를 먼저 고른다"는 순서를 바꿔, 로컬 runtime과 product policy를 먼저 시험하게 합니다.

**편집 판단:** 이 공개의 실무 가치는 benchmark 1위 주장보다 배포 선택지에 있습니다. 클라우드 API 비용, 개인정보, offline 동작, device-local latency가 중요한 업무에서는 2.6B급 agent model을 shadow workflow에 붙여 볼 이유가 생깁니다. 반대로 회사 규모가 license threshold를 넘거나, coding-heavy task와 지식 집약 task가 핵심이면 곧바로 production 후보로 올리기보다 larger model fallback, tool-call validation, legal review를 먼저 둬야 합니다.

## benchmark 또는 재현 결과

이 기사에서 성능 표는 Liquid AI가 작성한 벤더 평가로만 다룹니다. blog와 model card는 STEM, instruction following, tool use, agentic workflow benchmark를 제시하고, LFM2.5-2.6B가 sub-10B 비교군 가운데 instruction-following과 tool-use 일부에서 강하다고 설명합니다. 예를 들어 model card는 BFCLv4 56.88, ToolSandbox 77.83, Claw-Eval average 62.85, BrowseComp+ 26.89를 적습니다.

benchmark 조건 일부는 공개되어 있습니다. Liquid AI는 footnote에서 BFCLv4는 temperature 0.001과 max output 4096, ToolSandbox는 temperature 0과 max output 1024, PinchBench는 temperature 0.6과 max output 8192, τ³-Bench와 Claw-Eval은 temperature 0 및 no output limit을 썼다고 설명합니다. GPU throughput은 SGLang 0.5.16, 1,024 input tokens, 최대 256 output tokens, BF16, concurrency별 3회 평균 조건으로 설명됩니다.

재현성은 R2입니다. 공개 checkpoint와 실행 문서가 있어 독자가 실행을 시작할 수 있지만, 편집국은 모델을 내려받거나 benchmark를 재실행하지 않았습니다. 또한 Liquid AI의 비교 benchmark가 독립 기관 결과가 아니므로 "가장 빠르다", "더 낫다" 같은 문장은 Liquid AI의 측정 조건 안에 묶어 읽어야 합니다.

## 적용 범위와 확인하지 못한 것

LFM2.5-2.6B는 모든 local AI 작업의 대체재가 아닙니다. model card도 agentic coding과 knowledge-heavy task에는 권하지 않는다고 적습니다. 긴 문서 RAG, tool use, data extraction, local workflow automation처럼 context와 도구 호출이 중요하지만 최고 수준 reasoning이 필수는 아닌 작업이 우선 검토 범위입니다.

training data도 완전히 재현 가능한 형태는 아닙니다. model card와 blog는 약 34T token pre-training, 128K context extension, SFT, teacher specialization, multi-domain on-policy distillation, agentic reinforcement learning을 설명하지만, 전체 training corpus와 rollout trace가 공개된 것은 아닙니다. 따라서 architecture와 공개 artifact는 확인 가능하지만, training pipeline 자체는 외부 재현 대상이 아닙니다.

한국어 지원도 신중히 봐야 합니다. model card의 language tag와 설명에는 Korean이 들어가지만, 한국어 tool-use benchmark나 국내 업무 문서에서의 별도 수치는 확인하지 못했습니다. 한국 독자는 직접 eval set을 만들어 function-call parse success, tool argument hallucination, 긴 한국어 문서 요약, 개인정보 포함 prompt에서의 local logging 정책을 같이 측정해야 합니다.

## 독자가 내릴 수 있는 기술 판단

먼저 license gate를 통과시켜야 합니다. `lfm1.0`의 연 매출 1천만 달러 threshold가 조직에 적용되는지 확인하지 않은 상태에서 commercial PoC를 고객 데이터와 연결하면 위험합니다. permissive OSS 모델처럼 내부 artifact registry에 올리고 재배포하는 흐름도 법무 검토 없이 진행하면 안 됩니다.

그다음은 shadow agent입니다. 기존 cloud model이 처리하는 저위험 task 중 data extraction, internal search, ticket triage, local file workflow 같은 좁은 경로를 고르고, LFM2.5-2.6B를 tool router 뒤에 붙여 call validity와 recovery behavior를 봅니다. 성공률만 보지 말고 invalid tool call, 잘못된 argument, 반복 호출, context overflow, latency tail을 같이 기록해야 합니다.

runtime 선택은 device와 운영 목적에 맞춰 나눠야 합니다. desktop이나 laptop PoC는 GGUF 또는 MLX가 빠르고, server-side batch나 high concurrency는 vLLM·SGLang이 자연스럽습니다. browser 또는 cross-platform client는 ONNX/WebGPU가 후보입니다. 같은 모델이라도 quantization과 backend가 바뀌면 품질과 latency가 달라지므로, production 판단은 하나의 vendor graph가 아니라 실제 배포 target에서 다시 내려야 합니다.

## 이해상충과 취재 조건

Liquid AI는 LFM2.5-2.6B의 개발·배포 주체이며 blog, docs, Hugging Face model card, model repository, license를 작성했습니다. 이 자료는 출시 사실, 공개 artifact, model configuration, license 조건, 벤더가 밝힌 benchmark 조건의 1차 근거이지만, 성능 우월성의 독립 검증은 아닙니다.

이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 웹 문서와 인증이 필요 없는 Hugging Face API metadata만 사용했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Liquid AI는 2026년 8월 4일 LFM2.5-2.6B와 LFM2.5-2.6B-Base를 Hugging Face에 공개했습니다. | E2 · P1/P2 · R2 | Liquid AI blog, Hugging Face model card, Hugging Face API metadata로 확인했습니다. repository main branch는 갱신될 수 있습니다. |
| C2. LFM2.5-2.6B는 2.69B parameter, 30 layers, 131,072 token context, 한국어 포함 16개 언어, tool-use template을 갖춘 text-only model입니다. | E2 · P1/P2 · R2 | Hugging Face README와 config, Liquid docs가 같은 모델 범위를 설명합니다. 실제 한국어 성능은 재현하지 않았습니다. |
| C3. native, GGUF, ONNX, MLX 공개 경로가 있어 여러 local runtime에서 실행 검토를 시작할 수 있습니다. | E2 · P2 · R2 | Hugging Face sibling listing과 format별 model card로 파일 공개를 확인했습니다. 파일 다운로드, checksum 검증, local execution은 하지 않았습니다. |
| C4. lfm1.0 license는 연 매출 1천만 달러 이상 법인의 상업 사용을 이 계약의 허가 밖에 둡니다. | E2 · P1 · R1 | Hugging Face raw LICENSE 원문으로 확인했습니다. 법률 자문이 아니며 조직별 계약 판단은 별도 검토가 필요합니다. |
| C5. Liquid AI의 benchmark와 speed 수치는 벤더가 공개한 조건의 결과이며 독립 재현이 아닙니다. | E2 · P1 · R1 | blog와 model card의 benchmark table, footnote, throughput 조건을 확인했습니다. 편집국은 실행하지 않았습니다. |

## 출처

- Liquid AI, "LFM2.5-2.6B: Deploy Agents Everywhere" (2026년 8월 4일): https://www.liquid.ai/blog/lfm2-5-2-6b
- Liquid AI Docs, "LFM2.5-2.6B": https://docs.liquid.ai/lfm/models/lfm25-2.6b
- Hugging Face, `LiquidAI/LFM2.5-2.6B` model card: https://huggingface.co/LiquidAI/LFM2.5-2.6B
- Hugging Face API metadata, `LiquidAI/LFM2.5-2.6B`: https://huggingface.co/api/models/LiquidAI/LFM2.5-2.6B
- Hugging Face, `LiquidAI/LFM2.5-2.6B-Base`: https://huggingface.co/LiquidAI/LFM2.5-2.6B-Base
- Hugging Face, `LiquidAI/LFM2.5-2.6B-GGUF`: https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF
- Hugging Face, `LiquidAI/LFM2.5-2.6B-ONNX`: https://huggingface.co/LiquidAI/LFM2.5-2.6B-ONNX
- LFM Open License v1.0: https://huggingface.co/LiquidAI/LFM2.5-2.6B/raw/main/LICENSE
