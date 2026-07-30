---
edition: ai
decision: publish-candidate
title: "GitHub Models 종료: HTTP 410으로 확인한 끊긴 API와 Foundry 이관 경계"
date: 2026-07-31
subject: "GitHub Models retirement on 2026-07-30 and Microsoft Foundry migration boundary"
summary: "GitHub Models의 catalog와 inference API가 실제로 HTTP 410을 반환합니다. 공식 quickstart는 아직 종료된 endpoint와 성공 응답을 안내하므로, 기존 workflow는 재시도보다 endpoint·인증·deployment 경계를 함께 바꾸는 이관이 필요합니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["GitHub와 Microsoft는 각각 종료한 서비스와 권장 대체 서비스의 운영 주체입니다. 이 기사에는 사전 접근, 유료 계정·credit 제공, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

GitHub가 7월 30일 GitHub Models 종료 완료를 공개했습니다. 개발자에게 중요한 변화는 공지 문구보다 먼저 기존 `models.github.ai` 호출 경로가 HTTP `410 Gone`으로 끊겼다는 점입니다. 반면 공식 quickstart와 REST reference는 7월 31일 확인 시점에도 같은 endpoint와 성공 응답을 안내하므로, 문서 예제를 availability check로 사용하면 잘못된 운영 판단을 내릴 수 있습니다.

## 세 줄 요약

- GitHub는 playground, model catalog, inference API와 bring your own key(BYOK)가 기존 사용자를 포함한 모든 고객에게 더 이상 제공되지 않는다고 밝혔습니다.
- 7월 31일 08:05 KST에 catalog `GET`과 chat completions `POST`를 인증 정보 없이 확인하자 둘 다 HTTP `410`과 `github_models_retirement_brownout` body를 반환했습니다.
- Microsoft Foundry로 옮기려면 GitHub token과 사전 구성 catalog에 기대던 workflow를 Azure subscription, resource endpoint, credential, model deployment 이름에 맞춰 다시 검증해야 합니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 종료 공지, 두 API의 `410` 응답, 아직 남아 있는 GitHub quickstart·REST 예제, Foundry의 deployment·endpoint·인증 계약을 공개 원문에서 확인할 수 있습니다.
- **도입 전에 확인할 것:** repository와 Actions에서 `models.github.ai`, `models: read`, GitHub PAT·`GITHUB_TOKEN`, model ID, retry policy, prompt·평가 UI 의존성을 각각 찾아 대체 경로를 정해야 합니다.
- **아직 결론 내릴 수 없는 것:** 기존 GitHub Models의 model별 설정이 Foundry에서 같은 지역·가격·quota·content filter로 제공되는지, 실제 workload의 품질·latency·비용이 유지되는지는 이번 공개 자료와 무인증 probe만으로 판단할 수 없습니다.

## 이 공개의 의의와 편집 판단

GitHub는 6월 16일 신규 고객 접근을 닫았고, 7월 1일에는 기존 고객까지 포함한 7월 30일 완전 종료와 7월 16일·23일 brownout을 예고했습니다. 7월 30일 후속 공지는 playground, catalog, inference API와 BYOK가 이제 모든 고객에게 제공되지 않는다고 명시합니다. 전날 서울 발행 시점에는 완전 종료를 직접 관찰하지 못했지만, 오늘은 이전 API surface의 `410` 응답을 재현할 수 있습니다.

**편집 판단:** 이 변화의 핵심은 model 공급자가 하나 줄었다는 데 있지 않습니다. GitHub identity와 repository permission으로 호출하던 inference boundary가 사라지고, 대체 경로에서는 cloud resource, deployment, credential, billing과 region을 application이 소유해야 한다는 데 있습니다. 따라서 migration 완료 조건은 새 endpoint에서 한 번 응답을 받는 것이 아니라 기존 model ID·권한·retry·관측·비용 통제가 새 deployment 계약으로 옮겨졌는지 확인하는 것입니다.

## 기존 호출은 인증 단계 전에 410으로 끝납니다

편집국은 7월 31일 08:05:31 KST에 `https://models.github.ai/catalog/models`로 인증 정보 없는 `GET`을 보냈습니다. 응답은 HTTP `410`, `content-type: application/json`이었고 body의 error code는 `github_models_retirement_brownout`이었습니다. 같은 시각 chat completions endpoint에 최소 JSON body를 넣어 보낸 무인증 `POST`도 동일한 `410`과 152-byte body를 반환했습니다.

