---
edition: ai
decision: publish-candidate
title: "Claude API on-demand compaction 공개 - 긴 agent 대화를 백그라운드에서 요약합니다"
date: 2026-09-16
subject: "Claude Messages API compact-on-demand beta, compact-2026-09-04"
summary: "Anthropic은 Claude Messages API에서 긴 대화를 별도 요청으로 요약하고, 이후 요청에서 signed compaction block으로 오래된 message를 대체하는 beta 기능을 공개했습니다. 긴 coding agent와 업무 agent는 응답을 멈추지 않고 history를 줄일 수 있지만, block 위치, 그대로 남길 최근 turn, tool·system 변경, 첨부 파일 손실과 과금 집계를 직접 설계해야 합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Anthropic은 Claude API와 Claude 모델의 개발·운영 주체이며 이번 release note와 compaction 문서를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Anthropic이 2026년 9월 14일 Claude Messages API에 on-demand compaction beta를 추가했습니다. 이 기능은 긴 agent 대화에서 오래된 message를 별도 요청으로 요약하고, 다음 요청부터 그 구간을 `compaction` block 하나로 바꿔 보낼 수 있게 합니다. coding agent나 업무 자동화 agent처럼 여러 시간 동안 tool 결과와 사용자 지시를 쌓는 runtime은 대화를 멈추지 않고 context를 줄일 수 있습니다.

기존 server-side compaction은 대화가 token threshold에 닿을 때 API가 자동으로 요약을 만들고 이어서 응답했습니다. 새 방식에서는 개발자가 원할 때 최상위(top-level) `compaction` parameter로 요약만 요청합니다. 이 요청은 실제 사용자 turn과 분리해 백그라운드에서 실행할 수 있고, 응답으로 받은 signed block은 나중에 history 앞쪽 message와 교체합니다.

중심 변화는 모델이 더 똑똑해졌다는 주장이 아닙니다. agent runtime이 직접 요약 prompt를 만들고 임의의 text summary를 끼워 넣던 방식에서, API가 인식하는 `compaction` block으로 history의 경계를 표시하는 방식으로 옮겨 간다는 점입니다. 그래서 이 기능의 가치는 성능 순위보다 conversation state, prompt cache, preserved thinking, 비용 회계, 실패 복구를 어떻게 설계할지에 있습니다.

## 오래된 대화 구간을 compaction block으로 바꿉니다

on-demand compaction을 쓰면 application은 요약하고 싶은 message 묶음을 API에 보냅니다. API는 정상적으로 요약을 만들면 `stop_reason`을 `compaction`으로 두고, 응답 content에 `compaction` block을 돌려줍니다. 이후 요청에서는 이 block을 `messages`의 맨 앞에 두고, 이미 요약된 message는 제거해야 합니다.

이 구조가 중요한 이유는 긴 agent가 보통 두 가지 일을 동시에 해야 하기 때문입니다. 앞선 작업 상태는 잃지 않아야 하고, 최근 tool 결과나 사용자의 마지막 수정 지시는 원문 그대로 남겨야 합니다. Anthropic 문서는 최근 turn을 그대로 보존하려면 그 turn을 compaction 요청에 넣지 말고, 돌아온 block을 보존한 turn 앞에 붙이라고 설명합니다.

즉 개발자는 runtime 정책에서 “무엇을 요약하고 무엇을 원문으로 남길지”를 정해야 합니다. 예를 들어 repository 전체를 훑은 tool 결과와 오래된 설계 토론은 요약 대상이 될 수 있습니다. 반대로 방금 실패한 test log, 사용자가 고친 요구사항, 다음 요청에서 바로 참조할 파일 block은 원문으로 남기는 편이 안전합니다.

## 백그라운드 요약은 agent를 멈추지 않게 합니다

