---
edition: ai
decision: publish-candidate
title: "Codex harness 공개 - 제품 안에 붙이는 코딩 에이전트 실행 루프"
date: 2026-08-24
subject: "OpenAI Codex as a platform, open-source Codex harness, app-server and Codex SDK, August 19 2026"
summary: "OpenAI는 Codex를 하나의 앱이나 CLI가 아니라 공개 harness 위에서 도는 에이전트 실행 시스템으로 설명했습니다. 핵심 변화는 모델 호출 자체보다 그 바깥에서 작업을 이어 가는 루프입니다. 애플리케이션은 화면, 문서, 도구, 승인 흐름을 유지하고 Codex harness는 thread, turn, tool call, sandbox, approval, event stream을 맡습니다. 공개 저장소와 SDK 패키지로 구조는 확인되지만, 성능 수치는 OpenAI가 제시한 자체 결과입니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["OpenAI는 Codex, Codex CLI, app-server, Codex SDK와 관련 문서의 개발·배포 주체이며 이 기사에 쓴 발표문, 문서, GitHub 저장소와 npm package metadata를 관리합니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

OpenAI가 2026년 8월 19일 Codex를 하나의 코딩 앱보다 넓은 플랫폼으로 설명했습니다. 바뀐 지점은 모델 이름이 아닙니다. Codex가 작업을 이어 가는 실행 루프를 공개 harness, app-server, SDK로 나누고, 다른 제품 안에 넣을 수 있게 했다는 점입니다.

코딩 에이전트는 prompt를 보내고 답을 받는 기능만으로 움직이지 않습니다. repository를 읽고, 필요한 파일을 고르고, 명령을 실행하고, 실패를 확인한 뒤 다음 행동을 정해야 합니다. 위험한 작업 앞에서는 사용자 승인도 받아야 합니다. OpenAI가 말하는 harness는 이 과정을 둘러싼 실행 시스템입니다. 모델은 그 안에서 판단하지만, 실제 제품 통합에서는 화면, 문서, 도구 권한, 승인 정책을 누가 소유하는지가 더 중요해집니다.

SW 엔지니어에게 이 공개가 중요한 이유는 코딩 에이전트를 범용 chat 창으로만 도입하지 않아도 되기 때문입니다. 보안 조사 도구, 운영 dashboard, 내부 ticket system, code review workflow 같은 기존 제품이 자기 UI와 기록 체계를 유지한 채 Codex의 실행 루프를 붙일 수 있습니다. 다만 공개된 것은 harness와 통합 표면입니다. 모델 접근, managed service, 실제 업무별 성능은 별도 조건으로 봐야 합니다.

## 코딩 작업은 모델 호출 뒤에도 계속됩니다

일회성 code generation에서는 모델이 한 번에 파일 변경안을 내는 것처럼 보입니다. 하지만 실제 개발 작업은 그렇게 끝나지 않습니다. 에이전트는 작업 설명을 이해한 뒤 repository 구조를 찾고, 관련 파일을 읽고, patch를 만들고, test를 실행합니다. 실패하면 원인을 다시 좁힙니다. 그 과정에서 어디까지 파일을 읽을 수 있는지, 어떤 명령을 허락 없이 실행할 수 있는지, 어떤 결과를 사용자에게 stream할지도 정해야 합니다.

Codex 발표문은 이 부분을 harness라고 부릅니다. harness는 conversation state를 관리하고, 실행 중 event를 보내며, tool을 호출하고, sandbox와 approval policy를 적용합니다. 그래서 같은 모델을 써도 harness 설계가 다르면 결과가 달라질 수 있습니다. OpenAI는 ARC-AGI-3에서 retained reasoning과 context compaction을 넣은 harness가 GPT-5.6 Sol 점수를 13.3%에서 38.3%로 올리고 output token을 6분의 1로 줄였다고 밝혔습니다. 이 수치는 OpenAI 자체 설명으로만 다루며, 이 기사에서는 독립 성능 결론으로 쓰지 않습니다.

