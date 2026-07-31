---
edition: ai
decision: publish-candidate
title: "vLLM 0.26.0 보안 경계: prompt fan-out 상한과 pickle cache 제거"
date: 2026-08-01
subject: "vLLM 0.26.0 security and resource-boundary changes"
summary: "vLLM 0.26.0은 `/v1/completions`의 prompt fan-out에 기본 상한을 두고, structured-output regex timeout을 한 backend까지 넓히며, Outlines disk cache의 pickle 역직렬화 경로를 제거했습니다. 공개 코드로 구현은 확인되지만 실제 배포의 인증·proxy·model 조건과 성능 영향은 별도 canary가 필요합니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["vLLM 프로젝트와 기여자는 자체 릴리스·코드·test를 설명하는 주체입니다. 이 기사에는 사전 접근, 제공받은 hardware·account·credit, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

vLLM 0.26.0 공개가 SW 엔지니어에게 중요한 이유는 모델 지원과 성능 개선 외에도 inference server가 한 요청을 얼마나 많은 내부 작업으로 확장하는지, 복잡한 regex를 얼마나 오래 compile하는지, 오류 응답에 서버 경로를 노출하는지를 코드에서 제한했기 때문입니다. 공개 API를 multi-tenant 환경에 두는 팀이라면 단순한 version update보다 request validation, structured output, cache directory와 gateway limit가 맞물리는 방식을 확인할 가치가 있습니다. 다만 이번 검증은 고정 tag와 공식 PyPI source artifact의 코드·test를 확인한 것이며, GPU server에서 공격 입력이나 production traffic을 재현한 결과는 아닙니다.

## 세 줄 요약

- `/v1/completions`의 `prompt` 또는 `prompt_embeds`가 여러 prompt를 담는 list이면 기본 최대 1,024개까지만 허용하며, Pydantic validation에서 초과 요청을 거절합니다.
- structured-output의 `lm-format-enforcer` regex parser도 기본 5초 compile timeout을 사용하고, derender payload 크기와 validation error의 파일 경로 노출에도 별도 방어선을 추가했습니다.
- Outlines disk cache는 `diskcache`의 pickle 역직렬화 대신 SQLite와 `outlines_core.Index`의 native binary serialization을 사용하지만, 이것이 vLLM 전체에서 pickle을 제거했다는 뜻은 아닙니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** v0.26.0 tag `568afb3a13806beb53bb2e6bd518269357b237c0`, 공식 release note, 여섯 security 관련 merge commit의 tag 포함 관계, PyPI sdist hash와 source·regression test를 공개 artifact에서 확인할 수 있습니다.
- **도입 전에 확인할 것:** API gateway의 body·batch limit, `VLLM_MAX_COMPLETION_PROMPTS`, `VLLM_MAX_N_SEQUENCES`, `max_model_len`, `max_logprobs`, `VLLM_REGEX_COMPILATION_TIMEOUT_S`, Outlines cache directory의 소유권과 기존 cache 정리 정책을 함께 점검해야 합니다.
- **아직 결론 내릴 수 없는 것:** 실제 workload에서의 latency·throughput·GPU memory 변화, 모든 backend와 plugin의 보안성, 기존 client가 새 validation error를 처리하는지, 공개하지 않은 deployment의 exploitability는 이번 source inspection으로 판단할 수 없습니다.

## 이 공개의 의의와 편집 판단

vLLM은 7월 27일 v0.26.0 release note에서 411개 commit 가운데 security 항목을 따로 제시했습니다. 그 목록에는 diskcache 교체, completion prompt list 상한, derender resource bound, validation error의 server path 제거, regex compile timeout 확대와 sparse invariant race 수정이 포함됩니다. 각 merge commit은 v0.26.0 tag의 조상이며, 7월 25일 PyPI에 올라온 sdist의 SHA-256 `23e9fa19d7e20ce7dcc1c074d41503e2116d23f19e688f5d5ea91b741f958502`에서도 해당 source를 확인했습니다.

**편집 판단:** 이번 release의 핵심은 특정 benchmark가 빨라졌다는 데 있지 않습니다. OpenAI-compatible endpoint 하나가 내부 engine request 여러 개로 증폭되는 경로, caller가 보낸 구조가 tokenizer·parser의 CPU·memory 작업으로 이어지는 경로, structured-output artifact가 disk에서 다시 object로 복원되는 경로에 각각 상한이나 더 안전한 representation을 둔 점이 중요합니다. 운영팀은 v0.26.0을 “보안 완료” 표식으로 사용하지 말고, application과 gateway가 같은 resource budget을 공유하도록 만드는 기준점으로 사용하는 편이 타당합니다.