두 응답 body의 SHA-256은 모두 `eb684b77670c904f8a8ac2304cacadd359f792928a5ff14d502912342ee84afd`입니다. 이 probe에는 GitHub PAT, 조직 정보, 유료 account나 실제 prompt data를 사용하지 않았습니다. 따라서 authenticated request의 세부 응답이나 model별 상태를 확인한 것은 아니지만, public route가 이전의 token 검증과 model 처리 경로까지 요청을 진행시키지 않는 상태는 확인했습니다.

응답 body는 “temporarily unavailable”과 “scheduled retirement brownout”이라고 적지만, HTTP status는 `410 Gone`입니다. HTTP Semantics 표준인 RFC 9110은 `410`을 target resource에 대한 접근이 더 이상 없고 그 상태가 영구적일 가능성이 높을 때 쓰는 status로 정의합니다. 공식 종료 공지도 서비스가 더 이상 제공되지 않는다고 밝히므로, client는 body의 “temporarily”만 보고 무한 재시도를 구성하면 안 됩니다.

운영 코드에서는 `410`을 transient `429`나 `5xx`와 분리해야 합니다. 자동 retry를 멈추고 migration-required 상태로 전환하며, queue에 쌓인 작업의 idempotency key와 원 prompt를 보존한 뒤 새 provider에서 명시적으로 replay하는 편이 안전합니다. 이 기사는 brownout error code가 언제 다른 retirement code로 바뀌는지까지는 확인하지 않았으므로 alert 조건은 body 문자열보다 HTTP status와 host를 우선하는 편이 좋습니다.

## 공식 문서는 아직 종료된 성공 경로를 보여 줍니다

7월 31일 확인한 GitHub Models quickstart는 여전히 playground가 sign-in만으로 동작한다고 설명합니다. 같은 문서의 API 예제는 GitHub PAT의 `models` scope로 `https://models.github.ai/inference/chat/completions`를 호출하면 chat completion을 받는다고 안내합니다. Actions 예제도 `permissions: models: read`와 `GITHUB_TOKEN`으로 같은 endpoint를 호출합니다.

REST inference reference 역시 `X-GitHub-Api-Version: 2026-03-10`과 `models: read` token을 사용한 request 뒤 HTTP `200` 예시를 노출합니다. 이 문서는 API schema와 과거 contract를 이해하는 자료로는 쓸 수 있지만, 현재 availability나 smoke test의 정답으로 사용하면 안 됩니다. 종료 공지와 live `410`이 runtime 판단의 우선 근거입니다.

이 차이는 migration inventory에 문서도 포함해야 한다는 뜻입니다. repository 안의 README, runbook, onboarding 문서, workflow template, internal SDK wrapper가 공식 quickstart를 복제했을 수 있습니다. production code만 새 provider로 바꾸고 운영 문서를 남겨 두면 신규 token 발급이나 `models: read` 권한 확대처럼 더 이상 의미 없는 조치가 장애 대응 절차에 남습니다.

GitHub의 종료 공지는 model access가 필요한 project에는 Microsoft Foundry를, GitHub 안에서 AI workflow를 만들 목적에는 GitHub Copilot을 제시합니다. 두 선택지는 같은 API의 새 이름이 아닙니다. 일반 application inference와 repository-native coding workflow를 먼저 구분한 뒤 각각의 대체 경로를 선택해야 합니다.

## Foundry 이관은 endpoint만 바꾸는 작업이 아닙니다

Microsoft의 GitHub Models upgrade 문서는 paid Azure account와 유효한 결제 수단이 연결된 subscription을 prerequisite로 둡니다. partner·community model은 Azure Marketplace 접근 권한도 필요할 수 있습니다. GitHub Models에서는 catalog의 model이 이미 구성돼 있었지만, Foundry Tools resource에서는 사용할 model을 직접 deployment로 추가하고 configuration을 정해야 합니다.

