---
edition: ai
decision: publish-candidate
title: "Claude Opus 5.5 공개 - 긴 코딩 agent의 비용과 API 호출 방식이 함께 바뀝니다"
date: 2026-09-28
subject: "Anthropic Claude Opus 5.5, released 2026-09-22"
summary: "Anthropic이 Claude Opus 5.5를 공개하며 긴 agentic coding과 지식 작업용 Opus 계열을 낮은 단가와 새 API 제약으로 다시 배치했습니다. 1M token context와 128K output, 항상 켜진 adaptive thinking, effort 기반 제어, computer use toolset 변경은 긴 작업 agent를 붙인 제품이 모델 ID뿐 아니라 호출 방식과 승인 로직까지 점검해야 한다는 뜻입니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["없음"]
---

Anthropic이 2026년 9월 22일 Claude Opus 5.5를 공개했습니다. 이 모델은 `claude-opus-5-5`라는 API ID로 제공됩니다. Anthropic은 이 모델을 긴 agentic coding과 지식 작업에 맞춘 Opus 계열 모델로 설명합니다. 개발자가 먼저 봐야 할 변화는 성능표의 1위 여부가 아닙니다. 긴 작업을 맡기는 agent에서 비용 구조와 API 제어 방식이 함께 바뀐 점입니다.

Opus 5.5는 1M token context window와 128K max output을 문서화했습니다. 기본 thinking은 끌 수 없습니다. Anthropic의 release note는 `thinking` 필드를 직접 켜거나 끄지 말고, `effort` parameter로 깊이를 조절하라고 안내합니다. 또 Claude API와 Google Cloud에서 computer use를 쓰려면 `computer_toolset_20260801`이 필요합니다. 이전 `computer_20251124` 도구는 오류를 낸다고 적었습니다.

이 변화는 단순한 모델 교체보다 운영 조건 변경에 가깝습니다. 장기 coding agent는 여러 파일을 읽고, 도구를 부르고, 긴 대화 이력을 유지하면서 작업합니다. 따라서 모델이 조금 더 똑똑해졌다는 주장보다 “어떤 context를 넣을 수 있는가”, “thinking을 어떻게 제어하는가”, “어떤 tool schema가 허용되는가”가 실제 제품 통합의 병목이 됩니다.

## 긴 작업 agent는 모델 ID만 바꿔서는 안 됩니다

Opus 5.5의 공개 문서에서 반복되는 용도는 긴 agentic coding과 knowledge work입니다. Anthropic의 모델 overview는 Opus 5.5를 장기 코딩 agent와 지식 작업용 모델로 두고, 현재 모델 중 대부분의 workload에서 먼저 검토할 대상으로 적었습니다. 같은 표는 Opus 5.5가 1M token context, 128K output, 항상 켜진 adaptive thinking을 갖는다고 설명합니다.

이 사양은 긴 저장소 작업에서 의미가 큽니다. agent가 한 번에 더 많은 파일과 로그, 이전 결정을 볼 수 있으면 compaction과 검색을 덜 자주 해도 됩니다. 하지만 context가 길다고 해서 작업이 자동으로 안전해지는 것은 아닙니다. 긴 입력은 비용과 latency를 키웁니다. 오래된 결정이나 잘못된 tool 결과도 모델 입력에 함께 남을 수 있습니다.

그래서 Opus 5.5를 도입할 때는 “더 긴 context”보다 “어떤 정보를 오래 들고 갈지”를 먼저 정해야 합니다. 코드베이스 구조, 실패한 테스트 로그, 사람의 승인 기록, tool 결과를 같은 priority로 밀어 넣으면 agent가 핵심 변경 이유를 놓칠 수 있습니다. 긴 context 모델을 쓰는 일은 저장 공간을 늘리는 일이 아니라, 작업 상태를 어떻게 남길지 설계하는 일에 가깝습니다.

## Thinking은 끄지 않고 effort로 조절합니다

Release note의 API 변화는 분명합니다. Opus 5.5에서는 `thinking: {"type": "disabled"}`와 `thinking: {"type": "enabled", ...}`가 400 error를 반환합니다. 문서는 `thinking` field를 생략하고 `effort` parameter로 thinking depth를 제어하라고 설명합니다.

