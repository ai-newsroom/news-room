---
edition: ai
decision: publish-candidate
title: "vLLM 0.28.0 공개 - 대형 에이전트 모델 서빙의 런타임 병목을 다룹니다"
date: 2026-09-01
subject: "vLLM v0.28.0 release, GitHub tag v0.28.0, published 2026-08-26"
summary: "vLLM 0.28.0은 새 모델 하나를 더 지원하는 패치가 아닙니다. Kimi-K3, DeepSeek V4, Qwen3.8 같은 대형 MoE·장문맥 모델을 실제로 서빙할 때 생기는 decode, KV cache, speculative decoding, GPU·ROCm·XPU 배포 문제를 함께 다룬 릴리스입니다. 공개 release note, tag, wheel artifact와 source repository로 변경 범위는 확인할 수 있지만, 릴리스에 적힌 kernel-level 속도 향상은 프로젝트 자체 측정과 PR 설명에 머뭅니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["vLLM 프로젝트는 이번 릴리스와 release note의 작성·배포 주체입니다. GitHub와 PyPI/Docker 배포 경로는 공개 artifact를 제공합니다. 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

vLLM 프로젝트가 2026년 8월 26일 `v0.28.0`을 공개했습니다. 이번 릴리스의 핵심은 지원 모델 목록을 늘린 데서 끝나지 않습니다. Kimi-K3, DeepSeek V4, Qwen3.8처럼 MoE, 긴 문맥, speculative decoding, multimodal 입력을 함께 쓰는 모델을 실제 서비스에서 돌릴 때 runtime이 맡아야 할 일이 더 분명해졌습니다.

대형 모델을 API로 제공하는 팀은 이제 “모델이 지원되는가”만 볼 수 없습니다. 긴 prompt를 먼저 처리하고, token을 하나씩 decode하며, KV cache를 어디에 둘지 정해야 합니다. draft model이나 MTP로 다음 token 후보를 빨리 검증하는 방식도 전체 latency와 비용에 영향을 줍니다. vLLM 0.28.0은 이 병목을 engine core, hardware backend, large-scale serving, API frontend에서 함께 다룬 릴리스입니다.

이번 후보의 중심 근거 수준은 E2입니다. release note와 GitHub tag, 공개 wheel과 source tarball, commit metadata가 있어 변경 범위와 배포 artifact는 추적할 수 있습니다. 다만 “얼마나 빨라졌는가”는 각 PR과 프로젝트 release note가 고른 조건에서 설명한 수치이므로, 독립 benchmark 순위나 모든 workload의 성능 향상으로 쓰지 않습니다.

## 큰 모델을 서빙하려면 런타임이 더 많은 일을 맡아야 합니다

Kimi-K3와 DeepSeek V4 같은 모델은 단순한 dense transformer보다 서빙 조건이 복잡합니다. 일부 layer와 expert만 쓰는 MoE 구조가 있고, sparse MLA나 KDA 같은 attention 변형도 들어갑니다. 여기에 MTP와 DSpark speculative decoding, 긴 context, multimodal encoder가 함께 붙습니다. 모델 카드가 공개돼도 runtime이 이 조합을 효율적으로 처리하지 못하면 제품에서는 latency, 메모리, 장애 복구가 병목이 됩니다.

vLLM 0.28.0의 highlights는 이 문제를 정면으로 보여 줍니다. Kimi-K3 쪽에는 Decode Context Parallel 지원, FlashKDA decode·prefill fused kernel, sequence parallelism용 GEMM-RS, speculative token budget 조정, shared expert sharding이 들어갔습니다. DeepSeek V4 쪽에서는 sparse MLA가 plain decode, MTP, DSpark speculative decoding에서 end-to-end로 동작한다고 release note가 설명합니다.