Foundry endpoint 문서는 deployment가 model name·version, capacity type, content filtering, rate limit configuration을 묶는다고 설명합니다. request의 `model` 값도 단순한 vendor model ID가 아니라 resource 안에서 정한 deployment 이름을 가리킬 수 있습니다. 기존 `openai/gpt-4.1` 같은 문자열을 그대로 유지할 수 있다고 가정하지 말고 새 deployment manifest와 mapping table을 만들어야 합니다.

인증 경계도 달라집니다. GitHub Actions의 repository-scoped `GITHUB_TOKEN`과 `models: read` permission 대신 Foundry key 또는 Microsoft Entra ID 권한을 준비해야 합니다. endpoint는 `https://<resource>.services.ai.azure.com` 또는 OpenAI/v1 형태를 사용하며, resource·deployment와 credential을 secret management 및 role assignment에 연결해야 합니다.

Microsoft 문서는 Foundry의 Azure AI Inference beta SDK가 8월 26일 종료될 예정이므로 stable OpenAI SDK와 OpenAI/v1 API로 옮기라고 안내합니다. GitHub Models 종료를 피하려고 곧 종료될 beta SDK에 새 의존성을 만드는 것은 migration을 두 번 수행하는 경로가 될 수 있습니다. 새 implementation은 현재 지원되는 endpoint와 SDK lifecycle을 함께 확인해야 합니다.

## 작은 canary로 권한과 동작을 따로 검증해야 합니다

먼저 source와 configuration에서 이전 surface를 inventory합니다. `models.github.ai`, `github.com/marketplace/models`, `models: read`, PAT scope, `GITHUB_TOKEN`, GitHub Models SDK package, prompt file과 evaluation command를 찾습니다. 각 의존성을 inference, catalog discovery, prompt storage, evaluation, UI workflow로 분류해야 누락을 줄일 수 있습니다.

다음으로 provider-neutral request fixture를 만듭니다. 최소 chat completion, streaming, tool call, structured output, embeddings처럼 실제 workload에 필요한 기능만 고르고, response schema와 error mapping을 고정합니다. GitHub Models에서 사용한 model ID와 Foundry deployment 이름을 분리해 mapping하며, deployment가 없는 model은 startup이나 CI에서 fail-closed로 검출합니다.

그다음 read-only 또는 낮은 risk의 canary traffic을 새 deployment로 보냅니다. authentication failure, quota, region availability, content filter, timeout, streaming termination, usage accounting을 각각 관찰합니다. quality·latency·cost는 old provider의 문서 예시가 아니라 보존된 application fixture와 production에 가까운 concurrency에서 다시 측정해야 합니다.

마지막으로 retry와 rollback을 분리합니다. 이전 host의 `410`은 retry 대상에서 제거하고 새 provider의 `429`·`5xx`만 제한된 backoff 정책으로 처리합니다. rollback은 종료된 GitHub Models로 돌아가는 것이 아니라, 검증된 다른 deployment나 provider로 traffic을 전환하는 configuration이어야 합니다. prompt와 idempotency key, user-visible failure 상태를 보존해야 중복 side effect를 막을 수 있습니다.

## 직접 확인할 수 있는 최소 probe

아래 명령은 credential이나 유료 inference를 사용하지 않고 종료된 public route의 status와 body만 확인합니다. 응답 body는 이후 바뀔 수 있으므로 `410`이 아닌 결과가 나오면 공식 공지와 status page를 다시 확인해야 합니다.

```bash
curl -sS -D - https://models.github.ai/catalog/models

curl -sS -D - \
  -X POST \
  -H 'Content-Type: application/json' \
  https://models.github.ai/inference/chat/completions \
  --data '{"model":"openai/gpt-4.1","messages":[{"role":"user","content":"health probe"}]}'
```

실제 migration test에서는 이 probe에 production secret을 붙이지 않습니다. 새 Foundry resource에서 별도 canary credential과 deployment를 만들고, secret scanner와 audit log가 활성화된 환경에서 application fixture를 실행해야 합니다. 이번 기사에서는 Azure subscription이나 Foundry deployment를 만들지 않았고 유료 inference도 호출하지 않았습니다.

## 적용 범위와 확인하지 못한 것

이 기사가 직접 재현한 범위는 인증 정보 없는 catalog `GET`과 chat completions `POST`가 관찰 시점에 `410`을 반환한다는 사실입니다. GitHub가 밝힌 모든 customer와 모든 surface의 계정별 동작을 별도 로그인으로 확인하지 않았습니다. Marketplace URL은 로그인 page로 이동했으므로 playground UI 제거 상태를 독립적으로 판정하지 않았습니다.

