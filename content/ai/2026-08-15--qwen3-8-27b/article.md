---
edition: ai
decision: publish-candidate
title: "Qwen3.8-27B 공개 - 장기 에이전트 실행이 담긴 27B 모델"
date: 2026-08-15
publication_kind: special
subject: "Qwen3.8-27B open-weight vision-language model, Hugging Face release 2026-08-14 UTC"
summary: "Qwen이 팀이 직접 내려받아 운영할 수 있는 Qwen3.8-27B 가중치를 공개했습니다. 27B dense 규모에서 hybrid attention으로 긴 작업을 더 효율적으로 처리하고, preserve_thinking으로 이전 reasoning context를 이어 받으며, multimodal 입력과 tool-call parser 기반 구조화된 도구 호출을 한 흐름에 묶은 점이 핵심입니다. 의미는 단순한 benchmark가 아니라 장기 에이전트 실행을 직접 배포 가능한 27B급 모델로 가져온 데 있습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["Qwen Hugging Face 모델 카드와 FP8 checkpoint는 Qwen의 1차 자료이고, SGLang·vLLM recipe는 serving framework 문서입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

Qwen이 `Qwen3.8-27B` 공개 가중치를 올렸습니다. 이 모델은 Apache-2.0 라이선스의 vision-language 모델이라 텍스트뿐 아니라 이미지와 비디오 입력도 받습니다. 이번 공개의 핵심은 27B dense 모델에서 장기 에이전트 실행에 필요한 구조와 runtime 제어를 팀이 직접 운영할 수 있게 됐다는 점입니다.

27B dense라는 말은 모델이 새 token을 하나 만들 때마다 270억 개 parameter 전체를 사용한다는 뜻입니다. MoE router가 일부 expert만 고르는 방식보다 구조와 배포 판단이 단순해질 수 있지만, BF16 checkpoint를 소비자 GPU 한 장에 그대로 올릴 수 있다는 뜻은 아닙니다. Qwen은 BF16 모델과 별도 FP8 checkpoint를 공개했고, SGLang과 vLLM 문서는 더 공격적인 NVFP4 quantization까지 다루지만 품질·속도·메모리 효과는 환경별 측정이 필요합니다.

SW 엔지니어가 봐야 할 지점은 benchmark 순위보다 agent runner가 어떻게 연결되는지입니다. `reasoning_effort`로 생각의 깊이를 조절하고, `preserve_thinking`으로 이전 reasoning context를 다음 turn에 넘깁니다. 여기에 `qwen3` reasoning parser와 `qwen3_coder` tool-call parser를 serving engine에 붙이면 모델이 낸 도구 호출 문장이 구조화된 tool call로 번역됩니다. screenshot, 문서, 동영상 같은 multimodal 입력까지 함께 쓰면 self-hosted agent의 작업 범위가 코드 편집을 넘어 browser·desktop·mobile workflow로 넓어집니다.

## 모델 크기보다 에이전트 실행 방식이 뉴스입니다

Qwen3.8-27B의 모델 카드는 이 checkpoint를 post-trained model weight와 configuration으로 설명합니다. Hugging Face API에서 확인한 `Qwen/Qwen3.8-27B`의 현재 `main` sha는 `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`이고, repo metadata는 `license:apache-2.0`, `image-text-to-text`, `safetensors`를 표시합니다. 따라서 공개 가중치와 license 자체는 독자가 직접 열어 확인할 수 있는 artifact입니다.

모델 개요는 27B parameter, hidden size 5120, 64 language-model layer, native context length 262,144 tokens를 적습니다. architecture는 `Qwen3_5ForConditionalGeneration`이고 config에는 vision encoder가 들어 있습니다. Qwen은 Qwen Cloud hosted service에서 1M context와 built-in tools를 제공할 예정이라고 적지만, 모델 카드 기준으로 hosted service는 coming soon입니다.

이 구분이 중요합니다. self-hosted checkpoint의 native context는 262,144 tokens이고, 1M context는 native 262,144 tokens를 넘어 serving configuration으로 확장하는 운용 선택입니다. 긴 context가 곧 정확한 장기 기억을 보장하지 않으며, KV cache와 Gated DeltaNet state는 concurrency와 메모리를 함께 소비합니다.

## 긴 문맥을 매번 처음부터 다시 읽지 않습니다

이 구조의 정확한 이름은 hybrid attention입니다. Qwen3.8-27B의 language model은 64개 층을 16번 반복되는 묶음으로 구성합니다. 각 묶음에는 Gated DeltaNet과 FFN을 거치는 선형 attention 층 세 개, 그리고 Gated Attention과 FFN을 거치는 full attention 층 한 개가 들어갑니다. 결과적으로 48개 층은 recurrent state를 갱신하고, 16개 층만 token 사이의 직접 관계를 넓게 다시 봅니다.

