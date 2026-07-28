---
edition: ai
decision: publish-candidate
title: "Kimi K3 weights 공개의 실제 범위: 1.56 TB artifact와 8-GPU 배포 경계"
date: 2026-07-29
subject: "Moonshot AI Kimi K3, Hugging Face revision 9f62e4e9fffbd0a83ddd60e1c209d828994b3569, GitHub commit 7c5be9599120d7993748de66a76128614f15f210"
summary: "Kimi K3의 전체 weights, config, 기술보고서와 serving code가 공개됐습니다. 다만 96개 weight shard가 약 1.56 TB이고 공개 recipe가 최소 8대의 고용량 accelerator와 nightly runtime을 전제하므로, open-weight와 손쉬운 자체 배포를 같은 뜻으로 보면 안 됩니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["Moonshot AI는 Kimi K3와 공개 weights·기술보고서의 개발 주체입니다. 이 기사에는 Moonshot AI 또는 serving 업체의 사전 접근, 계정·credit·hardware 제공, 후원, 광고, NDA나 embargo가 없었습니다."]
---

Kimi K3 weights 공개에서 개발자에게 중요한 변화는 API로만 보던 모델을 고정 revision의 artifact와 code로 직접 검사할 수 있게 됐다는 점입니다. 동시에 공개된 파일 크기와 serving recipe는 이 모델이 개인 workstation용 local model이 아니라는 점도 분명히 보여줍니다. 자체 배포를 검토하는 팀이라면 benchmark 순위보다 먼저 1.56 TB checkpoint, 최소 8-GPU topology, custom license와 아직 이동 중인 runtime 통합 상태를 확인할 가치가 있습니다.

## 세 줄 요약

- Hugging Face revision `9f62e4e9fffbd0a83ddd60e1c209d828994b3569`에는 인증 gate 없이 접근 가능한 96개 `safetensors` weight shard가 있으며, 합계는 1,560,936,091,448 byte로 약 1.56 TB입니다.
- Kimi K3는 전체 2.8T parameter 가운데 token마다 104B parameter를 활성화하는 전문가 혼합(Mixture-of-Experts, MoE) 모델이며, config는 최대 1,048,576-token context를 기록합니다.
- 공개 vLLM recipe는 최소 8대의 GB300 또는 MI350X·MI355X와 K3 지원 nightly를 전제하고, SGLang 문서는 여러 8~32 GPU topology를 제시하면서도 final weights 대상 serving round를 다시 측정하라고 경고합니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 고정 revision에서 weights의 존재와 byte 크기, model config, custom license, 1M context 설정, Moonshot의 API message 계약, vLLM·SGLang의 K3 model code와 배포 recipe를 검사할 수 있습니다.
- **도입 전에 확인할 것:** 1.56 TB artifact의 mirror·hash·load 시간, 최소 8-GPU node의 HBM과 interconnect, nightly image의 exact digest, 1M context에서의 동시성, `reasoning_content` 보존, license의 서비스·표시 조건을 조직 환경에서 검토해야 합니다.
- **아직 결론 내릴 수 없는 것:** 공개 weights만으로 API와 자체 배포의 output 동등성, production throughput·tail latency·장애율, 한국어 품질, 장문 context의 실제 유효 길이, 다른 frontier 모델 대비 우월성을 결론 내릴 수 없습니다.

## 이 공개의 의의와 편집 판단

7월 27일 Hugging Face에 올라온 Kimi K3 revision은 비공개 API endpoint와 별개로 model weight, tokenizer, config와 remote code를 내려받아 검사할 수 있는 경로를 제공합니다. 7월 28일 갱신된 GitHub repository에는 기술보고서와 model summary가 있고, vLLM과 SGLang에도 K3 전용 recipe와 kernel·model code가 공개돼 있습니다.

**편집 판단:** 이 공개의 의미는 “누구나 노트북에서 frontier model을 돌린다”는 데 있지 않습니다. API 사업자의 구현만 믿던 단계에서 weight와 runtime 양쪽의 변경을 각각 고정하고 검증할 수 있는 단계로 이동했다는 데 있습니다. 자체 배포의 첫 의사결정은 benchmark 1위 여부가 아니라 artifact 공급망, 8-GPU 이상 cluster를 운영할 이유, runtime 통합의 성숙도, custom license가 주는 운영 조건을 비용과 함께 비교하는 일이어야 합니다.

