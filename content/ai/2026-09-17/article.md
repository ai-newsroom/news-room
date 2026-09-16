---
edition: ai
decision: publish-candidate
title: "Agents API 공개 - 모델 호출을 관리형 agent session으로 묶습니다"
date: 2026-09-17
subject: "OpenAI Agents API public beta, September 10 2026"
summary: "OpenAI는 Agents API public beta로 Codex harness, durable session, sandbox, MCP 연결, subagent, 진행 event와 사용량 추적을 API 제품으로 묶었습니다. 개발팀은 이제 Responses 호출을 직접 반복할지, OpenAI가 session과 context compaction, recovery를 맡는 구조에서 환경·도구·권한을 설계할지 나눠 평가해야 합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["OpenAI는 Agents API와 Codex harness의 개발·운영 주체이며 changelog와 API 문서를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

OpenAI가 2026년 9월 10일 Agents API를 public beta로 공개했습니다. 이 API는 모델에 요청을 한 번씩 보내는 interface라기보다, Codex harness를 관리형 session으로 빌려 쓰는 방식에 가깝습니다. 애플리케이션은 작업을 보내고 event와 결과를 받습니다. OpenAI는 session orchestration, context compaction, recovery를 맡습니다.

이 변화가 중요한 이유는 agent 제품에서 prompt 하나를 잘 쓰는 것만으로는 부족하기 때문입니다. 장기 coding agent나 업무 자동화 agent는 파일을 읽고, 명령을 실행하고, MCP server를 호출하고, 중간에 사용자의 새 지시를 받아야 합니다. Agents API는 이런 실행 상태를 API의 기본 단위로 다룹니다. 그래서 개발자는 “모델 호출”이 아니라 “작업 세션”을 설계하게 됩니다.

중심 주장은 좁습니다. Agents API가 agent 품질이나 비용을 독립적으로 개선한다고 확인된 것은 아닙니다. 공개 문서로 확인되는 변화는 OpenAI가 Codex harness, environment, tool 연결, session event, usage 관측을 하나의 runtime 계약으로 내놓았다는 점입니다. 실제 정확도, latency, 총비용은 각 팀이 자기 workload와 권한 정책으로 다시 재야 합니다.

## agent 작업은 session 단위로 이어집니다

Agents API의 기본 구조는 agent, environment, session, events and items입니다. agent는 모델과 지시문, 도구와 MCP server 구성을 담습니다. environment는 agent가 파일을 읽거나 명령을 실행할 공간입니다. session은 agent가 이어서 일하는 durable instance이고, event는 입력과 진행 상황, 결과를 전달하는 기록입니다.

기존에 Responses API를 직접 반복 호출하던 구현에서는 애플리케이션이 대화 history, tool result, retry, 요약, 재개 상태를 대부분 직접 관리해야 했습니다. Agents API에서는 harness가 session을 유지합니다. 애플리케이션은 같은 session에 후속 message를 보내거나 진행 중인 turn을 steering할 수 있습니다. saved agent 설정 변경은 새 session에만 적용되며, 기존 session의 모델이나 reasoning effort 같은 값은 session settings로 바꿔야 한다는 점도 문서화되어 있습니다.

이 구조는 특히 장기 작업에서 의미가 있습니다. 사용자가 “이 버그를 재현하고 수정한 뒤 test 결과를 알려 달라”고 맡기면 agent는 한 번의 completion으로 끝나지 않습니다. repository 상태, 실패 log, 수정 파일, 새 지시를 이어 받아야 합니다. Agents API는 이 연속 작업의 단위를 API resource로 만들었습니다.

## 코드를 실행하려면 sandbox 선택이 먼저입니다

Agents API는 environment 없이도 쓸 수 있습니다. 이 경우 harness는 모델과 remote MCP, function tool을 사용할 수 있지만 built-in Bash, apply-patch, workspace file, executor MCP는 없습니다. 질문 답변이나 외부 API 도구 호출만 필요한 agent라면 이 구성이 더 단순합니다.

파일을 다루고 코드를 실행해야 하면 OpenAI-hosted sandbox나 self-hosted sandbox를 선택합니다. OpenAI-hosted sandbox는 `/workspace`를 작업 디렉터리로 쓰는 Linux workspace를 만들고, Python, Node.js, command-line tool을 제공합니다. 개발자는 session을 만들 때 package, setup command, file, environment variable, skill, plugin, network policy를 설정합니다. 각 session은 별도 workspace를 가지며, `/workspace/outputs` 아래 파일은 turn 완료 뒤 다운로드 가능한 artifact로 보존됩니다.