GitHub quickstart와 REST reference는 이동 가능한 live 문서입니다. 7월 31일에는 이전 endpoint와 `200` 예시가 남아 있었지만 article 공개 뒤 갱신될 수 있습니다. 문서 잔존을 서비스 복구 신호로 해석하지 않으며, 향후 문서가 고쳐져도 관찰 시점의 `410`과 종료 공지 자체는 달라지지 않습니다.

Foundry의 feature, 인증과 deployment contract는 공식 문서에서 확인했지만 실제 resource를 만들거나 model을 배포하지 않았습니다. 지역별 availability, quota, content filter 결과, 한국에서의 latency, 환율을 포함한 비용, 품질 동등성은 측정하지 않았습니다. Copilot도 일반 inference API의 drop-in replacement로 시험하지 않았습니다.

## 이해상충과 취재 조건

GitHub는 종료한 GitHub Models와 권장한 GitHub Copilot의 운영 주체입니다. Microsoft는 권장 대체 경로인 Foundry와 Azure billing·deployment 문서의 운영 주체입니다. 두 회사의 migration 설명은 자기 제품의 availability와 contract를 확인하는 1차 근거이며, 성능·비용 우월성의 독립 근거가 아닙니다.

이 기사에는 GitHub 또는 Microsoft의 사전 briefing, 제공받은 account·credit, 유료 subscription, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 문서와 credential 없는 HTTP probe만 사용했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. GitHub Models는 7월 30일 종료됐고, 7월 31일 08:05 KST에 catalog와 inference route가 모두 HTTP `410`을 반환했습니다. | E2 · P1/P2 · R2 | GitHub 종료 공지와 두 credential-free HTTP probe를 대조했습니다. Authenticated customer별 동작은 시험하지 않았습니다. |
| C2. 공식 GitHub quickstart와 REST reference는 관찰 시점에도 종료된 endpoint, GitHub token 권한과 HTTP `200` 예시를 안내했습니다. | E2 · P1/P2 · R2 | Live 공식 문서와 실제 `410` 응답을 비교했습니다. 문서는 article 공개 뒤 갱신될 수 있습니다. |
| C3. Foundry는 Azure subscription·resource·credential·model deployment를 요구하므로 기존 GitHub token workflow의 운영 경계를 다시 구성해야 합니다. | E2 · P1 · R1 | Microsoft의 upgrade·endpoint 문서를 확인했습니다. Azure resource 생성과 유료 inference는 수행하지 않았습니다. |
| C4. 현재 body의 “temporary brownout” 표현과 달리 HTTP `410`은 영구적일 가능성이 높은 제거 상태를 뜻하므로 무한 retry 대상으로 두면 안 됩니다. | E2 · P1/P2 · R2 | RFC 9110의 `410` 의미, GitHub 종료 공지와 live response를 함께 적용했습니다. GitHub의 최종 error code 유지 기간은 확인하지 않았습니다. |

## 출처

1. GitHub Models is now retired, 2026-07-30: https://github.blog/changelog/2026-07-30-github-models-is-now-retired/
2. GitHub Models full-retirement timeline, 2026-07-01: https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026/
3. GitHub Models catalog endpoint, observed HTTP 410 on 2026-07-31: https://models.github.ai/catalog/models
4. GitHub Models chat completions endpoint, observed HTTP 410 on 2026-07-31: https://models.github.ai/inference/chat/completions
5. GitHub Models quickstart, accessed 2026-07-31: https://docs.github.com/en/enterprise-cloud@latest/github-models/quickstart
6. GitHub Models REST inference reference, accessed 2026-07-31: https://docs.github.com/en/rest/models/inference
7. Upgrade from GitHub Models to Microsoft Foundry Models, accessed 2026-07-31: https://learn.microsoft.com/en-gb/azure/foundry/foundry-models/how-to/quickstart-github-models
8. Endpoints for Microsoft Foundry Models, accessed 2026-07-31: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/endpoints
9. RFC 9110, section 15.5.11 `410 Gone`: https://www.rfc-editor.org/rfc/rfc9110.html#name-410-gone