이 차이는 agent 제품의 설정 UI와 평가 코드에 영향을 줍니다. 이전 모델에서 “thinking 켜기/끄기”를 명시적으로 저장했다면, Opus 5.5에서는 그 설정을 그대로 보내면 오류가 날 수 있습니다. 또 품질·비용 평가도 effort별로 다시 나눠야 합니다. 같은 prompt라도 medium effort와 높은 effort는 output token, 지연시간, 실패 양상이 달라질 수 있기 때문입니다.

Anthropic은 Fast mode도 research preview로 제공합니다. 공개 글은 Fast mode가 Claude Code와 Claude Platform에서 최대 2.5배 속도를 제공한다고 설명합니다. 가격은 입력 100만 token당 8달러, 출력 100만 token당 40달러입니다. 표준 Opus 5.5 가격보다 비싸지만, 긴 작업에서 wall-clock time이 더 중요한 팀은 별도 평가 후보로 볼 수 있습니다.

## 도구 호출 방식도 다시 맞춰야 합니다

Opus 5.5는 도구 호출 쪽에서도 마이그레이션 조건을 둡니다. Release note는 `tool_choice`의 `any`와 `tool` type이 Opus 5.5에서 400 error를 반환하며, strict tool use와 함께 `auto`를 쓰라고 안내합니다. Computer use도 플랫폼별 차이가 있습니다. Claude API와 Google Cloud에서는 `computer_toolset_20260801`이 필요하지만, Amazon Bedrock에서는 이전 `computer_20251124`가 계속 동작한다고 적었습니다.

이런 차이는 agent runtime을 직접 운영하는 팀에 바로 걸립니다. tool choice를 강제로 고정해 특정 function만 부르게 하던 코드, computer use tool version을 상수로 박아 둔 adapter, provider별 tool schema를 하나로 추상화한 wrapper가 모두 영향을 받을 수 있습니다. 모델 ID만 바꾼 canary test로는 이런 오류를 충분히 찾기 어렵습니다.

도입 순서는 단순해야 합니다. 먼저 API 요청에서 `thinking` field와 `tool_choice` 값을 검사해야 합니다. computer use를 쓰는 workflow는 platform별 toolset을 분리해야 합니다. 그다음 effort별 비용과 성공률을 같은 작업 묶음에서 따로 측정해야 합니다. “Opus 5.5가 Opus 5보다 낫다”는 벤더 주장만으로는 우리 제품의 최적 effort와 tool policy를 정할 수 없습니다.

## 낮아진 단가는 실제 trace로 다시 계산해야 합니다

Anthropic의 가격 문서는 Opus 5.5의 기본 입력 단가를 100만 token당 4달러, 출력 단가를 20달러로 적었습니다. Opus 5의 5달러·25달러보다 낮습니다. Prompt cache도 Opus 5.5에서 5분 write는 5달러, 1시간 write는 8달러, hit와 refresh는 0.20달러로 문서화됐습니다.

다만 token 단가만 비교하면 부족합니다. 같은 가격 문서는 Claude 4.7 이후 모델과 Claude Mythos Preview가 새 tokenizer를 쓴다고 설명합니다. 같은 text에서 약 30% 더 많은 token을 만들 수 있지만, 증가 폭은 내용과 workload 모양에 따라 달라집니다. 즉 실제 청구액은 입력 문서의 언어, 코드 비율, cache hit율, output 길이, effort에 따라 달라집니다.

한국어와 코드가 섞인 제품이라면 이 부분을 직접 재야 합니다. 한국어 문서, 영어 API 문서, TypeScript나 Python 파일, test log가 같은 비율로 들어가지 않기 때문입니다. Opus 5.5의 낮아진 단가는 유리한 신호지만, 실제 비용 결론은 각 팀의 trace에서 tokenization과 cache를 같이 보아야 합니다.

## 성능표만으로 우위를 결론낼 수는 없습니다