self-hosted sandbox는 더 많은 책임을 개발팀에 남깁니다. OpenAI가 agent harness를 실행하고, 개발팀은 자기 환경 안에서 `codex exec-server` executor를 띄웁니다. executor는 outbound WebSocket으로 연결해 harness가 요청한 command와 tool을 실행합니다. 사내 network, custom image, 자체 compute가 필요한 팀에는 이 경로가 필요합니다. 대신 환경 lifecycle과 격리, 로그, cleanup 정책도 함께 설계해야 합니다.

## MCP는 접속 위치와 credential 경계가 중요합니다

Agents API의 MCP 연결은 어디서 server에 접속할지에 따라 달라집니다. HTTP MCP를 OpenAI service에서 직접 호출할 수도 있고, session environment에서 호출하게 할 수도 있습니다. stdio MCP는 environment 안의 process로 띄웁니다. 사내 검색, database, 고객 관리 시스템처럼 private network에 있는 도구는 environment-origin 연결이나 self-hosted 환경이 필요합니다.

문서에서 더 중요한 부분은 credential 경계입니다. HTTP credential은 session 생성 때 inline으로 넣거나 vault에 저장해 붙일 수 있습니다. stdio credential은 environment variable로 넘기므로 agent가 실행한 코드가 읽을 수 있습니다. OpenAI 문서는 오래 쓰는 third-party credential을 environment 밖에 두라고 권합니다. 가능하면 credential broker가 허용된 outbound request에만 secret을 주입하게 하라는 설명도 함께 둡니다.

이 말은 agent 보안을 “도구 목록 제한”만으로 끝낼 수 없다는 뜻입니다. agent가 생성한 코드가 environment의 파일, credential, network에 접근할 수 있으므로 사용자별 또는 workload별 격리가 필요합니다. 네트워크도 approved endpoint로 제한해야 합니다. 한국 기업 환경처럼 사내 repository와 고객 데이터를 함께 다루는 agent라면, MCP server 위치와 secret 주입 방식을 agent architecture의 첫 결정으로 봐야 합니다.

## 비용은 한 번의 응답이 아니라 작업 전체로 봐야 합니다

Agents API는 live progress와 completed work, token usage를 session log와 event, dashboard에서 추적하도록 문서화했습니다. 그러나 이 usage는 작업의 최종 청구서를 그대로 대신하지 않습니다. 문서는 turn usage가 best-effort일 수 있고, 값이 `null`이거나 나중에 바뀔 수 있다고 밝힙니다. trace retrieval과 external exporter도 public beta API의 일반 기능은 아닙니다.

비용 계산도 더 복잡해집니다. agent는 하나의 task를 끝내는 동안 model call을 여러 번 할 수 있고, subagent도 별도 model call을 만듭니다. input token에는 지시문, tool definition, history, file, image, tool result가 들어갑니다. reasoning token은 output token으로 과금됩니다. sandbox compute, OpenAI tool, third-party service charge도 별도로 붙을 수 있습니다.

prompt caching도 비용을 자동으로 줄인다고 단정하면 안 됩니다. session이 context를 이어 간다고 해서 cache hit가 보장되지는 않습니다. prefix가 맞고 모델의 cache rule에 들어야 합니다. 따라서 Agents API를 검토하는 팀은 “한 turn의 token 단가”보다 “우리 작업 하나를 끝내는 데 root agent와 subagent가 몇 번 호출되는가”를 먼저 측정해야 합니다.

## 이번 공개가 바꾸는 판단 기준

Agents API는 GPT-6 Astra 같은 새 모델을 더 쉽게 호출하는 wrapper가 아닙니다. 모델과 tool loop, sandbox, context 관리, 재개, subagent, 관측을 함께 묶어 agent runtime을 제품화한 공개입니다. 그래서 채택 판단도 모델 품질표만으로는 부족합니다.

가벼운 도구 호출형 agent라면 Responses API와 function calling으로 충분할 수 있습니다. 파일 수정, 장시간 조사, 사내 MCP, subagent delegation, 진행 event, artifact가 필요한 agent라면 Agents API가 줄이는 운영 부담이 큽니다. 반대로 production에 넣을 때는 environment 격리, network policy, credential broker, usage accounting, session cleanup을 직접 검증해야 합니다.

