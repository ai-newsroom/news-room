---
edition: ai
decision: publish-candidate
title: "GPT-6 Sol과 Luna 공개 - 긴 에이전트 작업의 비용은 cache 재사용에 달렸습니다"
date: 2026-09-26
subject: "OpenAI GPT-6 Sol and GPT-6 Luna, released 2026-09-22"
summary: "OpenAI가 GPT-6 Sol과 GPT-6 Luna를 API와 Codex·ChatGPT Work에 공개했습니다. 이번 변화의 핵심은 더 싼 모델 두 개가 추가됐다는 사실만이 아닙니다. 긴 coding agent와 업무 agent가 반복해서 보내는 지시문, 도구 정의, repository context를 cache로 다시 쓰도록 prompt caching, cache diagnostics, reasoning effort 변경 방식을 함께 손봤다는 점입니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["OpenAI는 GPT-6 Sol, GPT-6 Luna, API 문서, system card와 prompt caching 문서의 작성·배포 주체입니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

OpenAI가 GPT-6 Sol과 GPT-6 Luna를 공개했습니다. 두 모델은 GPT-6 Astra보다 낮은 비용과 빠른 사용을 겨냥한 GPT-6 계열 모델입니다. 개발자에게 중요한 변화는 모델 이름이 늘어난 데서 끝나지 않습니다. 긴 coding agent나 업무 agent는 같은 repository, 도구 목록, 지시문을 여러 번 다시 보냅니다. 이번 공개에서는 이 반복 입력을 cache로 더 잘 재사용할 수 있도록 API 계약과 진단 도구가 함께 바뀌었습니다.

Sol과 Luna는 OpenAI API에서 각각 `gpt-6-sol`, `gpt-6-luna`로 제공됩니다. 발표문과 API changelog는 Sol의 표준 가격을 input 100만 token당 2달러, cached input 100만 token당 0.20달러, output 100만 token당 10달러로 적었습니다. Luna는 input 100만 token당 0.10달러, cached input 100만 token당 0.01달러, output 100만 token당 0.50달러입니다. 이 글은 두 모델이 경쟁 모델보다 낫다는 순위 결론을 내리지 않습니다. 확인된 변화는 GPT-6 계열의 낮아진 단가, prompt caching의 새 제어 방식, cache miss를 찾는 진단 도구, 그리고 safety system card에 공개된 제한 조건입니다.

## 긴 에이전트 작업은 같은 맥락을 반복해서 보냅니다

에이전트가 한 번에 답을 내는 작업은 비용 계산이 비교적 단순합니다. 입력과 출력 token을 세고 모델 단가를 곱하면 됩니다. 하지만 코드베이스를 고치거나 여러 앱을 오가며 업무를 처리하는 agent는 다릅니다. 같은 system instruction, tool schema, repository 요약, 이전 작업 상태를 여러 요청에 걸쳐 다시 보냅니다. 작업이 길어질수록 새 질문보다 반복되는 prefix가 더 커질 수 있습니다.

OpenAI가 이번 발표에서 함께 강조한 prompt caching은 반복되는 prefix를 다시 계산하지 않도록 하는 장치입니다. GPT-6 계열에서는 eligible shared prefix를 30분 안에 다시 쓰면 cached input token 할인을 받을 수 있다고 문서화했습니다. 발표문은 cached input token 할인 폭을 최대 90%로 설명합니다. Sol과 Luna의 낮은 기본 단가에 cache read 가격이 더해지면, 긴 agent 작업의 비용 병목은 “모델이 얼마나 똑똑한가”뿐 아니라 “같은 context를 얼마나 안정적으로 재사용하는가”로 옮겨갑니다.

이 변화는 설계 습관을 바꿉니다. 매 요청마다 tool definition을 새로 만들거나 날짜·사용자 상태·임시 지시를 앞부분에 끼워 넣으면 cache가 깨질 수 있습니다. 반대로 안정적인 instruction과 도구 정의를 앞에 두고 자주 바뀌는 내용을 뒤로 보내면, 같은 작업에서도 비용과 latency가 달라질 수 있습니다.

