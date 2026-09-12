---
edition: ai
decision: publish-candidate
title: "Gemini 3.8 Flash 공개 - 긴 agent 작업을 겨냥한 Flash 모델"
date: 2026-09-13
subject: "Google Gemini 3.8 Flash and Gemini 3.8 Flash Cyber, published 2026-09-02"
summary: "Gemini 3.8 Flash는 Flash 계열의 낮은 가격과 속도를 유지하면서 긴 software engineering과 agent workflow에서 추론 단계와 도구 호출을 더 많이 쓰도록 설계된 production 모델입니다. Google은 1M token context, 64K output, low·medium·high thinking level, built-in tools와 Antigravity 기본 모델 전환을 문서화했습니다. 성능 수치는 Google과 연결 평가 문서의 조건 안에서만 읽어야 하며, 독립 재현이나 한국어 업무 환경 검증은 아직 없습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Google과 Google DeepMind는 Gemini 3.8 Flash의 개발·배포 주체이며 발표문, model card, API 문서, 가격표와 평가 방법 문서를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Google이 Gemini 3.8 Flash를 production용 Gemini API 모델로 공개했습니다. 이 모델은 짧은 답을 빨리 내는 일반 Flash 모델에 그치지 않습니다. 긴 coding agent와 업무 agent가 여러 단계로 생각하고 도구를 반복 호출하는 작업을 겨냥합니다. SW 엔지니어에게 중요한 변화는 benchmark 순위가 아닙니다. 같은 Flash 가격대에서 긴 작업을 어디까지 맡길 수 있는지 다시 재야 한다는 점입니다.

Google 문서는 `gemini-3.8-flash`가 1M token input context와 65,536 token output limit을 지원한다고 설명합니다. 개발자는 `low`, `medium`, `high` thinking level 가운데 하나를 고를 수 있습니다. 또 code execution, computer use preview, file search, function calling, search grounding, URL context, structured output 같은 built-in tool을 같은 모델 페이지에 묶어 두었습니다. 그래서 이 모델은 텍스트 답변 성능만 볼 문제가 아닙니다. agent runtime에서 비용, latency, 실패 복구를 함께 조절해야 합니다.

이 글의 중심 주장은 좁습니다. Gemini 3.8 Flash는 Flash 계열의 효율 모델이 긴 software engineering과 agent workflow 쪽으로 이동했다는 발표입니다. API 문서와 model card로 사용 조건을 확인할 수 있습니다. 다만 성능 우위 주장은 Google이 작성한 benchmark와 외부 leaderboard를 일부 끌어온 평가 방법에 머뭅니다. 따라서 도입 여부는 자체 agent workload에서 effort, 도구 호출, timeout, cache 비용을 함께 재서 판단해야 합니다.

## Flash 모델의 목표가 긴 agent 작업으로 넓어졌습니다

Flash 계열은 보통 빠른 응답과 낮은 단가를 먼저 떠올리게 합니다. Gemini 3.8 Flash 발표에서 달라진 점은 Google이 이 모델을 “workhorse”로 부르며 긴 software engineering, autonomous agent, 복잡한 enterprise workflow를 앞세운다는 점입니다. model card도 Gemini 3.7 Flash를 기반으로 하되 software engineering과 agentic knowledge workflow 성능을 높였다고 설명합니다.

이 변화는 agent를 설계하는 방식에 직접 닿습니다. 기존에는 비용이 낮은 모델을 routing의 첫 단계에 두고, 어려운 계획 수립이나 multi-file refactor가 나오면 비싼 frontier 모델로 넘기는 구성이 흔했습니다. Gemini 3.8 Flash는 그 경계를 흐리려 합니다. Google은 3.7 Flash와 같은 introductory 가격을 유지하면서, 어려운 작업에서는 더 많은 reasoning step과 반복 tool call을 쓰도록 설계했다고 설명합니다.

