---
edition: ai
decision: publish-candidate
title: "Qwen3.8-Flash-Next 공개 - 긴 에이전트 문맥의 계산을 줄이는 Qwen4 실험 구조"
date: 2026-08-27
subject: "Qwen3.8-Flash-Next open-weight model, Hugging Face revision f5d08274bafd880402bd16f5e3e6c514136ec06c and QwenLM technical report, August 2026"
summary: "Qwen이 Qwen4로 이어질 실험 구조를 공개 가중치 모델 Qwen3.8-Flash-Next로 내놨습니다. 이 모델은 긴 문맥 전체를 같은 방식으로 훑지 않고 Gated DeltaNet, Qwen Sparse Attention, n-gram embedding을 조합해 agent 작업의 긴 입력과 반복 호출 비용을 줄이려 합니다. 가중치와 config는 공개됐지만 성능 비교는 Qwen이 고른 benchmark 결과입니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["Qwen은 Qwen3.8-Flash-Next의 개발·공개 주체이며 모델 카드와 기술 보고서를 작성했습니다. Hugging Face는 모델 registry와 artifact hosting을 제공합니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Qwen이 2026년 8월 Qwen3.8-Flash-Next를 공개했습니다. 이 공개 가중치 모델은 단순히 모델을 키우기보다 긴 agent 문맥을 더 낮은 비용으로 처리하는 구조를 보여 줍니다. Hugging Face의 공식 Qwen repository에는 model weights, config, license, README가 올라와 있고, QwenLM GitHub repository에는 같은 구조를 설명하는 technical report가 연결되어 있습니다.

핵심 변화는 긴 입력을 처리할 때 attention 전체를 같은 방식으로 계산하지 않는다는 점입니다. Qwen3.8-Flash-Next는 Gated DeltaNet으로 많은 token 흐름을 선형 attention처럼 처리하고, 일정 간격마다 Qwen Sparse Attention으로 필요한 micro-block을 고릅니다. 여기에 n-gram embedding을 붙여 단어 조각 하나가 아니라 짧은 token 묶음의 정보를 embedding 쪽에서 크게 키웁니다. Qwen은 이 조합을 Qwen4 architecture의 실험 preview라고 설명합니다.

SW 엔지니어가 봐야 할 지점은 agent 실행입니다. coding agent나 research agent는 한 번 묻고 끝나는 chatbot보다 긴 repository, 문서, tool 결과를 계속 prompt에 넣고 다음 행동을 고릅니다. 이때 모든 token을 full attention으로 처리하면 context가 길어질수록 latency와 memory 부담이 커집니다. Qwen3.8-Flash-Next는 이 병목을 줄이기 위해 sparse attention, linear attention, MoE, n-gram embedding을 한 모델 안에 배치한 사례입니다.

## 긴 문맥 전체를 같은 방식으로 계산하지 않습니다

Transformer의 full attention은 현재 token이 앞의 많은 token을 직접 볼 수 있게 합니다. 품질에는 강한 구조지만, 문맥이 길어질수록 계산량과 KV cache 부담이 커집니다. 그래서 긴 문서를 읽거나 여러 tool 결과를 누적하는 agent에서는 attention 자체가 비용과 latency의 큰 부분을 차지합니다.

Qwen3.8-Flash-Next는 이 문제를 두 갈래로 나눕니다. Gated DeltaNet은 대부분의 layer에서 token 흐름을 더 싸게 처리하는 역할을 맡습니다. Qwen Sparse Attention은 모든 token을 하나씩 고르는 방식이 아니라 micro-block 단위로 중요한 영역을 고릅니다. 모델 카드에는 Qwen Sparse Attention의 budget이 512 blocks 또는 2048 tokens로 적혀 있습니다.

이 구조는 “긴 문맥을 지원한다”는 문구보다 구체적입니다. Qwen은 이 모델이 262,144 token context를 native로 지원하고, RoPE scaling을 쓰면 1,000,000 token까지 확장할 수 있다고 설명합니다. 다만 1M context는 model card의 권장 설정과 구조 설명으로 확인한 범위입니다. 편집국이 같은 hardware에서 실제 agent workload를 재실행해 검증한 결과는 아닙니다.

## n-gram embedding은 일부 비용을 embedding 쪽으로 옮깁니다

Qwen3.8-Flash-Next의 parameter 표기는 일반적인 dense model과 다르게 읽어야 합니다. 모델 카드는 language model이 125B parameter이며 그중 6B가 활성화되고, 여기에 51B n-gram embedding과 4B MTP가 붙는다고 설명합니다. MoE는 512 experts 중 10 routed experts와 1 shared expert를 활성화합니다.

