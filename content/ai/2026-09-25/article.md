---
edition: ai
decision: publish-candidate
title: "Claude Opus 5.5 공개 - 긴 에이전트 작업의 API 계약이 달라졌습니다"
date: 2026-09-25
subject: "Anthropic Claude Opus 5.5, released 2026-09-22"
summary: "Claude Opus 5.5는 긴 코딩 에이전트 작업과 지식 업무를 겨냥한 새 Opus 모델입니다. 낮아진 가격보다 더 큰 변화는 adaptive thinking이 항상 켜지고, thinking block 보존, tool choice, computer use toolset 처리 방식이 달라졌다는 점입니다. 성능 우위는 Anthropic이 공개한 평가와 early tester 사례에 머물지만, API 문서와 migration guide만으로도 기존 Opus 5 통합을 점검해야 할 이유는 충분합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Anthropic은 Claude Opus 5.5의 개발·배포 주체이며 발표문, system card, API 문서, release note와 migration guide를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Anthropic이 Claude Opus 5.5를 공개했습니다. 이 모델은 긴 코딩 에이전트 작업과 지식 업무를 겨냥합니다. 개발자에게 더 중요한 변화는 성능표의 순위보다 API 계약입니다. Opus 5에서 쓰던 일부 요청을 그대로 보내면 400 error가 나고, 에이전트가 중간 진행 상황을 보여 주는 방식도 달라질 수 있습니다.

Opus 5.5는 `claude-opus-5-5`라는 고정 모델 ID로 제공됩니다. 문서상 context window는 1M token이고, 일반 max output은 128K token입니다. 가격은 input 100만 token당 4달러, output 100만 token당 20달러로 적혀 있습니다. Claude Opus 5보다 단가는 낮지만, 항상 켜진 thinking이 output token 예산과 청구액에 포함되므로 실제 비용은 workload별로 다시 재야 합니다.

이 글의 중심 주장은 좁습니다. Opus 5.5는 Anthropic이 긴 에이전트 작업용으로 낸 새 모델입니다. 공개 문서는 기존 Opus 5 통합에서 request schema, thinking block 처리, tool 호출 정책, computer use toolset을 다시 점검해야 함을 보여 줍니다. 다만 Opus 5.5가 경쟁 모델보다 일반적으로 낫다는 결론은 내리지 않습니다. 성능 비교에는 Anthropic이 작성한 결과와 일부 외부 benchmark 출처가 섞여 있으며, 이 글에서는 API와 migration 조건을 확인된 변화로 다룹니다.

## 항상 켜진 thinking이 요청 형식을 바꿉니다

이전 모델에서는 작업에 따라 thinking을 끄거나 수동 budget을 줄 수 있었습니다. Opus 5.5에서는 adaptive thinking이 항상 켜져 있습니다. `thinking: {"type": "disabled"}`를 보내거나 수동 budget을 지정하면 문서상 `invalid_request_error`가 납니다. Anthropic은 thinking의 깊이를 `output_config.effort`로 조절하라고 안내합니다.

이 차이는 단순한 옵션 이름 변경이 아닙니다. 매 turn마다 thinking block이 먼저 나올 수 있고, `max_tokens`는 thinking과 최종 text를 함께 제한합니다. 기존 코드가 첫 content block을 곧바로 사용자에게 보여 주거나, 출력 token 예산을 답변 text 기준으로만 잡았다면 깨질 수 있습니다. 문서는 content block을 위치가 아니라 `type`으로 골라 처리하라고 설명합니다.

에이전트 운영에서도 비용 계산이 바뀝니다. thinking text가 사용자에게 보이지 않아도 token은 output token으로 계산됩니다. 따라서 Opus 5에서 thinking을 꺼 두고 쓰던 workflow는 모델 ID만 바꿔도 더 많은 output token을 쓸 수 있습니다. 새 모델을 넣기 전에 effort level, `max_tokens`, timeout, fallback 기준을 함께 재측정해야 합니다.