## 하나의 HTTP 요청이 engine request 1,024개까지 확장될 수 있습니다

v0.26.0의 `CompletionRequest`는 `prompt`가 여러 text prompt 또는 여러 token-id list를 담을 때 개수를 검사합니다. `prompt_embeds` list도 같은 검사를 받습니다. 기본값은 `VLLM_MAX_COMPLETION_PROMPTS=1024`이며, 한도를 넘으면 renderer preprocessing, engine generator allocation과 response buffering 전에 validation error를 만듭니다.

이 상한은 token 수 제한과 다른 축입니다. `prompt=[1, 2, 3]`처럼 정수 list 하나는 tokenized single prompt이므로 prompt 개수 상한의 대상이 아닙니다. 반면 `prompt=["a", "b"]`나 `prompt=[[1], [2]]`는 두 engine request로 확장될 수 있는 batch입니다. 각 prompt의 token 길이는 `max_model_len` 같은 기존 제한으로 별도 관리해야 합니다.

기본 1,024는 안전한 production 값이라는 보증이 아닙니다. 한 HTTP request가 최대 1,024개 backend 작업으로 확장될 수 있다는 뜻이므로, 작은 GPU pool이나 공용 queue에서는 더 낮은 application limit가 필요할 수 있습니다. 반대로 기존 batch client가 1,024개를 넘겨 보냈다면 upgrade 뒤 4xx validation failure를 받으므로, client-side chunking과 idempotency를 먼저 준비해야 합니다.

API gateway의 request body 크기만 제한해서는 이 경로를 완전히 통제하지 못합니다. 짧은 prompt를 많이 넣으면 body는 작아도 scheduler fan-out은 커질 수 있습니다. gateway에서는 인증 주체별 request rate와 body size를 제한하고, application에서는 prompt count와 예상 token budget을 제한하며, vLLM에서는 환경 변수 상한을 마지막 방어선으로 두는 세 층이 필요합니다.

## derender endpoint는 caller가 보낸 출력 구조도 먼저 제한합니다

`/v1/completions/derender`와 `/v1/chat/completions/derender`는 caller가 보낸 `GenerateResponse` 구조를 text로 되돌리는 경로입니다. v0.26.0은 tokenizer decode나 parser 호출 전에 `_validate_derender_bounds()`를 실행합니다. `generate_responses`와 `choices` 수는 `VLLM_MAX_N_SEQUENCES`, `token_ids`와 `prompt_logprobs` 길이는 `max_model_len`, 각 logprob entry의 후보 수는 model configuration의 `max_logprobs`와 비교합니다.

이 변경은 일반 generation request의 token limit가 derender 입력에도 자동으로 적용된다고 가정하면 안 된다는 점을 보여 줍니다. derender는 이미 생성된 것처럼 보이는 구조를 caller가 직접 공급하므로, 정상 generation path를 거치지 않는 별도 resource boundary입니다. 해당 endpoint를 외부에 노출하지 않는 배포도 있지만, route가 활성화되어 있다면 reverse proxy allowlist와 vLLM 내부 validation을 모두 확인해야 합니다.

공개 test는 상한을 넘는 choices, token IDs, response batch와 logprobs를 거절하는 case를 포함합니다. 편집국은 이 test code와 호출 순서를 확인했지만 실제 server process에 oversized payload를 보내지는 않았습니다. 따라서 특정 hardware에서 CPU·memory 고갈을 막는 정도나 error latency를 측정한 결과로 확대하지 않습니다.

## regex timeout은 세 번째 backend로 넓어졌지만 끌 수도 있습니다

GitHub Advisory `GHSA-rwxx-mrjm-wc2m`은 `structured_outputs.regex`에 복잡한 pattern을 넣어 grammar compilation을 오래 붙잡는 ReDoS 문제를 설명합니다. Advisory는 xgrammar와 outlines 경로가 v0.24.0에서 수정됐다고 기록합니다. v0.26.0의 추가 변경은 그 결론을 새 CVE처럼 반복한 것이 아니라, timeout을 거치지 않던 `lm-format-enforcer`의 `RegexParser`도 공통 `compile_regex_with_timeout` helper로 보내는 조치입니다.

