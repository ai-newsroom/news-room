---
edition: ai
decision: publish-candidate
title: "TensorRT-LLM 1.3.0rc23의 전환선: TensorRT engine을 빼고 PyTorch만 남겼습니다"
date: 2026-08-03
subject: "NVIDIA TensorRT-LLM v1.3.0rc23 legacy TensorRT backend removal"
summary: "TensorRT-LLM v1.3.0rc23은 legacy TensorRT engine backend와 build·conversion 경로를 제거하고 PyTorch를 유일한 실행 backend로 정리했습니다. 공개 tag·merge commit·migration 문서·PyPI stub으로 변화는 확인되지만, RC release note가 여러 model·GPU 조합의 hang·crash·OOM을 함께 밝히므로 기존 production은 새 배포 경로를 별도 canary로 검증해야 합니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["NVIDIA와 TensorRT-LLM 기여자는 자체 release·문서·code·package를 설명하는 주체입니다. 이 기사에는 사전 접근, 제공받은 hardware·account·credit, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

TensorRT-LLM `v1.3.0rc23` 공개가 SW 엔지니어에게 중요한 이유는 TensorRT engine을 build한 뒤 실행하던 배포 계약을 끝냈기 때문입니다. 7월 31일 공개된 공식 migration 문서는 `LLM(backend="tensorrt")`, `trtllm-build`, model별 `convert_checkpoint.py`와 `tensorrt` pip dependency를 제거하고, Hugging Face checkpoint를 직접 읽는 PyTorch backend만 남겼습니다.

이 변화는 이름이나 내부 refactor에 그치지 않습니다. 기존 자동화가 engine artifact 생성, checkpoint conversion, TensorRT SDK가 들어간 image와 `backend="tensorrt"` 설정을 전제로 했다면 upgrade 절차 자체를 다시 설계해야 합니다. 다만 이번 판은 stable release가 아니라 release candidate이며, 공식 release note가 특정 GB300·A100·model·quantization 조합의 hang, crash와 OOM을 알려진 문제로 공개합니다. 편집국은 공개 source와 package metadata를 검사했지만 NVIDIA GPU에서 inference를 실행하지 않았습니다.

## 세 줄 요약

- `v1.3.0rc23`에서 PyTorch는 TensorRT-LLM의 유일한 실행 backend이며, legacy TensorRT engine build·refit·prune와 checkpoint conversion 경로가 제거됐습니다.
- PyPI의 공개 `1.3.0rc23` sdist는 SHA-256 `07b5714cc51ff7f841cdf2f9fc2f71b68391e1480b1cf4d11ad7fbcac63f0b91`인 215,516바이트 `wheel-stub`이므로, 이 파일만 검사했다고 실제 NVIDIA wheel이나 container runtime을 검증한 것은 아닙니다.
- 공식 RC note는 DeepSeek·Qwen·Gemma 경로의 hang·crash·OOM을 함께 명시하므로, production upgrade는 engine build 제거와 runtime 안정성 검증을 분리한 canary가 필요합니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** tag `d41ab33df16740e18e8ef9c8735dad4efc46afd5`, 네 migration merge commit의 tag 포함 관계, exact-tag 문서, 삭제된 source 목록과 PyPI sdist metadata를 공개 artifact에서 확인할 수 있습니다.
- **도입 전에 확인할 것:** `trtllm-build`·`convert_checkpoint.py`·serialized engine에 의존하는 CI/CD를 찾고, Hugging Face checkpoint 직접 loading, pinned PyTorch·CUDA dependency, NGC image 또는 NVIDIA package index와 rollback artifact를 새로 검증해야 합니다.
- **아직 결론 내릴 수 없는 것:** 기존 TensorRT engine과 새 PyTorch 경로의 latency·throughput·memory·정확성 차이, 특정 GPU와 model의 안정성, NVIDIA index에서 받은 wheel의 내용과 production traffic의 호환성은 이번 source inspection으로 판단할 수 없습니다.

## 이 공개의 의의와 편집 판단

