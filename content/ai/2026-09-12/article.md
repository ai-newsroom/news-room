---
edition: ai
decision: publish-candidate
title: "Claude Fable 5.1 공개 - 긴 agent 대화에서 cache와 thinking을 유지하는 규칙이 바뀌었습니다"
date: 2026-09-12
subject: "Claude Fable 5.1 and Claude Mythos 5.1 API release, 2026-09-01"
summary: "Anthropic의 Fable 5.1은 고성능 모델 하나를 더한 발표라기보다 agent runtime 규칙을 바꾼 release에 가깝습니다. 1M token context와 낮아진 cache read 가격, append-only history에 묶인 thinking block, forced tool use 제거, per-message effort가 긴 coding agent와 업무 agent의 비용·오류 처리 방식을 바꿉니다. 공개 문서로 API 동작과 migration 조건은 확인되지만, 성능 우위는 Anthropic의 평가와 파트너 사례에 머뭅니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Anthropic은 Claude Fable 5.1과 Claude Mythos 5.1의 개발·배포 주체이며 발표문, API 문서, release note와 benchmark 설명을 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Anthropic이 2026년 9월 1일 Claude Fable 5.1과 Claude Mythos 5.1을 공개했습니다. Fable 5.1은 일반 고객이 Claude API와 주요 cloud platform에서 쓸 수 있는 모델입니다. Mythos 5.1은 같은 기반 모델에 더 완화된 safeguard를 적용한 버전으로, Project Glasswing 승인 고객에게만 제공됩니다. 이 발표에서 SW 엔지니어가 먼저 봐야 할 변화는 benchmark 순위가 아니라 긴 agent 대화를 처리하는 API 규칙입니다.

Fable 5.1은 1M token context와 128K output을 지원하며, 긴 coding agent와 문서·spreadsheet·slide 작업을 겨냥합니다. 하지만 이전 모델 이름만 바꾼다고 모든 agent harness가 그대로 좋아지는 것은 아닙니다. Anthropic 문서는 forced tool use 제거, thinking block 보존 규칙, cache read 가격 인하, per-message effort, turn-scoped system message를 migration 항목으로 묶어 설명합니다.

그래서 이 글의 중심 주장은 좁습니다. Fable 5.1은 "가장 뛰어난 모델"이라고 검증된 사례가 아닙니다. 긴 agent session에서 history를 어떻게 유지할지, cache를 어떻게 살릴지, tool call을 어떻게 유도할지를 바꾸는 release입니다. 성능 수치와 파트너 사례는 Anthropic이 공개한 자료이므로, 제품 선택의 출발점으로만 봐야 합니다.

## 도구 호출을 강제로 시키던 코드를 바꿔야 합니다

Claude Fable 5.1과 Mythos 5.1은 `tool_choice`의 `any`와 특정 `tool` 강제를 지원하지 않습니다. Anthropic은 이 설정이 들어오면 400 `invalid_request_error`를 반환한다고 문서화했습니다. `auto`와 `none`은 그대로 지원됩니다.

이 변화는 schema가 맞는 tool call을 얻으려고 매 turn마다 도구 호출을 강제하던 agent 코드에 영향을 줍니다. Fable 5.1에서는 도구를 반드시 써야 할 때 prompt에 조건을 분명히 쓰는 쪽을 권합니다. schema 검증은 `strict: true` 도구나 structured output으로 옮기라고 안내합니다. 특정 turn에서 application policy 때문에 도구 호출이 필요하다면, top-level system prompt를 바꾸기보다 mid-conversation system message를 추가하는 방식이 제시되어 있습니다.

이전 방식의 문제는 모델이 reasoning을 거치지 않고 곧바로 도구를 부르게 된다는 점이었습니다. Anthropic 문서는 forced tool call이 thinking을 생략하게 만들고, 모델이 tool argument 안에 작업 과정을 밀어 넣어 argument 품질을 낮춘다고 설명합니다. 즉 이번 변경은 개발자가 통제력을 조금 잃는 대신, 모델이 도구 입력을 만들기 전에 생각할 공간을 보장하려는 API 설계입니다.