이번 beta의 실무적 차이는 compaction 요청이 대화 turn과 분리된다는 데 있습니다. 긴 agent가 계속 tool을 호출하는 동안, runtime은 이미 보낸 앞쪽 history를 별도 요청으로 요약할 수 있습니다. 요약 block이 도착하면 다음 Claude 요청에서 그 block을 앞쪽 message 대신 넣고, 그 사이에 새로 붙은 message는 뒤에 둡니다.

이 방식은 client-side summarization보다 API에서 다루는 범위가 분명합니다. application이 text summary를 일반 user 또는 assistant message로 삽입하면, 모델은 그것을 “누가 한 말인지”와 “어떤 범위를 대체하는지”를 API 차원에서 알 수 없습니다. `compaction` block은 오래된 구간을 대체하는 content block으로 다뤄지므로, 이후 token counting과 prompt caching, 오류 처리에서 별도 규칙을 적용할 수 있습니다.

하지만 자동으로 안전해지는 것은 아닙니다. Anthropic 문서는 compaction 요청을 보낸 뒤 block을 교체하기 전까지 history를 편집하지 말고, block이 도착한 첫 요청에서 교체하라고 안내합니다. preserved thinking을 쓰는 모델에서는 보존한 turn이 요약된 message 바로 뒤에 이어져야 합니다. compaction 요청 때의 `system`과 non-deferred `tools`도 그대로여야 최근 thinking block이 유효하게 남습니다.

## 요약 block 비용과 실패도 따로 집계해야 합니다

compaction은 별도의 sampling step입니다. Anthropic 문서는 compaction이 발생하면 `usage.iterations`에 compaction iteration과 message iteration이 나뉘어 기록되고, 총 과금 token을 보려면 이 배열을 합산해야 한다고 설명합니다. 기존에 top-level `input_tokens`와 `output_tokens`만 집계하던 비용 dashboard는 compaction 비용을 놓칠 수 있습니다.

오류 처리도 단순하지 않습니다. 요약 요청이 `max_tokens`, `model_context_window_exceeded`, `refusal`, `tool_use`, `end_turn` 같은 이유로 summary text를 만들지 못하면, 응답은 200이어도 content가 비어 있을 수 있습니다. 도구가 정의된 요청에서는 내부 요약 단계에서 모델이 summary 대신 tool을 호출할 수 있습니다. 문서는 자체 `instructions`에 “tool을 호출하지 말고 text summary만 쓰라”는 조건을 넣는 방식을 제시합니다.

또 하나의 제약은 block 위치입니다. 이후 요청에서 `compaction` block 앞에 요약된 message가 남아 있으면 API는 `compaction_block_misplaced` 계열 400 오류를 낼 수 있습니다. block을 빼먹으면 요약이 전달되지 않고, block을 둘 이상 보내면 역시 오류가 됩니다. 긴 agent runtime은 compaction을 단순한 문자열 요약이 아니라 history를 옮겨 쓰는 작업으로 다뤄야 합니다.

## 첨부 파일과 임시 지시는 요약에 모두 남지 않습니다

on-demand compaction은 오래된 text context를 줄이는 기능이지, 모든 application state를 보존하는 저장소가 아닙니다. Anthropic 문서는 summarized message 안의 image, document, `container_upload` block, fetched URL은 block으로 대체된 뒤 사라진다고 밝힙니다. 이후 turn에서 다시 필요하면 파일을 다시 올리거나, summary에 남길 수 있는 형태로 필요한 내용을 다시 적어야 합니다.

대화 중간에 들어간 system message와 tool change도 주의해야 합니다. 요약 범위 안의 `role: "system"` message는 summary 안으로 들어가지만, 그 지시가 계속 적용되는 것은 아닙니다. 계속 필요한 지시는 다음 새 user turn 뒤에 다시 system message로 남겨야 합니다. 다만 block과 보존한 turn 사이에 끼워 넣으면 보존한 thinking을 깨뜨릴 수 있습니다.