## thinking block은 대화 이력에 묶입니다

Opus 5.5 문서에서 가장 실무적인 부분은 thinking block 보존 조건입니다. Opus 5.5가 만든 thinking block은 모델과 대화 앞부분에 묶입니다. system prompt, tools, 이전 message가 바뀐 뒤 같은 block을 다시 보내면 일부 계정에서는 요청이 실패할 수 있습니다. Anthropic은 대화 이력을 뒤에 덧붙이는 append-only 흐름을 유지하고, 지시나 도구 변경은 mid-conversation system message로 처리하라고 안내합니다.

이 제약은 긴 에이전트 작업에서 중요합니다. 에이전트는 몇 시간 동안 repository를 읽고, 도구를 부르고, 중간 계획을 이어 갑니다. 이때 conversation compaction, tool schema 변경, 모델 routing을 섞으면 이전 reasoning을 그대로 재사용할 수 있는지 확인해야 합니다. 문서는 Opus 5에서 Opus 5.5로 오거나, Opus 5.5에서 Fable 5.1·Mythos 5.1로 올라가는 일부 경우에는 reasoning을 유지할 수 있다고 설명합니다. 반대로 Fable·Mythos에서 Opus 5.5로 내려오는 경우나 다른 모델로 가는 경우에는 block이 읽히지 않을 수 있습니다.

쉽게 말해 Opus 5.5는 긴 작업의 상태를 더 엄격하게 이어 가도록 만듭니다. 그만큼 “대화를 조금 고쳐서 다시 보낸다”는 관행은 위험해집니다. 프롬프트 cache와 preserved thinking을 같이 쓰는 팀은 대화 이력을 수정하는 코드가 있는지 먼저 찾아야 합니다.

## 강제 tool 호출과 오래된 computer use 도구는 그대로 못 씁니다

Opus 5.5는 `tool_choice`에서 `any`나 특정 `tool` 강제를 지원하지 않습니다. 문서에 따르면 이런 요청은 400 error를 냅니다. Anthropic은 `auto`와 `none`을 쓰고, schema가 중요한 경우 strict tool use나 structured output을 쓰라고 안내합니다. 모델이 꼭 도구를 호출해야 하는 상황은 prompt와 schema 설계로 유도해야 합니다.

computer use도 옮겨야 할 부분이 있습니다. Claude API와 Google Cloud에서 Opus 5.5는 `computer_20251124` 도구를 받지 않고 `computer_toolset_20260801` toolset을 요구합니다. 이 변경은 desktop이나 browser 조작 에이전트를 직접 구현한 팀에 특히 중요합니다. 도구 이름만 바꾸는 문제가 아니라 member `tool_use` block, batch action, `toolset_name` 처리까지 바뀔 수 있습니다.

이런 API 제약은 불편하지만 이유가 있습니다. 긴 에이전트 작업은 모델이 도구를 어떤 순서로 부르고, 중간 reasoning을 어떻게 보존하고, 안전 classifier가 언제 끼어드는지에 따라 결과가 크게 달라집니다. Anthropic은 Opus 5.5를 model-only 교체보다 agent runtime과 함께 쓰도록 설계한 셈입니다.

## 진행 상황을 보여 주던 UI도 조용해질 수 있습니다

Opus 5.5는 도구 호출 사이의 짧은 진행 문구를 text block이 아니라 thinking block으로 돌려줄 수 있습니다. 기본 `display` 설정에서는 thinking field가 비어 있습니다. 기존 UI가 그 중간 text를 사용자에게 보여 주던 구조라면 갑자기 조용해질 수 있습니다. 요청이 실패하는 것은 아니어서 monitoring 없이는 놓치기 쉽습니다.