기술적으로 더 중요한 점은 책임이 나뉜다는 점입니다. 모델은 다음 행동을 고르지만, host application은 어떤 파일과 도구를 노출할지, 승인 요청을 어떻게 보여 줄지, 결과를 어느 업무 기록에 남길지 결정합니다. 이 구분이 생기면 에이전트 도입 판단은 “어느 모델이 더 똑똑한가”에서 “우리 제품의 상태와 권한 체계를 어느 harness에 연결할 것인가”로 옮겨 갑니다.

## app-server는 thread와 승인 흐름을 제품에 연결합니다

Codex app-server 문서는 이 기능을 rich client용 protocol로 설명합니다. 예를 들어 VS Code extension 같은 client는 app-server를 통해 authentication, conversation history, approval, streamed agent event를 다룹니다. 제품 안에 더 깊게 넣을 때도 같은 표면을 사용할 수 있습니다.

연결 방식은 JSON-RPC 2.0 메시지입니다. 기본 transport는 stdio이고, WebSocket과 Unix socket도 문서화되어 있습니다. WebSocket listener는 `GET /readyz`와 `GET /healthz` health probe를 제공하고, 원격 연결에는 token 기반 인증을 설정해야 합니다. 문서는 non-loopback WebSocket listener가 rollout 중 기본적으로 인증 없이 열릴 수 있으므로, 원격으로 노출하기 전에 WebSocket auth를 설정하라고 경고합니다.

이 경고는 제품 통합에서 핵심입니다. app-server를 쓰면 내부 도구가 에이전트가 실제로 움직이는 경로가 됩니다. 따라서 “Codex가 할 수 있는 일”은 모델 능력만으로 정해지지 않습니다. app-server가 연결된 host, filesystem, shell, MCP server, approval policy가 합쳐져 행동 범위가 정해집니다. 개발팀은 thread별 sandbox, remote host, network 노출, bearer token 보관, overload retry를 API 통합의 일부로 설계해야 합니다.

## SDK는 CI와 내부 도구에서 Codex를 호출합니다

OpenAI는 app-server와 별도로 Codex SDK를 문서화했습니다. TypeScript SDK는 애플리케이션이 local Codex thread를 시작하고, 이어서 실행하고, 과거 thread를 resume할 수 있게 합니다. Python SDK는 local Codex app-server를 JSON-RPC로 제어하며 Python 3.10 이상을 요구한다고 문서에 적혀 있습니다.

공개 npm metadata도 확인할 수 있습니다. `@openai/codex`와 `@openai/codex-sdk`는 확인 시점에 모두 `0.149.0`이었고, license는 Apache-2.0이며 repository는 `openai/codex`로 표시됩니다. GitHub의 `openai/codex` 저장소는 Codex CLI, Rust 구현, docs, SDK source를 포함하고, app-server source는 `codex-rs/app-server` 아래에 있습니다. 이 저장소의 `main` HEAD는 확인 시점에 `6677fd827d2c34cd65edb240418f80b3f97d2cc0`였고, `rust-v0.149.0` tag는 annotated tag를 거쳐 commit `758ef40f50c1a458425c7cfbf1eb12cbc07af0b0`를 가리켰습니다.

이 정보로 구현 표면은 확인할 수 있지만, 곧바로 운영 안정성을 확인했다고 볼 수는 없습니다. app-server 문서는 WebSocket transport와 command를 experimental, unsupported for production workloads로 표시합니다. SDK를 CI나 내부 도구에 넣는 팀은 package version만 고정해서는 부족합니다. Codex binary, sandbox preset, approval policy, workspace write 범위, log retention도 함께 고정해야 합니다.

## 공개된 harness와 닫힌 서비스는 구분해야 합니다