## reasoning effort와 tool 목록도 cache를 깨지 않게 바꿉니다

긴 agent 작업에서는 모든 turn의 난이도가 같지 않습니다. 쉬운 파일 탐색은 낮은 reasoning effort로 충분할 수 있고, merge 직전의 설계 판단에는 더 높은 effort가 필요할 수 있습니다. 이전에는 이런 설정 변경이 cached prefix를 깨뜨릴 위험이 컸습니다. OpenAI 문서는 GPT-6 이후 모델에서 `configuration_update` input item을 append해 reasoning effort를 바꾸면 앞쪽 prefix를 보존할 수 있다고 설명합니다.

도구도 비슷합니다. 작업 초반에는 검색과 파일 읽기가 필요하고, 후반에는 test 실행이나 patch 적용 도구가 필요할 수 있습니다. 문서는 tool definition과 순서를 안정적으로 유지하라고 안내합니다. 특정 요청에서 도구를 쓰지 않을 때도 목록을 지우기보다 `tool_choice`를 `"none"`으로 두라고 설명합니다. 필요한 도구만 열 때는 `allowed_tools`로 callable tool을 제한하는 편이 cache 재사용에 유리합니다.

이 부분은 성능표보다 실무적입니다. agent wrapper를 만드는 팀은 prompt를 잘 쓰는 것만큼 request shape를 안정적으로 유지해야 합니다. 같은 repository에서 여러 branch 작업을 동시에 돌리는 제품이라면, 어떤 prefix를 공유하고 어디서부터 사용자별 context로 나눌지 API 수준에서 정해야 합니다.

## cache가 왜 빗나갔는지 확인할 수 있습니다

cache는 보이지 않으면 운영하기 어렵습니다. 비용이 갑자기 늘었을 때 모델이 더 오래 생각한 것인지, tool schema가 달라져 cache가 깨진 것인지, routing이 다른 모델로 바뀐 것인지 알기 어렵기 때문입니다. OpenAI는 Prompt Caching Dashboard와 diagnostics tool을 함께 공개했습니다. API 문서는 최근 response와 현재 요청을 비교해 `cache_hit`, `cache_miss`, `comparison_response_not_found`, `unavailable` 같은 결과를 돌려준다고 설명합니다.

예를 들어 tools가 바뀌어 cache miss가 생기면 diagnostics 결과에 `reason: "tools_changed"`와 재사용하지 못한 token 추정치가 들어갈 수 있습니다. 이 값은 청구 사용량 자체가 아니라 miss 원인을 찾기 위한 진단값입니다. 실제 비용은 response usage field로 확인해야 합니다.

이 차이는 중요합니다. cache diagnostics는 “이번 요청이 왜 비싸졌는가”를 바로 결론 내리는 회계 장부가 아닙니다. 대신 request 구조가 cache 재사용을 방해했는지 확인하는 계측 도구입니다. 개발자는 이 신호를 로그와 tracing에 붙여, 특정 deploy 뒤 cache hit rate가 떨어졌는지 볼 수 있습니다.

## Sol과 Luna의 성능 주장은 조심해서 읽어야 합니다

OpenAI 발표문은 Sol과 Luna가 전문 업무, coding, computer use에서 비용 대비 성능을 높였다고 설명합니다. AutomationBench, Agents' Last Exam, FrontierCode, DeepSWE, OSWorld 같은 benchmark와 비용 비교도 제시했습니다. 하지만 이 수치들은 OpenAI가 작성한 발표문 안의 비교이고, competitor score는 공개 보고서에서 가져온 것도 섞여 있습니다. 각 모델의 effort, harness, fallback, tool set, production prompt 조건이 완전히 같다고 볼 수 없습니다.

따라서 이 글의 중심은 “Sol과 Luna가 어떤 순위에 올랐다”가 아닙니다. 확인할 수 있는 것은 모델 출시, 가격, API 제공 경로, prompt caching 개선, cache diagnostics, system card의 안전 평가 범위입니다. 실제 도입 판단은 각 팀의 workload로 다시 해야 합니다. 같은 issue set, 같은 test gate, 같은 timeout, 같은 tool policy로 Astra, Sol, Luna와 기존 모델을 나란히 돌려야 비용 대비 품질을 알 수 있습니다.