## 공개된 것은 API 약속이 아니라 실제 checkpoint입니다

Hugging Face API에서 확인한 revision `9f62e4e9fffbd0a83ddd60e1c209d828994b3569`는 public이며 gated가 아닙니다. 이 revision에는 `model-00001-of-000096.safetensors`부터 이어지는 96개 weight shard가 있습니다. 각 LFS object의 크기를 합산하면 1,560,936,091,448 byte이며, 이는 약 1.56 TB 또는 1.42 TiB입니다.

이 차이는 배포 계획에서 중요합니다. “가중치가 공개됐다”는 말은 파일에 접근할 수 있다는 뜻이지만, 한 번의 download와 한 장의 GPU로 실행할 수 있다는 뜻은 아닙니다. mirror를 두 번 만들면 저장 공간만 약 3.12 TB가 필요하고, cache·container·runtime artifact와 rollback용 이전 revision은 별도입니다.

고정 config는 model type을 `kimi_k3`, architecture를 `KimiK3ForConditionalGeneration`으로 기록합니다. 내부 `text_config`에는 93개 layer, hidden size 7,168, 최대 position 1,048,576이 적혀 있습니다. model card와 기술보고서는 총 2.8T parameter, token마다 104B activated parameter, 896개 routed expert 가운데 16개 선택, MXFP4 weight와 MXFP8 activation을 설명합니다.

MoE는 모든 parameter를 매 token 계산에 쓰지 않고 router가 일부 expert를 선택하는 구조입니다. 따라서 104B activated parameter는 계산량을 이해하는 데 유용하지만, 저장해야 할 weight가 104B 규모라는 뜻은 아닙니다. 1.56 TB artifact가 보여주듯 저장·load·분산 배치는 전체 2.8T parameter의 영향을 받습니다.

## 입력에서 출력까지는 reasoning state를 보존해야 합니다

Moonshot의 model README는 Kimi K3가 항상 thinking을 사용하고 `reasoning_effort`를 `low`, `high`, `max`로 조절한다고 설명합니다. multi-turn 대화와 tool call에서는 이전 assistant message의 `content`만 돌려보내지 말고 `reasoning_content`와 `tool_calls`를 포함한 message 전체를 다음 `messages`에 그대로 넣도록 요구합니다.

이 계약은 OpenAI-compatible endpoint라는 표면만 보고 기존 client를 교체할 때 놓치기 쉽습니다. proxy가 알려지지 않은 field를 제거하거나 conversation store가 `content`만 보존하면 다음 turn의 working state가 달라질 수 있습니다. API adapter test에는 request schema뿐 아니라 assistant message의 round-trip 보존과 tool-call 재연결을 포함해야 합니다.

공개 model summary는 modality를 Text와 Image로 표시합니다. 기술보고서는 training architecture가 image와 video를 함께 처리한다고 설명하지만, 현재 SGLang의 공개 serving 계약은 image input만 지원하며 processor가 video와 audio를 거부한다고 명시합니다. 기술보고서의 학습 범위와 지금 배포 가능한 public serving surface를 같은 capability로 취급하면 안 됩니다.

## 자체 배포의 시작점은 최소 8-GPU입니다

vLLM recipe의 고정 commit `5e93cbed6168919ef4d3e26ceda34a1245199499`는 Kimi K3를 `difficulty: hard`와 `pre-release`로 표시합니다. 기본 variant의 VRAM 추정치는 1,680 GB이고, single-node tensor parallel과 multi-node tensor·expert parallel의 최소 GPU 수를 8대로 둡니다. 안내문은 최소 8대의 GB300, ROCm에서는 최소 8대의 MI350X 또는 MI355X를 요구하며 실제 production traffic에는 multi-node를 권합니다.

recipe가 쓰는 `vLLM 0.27.0`과 K3 image는 아직 integration이 들어간 nightly를 요구합니다. 같은 파일은 공개 전 추정치인 1,680 GB와 “weights 공개 뒤 실제 footprint로 교체”하라는 주석도 유지합니다. 따라서 hardware가 `verified`로 표시돼 있어도 recipe metadata 전체가 최종 release contract로 정리됐다고 보기는 어렵습니다.