## thinking block은 앞선 대화와 함께 보존해야 합니다

Fable 5.1의 더 큰 migration 포인트는 thinking block입니다. Anthropic은 Fable 5.1이 Claude Opus 5, Fable 5, Mythos 5와 이전 모델의 thinking block을 읽을 수 있지만, 이전 모델은 Fable 5.1이 만든 block을 읽지 못한다고 설명합니다. router나 fallback이 오래된 모델로 이동하면 해당 block은 떨어지고, beta header를 쓰면 `input_transformations`로 어떤 block이 빠졌는지 볼 수 있습니다.

또 하나의 제약은 history binding입니다. Fable 5.1의 thinking block은 그 block이 만들어지기 전의 `system`, `tools`, `messages` prefix에 묶입니다. 개발자가 이전 turn을 삭제하거나 순서를 바꾸거나, system prompt와 tools 배열을 다시 만들면 다음 요청에서 block이 유효하지 않을 수 있습니다. 문서에 따르면 새 계정에는 2026년 8월 31일 이후 이 검사가 기본 적용됩니다.

긴 agent를 직접 구현하는 팀에는 이 규칙이 중요합니다. 많은 agent runtime은 context를 줄이기 위해 중간 turn을 잘라 내거나, 매 요청마다 system prompt에 현재 날짜와 작업 상태를 다시 씁니다. Fable 5.1에서는 이런 변경이 prompt cache와 thinking 보존을 동시에 깨뜨릴 수 있습니다. Anthropic이 권하는 방향은 history를 append-only로 유지하고, 바뀌는 지시사항은 mid-conversation system message로 추가하며, 오래된 context 정리는 server-side compaction이나 context editing에 맡기는 것입니다.

## cache 가격 인하는 긴 session에서 효과가 커집니다

Fable 5.1의 base input 가격은 100만 token당 10달러, output은 50달러로 Fable 5와 같습니다. 달라진 것은 cache read입니다. Anthropic 문서는 Fable 5.1과 Mythos 5.1의 cache read를 100만 token당 0.25달러로 낮췄고, 이는 base input 가격의 0.025배라고 설명합니다. 다른 Claude 모델의 0.1배보다 낮은 비율입니다.

이 가격 변화는 긴 agent session에서 특히 크게 작용합니다. coding agent가 repository 구조, issue 설명, 설계 문서, tool 결과를 반복해서 참조하면 같은 prefix를 여러 번 읽게 됩니다. cache hit가 안정적으로 나면, 긴 prefix를 다시 보내는 비용이 줄어듭니다. 반대로 매 요청마다 앞선 대화를 고치거나 client-side compaction으로 prefix가 달라지면 낮아진 cache read 가격을 충분히 쓰기 어렵습니다.

따라서 비용을 볼 때 token 단가만 비교해서는 부족합니다. Fable 5.1은 긴 작업에서 더 높은 품질을 목표로 하지만, high effort와 긴 output, fallback, retry가 함께 늘 수 있습니다. 제품팀은 "Fable 5.1이 싸졌다"가 아니라 "내 agent가 prefix를 얼마나 안정적으로 재사용하는가"를 먼저 재야 합니다.

## effort는 session 중간에도 바꿀 수 있습니다

Anthropic은 Fable 5.1에서 per-message effort 변경을 beta로 제공합니다. 문서에 따르면 `mid-conversation-output-config-2026-07-01` beta header를 쓰고, `role: "system"` message에 `output_config.effort`를 넣으면 다음 user turn부터 effort level을 바꿀 수 있습니다. 지원 값은 `low`, `medium`, `high`, `xhigh`, `max`입니다.

