---
edition: ai
decision: publish-candidate
title: "Claude Platform agent API 정식 출시 - 화면 조작, 절차 지식, 파일 상태를 한 루프로 묶었습니다"
date: 2026-08-21
subject: "Anthropic Claude Platform computer use, browser use, Skills API, and Files API general availability, August 19-20 2026"
summary: "Anthropic은 computer use, 새 browser use tool, Skills API, Files API를 Claude Platform의 일반 제공 기능으로 묶었습니다. 모델이 화면을 보고 클릭하는 데서 그치지 않고, 페이지 구조를 읽고, 조직의 절차 지식을 필요할 때만 불러오며, 파일을 API 상태로 재사용하는 agent loop를 만들 수 있게 됐지만 실행 환경, tenant 격리, prompt injection 방어는 여전히 애플리케이션 설계 책임으로 남습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Anthropic은 Claude Platform, computer use, browser use, Skills API, Files API의 개발·배포 주체이며 이 기사에 쓴 release note와 docs를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Anthropic이 2026년 8월 19일 Claude Platform release notes와 8월 20일 제품 글에서 agent용 API 묶음을 일반 제공으로 전환했습니다. 핵심은 모델 하나가 더 좋아졌다는 발표가 아니라, agent가 일을 끝내는 데 필요한 네 가지 표면을 한 흐름으로 연결한 점입니다. Claude는 데스크톱 화면을 조작하고, 웹페이지의 구조를 읽어 특정 요소를 대상으로 삼고, 조직이 만든 절차 지식을 필요할 때 불러오며, 입력·출력 파일을 반복 요청마다 다시 보내지 않고 `file_id`로 이어 쓸 수 있습니다.

SW 엔지니어에게 이 변화가 중요한 이유는 agent 구현의 병목이 prompt 작성에서 runtime 경계 설계로 옮겨가기 때문입니다. 이전의 computer use beta는 화면 좌표와 스크린샷 중심의 실험 기능에 가까웠습니다. 이번 GA 묶음은 `computer_toolset_20260801`, `browser_toolset_20260801`, `/v1/skills`, `/v1/files`처럼 API 계약이 붙은 부품을 제공합니다. 따라서 팀은 모델을 바꾸는 문제와 별개로, 어떤 환경에서 tool call을 실행하고 어떤 파일과 절차 지식을 어느 workspace에 두며 어떤 행동에 사람 확인을 요구할지 설계해야 합니다.

다만 이 발표를 “자율 agent가 production 준비를 끝냈다”는 뜻으로 읽으면 안 됩니다. 공식 문서는 computer use의 internet interaction과 prompt injection 위험을 별도 경계로 다루고, Files API의 파일은 end user나 session이 아니라 workspace 단위로 접근된다고 경고합니다. 이 기사의 중심 주장은 기능 출시와 작동 구조에 관한 E2 주장입니다. Anthropic이 제시한 고객 성과 수치나 agent 완성률은 독립 검증 없이 일반 성능 결론으로 쓰지 않습니다.

## 화면 좌표에서 페이지 구조로 이동하는 agent loop

computer use tool은 Claude에게 screenshot, mouse, keyboard control을 주는 client toolset입니다. 요청의 `tools` 배열에 `{"type": "computer_toolset_20260801"}` 하나를 넣으면 `screenshot`, `left_click`, `type`, `zoom` 같은 member tool 17개가 열립니다. Claude가 직접 사용자의 컴퓨터에 붙는 구조는 아닙니다. 애플리케이션이 Claude의 `tool_use` block을 받고, 자신이 관리하는 VM이나 container에서 해당 동작을 실행한 뒤, 결과를 `tool_result`로 다시 보냅니다.

이번 GA에서 중요한 변화는 batch action입니다. Claude는 한 turn에 click, type, screenshot 같은 여러 member tool call을 함께 반환할 수 있습니다. 실행자는 이 block들을 병렬로 처리하지 않고 순서대로 실행해야 합니다. 앞선 click이 어떤 입력창을 focus했는지에 따라 뒤의 type 결과가 달라지기 때문입니다. 하나가 실패하면 뒤의 action은 실행하지 않았다는 결과를 모두 돌려줘야 하며, 모든 `tool_use` block에 대응하는 `tool_result`가 없으면 다음 요청이 거부됩니다.

새 browser use tool은 같은 agent loop를 웹페이지에 더 가깝게 맞춥니다. `browser_toolset_20260801`은 browser viewport 안에서 동작하고, screenshot만 보는 대신 page structure, form, tab, element reference를 읽습니다. 문서 예시는 `read_page` 결과가 link, textbox, button을 reference와 함께 돌려주고, Claude가 다음 turn에서 그 reference를 대상으로 act할 수 있음을 보여 줍니다. 웹 애플리케이션 작업은 좌표를 추정해 클릭하는 방식보다 DOM과 accessibility tree에서 나온 참조를 쓰는 편이 더 안정적인 설계가 됩니다.