그러나 “더 많이 생각한다”는 말이 항상 더 싸거나 빠르다는 뜻은 아닙니다. 문서에는 복잡한 작업에서 token 사용량이 늘 수 있고, 낮은 effort level을 선택해 overhead를 줄일 수 있다고 적혀 있습니다. 제품팀은 평균 latency만 볼 것이 아니라 실패한 tool loop, retry, output token, user-visible timeout을 함께 봐야 합니다.

## API의 thinking level이 비용과 지연시간을 가릅니다

Gemini 3.8 Flash의 API 문서는 기본 thinking level을 `medium`으로 둡니다. 개발자는 `low`, `medium`, `high` 가운데 하나를 선택할 수 있고, `minimal`은 지원하지 않으며 error를 반환한다고 문서화되어 있습니다. 이 설정은 단순한 품질 옵션이 아니라 운영 조절값에 가깝습니다.

예를 들어 incident response pipeline이나 실시간 chat처럼 늦으면 가치가 떨어지는 흐름은 `low`가 맞을 수 있습니다. 반대로 결제 처리 코드의 race condition을 분석하거나 큰 refactor 계획을 세우는 요청은 `medium`이나 `high`가 필요할 수 있습니다. 같은 모델 ID를 쓰더라도 이 값에 따라 비용, 지연시간, tool call 횟수가 달라질 수 있습니다.

이 지점에서 이전 방식과 차이가 생깁니다. 예전에는 “빠른 모델”과 “깊게 생각하는 모델”을 서로 다른 모델 선택 문제로 다루는 경우가 많았습니다. Gemini 3.8 Flash는 같은 모델 안에서 effort를 조절하도록 설계되어 있습니다. 그래서 routing 정책은 모델 이름만 고르는 표에서 벗어나, 작업 종류별 effort와 실패 시 fallback 규칙까지 포함해야 합니다.

## 도구를 많이 쓰는 agent는 모델만 비교하기 어렵습니다

Gemini 3.8 Flash 모델 페이지는 function calling, code execution, file search, search grounding, URL context, structured output을 지원 기능으로 나열합니다. computer use는 preview로 표시됩니다. 이 기능 목록은 실제 agent 성능이 모델 가중치만으로 결정되지 않는다는 사실을 보여 줍니다.

긴 coding agent는 파일을 읽고, test를 실행하고, 실패 원인을 찾고, 다시 patch를 만듭니다. 업무 agent는 문서와 spreadsheet를 읽고, 외부 검색이나 내부 retrieval을 호출하며, 중간 결과를 다시 요약합니다. 이런 workflow에서는 도구 schema, timeout, permission, cache, context 보존 방식이 모델 답변만큼 중요합니다.

Google은 Antigravity agent와 Antigravity SDK가 Gemini 3.8 Flash를 기본으로 쓴다고 문서화했습니다. 이는 Google 생태계 안에서는 runtime까지 함께 조정된다는 뜻입니다. 반대로 자체 agent framework나 다른 cloud orchestrator에서 쓰는 팀은 같은 benchmark 조건을 그대로 기대하기 어렵습니다. 특히 computer use preview나 hosted tool 조합은 account와 platform 조건에 따라 달라질 수 있습니다.

## 성능 표는 방향을 보여 주지만 순위표로 쓰기 어렵습니다

Google model card와 별도 평가 방법 문서는 DeepSWE v1.1, Terminal-Bench, OSWorld 2.0, HLE-Verified, GDPVal-AA v2, Vals Finance Agent v2 같은 결과를 제시합니다. 예를 들어 model card는 DeepSWE v1.1에서 Gemini 3.8 Flash가 73.7%, Gemini 3.7 Flash가 65.3%라고 적습니다. HLE-Verified도 54.9%와 53.6%로 비교합니다.

