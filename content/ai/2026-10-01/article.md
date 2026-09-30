---
edition: ai
decision: publish-candidate
title: "GPT-6.1 Sol 공개 - 긴 코딩 작업을 자주 돌리기 위한 중간 모델"
date: 2026-10-01
subject: "GPT-6.1 Sol, released 2026-09-29"
summary: "OpenAI는 GPT-6.1 Sol을 공개하며 Astra에 가까운 복잡 작업 능력을 더 낮은 토큰 단가와 긴 context window로 제공한다고 밝혔습니다. 모델 문서, API changelog, GPT-6 가이드와 system card addendum으로 출시 조건과 평가 방법은 확인할 수 있지만, 독립 성능 재현이나 실제 비용 절감은 각 팀의 workload로 다시 확인해야 합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["없음"]
---

OpenAI가 2026년 9월 29일 GPT-6.1 Sol을 API에 공개했습니다. 이번 변화의 초점은 가장 강한 모델 하나를 더 비싸게 쓰는 데 있지 않습니다. 긴 코딩 작업과 computer use 작업을 더 자주 돌릴 수 있도록 모델 선택지를 다시 나눈 데 있습니다. OpenAI는 GPT-6.1 Sol이 복잡한 코딩, computer use, 전문 업무에서 GPT-6 Astra에 가까운 성능을 더 낮은 비용으로 제공한다고 설명했습니다.

SW 엔지니어에게 중요한 변화는 모델 이름보다 실행 단위입니다. GPT-6.1 Sol은 `gpt-6.1-sol` 모델 ID로 Responses API와 Chat Completions API에서 쓸 수 있습니다. 다만 문서는 도구 호출에는 Responses API를 쓰라고 안내합니다. 모델 문서에 따르면 이 모델은 입력 105만 토큰 context window, 최대 입력 92만2000 토큰, 최대 출력 12만8000 토큰을 지원합니다. 긴 코드베이스, 문서 묶음, 브라우저 조작 흐름을 한 요청 안에서 다루는 agent 제품에는 이 한도가 모델 선택의 실제 경계가 됩니다.

이 글의 결론은 좁습니다. GPT-6.1 Sol이 모든 코딩 작업에서 Astra나 경쟁 모델을 독립적으로 이겼다는 뜻이 아닙니다. 공개된 원문으로 확인할 수 있는 것은 OpenAI가 Sol 계열을 Astra보다 낮은 비용의 복잡 작업 모델로 재배치했다는 점입니다. API 문서는 그에 맞춰 context, reasoning effort, tool calling, 가격, 안전 평가 조건을 제시합니다.

## Astra와 Luna 사이의 선택지가 커졌습니다

GPT-6 계열 문서는 Astra, GPT-6.1 Sol, Luna를 서로 다른 용도에 둡니다. Astra는 가장 어려운 추론과 전문 업무용이고, Luna는 범위가 좁고 자주 실행되는 자동화용입니다. GPT-6.1 Sol은 그 사이에서 복잡하지만 비용을 관리해야 하는 작업을 맡습니다.

이 구분은 agent 운영에서 실용적입니다. 예를 들어 작은 코드 수정, 단순 분류, 짧은 데이터 추출은 Luna나 더 낮은 reasoning effort가 맞을 수 있습니다. 반대로 여러 저장소를 읽고, 브라우저를 열고, 보고서나 코드를 여러 번 고치는 작업은 더 강한 모델이 필요합니다. GPT-6.1 Sol은 이런 작업을 Astra로 전부 보내기 전에 먼저 시험할 수 있는 중간 선택지로 제시됐습니다.

OpenAI의 model selection 문서는 GPT-6.1 Sol을 “비용이 중요한 복잡 프로젝트”에 쓰라고 안내합니다. 재무 결과에서 발표 자료를 만들거나 제품 brief에서 웹사이트를 만드는 작업을 예로 듭니다. 이 설명은 모델이 단일 답변보다 여러 단계의 산출물을 만드는 흐름에 맞춰졌다는 신호입니다.

## 긴 입력은 cache 설계와 함께 봐야 합니다