공식 migration guide는 첫 문단에서 TensorRT engine backend가 제거됐고 PyTorch가 유일한 실행 backend라고 규정합니다. `LLM(backend="tensorrt")`는 이제 `ValueError`를 내며, `TrtLlmArgs`는 기본값인 `TorchLlmArgs`로 바꿔야 합니다. CLI에서는 `--backend tensorrt`를 제거하고 `trtllm-serve <hf_model>`처럼 checkpoint를 직접 지정합니다.

release에 포함된 PR #16369는 581개 파일에서 78,984줄을 삭제했고, `FindTensorRT.cmake`, `rawEngine.h`, `trtGptModel` 계열 source와 C++ benchmark를 포함한 legacy engine code를 제거했습니다. 뒤이은 PR #16610은 test·example·CI plumbing 24,298줄을 더 삭제했습니다. PR #16608은 build option `--trt_root`와 image의 TensorRT SDK 설치 경로를 없앴고, PR #16612는 legacy Python 경로와 문서를 정리했습니다. 네 merge commit은 모두 `v1.3.0rc23` tag의 조상으로 확인했습니다.

**편집 판단:** 이 release의 핵심은 “TensorRT-LLM이 더 빨라졌다”가 아닙니다. 배포 artifact의 단위가 미리 만든 TensorRT engine에서 PyTorch가 직접 읽는 model checkpoint와 runtime configuration으로 바뀌었다는 점이 중요합니다. 팀은 기존 engine cache를 새 release에서 재사용하는 방법을 찾기보다, build stage를 제거하고 checkpoint identity·dependency lock·runtime canary를 새 경계로 삼는 편이 타당합니다.

## 이름은 남았지만 실행 계약은 바뀌었습니다

이름에 TensorRT가 남아 있다는 사실과 TensorRT engine backend가 제거됐다는 사실은 모순이 아닙니다. project에는 CUDA kernel, C++ executor, KV cache와 여러 NVIDIA 최적화가 계속 남아 있습니다. 제거된 것은 serialized TensorRT engine을 build하고 해당 backend로 실행하는 legacy 경로입니다. 따라서 “TensorRT-LLM이 pure Python library가 됐다”거나 “C++ code가 모두 사라졌다”고 해석하면 안 됩니다.

migration table이 제시하는 대응은 좁고 명확합니다. Python API에서는 `backend` 인자를 빼고 `LLM(model="<hf_model>")`을 사용합니다. command line에서는 별도 engine을 넘기지 않고 `trtllm-serve <hf_model>`을 실행합니다. `trtllm-build`, `trtllm-refit`, `trtllm-prune`과 model별 conversion directory는 replacement command 없이 제거됐습니다. 이 경로를 감싼 shell script나 Kubernetes init container가 있다면 단순 option rename으로는 migration이 끝나지 않습니다.

engine build 단계가 사라지면 artifact provenance도 달라집니다. 이전에는 source checkpoint, conversion option, builder version, GPU target과 생성된 engine hash를 함께 고정했을 수 있습니다. 새 경로에서는 source checkpoint revision, tokenizer와 config revision, TensorRT-LLM package·container identity, PyTorch·CUDA stack과 serve option을 배포 manifest에 묶어야 합니다. checkpoint가 moving branch를 가리키면 같은 application release라도 다음 pod가 다른 weight나 config를 받을 수 있으므로 immutable revision을 사용해야 합니다.

rollback도 engine file 복원만으로 충분하지 않습니다. 이전 release의 container와 engine artifact를 함께 보존하고, 새 PyTorch 경로에서는 checkpoint cache·compiled kernel cache·runtime configuration을 별도 namespace로 두는 편이 안전합니다. 두 경로가 같은 cache directory를 공유하면 실패 원인을 package, model artifact와 generated cache 가운데 어디에서 찾아야 하는지 모호해질 수 있습니다.

## 공개 PyPI 파일은 실제 runtime wheel이 아니라 stub입니다

PyPI JSON에서 `tensorrt_llm` `1.3.0rc23`에 공개된 파일은 `tensorrt_llm-1.3.0rc23.tar.gz` 하나였습니다. 편집국이 내려받은 파일은 215,516바이트였고 registry의 SHA-256과 일치했습니다. 압축 안에는 `LICENSE`, `PKG-INFO`, `pyproject.toml`과 attribution 문서만 있으며 project source tree나 compiled library는 들어 있지 않았습니다.