한국 개발팀에는 특히 한국어 context가 변수입니다. 공개 benchmark와 partner 사례는 주로 영어 업무와 글로벌 SaaS workflow에 맞춰져 있습니다. 한국어 요구사항, 국내 서비스 로그, 사내 결재 문서, 개인정보 masking이 섞인 환경에서는 tokenization, retrieval 품질, tool permission, cache prefix 설계가 다르게 작동할 수 있습니다.

## 안전 문서는 낮은 단가와 낮은 위험을 구분합니다

OpenAI의 GPT-6 Astra system card에는 2026년 9월 22일 Sol과 Luna 부록이 추가됐습니다. 이 부록은 Sol과 Luna를 Preparedness Framework상 cybersecurity와 biological·chemical domain에서 High capability로 다룬다고 설명합니다. AI self-improvement에서는 High threshold에 이르지 않는다고 적었습니다. Sol과 Luna에 대해서는 GPT-5.6 Sol·Luna에 적용된 safeguard set을 이어 쓴다고 설명합니다.

이 말은 두 모델을 저가형 utility model로만 읽어서는 안 된다는 뜻입니다. 더 싼 모델이 agent workflow에 넓게 깔릴수록, 더 많은 도구 호출과 더 긴 자동 작업이 발생합니다. 안전성은 모델 자체 평가뿐 아니라 tool permission, human review, cache에 남는 shared context, logging과 retention 정책까지 함께 봐야 합니다.

system card는 static·multiturn jailbreak, health, alignment 관련 평가를 공개하지만, 이 결과도 OpenAI가 정의한 평가와 조건 안에 있습니다. 독립 재현이나 외부 audit이 같은 결론을 냈다는 뜻은 아닙니다. 자동 코드 수정이나 업무 agent에 붙일 때는 낮은 단가를 review gate를 줄이는 이유로 삼기보다, 같은 예산으로 더 많은 검증을 돌릴 수 있는 조건으로 봐야 합니다.

## 도입 판단은 모델 선택보다 context 설계에서 시작합니다

이번 발표가 SW 엔지니어에게 주는 실질적인 질문은 간단합니다. “어떤 모델이 가장 좋은가”보다 “우리 agent가 cache를 깨지 않도록 context를 어떻게 구성하고 있는가”입니다. Sol과 Luna의 가격 인하는 좋은 출발점입니다. 하지만 반복 prefix가 매 turn 새로 계산된다면 긴 작업의 비용 병목은 그대로 남습니다.

첫 점검 대상은 stable prefix입니다. system instruction, coding rule, tool definition, repository summary처럼 여러 turn에서 유지되는 정보가 앞에 놓여야 합니다. 자주 바뀌는 사용자 요청, 시간, 임시 지시, 실험 옵션은 뒤로 밀어야 합니다. 둘째는 tool 관리입니다. 도구 목록을 매번 재구성하는 대신 안정적으로 보존하고, 요청별 사용 범위만 제한하는 편이 낫습니다. 셋째는 계측입니다. cache hit rate, missed token 추정치, model routing, effort 변경, tool schema 변경을 한 로그에서 봐야 합니다.

OpenAI가 공개한 자료만으로 결론낼 수 있는 범위는 여기까지입니다. GPT-6 Sol과 Luna는 낮은 가격의 새 reasoning model이고, GPT-6 prompt caching 변화는 긴 agent 작업에서 반복 context 비용을 줄이는 API 설계 과제를 전면에 올렸습니다. 성능 우위는 각 팀의 workload에서 다시 검증해야 하지만, cache와 request shape를 먼저 점검해야 한다는 결론은 공식 문서만으로도 충분합니다.

## 이해상충과 취재 조건