이 변화는 최신 모델 발표를 따라잡기 위한 compatibility 작업이기도 하지만, 단순 호환보다 넓습니다. 긴 에이전트 요청에서는 prefill과 decode가 번갈아 병목이 됩니다. MoE 모델에서는 expert parallelism과 communication 비용도 함께 움직입니다. 그래서 runtime은 attention kernel 하나만 빠르게 만드는 데 그치지 않고 scheduling, KV cache, parallelism, hardware별 kernel을 같이 조정해야 합니다.

## speculative decoding은 켜고 끄는 옵션을 넘어섭니다

Speculative decoding은 작은 draft model이나 보조 구조가 여러 token 후보를 먼저 내고, 큰 모델이 이를 검증해 decode를 줄이는 방법입니다. 잘 맞으면 token을 하나씩 기다리는 시간을 줄일 수 있습니다. 반대로 draft가 자주 틀리면 검증 비용과 scheduling 부담이 커집니다. 그래서 성능은 모델, prompt 길이, concurrency, token budget에 크게 묶입니다.

vLLM 0.28.0은 이 영역을 별도 축으로 키웠습니다. release note는 DFlash2, DSpark confidence-scheduled verification, draft model의 async scheduling 자동 활성화, MTP trailing all-reduce fusion, adaptive speculative scheduled input token budget을 engine core 변경으로 적었습니다. DeepSeek V4 항목에서도 sparse MLA가 DSpark speculative decoding까지 이어진다고 설명합니다.

개발자에게 중요한 점은 speculative decoding을 단순한 on/off flag로 보면 안 된다는 것입니다. 에이전트 서비스에서는 첫 token 시간, token 사이 간격, 전체 작업 완료 시간, 재시도, tool call 사이의 공백이 모두 사용자 경험에 들어갑니다. vLLM 0.28.0은 runtime이 이런 변수를 더 세밀하게 다루기 시작한 릴리스입니다. 다만 자기 workload에서 draft acceptance와 tail latency를 다시 재야 합니다.

## KV cache는 GPU 메모리 밖까지 설계 대상이 됩니다

긴 문맥 모델은 attention 계산만큼 KV cache가 부담입니다. 여러 turn과 subagent를 유지하면 cache를 모두 GPU에 두기 어렵습니다. 일부를 CPU나 disk로 내리면 다시 가져오는 비용이 생깁니다. cache 이동이 느리면 모델 자체가 빨라도 요청이 끝날 때까지 걸리는 시간은 줄지 않습니다.

이번 릴리스는 tiered KV cache offloading을 크게 넓혔습니다. release note는 disk offloading, out-of-tree secondary tier manager, partial secondary-tier load result, tiering metric, data-parallel topology 노출, 병렬화 방식에 덜 묶이는 CPU layout을 large-scale serving 변화로 기록했습니다. engine core에도 MLA chunked context의 per-request scheduling, fine-grained prefix matching, KV packing layout refactor가 들어갔습니다.

이런 변화는 장문맥 모델을 쓰는 팀의 운영 판단과 직접 연결됩니다. “최대 context가 몇 token인가”보다 중요한 질문은 실제 session에서 cache hit가 얼마나 나는지입니다. cache miss가 생겼을 때 어느 tier에서 얼마나 늦어지는지도 함께 봐야 합니다. vLLM 0.28.0의 공개 artifact는 이 기능을 시험할 수 있는 출발점을 주지만, 기사 작성 시점에 편집국은 GPU cluster에서 benchmark를 재실행하지 않았습니다.

## 배포 대상은 넓어졌지만 업그레이드 점검이 필요합니다

GitHub release API는 `v0.28.0`이 2026년 8월 26일 공개됐고 9개의 asset을 포함한다고 반환했습니다. 공개 asset에는 source tarball, CPU wheel, CUDA 12.9 wheel, XPU wheel이 있고, release note는 PyPI 기본 CUDA 13.0 설치, ROCm 0.28.0 wheel index, CUDA 13.0·CUDA 12.9·ROCm·CPU·XPU Docker image를 안내합니다.