이 차이는 운영 구현에도 영향을 줍니다. 데스크톱 전체를 움직여야 하는 업무라면 computer use가 필요하지만, 웹 portal 안에서 양식을 채우거나 navigation을 수행하는 업무라면 browser use가 더 좁은 권한 경계를 제공합니다. 두 경우 모두 Claude가 action을 제안하고 애플리케이션이 실행하는 구조라서, sandbox와 네트워크 allowlist, credential 취급, consequential action의 human confirmation은 호출자가 설계해야 합니다.

## Skills와 Files는 prompt가 아니라 상태와 절차를 분리합니다

Skills API의 역할은 긴 system prompt를 계속 붙이는 것이 아닙니다. Anthropic 문서는 Skill을 instructions, metadata, optional resources가 들어 있는 filesystem 기반 디렉터리로 설명합니다. Claude는 시작 시 Skill의 name과 description 같은 metadata만 보고, 요청이 해당 description과 맞을 때 SKILL.md를 읽습니다. SKILL.md가 다른 reference file이나 script를 가리키면 그때 필요한 자료를 추가로 읽거나 실행합니다.

이 구조는 agent에게 조직의 업무 절차를 주입하는 방식을 바꿉니다. 예를 들어 보험 청구 agent가 있다면 filing procedure, template, validation script를 Skill 안에 넣고, Claude가 관련 작업에서만 이를 불러오게 만들 수 있습니다. 모든 요청에 긴 운영 매뉴얼을 붙이는 방식보다 context 사용량을 줄이고, 절차 지식의 version 관리도 API 객체나 파일 묶음에 가깝게 만들 수 있습니다.

Files API는 agent loop의 입력과 산출물을 message payload 밖으로 뺍니다. 파일을 한 번 upload하면 `file_id`를 받고, 이후 Messages API 요청에서 이 ID를 참조합니다. PDF와 text는 document block, image는 image block, code execution용 dataset 등은 container upload block으로 연결됩니다. Skills나 code execution tool이 만든 파일은 다운로드할 수 있지만, 사용자가 upload한 파일 객체는 기본적으로 같은 방식의 output artifact가 아닙니다.

여기서 가장 실무적인 경계는 workspace입니다. 공식 문서는 upload된 file이 end user, conversation, session이 아니라 workspace 전체에서 접근된다고 설명합니다. 같은 workspace의 API key는 같은 file에 접근할 수 있으므로, 다중 tenant 애플리케이션이 사용자에게서 `file_id`를 그대로 받아 신뢰하면 다른 사용자의 파일을 읽게 하는 참조 취약점이 생길 수 있습니다. Anthropic은 tenant별 workspace를 격리 경계로 쓰라고 안내합니다.

## API 계약은 넓어졌지만 검증 책임은 줄지 않았습니다

이번 출시가 agent 개발에 주는 의미는 “모델에게 브라우저를 보여주면 된다”보다 큽니다. agent runtime은 네 층으로 나뉩니다. 모델은 다음 action을 고르고, toolset은 action schema를 정하며, 호출자의 executor는 실제 OS나 browser에서 action을 수행하고, Files·Skills는 작업에 필요한 장기 입력과 절차 지식을 관리합니다. 이 분리가 명확해지면 실패를 분석할 위치도 분명해집니다. 클릭 실패는 모델 추론만의 문제가 아니라 browser reference, executor 구현, 화면 상태, permission policy의 문제일 수 있습니다.

또 하나의 변화는 비용과 지연시간의 모양입니다. batch action은 여러 API 왕복을 줄일 수 있지만, 한 turn 안에서 여러 행동이 실제로 실행되므로 human confirmation과 실패 처리도 action 단위로 들어가야 합니다. Files API는 같은 문서를 반복 전송하지 않게 해 주지만, 파일 보존 기간, workspace 접근권한, 삭제 정책을 별도 상태로 운영해야 합니다. Skills는 context를 아낄 수 있지만, Skill description이 너무 넓으면 원치 않는 절차가 로드될 수 있고, 너무 좁으면 필요한 순간에 호출되지 않을 수 있습니다.

보안 측면에서는 공식 문서의 경고가 중심입니다. computer use는 internet과 만날 때 표준 API보다 다른 위험을 갖고, 웹페이지나 이미지 안의 지시가 개발자의 instruction과 충돌할 수 있습니다. Anthropic은 prompt injection classifier와 confirmation 유도 방어층을 설명하지만, 동시에 전용 VM·container, 민감 정보 제한, 도메인 allowlist, 현실 영향이 큰 행동에 대한 사람 확인을 권장합니다. 즉 방어층은 runtime 설계를 대체하지 않고, runtime 설계 위에 얹히는 추가 신호입니다.