독자에게는 긴 문서를 읽을 때 모든 앞 문장을 매 단계 다시 펼쳐 보지 않고 요약 상태를 계속 갱신하되, 네 번째 층마다 원문 관계를 넓게 다시 확인하는 구조로 생각하면 됩니다. 다만 이 비유는 계산적으로 같은 설명이 아닙니다. recurrent state는 사람이 만든 문장 요약이 아니고, full attention 층이 모든 오류를 자동으로 고치는 장치도 아닙니다.

이 구조는 “Qwen3.8이 새 layer 하나를 발명해서 좋아졌다”는 식으로 쓰면 안 됩니다. SGLang 문서는 serving-relevant architecture가 Qwen3.6-27B와 같다고 적습니다. vLLM의 Qwen3.8 recipe도 64개 층 중 16개만 full attention이고 나머지 48개는 constant recurrent state를 쓰는 같은 layer mix를 설명합니다. 공개 자료가 강조하는 차이는 pre-training·post-training 결과, 장기 작업 수행, 환경 feedback 처리와 runtime 제어입니다. 상세 training data와 post-training recipe가 공개되지 않은 부분은 원인으로 분해할 수 없습니다.

## MTP는 답을 병렬 완성하는 기능이 아닙니다

Qwen3.8-27B checkpoint에는 여러 단계로 학습된 MTP, 즉 Multi-Token Prediction head가 들어 있습니다. serving engine은 이 head를 speculative decoding에 쓸 수 있습니다. vLLM recipe는 MTP를 켜려면 `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'`를 추가한다고 설명하고, SGLang recipe는 EAGLE 설정이 in-checkpoint MTP head를 사용한다고 적습니다.

이 기능은 답 전체를 병렬로 완성한다는 뜻이 아닙니다. 작은 draft 경로가 다음 몇 token 후보를 먼저 내고, 본 모델이 그 후보를 검증해 맞는 구간을 한 번에 채택하는 방식입니다. 생성 속도와 tail latency 개선 폭은 GPU, precision, batch, prompt 길이, average request length, speculative token 수, framework 설정에 따라 달라집니다. 이 기사는 모델을 실행하지 않았으므로 실측 throughput을 만들지 않습니다.

SGLang 문서가 특히 실무적인 이유는 hybrid GDN 모델의 post-weight memory를 GDN state pool과 paged attention KV pool로 나눠 설명하기 때문입니다. 평균 요청 길이와 목표 concurrency가 바뀌면 `--mamba-full-memory-ratio` 또는 `--max-mamba-cache-size` 같은 설정이 처리량을 좌우할 수 있습니다. 긴 agent session을 여러 개 동시에 돌리는 팀은 모델을 띄웠다는 사실보다 이 state와 KV의 균형을 봐야 합니다.

## 생각을 이어 주고, 도구 호출을 통역합니다

Qwen3.8은 thinking mode가 기본으로 켜져 있고, `reasoning_effort`를 `low`, `medium`, `xhigh`로 조절할 수 있습니다. 모델 카드는 복잡한 작업에는 `xhigh`를 기본값으로 두고, 낮은 reasoning effort가 한 turn 응답을 빠르게 만들 수는 있지만 다중 turn agent 작업에서는 실패와 재시도로 전체 latency와 token 사용량을 늘릴 수 있다고 설명합니다. 따라서 `low`는 비용 절감 버튼이 아니라 task class별로 검증해야 할 runtime knob입니다.

`preserve_thinking`은 더 직접적으로 agent 실행과 연결됩니다. Qwen3.8은 기본적으로 과거 message의 thinking block을 보존해 reasoning trace의 연속성을 유지한다고 설명합니다. 긴 코드 수정, 조사, UI 조작처럼 이전 결정의 맥락이 다음 turn의 행동을 바꾸는 작업에서는 이 기능이 중복 reasoning을 줄이고 decision consistency를 높일 수 있습니다. 반대로 민감한 intermediate reasoning을 어디까지 저장하고 전달할지, 로그와 권한 경계를 어떻게 둘지는 harness 설계 문제로 남습니다.

도구 호출은 모델만 serve한다고 끝나지 않습니다. SGLang recipe는 모든 recipe에 `--reasoning-parser qwen3 --tool-call-parser qwen3_coder`가 들어간다고 설명합니다. 이 parser가 빠지거나 harness가 다른 payload 형식을 기대하면 모델이 만든 tool call이 구조화된 `tool_calls`가 아니라 일반 텍스트로 흘러갈 수 있습니다. vLLM recipe도 `--reasoning-parser qwen3`, `--enable-auto-tool-choice`, `--tool-call-parser qwen3_coder`를 launch command에 넣습니다. agent 배포에서 확인해야 할 접점은 모델 weight, endpoint URL, parser, tool schema, approval policy가 같은 형식으로 맞물리는지입니다.