`pyproject.toml`은 build backend로 `wheel_stub.buildapi`를 사용하고 `https://pypi.nvidia.com/`을 index로 지정합니다. 따라서 공개 PyPI sdist의 hash와 metadata를 검증한 일은 실제 설치 과정이 가져올 NVIDIA-hosted wheel의 byte identity를 검증한 일이 아닙니다. air-gapped build나 dependency allowlist를 운영하는 팀은 이 간접 download를 명시적으로 모델링해야 합니다.

`PKG-INFO`에는 Python `>=3.10,<4`, `torch==2.11.0`, `cuda-python>=13`, `transformers==5.5.4`, `triton==3.6.0`을 비롯한 pinned·bounded dependency가 기록돼 있습니다. exact-tag installation guide도 PyPI wheel이 public PyTorch build를 기준으로 만들어져 NGC PyTorch container와 맞지 않을 수 있다고 경고하고, NGC 전용 local-version wheel이나 release container 안의 wheel을 별도 경로로 안내합니다.

이 차이는 dependency resolver에 맡겨도 되는 사소한 세부가 아닙니다. 기존 image에 `pip install tensorrt_llm`만 추가하면 PyTorch나 CUDA stack이 교체될 수 있고, public PyPI, NVIDIA index와 NGC container 가운데 어느 artifact를 설치했는지 build log만으로 불분명해질 수 있습니다. release canary에서는 최종 wheel filename·hash, resolver report, installed package list와 base image digest를 함께 보존해야 합니다.

## 알려진 문제는 model과 hardware 조합별로 읽어야 합니다

공식 release note는 `v1.3.0rc23`의 known issues로 여러 구체적 조합을 열거합니다. DeepSeek-V4-Pro는 GB300 disaggregated setup에서 멈출 수 있고, DeepSeek-R1 NVFP4의 PP4+MTP multi-GPU 실행은 GB300에서 MPI worker exit와 함께 crash할 수 있다고 적습니다. DeepSeek-V3-Lite BF16의 Python scheduler·chunked prefill도 완료되지 않을 수 있습니다.

Qwen MoE multi-LoRA는 routed expert, 서로 다른 rank와 eager 조건에서 sampling failure가 보고됐습니다. Gemma3-1B FP8 prequantized model은 `torch.compile`과 CUDA graph capture 조합에서 PyTorch CUDA allocator assert가 날 수 있습니다. Qwen3.5-35B-A3B BF16은 A100, CUTLASS, TP1 조건에서 CUDA OOM을 만날 수 있다고 적혀 있습니다.

이 목록은 project가 공개한 P1 문서이며 편집국의 재현 결과가 아닙니다. 반대로 목록에 없는 GPU·model 조합이 안전하다는 보증도 아닙니다. production 판단에는 자신이 쓰는 model revision, quantization, tensor·pipeline parallelism, attention backend, scheduler, disaggregated serving 여부와 GPU SKU를 key로 한 test matrix가 필요합니다.

RC에서 backend migration과 model support upgrade를 한 번에 수행하면 실패 원인이 섞입니다. 먼저 기존 production model 하나를 고정하고 request·output fixture를 새 PyTorch 경로에서 비교합니다. 그다음 새 model이나 quantization을 별도 change로 올리는 편이 rollback과 성능 회귀 분석에 유리합니다. known issue와 같은 조합을 쓴다면 stable release를 기다리거나, maintainer가 제시한 fix commit과 공식 후속 RC를 다시 확인해야 합니다.

## canary는 build 성공보다 output 계약을 먼저 봐야 합니다

첫 단계에서는 repository와 deployment manifest에서 legacy 경로를 정적으로 찾습니다. `backend="tensorrt"`, `TrtLlmArgs`, `trtllm-build`, `trtllm-refit`, `trtllm-prune`, `convert_checkpoint.py`, `--trt_root`와 serialized engine 확장자를 검색합니다. 발견된 각 항목을 삭제 대상, 새 checkpoint direct-load 경로, rollback 의존성으로 분류합니다.