GPT-6.1 Sol의 가격 구조는 agent 비용을 보는 방식을 바꿉니다. 모델 문서는 표준 가격을 입력 100만 토큰당 2달러, cached input 100만 토큰당 0.10달러, cache write 100만 토큰당 2.50달러, 출력 100만 토큰당 10달러로 제시합니다. cached input은 uncached input 가격의 5%입니다.

이 가격은 긴 context window와 함께 봐야 합니다. 긴 코드베이스나 사내 문서 묶음을 매번 처음부터 넣으면 입력 비용이 커집니다. 반대로 같은 prompt prefix와 큰 문맥을 반복해서 쓰는 agent라면 cache hit가 비용을 크게 줄일 수 있습니다. GPT-6.1 Sol이 “싸다”는 말은 단순한 토큰 단가보다 cache를 잘 맞추는 제품 설계가 있을 때 성립합니다.

문서에는 27만2000 토큰을 넘는 prompt에는 더 높은 가격이 적용된다는 조건도 있습니다. 그래서 100만 토큰 context window는 “항상 싸게 많이 넣어도 된다”는 뜻이 아닙니다. 긴 입력을 유지해야 하는 작업인지, 검색이나 파일 요약으로 줄일 수 있는 작업인지, cache boundary를 안정적으로 유지할 수 있는지가 비용 설계의 핵심이 됩니다.

## 도구 호출은 Responses API 쪽으로 모입니다

GPT-6.1 Sol은 Chat Completions도 지원하지만, 도구 호출은 Responses API를 쓰라고 문서가 안내합니다. 모델 문서는 web search, file search, image generation, code interpreter, hosted shell, apply patch, skills, computer use, MCP, tool search를 Responses API에서 지원하는 도구로 열거합니다.

이 변화는 agent runtime을 짜는 팀에 직접 닿습니다. 모델만 바꾸는 migration이라 해도 API route와 tool call 구조를 그대로 둘 수 없습니다. 기존에 Chat Completions에서 함수 호출을 중심으로 만든 흐름은 Responses API로 옮기면서 event 처리, tool result 반환, 중간 상태 저장, 실패 복구 방식을 다시 봐야 합니다.

GPT-6 가이드는 GPT-6 계열의 새 기능으로 async tool calling, mid-turn steering, reasoning effort 변경, misalignment monitoring을 설명합니다. async tool calling은 애플리케이션이 도구를 실행하는 동안 모델이 다른 추론이나 독립 작업을 계속할 수 있게 하는 방식입니다. mid-turn steering은 모델이 응답하는 중간에 새 지시를 넣는 기능입니다. 긴 작업을 끊지 않고 조정할 수 있다는 점에서 agent 제품의 체감 품질을 바꿀 수 있습니다.

## reasoning effort는 비용과 실패율을 함께 바꾸는 설정입니다

GPT-6.1 Sol은 `reasoning.effort`에서 `low`, `medium`, `high`, `xhigh`, `max`를 지원합니다. `none`과 `minimal`은 지원하지 않습니다. 기존 요청이 `minimal`이나 `none`에 의존했다면 문서가 안내하듯 `low`부터 대표 작업으로 비교해야 합니다.

이 설정은 단순한 품질 슬라이더가 아닙니다. 높은 effort는 더 많은 추론과 점검을 기대하게 하지만, 더 많은 출력과 긴 실행 시간, 더 높은 비용으로 이어질 수 있습니다. 낮은 effort는 반복 자동화에는 맞을 수 있지만, 여러 파일을 오가는 버그 수정이나 브라우저 조작처럼 실패 비용이 큰 작업에는 부족할 수 있습니다.

따라서 GPT-6.1 Sol을 도입하는 팀은 “모델 교체”보다 “라우팅 정책”을 먼저 정해야 합니다. 작은 수정은 낮은 effort로 시작하고, 테스트 실패나 불확실한 설계 판단이 나오면 높은 effort나 Astra로 올릴 수 있습니다. 같은 모델 안에서도 effort와 cache, tool call 구조를 함께 조정해야 실제 비용이 보입니다.

## 안전 평가는 높게 잡혔지만 원자료는 제한적입니다