하드웨어 backend도 넓어졌습니다. NVIDIA 쪽에는 SM12x FlashInfer XQA decode와 SM100 CuTeDSL fused query kernel이 들어갔습니다. AMD ROCm 쪽에는 torch 2.12와 triton 3.7 stack, DeepSeek V4 gfx11, gfx950 sparse-MLA decode 최적화, Kimi-K3 KDA decode kernel이 포함됐습니다. Intel XPU에는 XPU wheel release pipeline과 async scheduling 관련 변경이 들어갔습니다.

하지만 바로 올릴 수 있다는 뜻은 아닙니다. Breaking changes에는 bitsandbytes support의 out-of-tree plugin 이전, `calculate_kv_scales` 제거, `override_attention_dtype` 제거, Transformers 5.15.0 bump가 포함됩니다. 운영 환경에서 bitsandbytes quantization, custom attention dtype, 오래된 KV scale 설정, 특정 Transformers 버전에 묶인 모델 wrapper를 쓴다면 staging에서 먼저 확인해야 합니다.

## API도 agent 운영 흐름을 더 많이 받습니다

vLLM은 모델 서버이지만, agent 서비스에서는 frontend 동작도 성능과 안정성에 영향을 줍니다. 이번 릴리스에는 HTTP header에서 request priority를 읽는 기능, session ID plumbing, streaming parser의 `count_reasoning_tokens`, gRPC multimodal image inference, data-parallel rank routing, Rust frontend의 protobuf schema 공개가 들어갔습니다.

이 변화는 운영자가 요청을 더 세밀하게 나눌 수 있다는 뜻입니다. 짧은 대화, 긴 agent 실행, multimodal 요청, retry 요청을 같은 queue에 넣으면 tail latency가 나빠질 수 있습니다. priority와 session 식별자가 runtime 안으로 들어오면 scheduler, observability, quota 정책을 모델 호출 하나보다 넓은 작업 단위에 붙일 수 있습니다.

보안과 robustness 항목도 제품 운영에 중요합니다. release note는 audio decode duration guard를 우회하는 sample-rate forgery DoS를 고쳤고, DeepStream pixel limit, `resolve_trust_remote_code` guard, `--api-key`가 모든 endpoint를 막지 않는다는 문서 경고를 적었습니다. 공개 API 서버로 vLLM을 노출하는 팀은 모델 성능만큼 endpoint 경계와 입력 제한을 확인해야 합니다.

## 채택 기준은 모델 지원 여부보다 넓어졌습니다

vLLM 0.28.0을 채택할지는 “최신 모델을 지원하니 올린다”로 정하면 위험합니다. Kimi-K3나 DeepSeek V4를 운영한다면 decode kernel, sparse MLA, DSpark, ROCm enablement가 직접 이득을 줄 수 있습니다. 반대로 더 단순한 dense model을 안정적으로 돌리는 환경이라면 breaking changes와 dependency bump가 더 큰 비용일 수 있습니다.

이번 기사에서 확인한 것은 공개 release note, tag, asset, commit으로 추적되는 runtime 변화입니다. 재현성은 R2입니다. 소스와 wheel, Docker image 경로가 공개되어 설치와 재실행을 시도할 수 있습니다. 다만 편집국은 GPU·ROCm·XPU 환경에서 성능 benchmark를 돌리지 않았습니다. release note의 1.5~3배 kernel-level speedup, 약 60% TTFT 개선, 약 17GiB memory saving 같은 수치는 프로젝트가 적은 조건부 결과로 다룹니다.

실무적으로는 작은 canary가 먼저입니다. 업그레이드 전후로 같은 모델, 같은 tokenizer revision, 같은 quantization, 같은 context 길이, 같은 concurrency에서 TTFT, time between tokens, end-to-end latency, GPU memory, cache hit, request failure를 기록해야 합니다. 특히 speculative decoding과 KV offload를 켠 경우에는 평균보다 p95·p99와 실패 시 복구 시간을 봐야 합니다.

## 이해상충과 취재 조건