따라서 이 기능을 도입할 때의 핵심 질문은 “context window를 얼마나 아낄 수 있는가”만이 아닙니다. 어떤 상태는 summary로 충분하고, 어떤 상태는 별도 memory store나 database에 남겨야 하는지 나누어야 합니다. 어떤 파일을 다음 turn에 다시 첨부해야 하는지도 따로 정해야 합니다. 특히 한국의 기업 개발팀처럼 내부 코드와 고객 문서, 감사 로그를 함께 다루는 환경에서는 compaction block과 외부 state 저장소의 책임을 분리하는 설계가 필요합니다.

## 문서로 확인한 범위와 아직 남은 검증

공개 문서로 확인할 수 있는 것은 API 동작과 제약입니다. 2026년 9월 14일 release note는 `compact-2026-09-04` beta header, top-level `compaction` parameter, signed `compaction` block, 백그라운드 실행, 최근 turn 보존을 설명합니다. compaction 문서는 block 교체 순서, prompt caching, usage 집계, 실패 `stop_reason`, 지원 모델과 platform을 더 자세히 적고 있습니다.

확인하지 못한 것은 실제 workload에서의 품질과 비용입니다. 편집국은 API request를 실행하지 않았고, 긴 coding agent에서 summary가 bug reproduction 단계나 파일명, test 결과를 얼마나 잘 보존하는지도 재현하지 않았습니다. 따라서 이 글의 결론은 “on-demand compaction이 긴 agent history 관리에 새 API-level 선택지를 추가했다”는 데 머뭅니다. 특정 agent의 정확도나 비용이 개선된다는 주장은 각 팀이 자기 workload로 따로 측정해야 합니다.

## 이해상충과 취재 조건

Anthropic은 Claude API와 Claude 모델의 개발·운영 주체이며 이번 release note와 compaction 문서를 작성했습니다. 출시 사실, beta header, parameter, block 처리 규칙, 과금 집계와 제한 사항은 공식 문서로 확인했습니다. 성능 개선이나 비용 절감은 독립 검증하지 않았고 편집국 결론으로 쓰지 않았습니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 기존 source registry는 발견 신호로만 사용했고, 기사 본문 사실은 열린 공식 원문에 맞췄습니다.

## 근거 원장

| claim id | 기사에서 사용한 주장 | 근거와 등급 | 한계 |
|---|---|---|---|
| C1 | Anthropic은 2026년 9월 14일 Claude Messages API에 on-demand compaction beta를 추가했습니다. | E2 · P1 | release note와 compaction 문서로 확인했습니다. 계정별 beta availability는 API 호출로 확인하지 않았습니다. |
| C2 | `compact-2026-09-04` beta header와 top-level `compaction` parameter를 쓰면 별도 요청으로 summary를 받고, 이후 요청에서 signed `compaction` block을 앞쪽 message 대신 보낼 수 있습니다. | E2 · P1 | 문서 동작 설명입니다. 실제 SDK별 request와 error surface는 실행하지 않았습니다. |
| C3 | 보존할 최근 turn을 compaction 요청에서 제외하고, 돌아온 block을 그 turn 앞에 두면 오래된 message만 요약으로 대체할 수 있습니다. | E2 · P1 | preserved thinking이 유효하려면 보존 turn의 위치와 `system`·`tools` 조건을 지켜야 합니다. |
| C4 | compaction 사용 시 비용 집계는 `usage.iterations`를 합산해야 하며, 요약 실패는 200 응답 안의 빈 content와 stop reason으로 나타날 수 있습니다. | E2 · P1 | 실제 과금액과 실패 빈도는 workload와 계정 조건에 따라 달라질 수 있습니다. |
| C5 | summarized message 안의 image, document, `container_upload` block, fetched URL은 block으로 대체된 뒤 사라지므로 필요한 자료는 다시 제공해야 합니다. | E2 · P1 | 문서 제한 사항입니다. 파일별 product surface 동작은 직접 재현하지 않았습니다. |

## 출처

- Claude Platform release notes: https://platform.claude.com/docs/en/release-notes/overview
- Claude Platform Docs, Compaction: https://platform.claude.com/docs/en/build-with-claude/compaction