SGLang 문서는 더 넓은 topology를 제시합니다. B300과 MI350X·MI355X는 1 node × 8 GPU, B200과 H200은 2 × 8 GPU, GB200은 4 × 4 GPU, H100은 4 × 8 GPU를 기본 shape로 둡니다. 8-GPU B300 예제는 tensor parallel과 decode-context parallel을 각각 8로 설정하고, 대규모 preset은 16·32·64 GPU로 확장합니다.

그러나 SGLang 문서는 final weights와 현재 code 조합의 serving round가 아직 열려 있으며, throughput과 accuracy를 직접 다시 측정하라고 적습니다. 일부 large-scale preset도 final weights 전체 round를 마치지 않았다고 밝힙니다. 공개 code가 있다는 사실은 R2 실행 가능성을 만들지만, production 안정성과 성능을 독립 확인한 R3 근거는 아닙니다.

## custom license는 open source와 분리해 읽어야 합니다

Kimi K3 License는 weight, parameter, config, inference·training code와 문서를 사용·복사·수정·배포할 권한을 부여합니다. 동시에 Model as a Service 사업자의 관계사 합산 매출이 연속 12개월 동안 2,000만 달러를 넘으면 상업적 사용 전에 Moonshot AI와 별도 계약을 맺도록 합니다.

상업 제품이나 서비스가 월간 활성 사용자 1억 명 또는 월 매출 2,000만 달러를 넘으면 UI에 `Kimi K3`를 두드러지게 표시해야 하는 조건도 있습니다. 내부 사용과 Moonshot 공식 제품·인증 inference partner를 통한 사용에는 이 두 조건의 예외가 적혀 있습니다.

Hugging Face metadata도 license를 표준 permissive 식별자가 아니라 `other`, 이름을 `kimi-k3`로 표시합니다. 따라서 이 모델은 공개 weights를 가진 custom-license 모델로 분류하는 편이 정확합니다. 구체적인 서비스가 어느 조항에 해당하는지는 이 기사가 법률 판단을 대신하지 않으므로, 외부 제공 전 조직의 법무 검토가 필요합니다.

## 작은 검증은 download 전에 시작할 수 있습니다

첫 단계에서는 1.56 TB를 받지 않고 metadata를 고정할 수 있습니다. Hugging Face revision, 96개 shard의 LFS object ID와 size, `model.safetensors.index.json`, config, tokenizer, remote-code file과 license hash를 manifest로 만듭니다. mirror는 `main`이 아니라 revision `9f62e4e9fffbd0a83ddd60e1c209d828994b3569`를 기준으로 받아야 합니다.

두 번째 단계에서는 runtime을 별도로 고정해야 합니다. vLLM recipe commit, SGLang branch commit, container digest, CUDA 또는 ROCm version, driver, kernel package와 launch argument를 기록합니다. model revision과 runtime image를 한꺼번에 바꾸지 않아야 output 차이나 startup 실패의 원인을 분리할 수 있습니다.

세 번째 단계에서는 짧은 text·image·tool-call fixture부터 실행합니다. model list와 health check, deterministic하게 검사 가능한 schema, `reasoning_content` round trip, image processor, tool argument JSON, timeout과 OOM 처리를 저장합니다. Moonshot이 공개한 Vendor Verifier에는 parameter constraint, tool-call schema, K3 feature와 prompt-token 검사가 있으므로 provider API와 자체 endpoint에 같은 fixture를 적용할 출발점으로 쓸 수 있습니다.

마지막에만 workload 성능을 측정해야 합니다. 1M context를 한 요청에 넣는 demo보다 실제 prompt·output 길이 분포, 동시성, time to first token, inter-token latency, p95·p99 latency, GPU memory, 실패율과 재시도 비용을 함께 기록해야 합니다. 8-GPU에서 시작하는 모델은 idle capacity와 cluster 운영 비용이 API 단가보다 클 수 있으므로, 사용률을 제외한 token당 비용 비교는 불완전합니다.

## 공개 benchmark는 채택 결론으로 올리지 않았습니다

Moonshot의 README와 기술보고서는 coding, agentic, vision benchmark를 폭넓게 제시합니다. 다만 비교 대상마다 harness가 다르거나 vendor 결과를 가져온 항목이 있고, 일부 평가는 H100 대신 H20에서 세 번 실행했으며, 어떤 closed model은 fallback이나 cyber refusal이 결과에 포함됩니다.