OpenAI는 GPT-6 Sol, GPT-6 Luna, API changelog, prompt caching 문서, diagnostics 문서와 GPT-6 Astra system card의 작성·배포 주체입니다. 출시 사실, 가격, API model ID, cache 동작 설명, diagnostics 결과 유형, system card의 Sol·Luna 부록은 OpenAI 원문으로 확인했습니다. 성능 비교와 partner 사례는 발표 주체가 제시한 조건 안에서만 설명했고, 독립 우월성 결론으로 쓰지 않았습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 공식 뉴스 목록은 후보 발견에만 사용했고, 기사 사실은 OpenAI 공식 발표, API changelog, API docs, Deployment Safety Hub 문서로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. OpenAI는 2026년 9월 22일 GPT-6 Sol과 GPT-6 Luna를 공개했고, API에서 `gpt-6-sol`, `gpt-6-luna`로 제공한다고 문서화했습니다. | E2 · P1 | OpenAI 발표문과 API changelog로 확인했습니다. 계정별 실제 availability는 API 호출로 재현하지 않았습니다. |
| C2. API changelog는 Sol 가격을 input $2, cached input $0.20, output $10 per 1M tokens로, Luna 가격을 input $0.10, cached input $0.01, output $0.50 per 1M tokens로 적었습니다. | E2 · P1 | API changelog와 발표문 가격표로 확인했습니다. 장문 prompt, cache write, tier별 가격은 별도 가격표가 필요합니다. |
| C3. OpenAI는 GPT-6 계열의 prompt caching이 eligible shared prefix를 30분 안에 재사용하고 cached input token에 최대 90% 할인을 준다고 설명했습니다. | E2 · P1 | prompt caching 발표문과 API guide로 확인했습니다. 실제 cache hit rate와 latency는 workload와 request shape에 따라 달라집니다. |
| C4. GPT-6 이후 모델에서는 `configuration_update` input item을 append해 reasoning effort를 바꾸면서 앞쪽 cache prefix를 보존할 수 있다고 문서화되어 있습니다. | E2 · P1 | Prompt caching API guide로 확인했습니다. 편집국은 live request로 동작을 재현하지 않았습니다. |
| C5. cache diagnostics는 비교 response를 기준으로 cache hit/miss 여부와 miss reason, missed token 추정치를 제공할 수 있다고 문서화되어 있습니다. | E2 · P1 | Prompt cache diagnostics API guide로 확인했습니다. diagnostics token count는 실제 billing usage가 아니라 진단값입니다. |
| C6. GPT-6 Astra system card의 2026년 9월 22일 업데이트는 GPT-6 Sol과 Luna 부록을 추가했고, 두 모델을 cybersecurity와 biological·chemical domain에서 High capability로 다룬다고 설명했습니다. | E2 · P1 | OpenAI Deployment Safety Hub의 GPT-6 Astra system card change log와 Sol·Luna 부록으로 확인했습니다. 외부 독립 audit이나 재실행 결과는 확보하지 않았습니다. |
| C7. OpenAI의 benchmark와 비용 대비 성능 주장은 vendor-authored claim이며, 이 글은 이를 독립 순위 결론으로 올리지 않습니다. | E2 · P1 | 발표문, API changelog, system card를 대조해 분류했습니다. benchmark를 같은 harness로 재실행하지 않았습니다. |

## 출처

1. OpenAI, `Introducing GPT-6 Sol and Luna`, 2026-09-22: https://openai.com/index/introducing-gpt-6-sol-and-luna/
2. OpenAI API, `Changelog`, September 2026 entries: https://developers.openai.com/api/docs/changelog
3. OpenAI, `Better prompt caching for GPT-6`, 2026-09-22: https://openai.com/index/better-prompt-caching-for-gpt-6/
4. OpenAI API, `Prompt caching`: https://developers.openai.com/api/docs/guides/prompt-caching
5. OpenAI API, `Prompt cache diagnostics`: https://developers.openai.com/api/docs/guides/prompt-caching/diagnostics
6. OpenAI Deployment Safety Hub, `GPT-6 Astra System Card`, Sol·Luna appendix added 2026-09-22: https://deploymentsafety.openai.com/gpt-6-astra
