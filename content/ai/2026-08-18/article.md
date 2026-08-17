---
edition: ai
decision: publish-candidate
title: "Compliance API local session transcripts 공개 - 로컬 코딩 에이전트 감사가 API 기록으로 이동합니다"
date: 2026-08-18
subject: "Anthropic Compliance API local session transcripts beta for Claude Code and Cowork, announced 2026-08-11"
summary: "Anthropic은 Claude Enterprise 조직에서 사용자가 로컬 머신에서 실행하는 Claude Code와 Cowork 세션의 transcript를 Compliance API로 조회할 수 있게 했습니다. 이 변화는 로컬 coding agent를 중앙 감사·DLP workflow에 연결하지만, transcript는 Claude API로 오간 내용만 담고 system prompt·thinking block·대부분의 binary content와 API 밖 local activity는 빠집니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Anthropic은 Claude, Claude Code, Cowork와 Compliance API의 개발·배포 주체이며 이 기사에 쓴 release note와 docs를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Anthropic이 2026년 8월 11일 Claude Platform release notes에 추가한 변화는 모델 능력보다 agent 운영 방식에 가깝습니다. Claude Enterprise 조직은 이제 사용자의 로컬 머신에서 실행되는 Claude Code와 Cowork 세션을 Compliance API로 나열하고, 세션별 transcript를 조회할 수 있습니다. 로컬에서 움직이는 coding agent도 중앙 감사, eDiscovery, DLP workflow의 입력으로 들어오기 시작했다는 뜻입니다.

이전에도 Claude Code를 조직적으로 관측하는 방법은 있었습니다. OpenTelemetry logging은 사용량, 비용, tool activity를 조직이 운영하는 collector로 흘려보낼 수 있고, inference hooks는 모델 호출 전에 조직의 security server가 allow 또는 deny를 판단하게 합니다. 이번 session transcript API의 차이는 실시간 제어가 아니라 사후 감사입니다. 조직은 이미 보존된 세션 단위 기록을 API로 다시 읽고, 사용자 prompt, assistant response, tool call, tool result를 사건 조사나 정책 검토에 연결할 수 있습니다.

SW 엔지니어에게 이 변화가 중요한 이유는 agent가 더 이상 “개발자 노트북 안의 보조 도구”로만 남지 않기 때문입니다. Claude Code가 repository를 읽고 command를 제안하며 tool result를 주고받는 과정은 보안팀과 플랫폼팀이 설명해야 하는 생산 활동이 됩니다. 다만 이 API가 로컬 컴퓨터의 모든 행동을 기록하는 것은 아닙니다. Anthropic 문서는 서버가 이미 받는 Claude API 요청을 바탕으로 transcript를 재구성한다고 설명합니다.

## 로컬 실행과 중앙 기록 사이에 생긴 새 경계

Compliance API의 local session endpoint는 세 가지 경로를 둡니다. `GET /v1/compliance/apps/sessions/local`은 조직 안의 local session metadata를 나열하고, `GET /v1/compliance/apps/sessions/local/{session_id}`는 특정 세션 metadata를 가져오며, `GET /v1/compliance/apps/sessions/local/{session_id}/messages`는 해당 세션의 transcript를 반환합니다. release note는 이 세 endpoint가 기존 Compliance Access Key와 `read:compliance_user_data` scope를 쓴다고 적었습니다.

제품 범위도 명확합니다. 문서는 사용자의 머신에서 도는 Cowork in Claude Desktop과 Claude Code를 local session endpoint 대상으로 설명합니다. Claude Code의 실행 surface는 terminal, Claude Desktop, IDE extension을 포함합니다. 반대로 Claude Console API key로 인증한 Claude Code 세션, Bedrock·Google Cloud·Microsoft Foundry 같은 third-party cloud platform을 통한 세션, Claude Code on the web, HIPAA readiness가 켜진 조직의 local session, zero data retention이 적용되는 세션은 local endpoint의 결과에서 빠집니다.

이 구조는 agent 감사의 기준선을 바꿉니다. 개발자 노트북에 별도 감시 agent를 심는 방식이 아니라, Claude client가 Claude API로 보낸 요청과 응답을 Anthropic 쪽 보존 기록에서 다시 읽는 방식입니다. 그래서 설치 부담은 낮지만 관측 범위도 그만큼 좁습니다. 로컬 파일이 Claude API로 전송되지 않았다면 transcript에 없습니다. 모델 호출 바깥에서 발생한 shell activity도 tool call/result로 API에 들어가지 않으면 보이지 않습니다.