이 수치는 3.7 Flash와의 방향을 보는 데는 유용합니다. 하지만 다른 회사 모델과의 일반 순위로 바로 옮기기는 어렵습니다. 평가 방법 PDF는 Gemini 결과 일부가 self computed이고, non-Gemini 모델 수치는 provider self-reported number를 쓰거나 public leaderboard와 Artificial Analysis에서 가져왔다고 설명합니다. OSWorld 2.0 같은 computer use 평가에서는 harness, 화면 해상도, step limit, tool 방식이 결과를 크게 바꿀 수 있습니다.

따라서 기사에서는 Google의 benchmark를 독립 검증으로 올리지 않습니다. 더 강한 결론을 내려면 같은 agent harness, 같은 tool permission, 같은 timeout, 같은 비용 산정으로 다시 재야 합니다. 한국어 repository, 국내 업무 문서, 한국어 OCR·검색이 들어간 agent workload도 별도로 봐야 합니다.

## 낮은 token 단가만으로 실제 비용은 알 수 없습니다

Gemini API 가격표에 따르면 2026년 12월 31일까지 `gemini-3.8-flash` standard paid tier는 input 100만 token당 0.75달러, output 100만 token당 3.75달러입니다. 2027년 1월 1일부터는 각각 1.50달러와 7.50달러로 바뀐다고 문서화되어 있습니다. context caching은 2026년 말까지 100만 token당 0.075달러이고, storage price는 100만 token·시간당 0.50달러입니다.

이 가격은 긴 context agent에 매력적입니다. 하지만 output 가격에는 thinking token이 포함됩니다. 어려운 작업에서 모델이 reasoning step을 많이 쓰고 도구를 더 자주 부르면, 낮은 token 단가가 실제 청구액 감소로 곧장 이어지지 않을 수 있습니다.

엔지니어가 봐야 할 단위는 요청당 단가가 아닙니다. 한 issue를 닫는 데 들어간 총 token, tool call, wall-clock time, 성공률, 사람이 다시 고친 patch 비율을 같이 봐야 합니다. Gemini 3.8 Flash가 맞는지는 “모델이 싸다”보다 “우리 workload에서 같은 품질을 더 낮은 총비용으로 끝내는가”로 판단해야 합니다.

## 안전 문서는 한국어 서비스의 추가 검증을 요구합니다

Gemini 3.8 Flash model card는 알려진 한계도 비교적 분명히 적습니다. foundation model의 hallucination 가능성, 가끔 느려지거나 timeout이 생길 수 있다는 점, 높은 effort level에서 token 사용량이 늘 수 있다는 점을 밝힙니다. knowledge cutoff는 2026년 3월이며, 일부 영역에서는 Gemini 3 model family와 맞춰 2025년 1월 수준의 지식 제한을 경험할 수 있다고 설명합니다.

안전 평가에서는 Gemini 3.8 Flash가 3.7 Flash와 전반적으로 비슷하지만, non-English language safety는 3.7 Flash보다 약간 나빠졌다고 적습니다. Frontier Safety Framework와 관련해서는 3.8 Flash가 3.7 Flash 대비 해당 위험 영역에서 의미 있는 새 capability나 material increase를 보이지 않았다고 설명합니다.

이 대목은 한국 독자에게 중요합니다. 영어 중심 coding benchmark가 좋아져도 한국어 고객 문서, 국내 법·금융 표현, 한국어 instruction에서 safety와 refusal가 같은 품질로 동작한다고 볼 수는 없습니다. 국내 서비스에 넣으려면 한국어 prompt, 한국어 document retrieval, 민감 정보 masking, tool permission을 묶은 자체 평가가 필요합니다.

## 이해상충과 취재 조건