두 번째 단계에서는 작은 고정 model과 synthetic prompt set으로 process startup, model load, 첫 token, streaming 종료, structured output, tool call, cancellation과 shutdown을 확인합니다. response text만 비교하지 말고 token ID, finish reason, usage accounting, error code와 metric label도 저장합니다. backend가 바뀌면 같은 model이라도 kernel과 sampling path가 달라질 수 있으므로 bitwise identical output을 당연한 전제로 두지 않습니다.

세 번째 단계에서는 production과 같은 GPU·parallelism·quantization 조합으로 soak test를 실행합니다. GPU memory의 startup peak와 steady state, request queue, KV cache 사용량, MPI worker 생존, timeout 뒤 회복과 rolling restart를 관찰합니다. release note의 known issue 조건과 겹치는 경우에는 해당 failure가 발생하지 않았다는 negative evidence를 로그와 함께 남깁니다.

마지막으로 supply chain을 확인합니다. public PyPI sdist hash만 allowlist에 넣지 말고 실제로 설치된 wheel 또는 NGC image digest를 고정합니다. build가 외부 NVIDIA index에 접근한다면 redirect와 index URL, 최종 artifact hash를 기록하고 credential이 log에 남지 않게 합니다. rollback test는 이전 container·engine 조합이 새 checkpoint cache와 무관하게 다시 뜨는지까지 확인해야 합니다.

## 공개 artifact로 확인할 수 있는 최소 절차

아래 절차는 GPU inference를 실행하지 않고 public PyPI의 stub identity와 exact source tag를 확인하는 범위입니다. 편집국은 같은 URL에서 sdist를 내려받아 hash와 archive 목록을 대조했습니다.

```bash
python3 -m pip download --no-deps --no-binary=:all: tensorrt_llm==1.3.0rc23
shasum -a 256 tensorrt_llm-1.3.0rc23.tar.gz
tar -tzf tensorrt_llm-1.3.0rc23.tar.gz
tar -xOzf tensorrt_llm-1.3.0rc23.tar.gz \
  tensorrt_llm-1.3.0rc23/pyproject.toml
```

기대하는 SHA-256은 `07b5714cc51ff7f841cdf2f9fc2f71b68391e1480b1cf4d11ad7fbcac63f0b91`입니다. archive에는 runtime source 대신 `wheel-stub` 설정이 있으므로, 이 단계에서 검증을 멈추면 설치될 wheel의 내용과 동작은 미확인 상태입니다. 실제 rollout에서는 resolver가 선택한 최종 artifact를 별도로 hash해야 합니다.

source migration은 `v1.3.0rc23` tag `d41ab33df16740e18e8ef9c8735dad4efc46afd5`의 migration guide와 PR file list에서 확인할 수 있습니다. branch의 최신 문서는 후속 수정이 섞일 수 있으므로 tag URL을 사용해야 합니다. 이 절차는 removal과 package indirection을 확인할 뿐, 성능과 runtime 호환성을 재현하지 않습니다.

## 적용 범위와 확인하지 못한 것

이번 검증은 GitHub release note, exact tag, 네 merge commit과 file list, exact-tag migration·installation 문서, PyPI JSON과 공개 sdist에 한정합니다. PR의 code deletion과 문서의 새 API 계약은 확인했지만 repository test suite, NVIDIA wheel, NGC container와 GPU server는 실행하지 않았습니다.

PyTorch가 유일한 execution backend라는 결론은 project의 `v1.3.0rc23` migration contract에 관한 것입니다. CUDA kernel, C++ executor, TensorRT-LLM 전용 optimization이나 Triton Inference Server integration까지 제거됐다는 뜻이 아닙니다. AutoDeploy도 PyTorch backend 위에서 남아 있다고 문서가 명시합니다.

known issue는 maintainer가 보고한 조건을 그대로 좁혀 적었습니다. 해당 문제가 모든 deployment에서 발생한다고 단정하지 않으며, 목록 밖 조합의 안정성을 추정하지 않습니다. latency, throughput, memory, 정확성, cost와 기존 TensorRT engine 대비 성능 차이는 측정하지 않았습니다.