기본 timeout은 `VLLM_REGEX_COMPILATION_TIMEOUT_S=5`입니다. helper는 별도 thread에서 parser를 호출하고 시간이 지나면 `ValueError`를 반환합니다. 값이 `0` 이하이면 timeout을 사용하지 않으므로, production에서 이를 0으로 설정하면 이번 방어선을 운영자가 직접 해제하는 셈입니다.

timeout은 regex의 의미가 안전하거나 모든 계산량 공격이 제거됐음을 증명하지 않습니다. 이미 시작된 native code가 즉시 중단되는지, worker thread가 언제 자원을 돌려주는지, 다른 schema·grammar backend가 같은 budget을 지키는지는 별도 확인이 필요합니다. application이 사용자 regex를 받는다면 허용 기능 축소, pattern 길이 제한, compile timeout과 전체 request deadline을 함께 적용해야 합니다.

## Outlines cache에서는 pickle 경로가 사라졌습니다

기존 optional Outlines disk cache는 Python object cache library인 `diskcache`를 사용했고, PR은 이 library가 pickle로 object를 역직렬화하는 경로를 보안 scanner가 문제로 표시했다고 설명합니다. v0.26.0 source는 `diskcache` dependency를 requirements에서 제거하고 `OutlinesDiskCache`를 SQLite로 구현합니다. `outlines_core.Index`는 `to_binary()`로 저장하고 `Index.from_binary()`로 복원하며, string은 UTF-8 bytes로 구분해 저장합니다.

여기서 범위를 좁혀 읽어야 합니다. 해당 PR은 vLLM의 cache가 기본 비활성이며 `VLLM_V1_USE_OUTLINES_CACHE`로 켜고 untrusted user와 cache directory를 공유하지 말라고 이미 문서화했기 때문에, vLLM이 실사용에서 `CVE-2025-69872`에 취약하다고 주장하지 않습니다. 변경 목적은 optional cache에서 그 dependency와 pickle attack surface를 제거하는 것입니다.

또한 vLLM 전체에서 pickle이 사라진 것은 아닙니다. v0.26.0의 common requirements에는 lambda serialization 용도의 `cloudpickle`이 남아 있습니다. 따라서 scanner finding을 닫을 때는 “모든 pickle 제거”가 아니라 “Outlines disk cache의 diskcache dependency와 그 역직렬화 경로 제거”로 기록해야 합니다.

기존 cache directory를 그대로 재사용하는 upgrade도 canary에서 확인해야 합니다. 새 구현은 `outlines_cache.db`라는 SQLite database를 만들며 native binary와 string type tag를 사용합니다. 이전 cache artifact의 migration·삭제 정책을 source만으로 단정하지 말고, cache를 비운 상태와 기존 directory를 둔 상태에서 startup, first request와 cache hit를 각각 관찰해야 합니다.

## validation error는 서버의 절대 경로를 숨깁니다

FastAPI의 validation exception 문자열에는 endpoint의 절대 설치 경로, line과 function name이 들어갈 수 있습니다. v0.26.0은 client error message를 `str(exc)`에서 만들지 않고 `exc.errors()`의 구조화된 항목으로 조립합니다. 이후 `sanitize_message`가 traceback frame과 `/home`, `/usr`, `/opt`, `/var`, `/tmp` 같은 절대 경로 pattern을 제거합니다.

이 조치는 validation error를 통해 container image layout이나 package 설치 위치가 노출되는 범위를 줄입니다. 하지만 모든 exception과 plugin message가 이 handler를 통과한다고 확인한 것은 아닙니다. custom endpoint, middleware와 observability exporter가 원 exception을 응답이나 log에 다시 넣는지 별도로 시험해야 합니다.

운영 관점에서는 외부 response와 내부 log의 요구가 다릅니다. client에는 안정적인 error code, parameter와 검증 message만 주고, 내부 trace에는 request ID와 원 exception을 접근 제어 아래 보존해야 합니다. path sanitization 뒤에도 secret, model path, object-store URI와 prompt 일부가 다른 error field에 남지 않는지 negative fixture를 두는 편이 좋습니다.

## upgrade canary는 상한 바로 아래와 바로 위를 시험해야 합니다