n-gram embedding은 짧은 token 묶음을 embedding table에서 직접 찾는 방식입니다. Qwen은 bigram과 trigram을 layer 2에서 쓰며, n-gram embedding 규모를 20,000,000으로 공개했습니다. 이 선택은 모델의 지식을 모두 attention block이나 expert 계산에만 넣지 않고, embedding 쪽에도 크게 둘 수 있다는 뜻입니다.

개발자 입장에서는 장점과 제약이 함께 생깁니다. 활성 parameter가 작아도 weight 파일 전체는 큽니다. Hugging Face file tree는 전체 repository 크기를 360GB로 보여 줬고, safetensors shard가 131개 올라와 있습니다. 로컬에서 돌릴 수 있는 공개 가중치 모델이지만, 일반적인 개발 노트북에서 실험하기에는 무겁습니다. Qwen도 production이나 high-throughput 작업에는 vLLM, SGLang, TokenSpeed 같은 전용 serving engine을 권합니다.

## agent API는 thinking block 보존을 전제로 합니다

Qwen3.8-Flash-Next 모델 카드는 OpenAI-compatible Chat Completions API 형태의 사용 예를 제공합니다. 기본값은 thinking mode입니다. 모델은 최종 답변 전에 `<think>` block을 만들 수 있고, `enable_thinking`, `preserve_thinking`, `reasoning_effort`로 동작을 조절합니다.

여기서 `preserve_thinking`은 agent workflow와 직접 연결됩니다. Qwen은 기본적으로 이전 대화의 thinking block을 보존해 context continuity를 유지한다고 설명합니다. 긴 agent 작업에서 모델이 같은 문제를 다시 추론하는 일을 줄이고 KV cache 사용을 개선하려는 설계입니다.

주의할 점도 있습니다. model card는 낮은 reasoning effort가 항상 전체 작업 시간을 줄이지는 않는다고 적습니다. 한 turn은 빨라져도 분석이 부족해 실패와 재시도가 늘면 전체 latency와 token 사용량이 커질 수 있기 때문입니다. agent 운영자는 단일 응답 속도뿐 아니라 작업 완료율, 재시도 횟수, tool call 수, 전체 token 사용량을 함께 봐야 합니다.

## benchmark는 구조를 이해하는 자료이지 독립 순위가 아닙니다

Qwen은 Qwen3.8-Flash-Next의 benchmark 표를 공개했습니다. 표에는 Qwen3.8-27B, Qwen3.7-Plus, DeepSeek-V4-Flash-0731, Claude-Opus-4.6 Max 같은 비교 대상이 들어갑니다. coding, agentic coding, vision-language 평가가 함께 제시되고, DeepSWE 1.1은 Claude Code와 mini-SWE-agent harness에서 더 높은 값을 보고하는 방식이라고 주석을 달았습니다.

이 결과는 모델을 이해하는 데 쓸 수 있지만, 독립 성능 결론으로 올리지는 않습니다. 평가 표와 주석은 Qwen이 작성한 model card에 들어 있습니다. 일부 benchmark는 harness, prompt, judge model, context length, 수작업 ground-truth 수정 같은 조건의 영향을 받습니다. 특히 Vision2Web은 Claude Code harness와 `gpt-5.4-2026-03-05` judge를 쓴다고 적혀 있어, model 자체와 외부 평가 구성 요소를 나눠 읽어야 합니다.

따라서 이 기사의 중심 주장은 “Qwen3.8-Flash-Next가 다른 모델보다 일반적으로 낫다”가 아닙니다. 확인 가능한 중심은 공개 artifact가 있는 125B-class hybrid architecture가 나왔고, 긴 context와 agent 실행을 위해 어떤 계산을 줄이려 하는지가 model card, config, technical report URL로 추적된다는 점입니다.

## 지금 확인한 것은 구조와 공개 artifact입니다

재현성 상태는 R2입니다. Hugging Face API와 file tree로 model revision `f5d08274bafd880402bd16f5e3e6c514136ec06c`, 공개 config, README, license, safetensors shard 존재를 확인했습니다. QwenLM GitHub repository의 main commit은 `513aa6e18a335296fc13e538232a8735b230877d`였고, technical report PDF가 같은 repository에 있습니다.

다만 R2는 “실행 가능한 artifact가 있다”는 뜻이지, 편집국이 360GB model을 내려받아 같은 benchmark를 재현했다는 뜻이 아닙니다. 이 turn에서는 hardware와 시간이 부족해 모델 실행, latency 측정, benchmark 재실행을 하지 않았습니다. 성능 수치는 Qwen이 공개한 결과로만 다룹니다.