OpenAI의 open-source component 문서는 Codex CLI, Codex SDK, Codex App Server, Skills, Plugins, Universal cloud environment 같은 공개 component와 IDE extension, Codex cloud 같은 비공개 component를 구분합니다. 이 구분은 도입 판단에 직접 영향을 줍니다. local CLI와 SDK를 쓰면 harness source와 package metadata를 볼 수 있습니다. 그렇다고 ChatGPT 안의 cloud product나 IDE extension 전체 동작이 모두 공개됐다는 뜻은 아닙니다.

따라서 “Codex가 open source가 됐다”보다 정확한 표현은 “Codex의 핵심 harness와 여러 통합 component가 공개됐다”입니다. 모델 접근은 별도이고, managed service 운영, cloud 실행 환경, 일부 client surface는 여전히 OpenAI가 운영하는 닫힌 영역입니다. 반대로 공개된 harness는 제품팀이 agent loop, event stream, sandbox, approval 경계를 검토하고 자기 업무 앱에 맞게 감쌀 수 있는 출발점이 됩니다.

이 구조는 DeepSeek Harness, Claude Code, 다른 coding agent와 비교할 때도 기준을 바꿉니다. 단순히 모델 점수나 채팅 UI를 비교하기보다, 실행 loop가 어디까지 공개됐는지 봐야 합니다. app이 tool과 권한을 어떻게 주입하는지, 사용자가 승인한 행동이 어떤 event로 남는지도 확인해야 합니다. 같은 repository와 task라도 harness가 context를 압축하고 실패를 처리하는 방식에 따라 결과와 비용이 달라질 수 있기 때문입니다.

## 도입 전에는 기록과 권한부터 설계해야 합니다

국내 개발 조직에도 이 변화는 바로 닿습니다. 많은 팀은 이미 Jira, GitHub, GitLab, 사내 배포 dashboard, 보안 ticket queue처럼 특정 업무에 맞춘 화면과 승인 흐름을 갖고 있습니다. Codex harness를 그대로 chat 창으로 쓰는 대신 그 도구들 안에 붙이면 사용자는 기존 업무 기록을 떠나지 않고 에이전트 작업을 맡길 수 있습니다.

하지만 그만큼 보안과 감사 설계가 중요해집니다. 에이전트가 읽은 파일, 실행한 명령, 받은 tool result, 승인 요청과 승인자를 thread event로 남겨야 합니다. CI에서 Codex를 부른다면 실패한 test log와 patch diff뿐 아니라 sandbox preset, model id, SDK version, Codex binary version, network access, approval bypass 여부를 같이 보존해야 합니다.

한국의 금융, 공공, 대기업 환경에서는 특히 권한 분리가 먼저입니다. app-server나 SDK가 내부 시스템에 연결되는 순간 agent는 개발자 개인 도구가 아니라 업무 시스템의 일부가 됩니다. 사용자별 repository 권한, secret 접근, shell command 범위, 외부 network, audit log retention은 host application이 책임져야 합니다. Codex harness는 그 경계를 표현할 수 있는 표면을 제공하지만, 조직의 정책을 자동으로 대신 설계하지는 않습니다.

## 공개 자료로 확인한 범위는 구조까지입니다

이 기사의 중심 주장은 공개 문서와 공개 artifact로 확인한 구조에 한정됩니다. OpenAI 발표문, Codex app-server 문서, Codex SDK 문서, open-source component 문서, `openai/codex` GitHub 저장소, npm package metadata를 확인했습니다. 편집국은 Codex app-server를 실행하거나 SDK로 thread를 만들지는 않았습니다.

따라서 재현성 상태는 R1입니다. 공개 code와 package가 있어 독자가 실행을 시도할 수 있는 경로는 있지만, 이 기사 작성 과정에서는 local install, WebSocket 연결, JSON-RPC message trace, sandbox 변경, approval flow, CI 통합을 직접 재현하지 않았습니다. OpenAI가 제시한 ARC-AGI-3 harness 수치도 독립 실행하지 않았으므로 성능 주장이 아니라 vendor가 밝힌 배경 설명으로만 다뤘습니다.

## 이해상충과 취재 조건

