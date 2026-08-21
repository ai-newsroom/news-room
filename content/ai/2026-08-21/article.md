---
edition: ai
decision: publish-candidate
title: "Claude Platform agent API 정식 출시 - 화면 조작부터 파일 관리까지 연결"
date: 2026-08-21
subject: "Anthropic Claude Platform computer use, browser use, Skills API, and Files API general availability, August 19-20 2026"
summary: "Anthropic이 computer use, browser use, Skills API, Files API를 Claude Platform의 정식 기능으로 내놓았습니다. Claude가 화면과 웹페이지를 조작하고, 필요한 업무 절차를 불러오며, 작업 파일을 다음 요청에서도 이어 쓸 수 있게 됐습니다. 다만 실제 실행 환경과 사용자별 데이터 격리, prompt injection 방어는 애플리케이션이 직접 설계해야 합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Anthropic은 Claude Platform, computer use, browser use, Skills API, Files API의 개발·배포 주체이며 이 기사에 쓴 release note와 docs를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Anthropic이 2026년 8월 19일 Claude Platform release notes와 8월 20일 제품 글에서 agent 개발에 쓰는 기능 네 가지를 정식 출시했습니다. computer use는 데스크톱 화면을 조작하고, browser use는 웹페이지 구조를 읽습니다. Skills API는 조직의 업무 절차를 필요한 순간에 불러오고, Files API는 작업에 쓰는 파일을 다음 요청에서도 이어 쓸 수 있게 합니다.

예를 들어 Claude가 사내 보험 청구 시스템에서 문서를 확인하고 내용을 입력한다고 해보겠습니다. Claude는 browser use로 입력칸과 버튼을 찾고, Skills API에서 청구 절차를 읽은 뒤, Files API에 올라온 증빙 문서를 `file_id`로 참조할 수 있습니다. 데스크톱 프로그램까지 다뤄야 한다면 computer use로 화면을 보고 클릭하거나 글자를 입력합니다.

이번 출시는 이 기능들을 실험 단계에서 꺼내 API로 연결했다는 데 의미가 있습니다. `computer_toolset_20260801`, `browser_toolset_20260801`, `/v1/skills`, `/v1/files`처럼 호출 방법이 정해졌기 때문에 애플리케이션은 각 기능을 하나의 작업 흐름으로 구성할 수 있습니다. 다만 Claude가 실제 컴퓨터에 직접 접속하는 것은 아닙니다. 화면 조작을 실행할 환경, 사용자별 파일 격리와 prompt injection 방어는 여전히 개발자가 맡아야 합니다.

## computer use는 화면을 보고 조작합니다

computer use는 Claude가 screenshot을 보고 mouse와 keyboard 동작을 선택하게 하는 client toolset입니다. 요청의 `tools` 배열에 `{"type": "computer_toolset_20260801"}`를 넣으면 `screenshot`, `left_click`, `type`, `zoom`을 비롯한 member tool 17개를 사용할 수 있습니다.

Claude가 클릭이나 입력을 선택해도 그 동작을 직접 실행하지는 않습니다. 애플리케이션이 Claude의 `tool_use` block을 받은 뒤 자신이 관리하는 VM이나 container에서 동작을 실행합니다. 실행 결과는 `tool_result`로 Claude에게 돌려보냅니다. 따라서 어떤 운영체제와 프로그램을 열어 줄지, 자격 증명을 어떻게 전달할지, 어느 행동 전에 사람의 확인을 받을지는 애플리케이션이 정합니다.

정식 버전에서는 여러 동작을 한 turn에 묶어 보내는 batch action도 지원합니다. API 왕복은 줄일 수 있지만 click, type, screenshot을 동시에 실행해서는 안 됩니다. 앞선 click이 입력칸을 선택해야 다음 type이 제대로 작동하므로, 받은 순서대로 실행해야 합니다. 중간 동작이 실패하면 뒤의 동작을 실행하지 않았다는 결과까지 돌려줘야 하며, 모든 `tool_use`에 대응하는 `tool_result`가 없으면 다음 요청이 거부됩니다.

## browser use는 좌표 대신 페이지 구조를 읽습니다

browser use는 웹페이지 작업에 범위를 좁힌 도구입니다. `browser_toolset_20260801`은 browser viewport 안에서 동작하며, screenshot만 보고 좌표를 짐작하는 대신 page structure, form, tab과 element reference를 읽습니다. 문서의 `read_page` 예시에서는 link, textbox, button이 각각 reference와 함께 반환됩니다. Claude는 다음 turn에서 그 reference를 지정해 원하는 요소를 조작합니다.

웹 portal에서 양식을 채우거나 메뉴를 이동하는 작업이라면 페이지 구조를 읽는 방식이 좌표를 추정하는 것보다 안정적입니다. 데스크톱 전체를 움직여야 할 때는 computer use가 필요하지만, 웹페이지 안에서 끝나는 작업은 browser use로 권한 범위를 더 좁힐 수 있습니다. 두 기능 모두 Claude가 행동을 제안하고 애플리케이션이 실행하므로 sandbox, 네트워크 allowlist와 중요한 행동에 대한 사람 확인이 필요합니다.

## Skills는 필요한 업무 절차만 불러옵니다