먼저 현재 traffic에서 batch 크기와 structured-output 사용량을 수집합니다. prompt list의 p95·p99와 최대값, regex 또는 JSON schema를 caller가 직접 넣는 비율, derender route 사용 여부, Outlines cache 활성화 여부를 확인합니다. 수집 과정에서 실제 prompt나 credential을 log에 남기지 않고 count, token estimate와 error type만 기록해야 합니다.

다음으로 boundary fixture를 만듭니다. 설정한 prompt 상한이 `N`이면 `N`개는 통과하고 `N+1`개는 engine allocation 전에 4xx로 끝나는지 확인합니다. `max_model_len`, `VLLM_MAX_N_SEQUENCES`와 `max_logprobs`도 같은 방식으로 바로 아래와 바로 위를 시험합니다. response body에는 server path가 없어야 하며 내부 trace에는 같은 request ID가 남아야 합니다.

structured output은 정상적인 짧은 regex, 의도적으로 복잡하지만 안전한 synthetic regex, timeout을 넘기는 adversarial fixture를 분리합니다. 전체 request deadline이 compile timeout보다 길고 무한하지 않은지 확인하며, timeout 뒤 worker와 queue depth가 회복되는지 봅니다. production model이나 사용자 data 없이 작은 canary model로 먼저 실행하는 편이 안전합니다.

마지막으로 cache를 확인합니다. cache를 끈 baseline, 빈 새 directory, 기존 directory의 세 경우를 나누고 startup과 first compilation을 관찰합니다. rollback은 binary와 환경 변수를 이전 version으로 돌리는 절차뿐 아니라 새 SQLite cache를 분리하거나 비우는 절차까지 포함해야 합니다. v0.26.0의 performance 개선이나 security fix를 이유로 검증되지 않은 model·quantization·backend 변경을 같은 rollout에 섞지 않는 편이 원인 분리에 유리합니다.

## 공개 artifact로 확인할 수 있는 최소 절차

편집국은 PyPI JSON에 기록된 source distribution을 내려받아 SHA-256을 대조하고 압축을 푼 뒤, 고정 source에서 환경 변수와 validation helper를 확인했습니다. 아래 절차는 GPU server를 실행하지 않으며 source artifact의 내용만 검사합니다.

```bash
python3 -m pip download --no-deps --no-binary=:all: vllm==0.26.0
shasum -a 256 vllm-0.26.0.tar.gz
tar -xzf vllm-0.26.0.tar.gz

rg -n "VLLM_MAX_COMPLETION_PROMPTS|validate_prompt_list_length" vllm-0.26.0/vllm
rg -n "compile_regex_with_timeout|VLLM_REGEX_COMPILATION_TIMEOUT_S" vllm-0.26.0/vllm
rg -n "OutlinesDiskCache|Index.from_binary|sqlite3" vllm-0.26.0/vllm
rg -n "_validate_derender_bounds|sanitize_message" vllm-0.26.0/vllm
```

기대하는 sdist SHA-256은 `23e9fa19d7e20ce7dcc1c074d41503e2116d23f19e688f5d5ea91b741f958502`입니다. PyPI artifact가 다시 게시되거나 mirror가 다른 파일을 주면 설치를 중단하고 공식 registry metadata를 다시 확인해야 합니다. 이 절차는 source 존재와 배포 artifact 일치를 확인할 뿐, compiled wheel, container image, 특정 CUDA·ROCm 환경의 동작을 검증하지 않습니다.

## 적용 범위와 확인하지 못한 것

이번 검증은 v0.26.0의 Git tag, release note, merge commit, GitHub Advisory, PyPI metadata와 source distribution에 한정합니다. 두 Linux wheel과 sdist가 게시된 사실과 hash는 확인했지만 wheel을 설치하거나 GPU inference server를 실행하지 않았습니다. 공개 regression test도 읽었지만 project test suite를 재실행하지 않았습니다.

completion 상한은 여러 prompt를 담은 list와 `prompt_embeds`에 적용됩니다. 한 prompt의 token 수, chat completions의 별도 batching, custom endpoint, plugin 또는 proxy가 만드는 fan-out 전체를 하나의 환경 변수로 제한하지 않습니다. derender 제한도 명시된 두 endpoint의 caller-supplied response structure에 대한 것입니다.