## transcript는 실행 로그가 아니라 API 대화의 재구성입니다

messages endpoint가 돌려주는 단위는 `user`와 `assistant` role의 message이고, content block은 `text`, `tool_use`, `tool_result` 중심입니다. 예를 들어 assistant가 `Read` tool을 호출하면 tool name과 JSON-encoded input이 남고, 뒤이어 tool result의 text 부분이 user-role content로 들어옵니다. MCP tool call과 대부분의 server tool call도 같은 형태로 normalize된다고 문서는 설명합니다.

그러나 이 transcript를 완전한 forensic log로 보면 안 됩니다. thinking block은 포함되지 않습니다. request system prompt도 원문이 아니라 `[system prompt content not shown]` 같은 marker로 표시됩니다. tool definition과 MCP server configuration도 transcript 자체에는 들어가지 않습니다. image, PDF, 다른 binary 또는 structured block은 placeholder text와 `truncated` 표시로 대체됩니다. citation metadata도 빠질 수 있습니다.

이 한계는 설계상 중요합니다. 보안팀이 “agent가 왜 그런 결정을 했는지”까지 재구성하려면 transcript만으로는 부족합니다. 어떤 tool schema가 주어졌는지, MCP server가 어떤 권한으로 연결됐는지, repository checkout과 policy 설정이 무엇이었는지는 별도 system에서 보존해야 합니다. 반대로 transcript는 사용자가 무엇을 요청했고, Claude가 어떤 tool 호출을 제안했으며, tool result의 text가 어떻게 대화로 들어갔는지를 중앙 API로 묶는 역할을 합니다.

## 감사 파이프라인은 시간 창과 retention을 기준으로 다시 짜야 합니다

local session list는 `created_at` 범위로 조회하고, 결과는 reverse chronological order로 오며, `page`와 `next_page` token으로 pagination합니다. local session에는 server-side lifecycle이 없기 때문에 `status`나 `updated_at`이 없습니다. 세션이 계속 길어져도 `created_at`이 나중으로 밀려 다시 나타나는 구조가 아니므로, export job은 trailing window를 다시 훑고 같은 `id`를 기준으로 deduplicate해야 합니다.

문서는 새 세션과 메시지가 결과에 나타나기까지 보통 수 분의 processing delay가 있을 수 있다고 설명합니다. cursor는 24시간 안에 완주하는 것이 권장됩니다. 오래된 cursor는 현재 retention boundary를 기준으로 다시 평가될 수 있어, retention 경계에 걸린 session activity를 놓칠 수 있습니다.

retention도 구현 판단에 직접 영향을 줍니다. local session transcript는 기본 6년 보존이지만, 조직의 custom conversation retention period가 유한하게 설정되어 있으면 그 기간이 적용됩니다. 모든 call이 retention에서 벗어나면 session은 더 이상 반환되지 않습니다. zero data retention이 적용된 local session은 list 결과에서 제외되고 retrieve/messages endpoint는 404를 반환합니다.

## 운영상 의미는 감시 강화보다 책임 경계의 명확화입니다

이 API는 agent 사용을 더 안전하게 만든다고 자동으로 말할 수는 없습니다. 실시간 차단 기능이 아니고, transcript가 API 밖 local activity를 포착하지도 않습니다. 대신 조직이 coding agent 사용을 승인할 때 필요한 책임 경계를 더 분명하게 만듭니다. 무엇을 사후 감사할 수 있고, 무엇은 별도 telemetry나 endpoint control이 필요한지 구분할 수 있기 때문입니다.

플랫폼팀은 최소 세 가지를 함께 설계해야 합니다. 첫째, Compliance API transcript는 legal·security review용 record로 다루고, OpenTelemetry logging은 비용·사용량·tool activity의 near-real-time 운영 관측으로 둡니다. 둘째, inference hooks 같은 inline control을 쓰는 경우 denial record와 session transcript를 같은 incident id나 SIEM correlation key로 묶을 방법을 정합니다. 셋째, transcript에 system prompt와 tool definition이 빠지는 점을 보완하기 위해 agent configuration, MCP server inventory, repository policy를 별도 immutable log로 남깁니다.