Anthropic의 공개 글은 Opus 5.5가 Terminal-Bench 4.0, FrontierCode v1.1, CursorBench 4.0, AutomationBench, OSWorld 2.0 등에서 높은 점수를 냈다고 설명합니다. 또한 여러 early tester 사례와 비용 절감 사례를 제시합니다. 이 자료는 어떤 작업을 Anthropic이 중요하게 보는지 보여 주는 데 유용합니다.

하지만 이 글은 Opus 5.5가 경쟁 모델보다 일반적으로 우수하다고 결론 내리지 않습니다. 공개 글의 성능 수치는 Anthropic 또는 Anthropic이 인용한 평가 조건에 묶여 있습니다. 일부 수치는 early access 환경과 safeguard fallback 조건도 포함합니다. 편집국은 모델을 직접 실행하지 않았고, 동일한 codebase와 tool policy에서 재현하지도 않았습니다.

이번 후보의 중심 주장은 더 좁습니다. Opus 5.5는 긴 coding agent 작업을 겨냥한 모델로 공개됐고, API 문서는 thinking, effort, tool choice, computer use toolset, 가격과 context 조건을 함께 바꿨습니다. SW 팀이 실제로 판단해야 할 것은 benchmark 순위가 아니라, 자기 agent runtime에서 이 새 호출 계약을 감당할 수 있는지입니다.

## 이해상충과 취재 조건

이 글은 공개 웹 문서만 읽어 작성했습니다. Anthropic, OpenAI, Google, Qwen, DeepSeek, Mistral 또는 다른 공급자로부터 계정, 크레딧, 장비, 브리핑, 엠바고 자료를 제공받지 않았습니다. 이해상충은 확인된 바 없습니다.

## 근거 원장

| claim_id | 주장 | 근거 | 등급 | 한계 |
| --- | --- | --- | --- | --- |
| C1 | Anthropic은 2026년 9월 22일 Claude Opus 5.5를 공개했고, API ID는 `claude-opus-5-5`입니다. | Anthropic launch page, Claude Platform release notes | E2 | 계정별 실제 availability는 API 호출로 확인하지 않았습니다. |
| C2 | Opus 5.5는 장기 agentic coding과 knowledge work용 모델로 문서화됐고, 1M token context window와 128K max output을 제공합니다. | Claude Platform release notes, Models overview | E2 | 문서상 사양 확인이며 실제 workload에서 긴 context 품질을 측정하지 않았습니다. |
| C3 | Opus 5.5에서는 thinking을 끄거나 직접 enable하는 요청이 400 error를 내며, effort parameter로 thinking depth를 조절해야 합니다. | Claude Platform release notes | E2 | 오류 조건은 문서 확인이며 실제 API request를 실행하지 않았습니다. |
| C4 | Opus 5.5의 `tool_choice`는 `any`와 `tool` type을 허용하지 않고, computer use는 Claude API와 Google Cloud에서 `computer_toolset_20260801`이 필요합니다. | Claude Platform release notes | E2 | Platform별 동작은 Anthropic 문서에 근거하며 Bedrock, Google Cloud, Claude API에서 직접 비교하지 않았습니다. |
| C5 | Opus 5.5의 표준 가격은 입력 100만 token당 4달러, 출력 20달러이고, prompt cache write와 hit 가격도 별도 문서화됐습니다. | Claude Platform pricing, Anthropic launch page | E2 | 실제 비용은 tokenization, cache hit율, effort, 출력 길이에 따라 달라집니다. |
| C6 | Anthropic은 Opus 5.5의 benchmark와 early tester 성과를 공개했지만, 이 글은 이를 독립 성능 우위 결론으로 쓰지 않습니다. | Anthropic launch page | E1 | 성능 수치의 상당 부분은 벤더 공개 또는 초기 사용자 사례이며 편집국 재현이 없습니다. |

## 출처

- Anthropic, “Claude Opus 5.5,” September 22, 2026. https://www.anthropic.com/claude-opus-5-5
- Claude Platform Docs, “Claude Platform release notes,” September 22, 2026 entry. https://platform.claude.com/docs/en/release-notes/overview
- Claude Platform Docs, “Models overview.” https://platform.claude.com/docs/en/models/overview
- Claude Platform Docs, “Pricing.” https://platform.claude.com/docs/en/about-claude/pricing