Skills API는 긴 운영 매뉴얼을 모든 요청의 system prompt에 붙이는 대신, 필요한 절차만 골라 읽게 합니다. Anthropic은 Skill을 instructions, metadata와 optional resources가 들어 있는 filesystem 기반 디렉터리로 설명합니다. Claude는 처음에 Skill의 name과 description만 확인합니다. 현재 작업과 맞는 Skill을 찾으면 SKILL.md를 읽고, 그 파일이 가리키는 reference file이나 script가 필요할 때 추가로 불러옵니다.

보험 청구 업무라면 filing procedure, template과 validation script를 하나의 Skill에 넣을 수 있습니다. Claude는 보험 청구 작업을 할 때만 이 자료를 읽습니다. 이렇게 하면 매번 긴 지침을 보내지 않아도 되고, 업무 절차와 관련 파일을 한 묶음으로 version 관리할 수 있습니다. 다만 Skill description이 너무 넓으면 관계없는 작업에서도 불러올 수 있고, 너무 좁으면 필요한 때 선택하지 못할 수 있습니다.

## Files API는 같은 파일을 다시 보내지 않습니다

Files API에서는 파일을 한 번 upload한 뒤 받은 `file_id`를 Messages API 요청에서 다시 사용합니다. PDF와 text는 document block으로, image는 image block으로 연결합니다. code execution에 쓸 dataset 등은 container upload block으로 전달합니다. Skills나 code execution tool이 만든 파일은 내려받을 수 있지만, 사용자가 upload한 파일 객체가 모두 같은 방식의 output artifact가 되는 것은 아닙니다.

중요한 점은 파일의 접근 범위입니다. 공식 문서에 따르면 upload된 file은 end user, conversation이나 session이 아니라 workspace 전체에서 접근됩니다. 같은 workspace의 API key는 같은 file을 읽을 수 있습니다. 다중 tenant 서비스가 사용자가 보낸 `file_id`를 확인 없이 신뢰하면 다른 사용자의 파일을 읽는 참조 취약점이 생길 수 있습니다. Anthropic은 tenant마다 workspace를 나누어 격리하라고 안내합니다.

## 실제 동작과 보안은 애플리케이션이 맡습니다

Claude는 다음 행동을 고르지만, 실제 OS나 browser에서 실행하는 주체는 호출자의 executor입니다. toolset은 Claude가 선택할 수 있는 행동의 형식을 정하고, Files와 Skills는 작업 파일과 업무 절차를 보관합니다. 이 역할을 나누어 보면 오류가 난 곳도 찾기 쉬워집니다. 클릭이 실패했을 때는 모델의 판단뿐 아니라 browser reference, executor 구현, 화면 상태와 permission policy를 함께 확인해야 합니다.

기능을 연결하면 운영해야 할 상태도 늘어납니다. batch action은 API 왕복을 줄이지만 각 행동의 실패 처리와 사람 확인이 필요합니다. Files API를 쓰면 같은 문서를 반복 전송하지 않아도 되지만 파일 보존 기간, workspace 접근권한과 삭제 정책을 정해야 합니다. Skills는 context 사용량을 줄일 수 있지만 어떤 절차가 언제 선택됐는지 추적할 수 있어야 합니다.

보안은 API가 대신 해결해 주지 않습니다. 웹페이지나 이미지 안에 Claude의 행동을 바꾸려는 지시가 들어 있으면 개발자가 준 instruction과 충돌할 수 있습니다. Anthropic은 prompt injection classifier와 확인을 유도하는 방어 기능을 설명하면서도 전용 VM·container, 민감 정보 제한, 도메인 allowlist와 현실에 큰 영향을 주는 행동에 대한 사람 확인을 권장합니다.

한국의 개발 조직도 내부 업무 시스템이나 금융·보험 portal처럼 API가 없거나 자동화가 제한된 화면에서 이 기능을 검토할 수 있습니다. 개인정보와 고객 문서를 다룬다면 Files API의 workspace 경계를 특히 주의해야 합니다. HIPAA 같은 미국 규제 workload eligibility가 한국의 개인정보보호법이나 전자금융감독규정 요구를 자동으로 충족하는 것은 아닙니다.

## 공개 문서로 확인한 범위

이 기사는 Claude Platform API를 직접 호출하지 않았으며 재현성 상태는 R1입니다. Anthropic account, 해당 기능을 사용할 수 있는 모델 접근권한, sandbox executor, browser runtime과 테스트용 파일·Skill 구성이 필요하기 때문입니다. 공식 문서에서 request shape, toolset 이름, agent loop, batch action 처리, Skills가 필요한 자료만 불러오는 방식과 Files API의 workspace 경계를 확인했습니다. 하지만 편집국이 실제 workflow를 실행해 latency, cost와 completion rate를 측정한 로그는 없습니다.

Anthropic 제품 글에는 고객의 workflow 시간이 줄었다는 사례가 나옵니다. 그러나 workload, baseline, 반복 횟수, 실패 처리와 비용 산정 방식이 공개 benchmark 수준으로 제시되지는 않았습니다. 따라서 이번 기사에서는 기능이 정식 API로 연결됐다는 사실과 문서에 나온 실행 구조까지만 설명하며, 실제 성능은 별도 검증이 필요한 영역으로 남깁니다.

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