이 기능은 긴 workflow에서 자연스럽게 쓰일 수 있습니다. 예를 들어 repository 전체를 이해하고 migration plan을 짜는 turn은 높은 effort가 필요할 수 있습니다. 이미 정한 계획을 짧게 요약하거나 단순한 파일 목록을 정리하는 turn은 낮은 effort로 충분할 수 있습니다. 이전처럼 요청 parameter만 바꿔 cache를 깨는 방식보다, 대화 안에 effort 변경을 append하는 방식이 cache와 thinking 보존에 맞습니다.

하지만 beta 기능이 production 안정성을 자동으로 보장하지는 않습니다. account와 platform별 availability, header 관리, 실패 시 retry 정책을 따로 확인해야 합니다. 특히 model fallback을 쓰는 경우 Fable 5.1의 thinking block을 older model이 읽지 못하는 경로가 생깁니다. 비용과 latency뿐 아니라 error handling도 함께 테스트해야 합니다.

## 성능 수치는 평가 계획으로 써야 합니다

Anthropic은 Fable 5.1이 agentic coding, long-context work, computer use, document·spreadsheet·slide 작업, research와 search에서 Fable 5보다 좋아졌다고 설명합니다. 발표문은 Terminal-Bench, OSWorld, Humanity's Last Exam, AutomationBench, CursorBench 같은 benchmark 수치와 파트너 사례를 제시합니다. System card도 따로 공개했다고 안내합니다.

그렇지만 이 수치들은 제품팀의 최종 결론이 되기 어렵습니다. 발표문과 API 문서는 개발 주체가 고른 평가와 조건을 담은 1차 자료입니다. benchmark 결과는 agent harness, tool permission, timeout, browser 환경, network access, compaction 정책에 크게 좌우됩니다. 이 점은 이미 여러 model release에서 반복해서 드러났습니다.

Fable 5.1을 검토하는 팀은 자기 agent의 실패 유형을 먼저 나눠야 합니다. 도구 호출 형식 오류가 많은지, 긴 history를 줄이는 과정에서 맥락을 잃는지, retrieval을 너무 적게 호출하는지 따로 봐야 합니다. 사용자가 보는 progress update가 부족한지, output token이 과도하게 늘어나는지도 분리해서 확인해야 합니다. 그런 다음 Fable 5.1의 migration 규칙에 맞춰 같은 workload를 다시 재면 됩니다.

## 한국 개발팀은 데이터 보존 조건도 함께 봐야 합니다

Fable 5.1은 Claude API뿐 아니라 Amazon Bedrock, Claude Platform on AWS, Google Cloud, Microsoft Foundry에서도 제공됩니다. 기업용 agent를 만드는 국내 팀에는 이 availability가 중요합니다. 사내 code, 고객 문서, 금융·의료 데이터가 들어가는 workflow에서는 어느 region과 cloud 계약에서 어떤 data retention 조건을 적용할 수 있는지가 모델 품질만큼 중요하기 때문입니다.

Anthropic 문서는 Fable 5.1과 Mythos 5.1이 30일 data retention을 요구하며, zero data retention은 Anthropic이 명시적으로 승인한 경우가 아니면 사용할 수 없다고 설명합니다. 동시에 Enterprise Frontier Safeguards는 고객 cloud infrastructure에 activity data를 저장하고 automated monitoring signal을 고객에게 보내는 방향으로 단계적 rollout을 예고했습니다.

이 말은 Fable 5.1을 곧바로 민감한 production agent에 넣어도 된다는 뜻이 아닙니다. 오히려 모델 선택 표에 보안·보존·감사 항목을 먼저 올려야 한다는 뜻에 가깝습니다. 긴 context agent는 코드와 문서를 많이 읽고 오래 기억하도록 설계됩니다. 그래서 data retention과 audit log는 부가 조건이 아니라 runtime 설계의 일부입니다.

## 이해상충과 취재 조건