한국 독자에게도 이 지점은 실무적입니다. 금융, 공공, 대기업 개발 조직은 local coding agent 도입을 productivity 문제가 아니라 감사와 데이터 거버넌스 문제로 검토합니다. 이번 API는 Claude Enterprise 안에서 그 논의를 가능하게 하는 원문 근거를 제공합니다. 다만 Anthropic의 beta 기능이고 Enterprise 조직에 한정되므로, 일반 Claude API나 다른 cloud provider 경유 사용에 그대로 적용하면 안 됩니다.

## benchmark 또는 재현 결과

이 기사는 Anthropic Compliance API를 직접 호출하지 않았습니다. Enterprise tenant, Compliance Access Key, 실제 Claude Code 또는 Cowork 세션이 필요하기 때문입니다. 재현성 상태는 R1입니다. endpoint, scope, response shape, retention, 제외 범위는 공식 문서로 설명 가능하지만, 편집국이 실제 조직 세션을 생성해 transcript를 회수한 로그는 없습니다.

성능 benchmark도 없습니다. 이 주제의 중심은 모델 품질이 아니라 agent session record의 API 표면입니다. 따라서 제목과 요약은 보안성 향상이나 완전한 감사 가능성을 단정하지 않고, local session transcript가 Compliance API 대상으로 들어온 변화와 그 한계를 중심으로 제한했습니다.

## 이해상충과 취재 조건

이 기사에 사용한 release note와 Compliance API 문서는 Anthropic이 작성한 1차 자료입니다. API availability, endpoint, scope, product surface, retention, excluded coverage를 확인하는 데는 적합하지만, Anthropic의 governance 기능이 충분하다는 독립 감사 근거는 아닙니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 기존 후보 원장은 발견 신호와 중복 확인에만 사용했고, 기사 사실은 공개된 Anthropic 공식 문서로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Anthropic은 2026년 8월 11일 Claude Enterprise 조직에 local Claude Code·Cowork session transcript 조회를 Compliance API beta로 추가했다고 공지했습니다. | E1 · P1 | Claude Platform release notes로 확인했습니다. 출시·지원 사실의 근거이며 기능 충분성의 독립 검증은 아닙니다. |
| C2. local session transcript API는 list, retrieve, messages endpoint를 제공하고 기존 Compliance Access Key와 `read:compliance_user_data` scope를 사용합니다. | E2 · P1 | release notes와 session transcript docs로 확인했습니다. 실제 호출은 하지 않았습니다. |
| C3. local endpoint 대상은 사용자의 머신에서 실행되는 Cowork in Claude Desktop과 Claude Code이며, Claude Code terminal·Desktop·IDE extension surface를 포함합니다. | E2 · P1 | session transcript docs의 product mapping으로 확인했습니다. coverage는 제품 확대에 따라 바뀔 수 있습니다. |
| C4. transcript는 Claude API로 오간 prompt, assistant response, tool call, tool result text를 재구성하지만 thinking block, system prompt 원문, tool definition, MCP server config, 대부분의 binary/structured content는 포함하지 않습니다. | E2 · P1 | session transcript docs의 messages endpoint 설명으로 확인했습니다. API 밖 local activity는 포착하지 않습니다. |
| C5. local session list에는 `status`나 `updated_at`이 없고, export job은 trailing window 재조회와 session id deduplication을 고려해야 합니다. | E2 · P1 | session transcript docs의 pagination, retention, created_at 설명에서 파생했습니다. 조직별 retention 설정은 별도로 확인해야 합니다. |
| C6. Compliance API는 사후 record 조회 도구이고, OpenTelemetry logging과 inference hooks는 각각 telemetry stream과 inline allow/deny control로 역할이 다릅니다. | E2 · P1 | Compliance API overview의 related features 비교와 Claude Code monitoring docs로 확인했습니다. 실제 SIEM integration은 구현하지 않았습니다. |

## 출처

- Claude Platform release notes: https://platform.claude.com/docs/en/release-notes/overview
- Retrieve session transcripts: https://platform.claude.com/docs/en/manage-claude/compliance-sessions
- Compliance API overview: https://platform.claude.com/docs/en/manage-claude/compliance-api
- Compliance API reference: https://platform.claude.com/docs/en/api/compliance
- Claude Code monitoring with OpenTelemetry: https://code.claude.com/docs/en/monitoring-usage