vLLM 프로젝트는 이번 릴리스와 release note의 작성·배포 주체입니다. GitHub와 PyPI/Docker 배포 경로는 공개 artifact를 제공합니다. 성능 개선 표현은 vLLM release note와 연결 PR의 설명으로 다루고, 독립 benchmark 결과로 승격하지 않았습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 2차 요약은 후보 발견과 중복 확인에만 사용했고, 기사 사실은 열린 GitHub release, GitHub API, source repository, release artifact metadata로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. vLLM 프로젝트는 2026년 8월 26일 `v0.28.0`을 공개했고, release note는 584개 commit과 270명 contributor를 포함한다고 적었습니다. | E2 · P1/P2 | GitHub release page와 GitHub release API로 확인했습니다. contributor 집계는 프로젝트가 산정한 값입니다. |
| C2. vLLM 0.28.0은 Kimi-K3에 Decode Context Parallel, FlashKDA fused decode·prefill kernel, GEMM-RS, adaptive speculative token budget, shared expert sharding을 추가하거나 개선했습니다. | E2 · P1/P2 | release note와 연결 PR 번호로 확인했습니다. 편집국은 Kimi-K3 workload를 실행하지 않았습니다. |
| C3. DeepSeek V4 쪽에서는 sparse MLA가 plain decode, MTP, DSpark speculative decoding에서 end-to-end로 동작한다고 release note가 설명합니다. | E2 · P1/P2 | release note의 DeepSeek V4 항목으로 확인했습니다. 특정 GPU, model revision, quantization별 성능은 재현하지 않았습니다. |
| C4. Engine core에는 DSpark confidence-scheduled verification, DFlash2, draft model async scheduling, adaptive speculative scheduled input token budget, MLA chunked context scheduling, prefix reuse와 KV packing 변경이 포함됐습니다. | E2 · P1/P2 | release note의 Engine Core 항목으로 확인했습니다. 각 PR의 microbenchmark 수치는 독립 benchmark로 쓰지 않았습니다. |
| C5. Large-scale serving에는 E/P/D disaggregation, disk KV offloading, secondary tier manager, tiering metric, data-parallel topology 노출과 connector 변경이 포함됐습니다. | E2 · P1/P2 | release note의 Large Scale Serving 항목으로 확인했습니다. production cluster에서 안정성 검증을 하지 않았습니다. |
| C6. release artifact는 source tarball과 CPU, CUDA 12.9, XPU wheel을 포함하고, release note는 CUDA 13.0, CUDA 12.9, ROCm, CPU, XPU Docker image와 ROCm wheel index를 안내합니다. | E2 · P2 | GitHub release API의 9개 asset metadata와 release note의 artifact 표로 확인했습니다. Docker image pull과 wheel 설치는 실행하지 않았습니다. |
| C7. Breaking changes에는 bitsandbytes support의 out-of-tree plugin 이전, `calculate_kv_scales` 제거, `override_attention_dtype` 제거, Transformers 5.15.0 bump가 포함됩니다. | E2 · P1 | release note의 Breaking Changes와 Dependencies 항목으로 확인했습니다. 개별 사용자 환경의 호환성은 직접 검증하지 않았습니다. |
| C8. Security 항목에는 audio decode duration guard 우회 DoS 수정, DeepStream pixel limit, `_load_ov2_processor`의 `resolve_trust_remote_code` guard, `--api-key` 경고 문서화가 포함됐습니다. | E2 · P1/P2 | release note의 Security 항목으로 확인했습니다. 취약점 재현이나 exploit 검증은 하지 않았습니다. |

## 출처

1. vLLM Project, `v0.28.0` release note: https://github.com/vllm-project/vllm/releases/tag/v0.28.0
2. GitHub API, `vllm-project/vllm` release `v0.28.0`: https://api.github.com/repos/vllm-project/vllm/releases/tags/v0.28.0
3. GitHub API, `vllm-project/vllm` commit `2cf0a6915ce544dc493a0990f2ea38d81601128a`: https://api.github.com/repos/vllm-project/vllm/commits/2cf0a6915ce544dc493a0990f2ea38d81601128a
4. vLLM source repository: https://github.com/vllm-project/vllm