Google과 Google DeepMind는 Gemini 3.8 Flash의 개발·배포 주체이며 발표문, model card, API 문서, 가격표와 평가 방법 문서를 작성했습니다. 출시 사실, model ID, API spec, 가격, thinking level, tool 지원, model card 한계는 원문으로 확인했습니다. 성능 비교는 Google이 공개한 표와 평가 방법의 조건 안에서만 설명했고, 독립 재현 결론으로 쓰지 않았습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 다른 웹 신호는 후보 발견에만 사용했고, 기사 사실은 Google과 Google DeepMind 원문으로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Google은 2026년 9월 2일 Gemini 3.8 Flash와 Gemini 3.8 Flash Cyber를 공개했고, 일반 개발자는 `gemini-3.8-flash`를 Gemini API와 Google AI Studio에서 사용할 수 있다고 설명했습니다. | E2 · P1 | 발표문, Gemini API latest-model page, model page, model card로 확인했습니다. 계정별 실제 availability는 API 호출로 확인하지 않았습니다. |
| C2. `gemini-3.8-flash`는 stable model ID, 1,048,576 input token limit, 65,536 output token limit, text·image·video·audio·PDF input, text output을 문서화했습니다. | E2 · P1 | Gemini API model page와 model card가 일치합니다. 실제 context limit과 modality 동작은 live request로 재현하지 않았습니다. |
| C3. Gemini 3.8 Flash는 `low`, `medium`, `high` thinking level을 지원하고 `minimal`은 지원하지 않는다고 문서화되어 있습니다. | E2 · P1 | latest-model page와 model page로 확인했습니다. effort별 latency와 token 사용량은 workload마다 달라집니다. |
| C4. Google은 Gemini 3.8 Flash가 function calling, code execution, file search, search grounding, URL context, structured output을 지원하고 computer use를 preview로 제공한다고 문서화했습니다. | E2 · P1 | Gemini API model page로 확인했습니다. 일부 hosted tool과 preview 기능은 account, region, product surface에 따라 다를 수 있습니다. |
| C5. Google은 Antigravity agent와 Antigravity SDK가 Gemini 3.8 Flash를 기본 모델로 쓴다고 문서화했습니다. | E2 · P1 | Gemini API latest-model page로 확인했습니다. Antigravity 내부 harness는 공개 코드로 재현하지 않았습니다. |
| C6. Google은 DeepSWE v1.1, Terminal-Bench, OSWorld 2.0, HLE-Verified 등에서 Gemini 3.8 Flash 결과를 공개했고, 평가 방법 문서는 Gemini 결과와 비-Gemini 비교 수치의 출처와 self-computed 조건을 설명합니다. | E2 · P1 | model card와 evaluation methodology PDF로 확인했습니다. 독립 재현이나 같은 조건의 편집국 재실행은 없으므로 일반 우월성 결론으로 쓰지 않았습니다. |
| C7. 2026년 말까지 Gemini 3.8 Flash standard paid tier 가격은 input 100만 token당 0.75달러, output 100만 token당 3.75달러이며 2027년 1월 1일부터 각각 1.50달러와 7.50달러로 바뀐다고 가격표가 문서화했습니다. | E2 · P1 | Gemini API pricing page로 확인했습니다. 가격은 이후 갱신될 수 있고, 실제 청구액은 cache, batch, priority, tool 사용량에 따라 달라집니다. |

## 출처

1. Google, `Introducing Gemini 3.8 Flash and Gemini 3.8 Flash Cyber`, 2026-09-02: https://blog.google/innovation-and-ai/models-and-research/gemini-models/3-8-flash-and-3-8-flash-cyber/
2. Google DeepMind, `Gemini 3.8 Flash - Model Card`, published 2026-09-02: https://deepmind.google/models/model-cards/gemini-3-8-flash/
3. Google AI for Developers, `What's new in Gemini 3.8 Flash`, last updated 2026-09-03: https://ai.google.dev/gemini-api/docs/latest-model
4. Google AI for Developers, `Gemini 3.8 Flash`, last updated 2026-09-02: https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
5. Google AI for Developers, `Gemini Developer API pricing`: https://ai.google.dev/gemini-api/docs/pricing
6. Google DeepMind, `Eval-Methodology-Gemini 3-8-Flash`: https://deepmind.google/models/evals-methodology/gemini-3-8-flash