regex timeout은 기본 5초지만 환경 변수로 해제할 수 있습니다. timeout helper가 모든 structured-output backend와 모든 parser 작업을 감싼다고 일반화하지 않습니다. diskcache 교체도 Outlines optional cache에 관한 변경이며 vLLM 전체의 serialization 정책을 대표하지 않습니다.

이 기사는 v0.26.0이 이전 version보다 성능·안전성에서 포괄적으로 우월하다고 결론 내리지 않습니다. model별 정확성, latency, throughput, memory, quantization, distributed serving과 hardware 호환성은 별도 workload에서 측정해야 합니다. 배포가 외부에 공개되지 않았거나 trusted single-user 환경이라면 위험과 upgrade 우선순위도 달라질 수 있습니다.

## 이해상충과 취재 조건

vLLM 프로젝트와 각 PR 작성자는 자신의 release와 구현을 설명하는 주체입니다. release note와 code는 version·동작·test의 1차 근거이지만, 모든 deployment에서 exploit이 차단됐다는 독립 감사가 아닙니다. GitHub Advisory는 공개 vulnerability 범위와 patched version을 확인하는 자료로 사용했으며, v0.26.0의 전체 보안을 인증하는 근거로 사용하지 않았습니다.

이 기사에는 vLLM, hardware vendor, cloud provider 또는 model vendor의 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 GitHub API, Advisory, PyPI metadata와 source artifact만 사용했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. vLLM v0.26.0 tag에는 여섯 security 관련 merge commit이 포함되고 공식 PyPI에 같은 version의 sdist와 Linux wheel이 게시됐습니다. | E2 · P1/P2 · R2 | Release note, tag ancestry와 PyPI artifact hash를 확인했습니다. Wheel 설치와 server 실행은 하지 않았습니다. |
| C2. `/v1/completions`의 multi-prompt list와 `prompt_embeds`는 기본 1,024개 상한을 Pydantic validation에서 적용받습니다. | E2 · P2 · R2 | 고정 tag의 protocol·env source와 boundary regression test를 확인했습니다. 실제 gateway와 engine allocation은 측정하지 않았습니다. |
| C3. `lm-format-enforcer` regex parser는 기본 5초인 공통 compile timeout을 사용합니다. | E2 · P1/P2 · R2 | Advisory, PR과 tag source를 대조했습니다. v0.24.0의 기존 xgrammar·outlines 수정과 v0.26.0의 backend 확대를 구분했습니다. Runtime timeout 회복은 재현하지 않았습니다. |
| C4. Outlines disk cache는 diskcache/pickle 대신 SQLite와 native binary serialization을 사용합니다. | E2 · P2 · R2 | requirements, cache implementation과 test를 확인했습니다. vLLM 전체의 pickle 제거로 일반화하지 않았고 기존 cache migration은 시험하지 않았습니다. |
| C5. derender payload는 decode 전에 count·token·logprob bound를 검사하고 validation error는 server path를 sanitize합니다. | E2 · P2 · R2 | 고정 source, 호출 순서와 regression test를 확인했습니다. Custom endpoint와 plugin exception은 확인하지 않았습니다. |

## 출처

1. vLLM v0.26.0 release note: https://github.com/vllm-project/vllm/releases/tag/v0.26.0
2. v0.26.0 tag commit `568afb3a13806beb53bb2e6bd518269357b237c0`: https://github.com/vllm-project/vllm/commit/568afb3a13806beb53bb2e6bd518269357b237c0
3. Prompt list fan-out bound PR #47845: https://github.com/vllm-project/vllm/pull/47845
4. Derender resource bounds PR #47260: https://github.com/vllm-project/vllm/pull/47260
5. lm-format-enforcer regex timeout PR #47595: https://github.com/vllm-project/vllm/pull/47595
6. ReDoS advisory GHSA-rwxx-mrjm-wc2m: https://github.com/advisories/GHSA-rwxx-mrjm-wc2m
7. Outlines diskcache replacement PR #44549: https://github.com/vllm-project/vllm/pull/44549
8. Validation error path sanitization PR #46415: https://github.com/vllm-project/vllm/pull/46415
9. Sparse invariant race fix PR #48583: https://github.com/vllm-project/vllm/pull/48583
10. vLLM 0.26.0 PyPI release files and hashes: https://pypi.org/project/vllm/0.26.0/