제품팀이 바로 얻을 수 있는 판단은 더 실용적입니다. 긴 context agent를 운영한다면 모델 크기만 볼 수 없습니다. context 처리 방식, preserved thinking의 cache 효과, serving engine 지원 상태, output token budget, retry가 전체 latency에 주는 영향을 함께 실험해야 합니다. Qwen3.8-Flash-Next는 그 실험을 공개 가중치로 시작할 수 있게 해 주지만, production에는 별도의 hardware 계획과 workload별 검증이 필요합니다.

## 이해상충과 취재 조건

Qwen은 Qwen3.8-Flash-Next의 개발·공개 주체이며 모델 카드, 기술 보고서, benchmark 표를 작성했습니다. Hugging Face는 model registry와 artifact hosting을 제공합니다. 따라서 출시 사실, 구조 설명, 공개 artifact 존재는 1차 자료로 확인했지만, Qwen이 제시한 성능 비교는 독립 검증으로 보지 않았습니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 2차 tracker는 후보 발견과 대안 확인에만 사용했고, 기사 사실은 열린 공식 원문, model registry, GitHub repository metadata로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Qwen은 Qwen3.8-Flash-Next를 Qwen4 architecture로 이어질 experimental preview이자 공개 가중치 모델로 공개했습니다. | E2 · P1/P2 | Hugging Face Qwen model card와 file tree, QwenLM GitHub technical report URL로 확인했습니다. 공개 시점과 설명은 Qwen이 작성했습니다. |
| C2. 모델은 Gated DeltaNet, Qwen Sparse Attention, Gated Residual, n-gram embedding, MoE를 결합하고, 125B language-model parameter 중 6B를 활성화하며 51B n-gram embedding과 4B MTP를 둡니다. | E2 · P1/P2 | model card의 Model Overview와 config.json으로 확인했습니다. 구조 설명은 공개되어 있지만 학습 데이터와 전체 training log는 공개되지 않았습니다. |
| C3. Qwen Sparse Attention은 micro-block 단위로 선택하며 budget은 512 blocks 또는 2048 tokens입니다. 모델은 262,144 token context를 native로 지원하고 RoPE scaling으로 1,000,000 token까지 확장할 수 있다고 설명합니다. | E2 · P1/P2 | model card와 config.json으로 확인했습니다. 편집국은 1M context 실행을 재현하지 않았습니다. |
| C4. Hugging Face model API는 revision `f5d08274bafd880402bd16f5e3e6c514136ec06c`, createdAt `2026-08-24T08:24:59Z`, lastModified `2026-08-26T12:29:54Z`, 144개 sibling file, ungated public repository 상태를 반환했습니다. | E2 · P2 | Hugging Face API 응답으로 확인했습니다. 모델 파일 전체를 내려받거나 hash를 개별 검증하지는 않았습니다. |
| C5. Qwen Community License 1.0은 model weights, parameters, config, inference code, documentation 사용을 허용하지만, 큰 상업 서비스에는 표시 의무를 두고 특정 경쟁 행위를 제한합니다. | E1 · P1 | Hugging Face repository의 LICENSE 파일로 확인했습니다. 법률 해석은 하지 않았습니다. |
| C6. Qwen이 공개한 benchmark 표는 coding과 vision-language 결과를 포함하지만, 일부 harness, judge model, prompt, context length, ground-truth 수정 조건을 포함한 Qwen 작성 결과입니다. | E2 · P1 | model card의 Benchmark Results와 footnote로 확인했습니다. 독립 benchmark나 편집국 재현 결과로 쓰지 않았습니다. |

## 출처

1. Qwen, `Qwen/Qwen3.8-Flash-Next` model card: https://huggingface.co/Qwen/Qwen3.8-Flash-Next
2. Hugging Face file tree, `Qwen/Qwen3.8-Flash-Next`: https://huggingface.co/Qwen/Qwen3.8-Flash-Next/tree/main
3. Hugging Face API, `Qwen/Qwen3.8-Flash-Next`: https://huggingface.co/api/models/Qwen/Qwen3.8-Flash-Next
4. QwenLM GitHub, `Qwen3.8-Flash-Next` technical report: https://github.com/QwenLM/Qwen3.8-Flash-Next/blob/main/tech_report.pdf
5. Raw config, `Qwen/Qwen3.8-Flash-Next`: https://huggingface.co/Qwen/Qwen3.8-Flash-Next/raw/main/config.json
6. Qwen Community License 1.0: https://huggingface.co/Qwen/Qwen3.8-Flash-Next/raw/main/LICENSE