이 변화는 사용자 경험과 운영 관측에 영향을 줍니다. 긴 refactor, spreadsheet 분석, browser agent 작업은 몇 분 이상 걸릴 수 있습니다. 사용자는 에이전트가 멈췄는지, 도구를 부르는 중인지, 다음 단계로 넘어갔는지 알아야 합니다. Opus 5.5로 옮길 때는 streaming UI가 text block만 보는지, thinking display 값을 따로 설정해야 하는지 확인해야 합니다.

같은 맥락에서 refusal 처리도 봐야 합니다. 문서는 Opus 5.5가 cybersecurity classifier에 더해 biology safety classifier를 쓰고, 내부 reasoning을 response text로 재현하라는 요청은 `reasoning_extraction` category로 거절될 수 있다고 설명합니다. 거절은 HTTP 200과 `stop_reason: "refusal"`로 올 수 있으므로, 단순 성공 응답으로 처리하면 안 됩니다.

## 가격 인하는 총비용 인하와 다릅니다

Anthropic은 Opus 5.5가 Opus 5보다 input·output token 가격이 낮고, cache read도 더 싸다고 문서화했습니다. 발표문은 typical workload에서 비용이 40% 낮다고 말합니다. 또 fast mode를 Claude API 연구 preview로 제공합니다. 가격표만 보면 Opus tier를 더 자주 쓸 수 있는 변화입니다.

하지만 긴 에이전트 작업의 총비용은 token 단가만으로 정해지지 않습니다. 항상 켜진 thinking, effort level, 도구 호출 횟수, 실패한 tool loop, retry, fallback, cache hit rate가 모두 비용을 바꿉니다. 예를 들어 thinking을 끄고 짧은 답만 받던 기존 Opus 5 workflow는 단가가 내려가도 output token이 늘 수 있습니다. 반대로 큰 코드 migration처럼 planning이 비용의 대부분인 작업은 더 낮은 effort와 cache read가 실제 이득으로 이어질 수 있습니다.

따라서 도입 판단의 단위는 “100만 token당 가격”이 아니라 “한 issue를 merge 가능한 patch로 끝내는 데 든 총비용과 시간”이어야 합니다. migration 후에는 같은 repository, 같은 test gate, 같은 timeout으로 Opus 5와 Opus 5.5를 나란히 돌려야 합니다. benchmark 표는 출발점일 뿐입니다.

## 성능과 안전성은 공개 조건 안에서만 읽어야 합니다

Anthropic 발표문은 Opus 5.5가 agentic coding, computer use, knowledge work에서 강해졌고, Opus 5보다 비용이 낮다고 설명합니다. system card와 model card 목록도 Opus 5.5 문서를 공개 대상으로 올렸습니다. 다만 성능표에는 Anthropic 자체 benchmark, early tester 사례, 외부 leaderboard에서 가져온 수치가 섞입니다. 경쟁 모델의 harness와 effort, fallback, safeguard 처리 조건이 완전히 같은지는 기사 근거만으로 확인할 수 없습니다.

그래서 이 글은 “Opus 5.5가 최고”라고 쓰지 않습니다. 확인할 수 있는 것은 Anthropic이 공개한 모델 ID, context와 output limit, always-on adaptive thinking, migration 제약, pricing, toolset 요구 조건입니다. 개발자가 바로 해야 할 일도 그 범위에 있습니다. 기존 integration에서 rejected parameter를 쓰는지, thinking block을 그대로 보존하는지, forced tool use와 computer use 도구를 어떻게 처리하는지 검사하는 일입니다.

한국 독자에게는 한 가지가 더 남습니다. 긴 agent coding benchmark는 대체로 영어 repository와 영어 업무 문서 중심입니다. 한국어 요구사항, 국내 서비스 로그, 한국어 표·문서, 개인정보 masking, 사내 도구 권한 모델에서 같은 비용과 안전성이 나오는지는 별도 검증이 필요합니다.

## 이해상충과 취재 조건