재현성은 R1입니다. 공개 문서로 API 동작과 구성 선택지는 설명할 수 있지만, 편집국은 beta API를 호출하지 않았고 실제 sandbox에서 command 실행, MCP 연결, 비용 집계, failure recovery를 재현하지 않았습니다. 따라서 이 글은 Agents API가 agent runtime 설계의 선택지를 바꿨다는 E2 주장에 머뭅니다. 특정 업무에서 정확도나 비용이 좋아진다는 결론은 workload별 실험 뒤에야 말할 수 있습니다.

## 이해상충과 취재 조건

OpenAI는 Agents API와 Codex harness의 개발·운영 주체이며 changelog, Agents API overview, architecture, sandbox, MCP, observability 문서를 작성했습니다. 출시일, public beta 상태, session과 environment 구조, sandbox 선택지, MCP 연결 방식, credential 주의사항, usage 추적 범위는 공식 문서로 확인했습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 기존 source registry는 발견 신호로만 사용했고, 기사 본문 사실은 열린 공식 원문과 release note에 맞췄습니다.

## 근거 원장

| claim id | 기사에서 사용한 주장 | 근거와 등급 | 한계 |
|---|---|---|---|
| C1 | OpenAI는 2026년 9월 10일 Agents API public beta를 공개했습니다. | E2 · P1 | OpenAI API changelog와 Agents API overview로 확인했습니다. 계정별 beta access는 API 호출로 확인하지 않았습니다. |
| C2 | Agents API는 OpenAI-managed Codex harness를 통해 session orchestration, context compaction, recovery를 관리하고, 애플리케이션은 tool과 execution environment를 고릅니다. | E2 · P1 | overview와 architecture 문서로 확인했습니다. 실제 recovery 품질은 재현하지 않았습니다. |
| C3 | Agents API의 주요 개념은 agent, environment, session, events and items이며, session은 같은 conversation을 이어 작업하고 active turn steering을 받을 수 있습니다. | E2 · P1 | overview와 session 문서로 확인했습니다. SDK별 error surface는 확인하지 않았습니다. |
| C4 | OpenAI-hosted sandbox는 Linux workspace, package/setup/file/env/network 설정, session별 workspace와 artifact 보존을 제공합니다. | E2 · P1 | OpenAI-hosted sandbox 문서로 확인했습니다. sandbox를 직접 띄워 실행하지 않았습니다. |
| C5 | self-hosted sandbox에서는 개발팀 환경의 `codex exec-server`가 outbound WebSocket으로 연결되고, agent-generated code가 읽을 수 있는 environment key는 환경 연결 권한만 갖도록 분리됩니다. | E2 · P1 | self-hosted sandbox와 sandbox security 문서로 확인했습니다. provider별 운영 안정성은 검증하지 않았습니다. |
| C6 | MCP server는 OpenAI service, session environment, stdio process 위치에서 연결할 수 있고, credential은 inline, vault, environment variable, broker 방식으로 나뉩니다. | E2 · P1 | MCP connections와 sandbox security 문서로 확인했습니다. 실제 MCP server 연결은 실행하지 않았습니다. |
| C7 | Agents API usage는 root-agent와 subagent turn 단위로 볼 수 있지만 best-effort일 수 있으며, 최종 비용은 여러 model call, cache, tool, sandbox, third-party 비용을 합산해야 합니다. | E2 · P1 | observability and usage 문서로 확인했습니다. 실제 billing record는 확인하지 않았습니다. |

## 출처

- OpenAI API Changelog: https://developers.openai.com/api/docs/changelog
- OpenAI API Docs, Agents API overview: https://developers.openai.com/api/docs/guides/agents-api/overview
- OpenAI API Docs, Agents API architecture: https://developers.openai.com/api/docs/guides/agents-api/architecture
- OpenAI API Docs, Run and continue sessions: https://developers.openai.com/api/docs/guides/agents-api/sessions
- OpenAI API Docs, OpenAI-hosted sandboxes: https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted
- OpenAI API Docs, Self-hosted sandboxes: https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted
- OpenAI API Docs, Sandbox security: https://developers.openai.com/api/docs/guides/agents-api/environments/security
- OpenAI API Docs, MCP connections: https://developers.openai.com/api/docs/guides/agents-api/tools/mcp
- OpenAI API Docs, Observability and usage: https://developers.openai.com/api/docs/guides/agents-api/observability