이 기사에 사용한 발표문, Codex 문서, GitHub 저장소와 npm package metadata는 OpenAI 또는 OpenAI 공식 계정이 관리하는 1차 자료입니다. 공개 component, version, license, protocol, warning, integration surface를 확인하는 데는 적합하지만, OpenAI의 성능 우월성을 독립적으로 증명하지는 않습니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 X, 2차 해설은 발견 신호와 중복 확인에만 사용했고, 기사 사실은 열린 공식 원문과 공개 artifact로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. OpenAI는 2026년 8월 19일 Codex를 공개 harness 위에 올린 플랫폼으로 설명했고, Codex harness가 context 수집, tool 사용, sandbox, approval, multi-turn 작업 지속을 맡는다고 밝혔습니다. | E1 · P1 | OpenAI Developer Blog 발표문으로 확인했습니다. 발표 사실과 OpenAI의 설명 범위이며 성능 우월성의 독립 검증은 아닙니다. |
| C2. Codex app-server는 rich client가 authentication, conversation history, approval, streamed agent event를 다루는 통합 표면이며, 구현은 `openai/codex` 저장소의 `codex-rs/app-server`에 공개되어 있습니다. | E2 · P1/P2 | app-server 공식 문서와 GitHub 저장소로 확인했습니다. app-server를 실행하지는 않았습니다. |
| C3. app-server protocol은 JSON-RPC 2.0 메시지를 쓰며 stdio, WebSocket, Unix socket transport를 문서화하고, 원격 WebSocket 노출에는 인증과 TLS가 필요하다고 경고합니다. | E2 · P1 | app-server 문서로 확인했습니다. 실제 WebSocket listener, auth, overload path를 재현하지는 않았습니다. |
| C4. Codex SDK는 TypeScript와 Python에서 local Codex thread를 시작·이어 실행·resume하는 경로를 제공하며, Python SDK는 local app-server를 JSON-RPC로 제어한다고 문서화되어 있습니다. | E2 · P1/P2 | SDK 문서와 npm package metadata로 확인했습니다. Python package는 이 실행 환경에 `pip` 모듈이 없어 조회하지 못했습니다. |
| C5. `@openai/codex`와 `@openai/codex-sdk` npm package는 확인 시점 기준 `0.149.0`, Apache-2.0 license, `openai/codex` repository URL을 표시했습니다. | E2 · P2 | npm registry metadata로 확인했습니다. package를 설치하거나 실행하지는 않았습니다. |
| C6. OpenAI open-source component 문서는 Codex CLI, Codex SDK, Codex App Server, Skills, Plugins, Universal cloud environment를 공개 component로, IDE extension과 Codex cloud를 비공개 component로 구분합니다. | E2 · P1/P2 | OpenAI open-source component 문서와 GitHub 경로로 확인했습니다. 각 component의 전체 release process나 managed service 운영은 확인하지 않았습니다. |
| C7. OpenAI는 ARC-AGI-3에서 retained reasoning과 context compaction을 넣은 harness가 GPT-5.6 Sol 점수를 13.3%에서 38.3%로 올리고 output token을 6분의 1로 줄였다고 밝혔습니다. | E2 · P1 | OpenAI 발표문으로 확인했습니다. 독립 benchmark가 아니며 raw log, exact harness config, 재실행 결과는 확인하지 못했습니다. |

## 출처

1. OpenAI Developer Blog, "Codex as a platform: build on the open agent harness": https://developers.openai.com/blog/codex-as-a-platform
2. GitHub, `openai/codex`: https://github.com/openai/codex
3. OpenAI Codex Docs, "Codex App Server": https://developers.openai.com/codex/app-server
4. OpenAI Codex Docs, "Codex SDK": https://developers.openai.com/codex/sdk
5. OpenAI Codex Docs, "Open Source": https://developers.openai.com/codex/open-source
6. npm, `@openai/codex`: https://www.npmjs.com/package/@openai/codex
7. npm, `@openai/codex-sdk`: https://www.npmjs.com/package/@openai/codex-sdk