이 기사는 그 점수를 Kimi K3의 우월성 근거로 사용하지 않습니다. weights와 evaluator code가 공개돼도 2.8T model을 같은 hardware·harness·effort·tool budget으로 다시 실행한 독립 결과가 자동으로 생기지는 않습니다. Vendor Verifier의 여러 provider 결과도 Moonshot이 제공한 harness로 API 호환성과 일부 평가를 비교하는 P2 artifact이지, 모든 workload의 독립 production benchmark는 아닙니다.

한국어 품질도 별도 gate가 필요합니다. 공개 표의 영어 중심 coding·knowledge 결과나 1M context 설정만으로 한국어 문서 검색, honorific, code-switching, 긴 한글 PDF의 OCR과 tool-use 정확도를 추정할 수 없습니다. 한국 팀은 실제 개인정보·보안 정책을 반영한 비식별 fixture와 한국어 실패 분류를 따로 준비해야 합니다.

## 적용 범위와 확인하지 못한 것

- 공개 여부는 Hugging Face revision과 GitHub commit에서 확인했지만, 1.56 TB weights를 내려받거나 hash를 다시 계산하지는 않았습니다.
- model binary를 load하거나 Kimi API, vLLM, SGLang endpoint를 호출하지 않았습니다.
- 8-GPU 이상 topology의 startup time, HBM 사용량, throughput, latency, 전력과 장애 복구를 재현하지 않았습니다.
- model card의 benchmark 수치를 독립 실행하지 않았으며, 다른 frontier model보다 우수하다는 결론을 내리지 않았습니다.
- training data의 전체 목록·라이선스·개인정보 처리, comprehensive safety card와 한국어 평가를 확인하지 못했습니다.
- vLLM과 SGLang recipe는 빠르게 갱신 중이므로 여기 적은 commit과 현재 branch의 차이를 배포 전에 다시 확인해야 합니다.

## 도입 판단: API 대체보다 artifact 검증 경로로 봐야 합니다

Kimi K3의 공개 weights는 자체 배포 가능성을 검토할 실체를 제공합니다. model revision을 고정하고 license, config, runtime code와 serving protocol을 inspect할 수 있으므로, 비공개 API만 있는 모델보다 공급망과 변경 관리의 선택지가 넓습니다.

하지만 현재 공개 자료가 보여주는 최소 단위는 8대의 최신 data-center accelerator와 nightly runtime입니다. 이미 이 cluster를 운영하고 높은 지속 사용률, 데이터 경계 또는 custom inference가 필요한 팀이 아니라면 API와 자체 배포를 바로 비용 경쟁으로 놓기 어렵습니다.

평가 순서는 metadata-only manifest, custom license 검토, 고정 image의 8-GPU smoke test, API parity fixture, workload별 성능·한국어 평가, 장애·rollback 순서가 적절합니다. 각 gate를 통과하기 전에는 “open-weight이므로 손쉽게 self-host할 수 있다”거나 “공개 benchmark가 높으므로 기존 모델을 교체할 수 있다”는 결론을 내리지 않는 편이 안전합니다.

## 이해상충과 취재 조건

Moonshot AI는 Kimi K3를 개발하고 model repository, weights, 기술보고서와 Vendor Verifier를 공개한 주체입니다. architecture, benchmark와 API 동작 설명은 개발 주체가 선택한 자료이며, 이 기사에서 독립 성능 검증으로 취급하지 않았습니다.

vLLM과 SGLang은 공개 serving engine 프로젝트이며 K3 전용 code와 recipe를 유지합니다. recipe의 지원 표기와 주석은 공개 구현 상태를 확인하는 근거이지만, 이 기사에서 해당 hardware를 실행한 결과는 아닙니다.

이 기사에는 Moonshot AI, vLLM, SGLang 또는 inference provider의 사전 briefing, 계정·credit·hardware 제공, 후원, 광고, NDA나 embargo가 없었습니다. 공개 웹 문서, API metadata, 고정 commit·revision의 code와 기술보고서만 확인했습니다.

## 근거 원장