## 코딩 모델에서 범용 작업 에이전트로 넓어졌습니다

Qwen3.6-27B도 같은 27B dense vision-language 계열이고, agentic coding과 thinking preservation을 강하게 내세운 모델이었습니다. Qwen3.6 모델 카드는 coding, repository-level reasoning, thinking preservation을 핵심 변화로 설명했고, Qwen-Agent와 Qwen Code 사용 예를 제공했습니다.

Qwen3.8-27B의 공식 자료는 coding을 포함하되 professional work, research, long-horizon agentic tasks, environment feedback, desktop·browser·mobile 사용을 더 넓게 강조합니다. 그래서 이번 차이는 “coding model의 다음 버전”보다 “팀이 직접 운영할 수 있는 범용 multimodal agent model”로 범위가 넓어진 것으로 보는 편이 정확합니다.

Qwen 자체 benchmark 표도 이 방향을 보여 줍니다. Qwen은 Terminal Bench 2.1에서 Qwen3.8-27B 73.0, Qwen3.6-27B 63.4를, SWE-bench Pro에서 각각 61.7과 53.5를 제시했습니다. 다만 이 수치는 Qwen 모델 카드의 자체 평가입니다. SWE-bench Pro는 Claude Code harness, temperature 1.0, top_p 0.95, 256K context window, corrected problematic tasks 같은 조건이 붙고, QwenSWEBench와 CoWorkBench, RecreationBench는 Qwen이 만든 in-house benchmark입니다. 독립 재현 결과처럼 쓰면 근거를 넘습니다.

## 실제 배포 선택지는 네 갈래로 나뉩니다

첫째, 조직 내부 코드와 문서를 262,144-token native context 안에서 다루는 self-hosted agent입니다. 이 경우 모델의 긴 context보다 더 중요한 것은 repo snapshot, tool permission, test runner, sandbox, audit log입니다. 긴 prompt를 넣을 수 있어도 잘못된 파일을 고치거나 권한 밖 명령을 실행하면 agent 품질이 아니라 운영 사고가 됩니다.

둘째, screenshot이나 설계 문서를 보고 browser·desktop tool을 호출하는 multimodal workflow입니다. Qwen3.8-27B는 image와 video understanding을 native feature로 제시하고, SGLang은 Qwen3-VL path로 vision tower가 recipe에서 live라고 설명합니다. 다만 vision·video 입력은 prompt injection 표면도 넓힙니다. 화면 안의 텍스트가 명령처럼 보이더라도 tool execution 권한과 외부 네트워크 접근은 별도 policy가 결정해야 합니다.

셋째, 작업별 reasoning budget 제어입니다. 단순 질의는 non-thinking 또는 `low`로 두고, 긴 코드 수정·조사·검증은 `medium`이나 `xhigh`를 쓰는 식의 routing이 가능합니다. 이때 평가는 한 요청의 latency만 보면 안 됩니다. 실패율, 재시도 횟수, 총 token, test 통과율, 사람이 되돌린 patch 비율을 함께 봐야 합니다.

넷째, OpenAI-compatible endpoint로 기존 agent harness에 붙이는 운영입니다. Hugging Face 모델 카드는 vLLM과 SGLang을 통한 OpenAI-compatible 호출 예를 제공합니다. SGLang은 OpenCode, Pi, Claude Code, Hermes Agent 연결 예를 보여 주고, vLLM은 OpenAI client usage와 parser 설정을 제공합니다. 기존 harness를 그대로 쓸 수 있다는 뜻이 아니라, transport와 parser와 model id가 일치하면 migration 비용이 줄어든다는 뜻입니다.

## 기술적 의미는 직접 운영 가능한 범위가 넓어졌다는 점입니다

이번 공개의 기술적 의미는 최신 agent capability가 폐쇄형 대형 API에만 머물지 않고, 조직이 가중치와 serving stack을 직접 통제할 수 있는 27B dense 급으로 내려왔다는 데 있습니다. dense 모델은 MoE router 없이 모든 parameter를 매 token 사용하므로 운영 모델을 이해하기 쉽지만, memory와 throughput 요구가 사라지는 것은 아닙니다.

공식 FP8 checkpoint와 제3자 NVFP4 quantization은 구분해야 합니다. Qwen의 FP8 repo는 fine-grained FP8 quantization, block size 128, 원 모델과 거의 같은 성능 지표라고 설명합니다. 반면 NVFP4 checkpoint는 SGLang과 vLLM 문서에서 별도 provider artifact로 다뤄집니다. quantization에 따른 품질 저하, tool-call 안정성, vision 입력 품질, latency와 memory는 각 팀의 workload에서 다시 재야 합니다.