Anthropic은 Claude Fable 5.1과 Claude Mythos 5.1의 개발·배포 주체이며 발표문, API 문서, release note와 benchmark 설명을 작성했습니다. 따라서 출시 사실, API ID, 가격, migration 조건, data retention, availability는 원문으로 확인했지만, 성능 우위는 독립 재현 결론으로 쓰지 않았습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 소셜 신호는 후보 발견에만 사용했고, 기사 사실은 Anthropic 발표문과 Claude Platform 공식 문서로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Anthropic은 2026년 9월 1일 Claude Fable 5.1과 Claude Mythos 5.1을 공개했고, Fable 5.1은 일반 고객이 Claude API와 partner platform에서 사용할 수 있다고 설명했습니다. | E2 · P1 | 발표문, Claude Platform model page, release note로 확인했습니다. 계정별 실제 availability는 API 호출로 확인하지 않았습니다. |
| C2. Fable 5.1은 1M token context, 128K max output, API model ID `claude-fable-5-1`, base input 100만 token당 10달러, output 50달러, cache read 0.25달러를 문서화했습니다. | E2 · P1 | model page, what's new, release note가 일치합니다. 가격과 platform 조건은 이후 바뀔 수 있습니다. |
| C3. Fable 5.1과 Mythos 5.1은 `tool_choice`의 `any`와 특정 `tool` 강제를 지원하지 않으며, `auto`와 `none`은 지원한다고 Anthropic이 문서화했습니다. | E2 · P1 | migration guide와 what's new page로 확인했습니다. 실제 SDK별 error surface는 실행하지 않았습니다. |
| C4. Fable 5.1의 thinking block은 생성 당시의 `system`, `tools`, `messages` prefix에 묶이며, 이전 turn을 수정하면 block이 invalid해질 수 있습니다. | E2 · P1 | migration guide와 what's new page의 preserved thinking 설명으로 확인했습니다. 이 turn에서 API request를 보내 검증하지는 않았습니다. |
| C5. Per-message effort, turn-scoped system message, progress update display는 beta header를 요구하는 기능으로 문서화되어 있습니다. | E2 · P1 | what's new, migration guide, effort page, compaction page로 확인했습니다. beta 기능 availability는 계정과 platform별로 다를 수 있습니다. |
| C6. Anthropic은 Fable 5.1이 agentic coding, research, long-context, computer use benchmark에서 Fable 5보다 좋아졌다고 설명합니다. | E2 · P1 | 발표문과 what's new page의 vendor-authored benchmark·capability 설명입니다. 독립 재현이나 편집국 실행 결과가 아니므로 순위 결론으로 쓰지 않았습니다. |
| C7. Fable 5.1과 Mythos 5.1은 30일 data retention을 요구하고 zero data retention은 명시 승인 없이는 사용할 수 없다고 문서화되어 있습니다. | E2 · P1 | migration guide와 model page로 확인했습니다. Enterprise Frontier Safeguards rollout은 발표된 계획이며 실제 고객별 적용 여부는 별도 확인이 필요합니다. |

## 출처

1. Anthropic, `Claude Fable 5.1 and Mythos 5.1`, September 2026: https://www.anthropic.com/claude-fable-and-mythos-5-1
2. Claude Platform Docs, `Claude Fable 5.1`: https://platform.claude.com/docs/en/models/fable-5-1/overview
3. Claude Platform Docs, `What's new in Claude Fable 5.1`: https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1
4. Claude Platform Docs, `Migrating to Claude Fable 5.1 and Claude Mythos 5.1`: https://platform.claude.com/docs/en/models/fable-5-1/migration-guide
5. Claude Platform Docs, `Claude Platform release notes`: https://platform.claude.com/docs/en/release-notes/overview
6. Anthropic, `Developing Enterprise Frontier Safeguards with our customers`, 2026-09-01: https://www.anthropic.com/news/enterprise-frontier-safeguards
7. Claude Platform Docs, `Compaction`: https://platform.claude.com/docs/en/build-with-claude/compaction
8. Claude Platform Docs, `Effort`: https://platform.claude.com/docs/en/build-with-claude/effort