Anthropic은 Claude Opus 5.5의 개발·배포 주체이며 발표문, system card, API 문서, release note와 migration guide를 작성했습니다. 출시 사실, model ID, API spec, migration 제약, 가격과 availability는 Anthropic 원문으로 확인했습니다. 성능 비교와 early tester 사례는 발표 주체가 제시한 조건 안에서만 설명했고, 독립 우월성 결론으로 쓰지 않았습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 Reddit 같은 커뮤니티 신호는 후보 발견과 반응 확인에만 사용했고, 기사 사실은 Anthropic 공식 발표, platform docs, release note, system card 목록으로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Anthropic은 2026년 9월 22일 Claude Opus 5.5를 공개했고, `claude-opus-5-5`를 Claude API, AWS, Google Cloud, Microsoft Foundry 등에서 제공한다고 문서화했습니다. | E2 · P1 | 발표문, platform release note, model page로 확인했습니다. 계정별 실제 availability는 API 호출로 재현하지 않았습니다. |
| C2. Claude Opus 5.5는 1M token context window, 128K max output, input 100만 token당 4달러와 output 100만 token당 20달러 pricing을 문서화했습니다. | E2 · P1 | model page와 release note로 확인했습니다. 실제 청구액은 effort, thinking token, cache, batch, tool 사용량에 따라 달라집니다. |
| C3. Opus 5.5에서는 adaptive thinking이 항상 켜져 있고, `thinking: disabled`나 수동 thinking budget은 400 error를 낸다고 문서화되어 있습니다. | E2 · P1 | What's new와 migration guide로 확인했습니다. 편집국은 live request로 error를 재현하지 않았습니다. |
| C4. Opus 5.5의 thinking block은 모델과 대화 앞부분에 묶이며, prompt나 tools가 바뀐 뒤 replay하면 일부 조건에서 error가 날 수 있다고 문서화되어 있습니다. | E2 · P1 | What's new와 migration guide로 확인했습니다. 계정 생성일, beta header, cloud platform별 차이는 실제 tenant에서 재현하지 않았습니다. |
| C5. Opus 5.5는 forced tool use인 `tool_choice: any`와 특정 `tool` 강제를 지원하지 않으며, Claude API와 Google Cloud에서는 `computer_20251124` 대신 `computer_toolset_20260801`을 요구한다고 문서화되어 있습니다. | E2 · P1 | What's new와 migration guide로 확인했습니다. Amazon Bedrock의 예외처럼 platform별 차이가 있습니다. |
| C6. 도구 호출 사이의 진행 문구가 text block이 아니라 thinking block으로 올 수 있고, 기본 display에서는 사용자에게 보이지 않을 수 있다고 문서화되어 있습니다. | E2 · P1 | What's new와 migration guide로 확인했습니다. UI 영향은 각 client의 streaming 처리 방식에 따라 달라집니다. |
| C7. Anthropic의 성능·비용 우위 설명은 발표문과 system card에 근거한 vendor-authored claim이며, 이 글은 이를 독립 순위 결론으로 올리지 않습니다. | E2 · P1 | 발표문, system card 목록, model page로 확인했습니다. 공개 benchmark를 같은 harness로 재실행하지 않았습니다. |

## 출처

1. Anthropic, `Claude Opus 5.5`, 2026-09-22: https://www.anthropic.com/claude-opus-5-5
2. Claude Platform Docs, `Claude Platform release notes`: https://platform.claude.com/docs/en/release-notes/overview
3. Claude Platform Docs, `Claude Opus 5.5`: https://platform.claude.com/docs/en/models/opus-5-5/overview
4. Claude Platform Docs, `What's new in Claude Opus 5.5`: https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5
5. Claude Platform Docs, `Migrating to Claude Opus 5.5`: https://platform.claude.com/docs/en/models/opus-5-5/migration-guide
6. Anthropic, `Model system cards`: https://www.anthropic.com/system-cards