아직 검증할 부분도 분명합니다. benchmark 대부분은 Qwen이 제시한 수치이고, 독립적인 장기 agent 재현은 충분하지 않습니다. detailed training data와 post-training recipe가 공개되지 않아 성능 향상의 원인을 구조만으로 분해할 수 없습니다. million-token context의 정확도, latency, memory, concurrency는 workload별 측정이 필요합니다. vision·video 입력과 tool execution에는 prompt injection, 권한 제한, sandbox, 감사 경계가 별도 설계로 붙어야 합니다.

## 이해상충과 취재 조건

Qwen Hugging Face 모델 카드와 FP8 checkpoint는 Qwen의 1차 자료입니다. 이 자료는 공개 가중치, license, 모델 구조, context, API 사용 예, benchmark 조건과 Qwen이 제시한 수치를 확인하는 데 적합하지만, 경쟁 모델 대비 일반적 우월성의 독립 근거는 아닙니다.

SGLang과 vLLM recipe는 serving framework 관점의 원문입니다. parser, MTP, memory, hardware fit, long-context 설정 같은 배포 지점을 확인하는 데 사용했습니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 웹 문서와 Hugging Face API metadata만 사용했고, 모델 실행이나 benchmark 재현은 하지 않았습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Qwen3.8-27B는 Apache-2.0 라이선스의 27B dense 공개 가중치 vision-language 모델입니다. | E2 · P2 · R2 | Qwen Hugging Face 모델 카드와 HF API metadata로 확인했습니다. 공개 repo와 config는 열람 가능하지만, 편집국은 weight를 내려받아 실행하지 않았습니다. |
| C2. 언어 모델은 64개 층, 16 × (3 × Gated DeltaNet → FFN, 1 × Gated Attention → FFN) 구조이며 native context는 262,144 tokens입니다. | E2 · P1 · R2 | 모델 카드, raw `config.json`, SGLang·vLLM recipe로 확인했습니다. 이 구조만으로 성능 향상의 원인을 단정하지 않습니다. |
| C3. Qwen3.8-27B에는 multi-step MTP head가 있고, serving engine은 speculative decoding에 쓸 수 있습니다. | E2 · P1 · R1 | 모델 카드, SGLang recipe, vLLM recipe로 확인했습니다. 실제 속도 향상은 측정하지 않았습니다. |
| C4. Qwen3.8은 `reasoning_effort`와 `preserve_thinking`을 지원하고, 낮은 effort가 전체 agent 작업 시간과 token 사용량을 항상 줄이지는 않는다고 Qwen이 설명합니다. | E2 · P1 · R1 | Qwen 모델 카드의 API usage와 best practice 설명으로 확인했습니다. 실제 agent success rate는 독립 재현하지 않았습니다. |
| C5. SGLang과 vLLM recipe는 Qwen3.8-27B agent harness 연결에 `qwen3` reasoning parser와 `qwen3_coder` tool-call parser를 사용합니다. | E2 · P1 · R1 | SGLang과 vLLM recipe로 확인했습니다. harness별 tool schema와 parser 호환성은 각 배포 환경에서 확인해야 합니다. |
| C6. Qwen 모델 카드의 Terminal Bench 2.1과 SWE-bench Pro 수치는 Qwen3.8-27B가 Qwen3.6-27B보다 높게 제시되지만, 자체 평가 조건과 in-house benchmark가 섞여 있습니다. | E2 · P1 · R1 | Qwen3.8 모델 카드 benchmark table과 footnote로 확인했습니다. 독립 순위 결론으로 쓰지 않았습니다. |
| C7. 중심 판단은 Qwen3.8-27B가 27B dense 규모에서 장기 에이전트 실행, multimodal 입력, thinking/runtime 제어, parser 기반 tool call을 함께 self-hosting 선택지로 묶었다는 것입니다. | E2 · derived · R2 | C1-C6에서 파생한 판단입니다. 배포 성능과 안전성은 team workload, serving framework, quantization, sandbox policy에 따라 달라집니다. |

## 출처

- Qwen/Qwen3.8-27B Hugging Face model card: https://huggingface.co/Qwen/Qwen3.8-27B
- Qwen/Qwen3.8-27B-FP8 Hugging Face checkpoint: https://huggingface.co/Qwen/Qwen3.8-27B-FP8
- Qwen/Qwen3.8-27B raw config: https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json
- Qwen/Qwen3.6-27B Hugging Face model card: https://huggingface.co/Qwen/Qwen3.6-27B
- SGLang Qwen3.8-27B cookbook: https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B
- vLLM Qwen3.8-27B recipe: https://recipes.vllm.ai/Qwen/Qwen3.8-27B