OpenAI의 system card addendum은 GPT-6.1 Sol을 cybersecurity에서 Critical capability, biological and chemical 영역에서 High capability로 취급한다고 적습니다. 이에 따라 GPT-6 Astra와 같은 safeguards stack을 적용한다고 설명합니다. 이 내용은 “성능이 좋아졌다”는 발표와 함께 봐야 합니다. 코딩과 computer use 능력이 커질수록 보안 점검에는 유용해지지만, 악용 가능한 작업에도 가까워지기 때문입니다.

Addendum은 여러 내부 평가 수치도 공개합니다. 예를 들어 ExploitGym에서 GPT-6.1 Sol은 intended-vulnerability success rate 35.1% per attempt를 기록했고, GPT-6 Astra 42.4%, GPT-6 Sol 22.1%, GPT-5.6 Sol 30.3%와 비교됐다고 설명합니다. 또 SEC-Bench Pro에서는 pass@1 78.8%로, Astra보다 낮고 GPT-5.6 Sol과 비슷한 peak 점수라고 적었습니다.

다만 이 수치들은 OpenAI가 설계하고 공개한 평가입니다. 일부는 내부 평가이고, 원 로그와 전체 재현 절차가 공개돼 있지 않습니다. 그래서 이 글은 안전 등급과 safeguard 적용 사실을 E2 수준의 공개 기술 근거로 다룹니다. 실제 배포 환경에서 위험이 줄었는지, 경쟁 모델보다 안전한지는 독립 결론으로 쓰지 않습니다.

## 한국 개발팀은 세 가지를 먼저 재야 합니다

한국의 제품팀이 GPT-6.1 Sol을 검토한다면 첫 번째 질문은 비용입니다. 긴 context를 자주 넣는 workflow에서 cached input이 실제로 얼마나 맞는지, 27만2000 토큰을 넘는 요청이 얼마나 생기는지, 출력 토큰이 어디서 늘어나는지 로그로 봐야 합니다. 토큰 단가만 보고 예산을 잡으면 agent가 도구를 여러 번 부르는 실제 비용을 놓칠 수 있습니다.

두 번째는 데이터 경계입니다. 모델 문서에 따르면 GPT-6.1 Sol은 US와 EU data residency를 지원하지만, fast mode는 EU data residency에서 쓸 수 없습니다. 한국 기업은 자사 계약, 지역 처리 조건, zero data retention, BAA 같은 요구와 service tier가 충돌하지 않는지 확인해야 합니다.

세 번째는 실패 복구입니다. 컴퓨터 사용과 hosted shell, apply patch 같은 도구를 붙인 agent는 모델 답변이 아니라 외부 상태를 바꿉니다. tool call이 비동기로 움직이고 중간 지시를 받을 수 있을수록, 감사 로그와 승인 흐름, rollback 조건이 더 중요해집니다. GPT-6.1 Sol의 의미는 더 강한 답변 하나보다, 이런 긴 작업을 어떤 가격과 안전장치로 반복할 수 있느냐에 있습니다.

## 확인된 변화와 남은 검증 과제

GPT-6.1 Sol은 이번 AI판 기준을 넘는 기사 후보입니다. 최신 모델 발표이고, API changelog, 모델 문서, GPT-6 가이드, system card addendum이 서로 맞물립니다. 개발자는 이 문서들로 model routing, Responses API migration, cache 비용, reasoning effort, data residency를 검토할 수 있습니다. 선정 점수는 9점입니다.

하지만 근거 등급은 E2에 머뭅니다. 공개 원문은 출시 사실, API 조건, 평가 설계 일부, safety classification을 확인하기에 충분합니다. 반대로 독립 benchmark 재현, 실제 업무별 비용 절감, safeguards 효과의 외부 검증은 아직 없습니다. 그래서 이 글은 GPT-6.1 Sol을 “Astra 대체”로 단정하지 않고, 긴 코딩·컴퓨터 사용 agent를 더 자주 돌리기 위한 중간 모델로 설명합니다.

## 이해상충과 취재 조건