| Claim | 판정 | 출처/근거 | 등급 | 한계·재확인 조건 |
|---|---|---|---|---|
| Kimi K3의 public·non-gated revision에는 96개 weight shard, 약 1.56 TB의 weights와 config가 있습니다 | Hugging Face API metadata와 고정 revision에서 확인 | Hugging Face revision `9f62e4e9fffbd0a83ddd60e1c209d828994b3569`, config, index | P2 / E2 / R2 | 전체 shard 미다운로드·hash 미재계산, upstream metadata 변경은 고정 revision으로 통제 |
| Kimi K3는 2.8T total·104B activated MoE이며 config는 1,048,576-token context를 기록합니다 | model card, config와 기술보고서로 확인 | GitHub commit `7c5be9599120d7993748de66a76128614f15f210`, arXiv 2607.24653, fixed config | P1+P2 / E2 / R2 | architecture 설명은 개발 주체 자료, 실제 유효 context와 품질 미재현 |
| 공개 vLLM·SGLang 경로는 최소 8-GPU급 배포와 moving runtime integration을 보여줍니다 | fixed recipe·code와 공개 문서에서 확인 | vLLM recipe commit `5e93cbed6168919ef4d3e26ceda34a1245199499`, SGLang commit `b5607ec5a4f416a8e52c6b47e23d476e3686c887`와 cookbook | P2 / E2 / R2 | 기사에서 실행하지 않았고 SGLang final-weight round와 일부 preset 검증이 진행 중 |
| multi-turn과 tool call은 `reasoning_content`를 포함한 assistant message 보존이 필요합니다 | 고정 model README의 usage contract로 확인 | Kimi K3 README at commit `7c5be9599120d7993748de66a76128614f15f210`, Vendor Verifier | P1+P2 / E2 / R2 | Moonshot API와 self-host endpoint의 parity 미검증 |
| Kimi K3는 공개 weights지만 custom license의 서비스·표시 조건을 가집니다 | license 원문과 Hugging Face metadata로 확인 | Kimi K3 License at fixed commit, Hugging Face model metadata | P1+P2 / E2 / R2 | 법률 해석이 아니며 조직·서비스별 별도 검토 필요 |
| 도입은 manifest, license, runtime smoke test, API parity, workload 평가 순으로 나눠야 합니다 | 편집 판단 | 위 artifact·topology·protocol·license claim에서 파생 | 편집 판단 / E2 / R2 | 조직의 hardware·traffic·보안·비용 조건으로 다시 검증 필요 |

## 출처

1. Moonshot AI, Kimi K3 repository, commit `7c5be9599120d7993748de66a76128614f15f210`, 조회 2026-07-29: https://github.com/MoonshotAI/Kimi-K3/tree/7c5be9599120d7993748de66a76128614f15f210
2. Moonshot AI, Kimi K3 model card, Hugging Face revision `9f62e4e9fffbd0a83ddd60e1c209d828994b3569`: https://huggingface.co/moonshotai/Kimi-K3/tree/9f62e4e9fffbd0a83ddd60e1c209d828994b3569
3. Kimi K3 fixed config: https://huggingface.co/moonshotai/Kimi-K3/blob/9f62e4e9fffbd0a83ddd60e1c209d828994b3569/config.json
4. Kimi K3 fixed weight index: https://huggingface.co/moonshotai/Kimi-K3/blob/9f62e4e9fffbd0a83ddd60e1c209d828994b3569/model.safetensors.index.json
5. Moonshot AI, “Kimi K3: Open Frontier Intelligence”, arXiv:2607.24653, submitted 2026-07-27: https://arxiv.org/abs/2607.24653
6. Kimi K3 License at commit `7c5be9599120d7993748de66a76128614f15f210`: https://github.com/MoonshotAI/Kimi-K3/blob/7c5be9599120d7993748de66a76128614f15f210/LICENSE
7. vLLM Kimi K3 recipe at commit `5e93cbed6168919ef4d3e26ceda34a1245199499`: https://github.com/vllm-project/recipes/blob/5e93cbed6168919ef4d3e26ceda34a1245199499/models/moonshotai/Kimi-K3.yaml
8. vLLM rendered Kimi K3 recipe, 조회 2026-07-29: https://recipes.vllm.ai/moonshotai/Kimi-K3
9. SGLang Kimi K3 cookbook, 조회 2026-07-29: https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3
10. SGLang Kimi K3 implementation tree, commit `b5607ec5a4f416a8e52c6b47e23d476e3686c887`: https://github.com/sgl-project/sglang/tree/b5607ec5a4f416a8e52c6b47e23d476e3686c887/python/sglang/srt/models
11. Moonshot AI Kimi Vendor Verifier, commit `def8ee5595e944b3afb57e04053e17ac6f6fbb60`: https://github.com/MoonshotAI/Kimi-Vendor-Verifier/tree/def8ee5595e944b3afb57e04053e17ac6f6fbb60