한국의 개발 조직에도 적용 지점이 뚜렷합니다. 내부 업무 시스템과 금융·보험 portal처럼 API가 없거나 자동화가 제한된 화면을 agent가 다루게 하려면, browser use와 computer use는 직접적인 검토 대상입니다. 동시에 개인정보와 고객 문서가 들어가는 workflow에서는 Files API의 workspace 경계, HIPAA 같은 미국 규제 workload eligibility가 한국의 개인정보보호법·전자금융감독규정 요구를 자동으로 충족하지 않는다는 점을 분리해서 봐야 합니다.

## benchmark 또는 재현 결과

이 기사는 Claude Platform API를 직접 호출하지 않았습니다. Anthropic account, 해당 기능을 쓸 수 있는 모델 접근권한, sandbox executor, browser runtime, 테스트용 파일·Skill 구성이 필요하기 때문입니다. 재현성 상태는 R1입니다. 공식 문서로 request shape, toolset 이름, agent loop, batch action 처리, Skills의 progressive disclosure, Files API의 workspace 경계는 설명할 수 있지만, 편집국이 실제 workflow를 실행해 latency, cost, completion rate를 측정한 로그는 없습니다.

Anthropic 제품 글에는 고객 workflow 시간이 줄었다는 사례가 나오지만, 이 기사는 그 수치를 성능 결론으로 쓰지 않습니다. workload, baseline, 반복 횟수, 실패 처리, 비용 산정 방식이 공개 benchmark 수준으로 제시되지 않았기 때문입니다. 중심 결론은 공개된 API 계약과 문서화된 실행 구조가 agent 설계의 경계를 바꿨다는 범위로 제한합니다.

## 이해상충과 취재 조건

이 기사에 사용한 release note, 제품 글, computer use·browser use·Skills·Files 문서는 모두 Anthropic이 작성한 1차 자료입니다. 기능 출시, toolset 이름, request/response shape, 보안 주의사항, workspace 접근 범위를 확인하는 데는 적합하지만, Anthropic agent runtime이 다른 vendor나 자체 구현보다 우수하다는 독립 근거는 아닙니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 기존 AI판 후보 원장은 발견 신호와 중복 확인에만 사용했고, 기사 사실은 공개된 공식 원문으로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Anthropic은 2026년 8월 19일 Claude Platform release notes에서 computer use, browser use, Files API, Skills API의 GA 전환과 관련 agent 기능을 공지했고, 8월 20일 제품 글에서 이를 production agent 묶음으로 설명했습니다. | E1 · P1 | Claude Platform release notes와 Anthropic 제품 글로 확인했습니다. 출시·지원 사실의 근거이며 제품 효과의 독립 검증은 아닙니다. |
| C2. `computer_toolset_20260801`은 no beta header GA toolset이며, 하나의 toolset 선언으로 screenshot, click, type, zoom 등 17개 member tool을 열고 호출자 환경에서 순차 실행하는 agent loop를 사용합니다. | E2 · P1 | computer use docs와 release notes로 확인했습니다. 실제 API 호출과 executor 구현은 수행하지 않았습니다. |
| C3. browser use tool은 `browser_toolset_20260801` client toolset으로, browser viewport에서 page structure와 element reference를 읽고 action 대상으로 삼을 수 있습니다. | E2 · P1 | browser use docs와 release notes로 확인했습니다. 특정 웹앱에서의 성공률이나 prompt injection 저항성은 검증하지 않았습니다. |
| C4. Skills API는 Skill을 filesystem 기반 instructions·metadata·resource 묶음으로 다루며, Claude는 metadata를 먼저 보고 필요한 경우 SKILL.md와 추가 파일·script를 불러오는 progressive disclosure 구조를 사용합니다. | E2 · P1 | Agent Skills docs와 release notes로 확인했습니다. 편집국이 custom Skill을 upload하거나 versioning API를 호출하지는 않았습니다. |
| C5. Files API는 파일을 한 번 upload한 뒤 `file_id`로 Messages API에서 재참조하게 하며, file 접근 경계는 end user나 session이 아니라 workspace입니다. | E2 · P1 | Files API docs와 release notes로 확인했습니다. 실제 파일 upload, expiration, deletion 동작은 실행하지 않았습니다. |
| C6. computer use와 browser use를 production workflow에 넣을 때는 sandbox, domain allowlist, 민감 정보 제한, prompt injection 방어, consequential action 확인을 호출자 설계에 포함해야 합니다. | E2 · P1 | computer use docs의 security considerations와 browser/computer agent loop 구조에서 도출했습니다. Anthropic의 classifier 방어 효과는 독립 평가하지 않았습니다. |

## 출처

1. Claude Platform release notes: https://platform.claude.com/docs/en/release-notes/overview
2. Anthropic, "Build production agents with computer use, the Skills API, and the Files API": https://claude.com/blog/computer-use-skills-api-files-api
3. Computer use tool docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
4. Browser use tool docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool
5. Agent Skills docs: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
6. Files API docs: https://platform.claude.com/docs/en/build-with-claude/files