PyPI sdist는 public registry에서 직접 검사했지만 실제 wheel fetch를 허용하거나 설치하지 않았습니다. NVIDIA index의 wheel 목록·hash, NGC image digest와 한국 지역에서의 download·지원 조건도 확인하지 않았습니다. 따라서 이 기사는 `v1.3.0rc23`을 production-ready라고 판정하지 않습니다.

## 이해상충과 취재 조건

NVIDIA와 TensorRT-LLM maintainer는 자신의 release, migration 방향, known issue, package와 test를 설명하는 주체입니다. 이 자료는 version·code·공식 지원 계약의 1차 근거이지만, 안정성과 성능의 독립 검증은 아닙니다. GitHub와 PyPI는 공개 artifact의 identity를 확인하는 hosting·registry로 사용했습니다.

이 기사에는 NVIDIA, cloud provider, model vendor 또는 hardware 판매자의 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 URL과 credential이 필요 없는 package만 조사했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. TensorRT-LLM `v1.3.0rc23`은 tag `d41ab33df16740e18e8ef9c8735dad4efc46afd5`로 공개됐고, legacy TensorRT backend 제거 관련 네 merge commit이 tag의 조상입니다. | E2 · P1/P2 · R2 | Release, tag ref, PR과 compare 결과를 확인했습니다. 실제 GPU runtime은 실행하지 않았습니다. |
| C2. TensorRT engine backend, build·refit·prune command, model별 conversion과 `tensorrt` pip dependency가 제거되고 PyTorch가 유일한 execution backend가 됐습니다. | E2 · P1/P2 · R2 | Exact-tag migration guide와 삭제된 source·build file을 대조했습니다. 모든 downstream wrapper를 조사하지 않았습니다. |
| C3. 공개 PyPI sdist는 215,516바이트 `wheel-stub`이며 SHA-256은 `07b5714c…f0b91`입니다. | E2 · P2 · R2 | PyPI JSON과 내려받은 archive의 hash·내용을 확인했습니다. NVIDIA index의 실제 wheel은 받거나 실행하지 않았습니다. |
| C4. RC note는 특정 DeepSeek·Qwen·Gemma와 GPU·scheduler·quantization 조합의 hang·crash·OOM을 known issue로 기록합니다. | E1 · P1 · R1 | 발표 사실과 조건은 확인했지만 편집국이 failure를 재현하지 않았고 목록 밖 안정성은 판단하지 않았습니다. |

## 출처

1. TensorRT-LLM v1.3.0rc23 release note: https://github.com/NVIDIA/TensorRT-LLM/releases/tag/v1.3.0rc23
2. v1.3.0rc23 tag commit `d41ab33df16740e18e8ef9c8735dad4efc46afd5`: https://github.com/NVIDIA/TensorRT-LLM/commit/d41ab33df16740e18e8ef9c8735dad4efc46afd5
3. Exact-tag TensorRT backend removal migration guide: https://github.com/NVIDIA/TensorRT-LLM/blob/d41ab33df16740e18e8ef9c8735dad4efc46afd5/docs/source/legacy/tensorrt-backend-removal.md
4. Legacy TensorRT backend removal PR #16369: https://github.com/NVIDIA/TensorRT-LLM/pull/16369
5. TensorRT SDK image installation removal PR #16608: https://github.com/NVIDIA/TensorRT-LLM/pull/16608
6. Legacy backend test·example·CI removal PR #16610: https://github.com/NVIDIA/TensorRT-LLM/pull/16610
7. Legacy Python·documentation cleanup PR #16612: https://github.com/NVIDIA/TensorRT-LLM/pull/16612
8. Exact-tag installation guide: https://github.com/NVIDIA/TensorRT-LLM/blob/d41ab33df16740e18e8ef9c8735dad4efc46afd5/docs/source/installation/installation-guide.md
9. TensorRT-LLM 1.3.0rc23 PyPI files and hashes: https://pypi.org/project/tensorrt-llm/1.3.0rc23/