이 글은 공개 웹 문서만 읽어 작성했습니다. OpenAI, Anthropic, Google, Qwen, DeepSeek, Mistral 또는 다른 공급자로부터 계정, 크레딧, 장비, 브리핑, 엠바고 자료를 제공받지 않았습니다. 이해상충은 확인된 바 없습니다.

## 근거 원장

| claim_id | 주장 | 근거 | 등급 | 한계 |
| --- | --- | --- | --- | --- |
| C1 | OpenAI는 2026년 9월 29일 GPT-6.1 Sol을 `gpt-6.1-sol`로 공개했고, 복잡한 코딩과 전문 업무에서 Astra보다 낮은 비용의 모델로 설명했습니다. | OpenAI API changelog, GPT-6.1 Sol model page, OpenAI announcement | E2 | OpenAI가 자기 모델을 설명한 원문이며 독립 성능 비교가 아닙니다. |
| C2 | GPT-6.1 Sol은 105만 토큰 context window, 최대 입력 92만2000 토큰, 최대 출력 12만8000 토큰을 지원한다고 모델 문서가 적습니다. | GPT-6.1 Sol model page | E2 | 실제 사용 한도는 계정, tier, rate limit, 지역 처리 조건에 따라 달라질 수 있습니다. |
| C3 | 표준 가격은 입력 100만 토큰당 2달러, cached input 0.10달러, cache write 2.50달러, 출력 10달러이며, 27만2000 토큰 초과 prompt에는 더 높은 가격이 적용됩니다. | GPT-6.1 Sol model page, API changelog | E2 | 가격 문서는 갱신될 수 있고 실제 비용은 cache hit, output length, tool call에 좌우됩니다. |
| C4 | GPT-6.1 Sol은 `low`, `medium`, `high`, `xhigh`, `max` reasoning effort를 지원하고 `none`과 `minimal`은 지원하지 않습니다. | GPT-6.1 Sol model page, GPT-6 guide | E2 | effort별 품질·비용 차이는 공개 문서만으로 일반화할 수 없습니다. |
| C5 | 도구 호출은 Responses API 사용이 권장되며, 모델 문서는 web search, file search, code interpreter, hosted shell, apply patch, computer use, MCP 등 지원 도구를 열거합니다. | GPT-6.1 Sol model page, GPT-6 guide | E2 | 도구별 실제 사용 가능성은 계정 권한, 제품, runtime 설정에 따라 달라질 수 있습니다. |
| C6 | OpenAI system card addendum은 GPT-6.1 Sol을 cybersecurity Critical, biological and chemical High capability로 취급하고 Astra와 같은 safeguards stack을 적용한다고 설명합니다. | GPT-6.1 Sol system card addendum | E2 | 평가 원자료와 production safeguard 효과는 독립적으로 재현하지 않았습니다. |

## 출처

- OpenAI, “GPT-6.1 Sol,” 2026-09-29. https://openai.com/index/introducing-gpt-6-1-sol/
- OpenAI API Docs, “Changelog,” September 29, 2026 entry. https://developers.openai.com/api/docs/changelog
- OpenAI API Docs, “GPT-6.1 Sol model page.” https://developers.openai.com/api/docs/models/gpt-6.1-sol
- OpenAI API Docs, “Using GPT-6.” https://developers.openai.com/api/docs/guides/latest-model
- OpenAI API Docs, “Model selection.” https://developers.openai.com/api/docs/guides/model-selection
- OpenAI Deployment Safety Hub, “Addendum to GPT-6 Astra System Card: GPT-6.1 Sol.” https://deploymentsafety.openai.com/gpt-6-1-sol
- Anthropic, “Claude Sonnet 5.5,” reviewed as a same-week model alternative. https://www.anthropic.com/claude-sonnet-5-5
- Google AI for Developers, “Gemini API release notes,” reviewed as an alternative. https://ai.google.dev/gemini-api/docs/changelog
- Mistral Docs, “Changelog,” reviewed as an alternative. https://docs.mistral.ai/resources/changelogs
- Qwen Hugging Face organization, recent models reviewed as alternatives. https://huggingface.co/Qwen/models
- DeepSeek GitHub organization, recent repositories reviewed as alternatives. https://github.com/deepseek-ai
