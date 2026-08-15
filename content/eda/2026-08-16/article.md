---
edition: eda
decision: publish-candidate
title: "OpenROAD-MCP 1.0.0은 물리설계 AI 보조를 채팅 답변에서 실행 세션으로 옮깁니다"
date: 2026-08-16
subject: "The-OpenROAD-Project OpenROAD-MCP v1.0.0 공개 릴리스와 OpenROAD/ORFS MCP 실행 경로"
summary: "OpenROAD-MCP 1.0.0은 MCP client가 OpenROAD 세션을 만들고 Tcl 명령을 실행하며 ORFS 리포트 이미지를 읽는 공개 경로를 npm과 Docker로 제공합니다. 다만 QoR, PPA, runtime 개선은 이 릴리스만으로 확인되지 않으며 실제 판단은 각 설계와 OpenROAD/ORFS 환경에서 재실행해야 합니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["중심 근거는 The-OpenROAD-Project의 공개 GitHub 릴리스, README, architecture/API/security 문서와 npm registry metadata입니다.", "편집국은 OpenROAD-MCP 서버와 OpenROAD/ORFS flow를 이번 턴에서 직접 실행하지 않았고, QoR·PPA·runtime 개선을 재현하지 않았습니다."]
---

물리설계에서 AI 보조가 쓸모 있으려면 대답을 잘 쓰는 것보다 설계 도구의 현재 상태를 읽고, 필요한 명령을 실행하고, 그 결과를 다시 판단에 넣을 수 있어야 합니다. The-OpenROAD-Project가 2026년 8월 11일 공개한 OpenROAD-MCP v1.0.0은 이 흐름을 공개 EDA 도구인 OpenROAD와 OpenROAD-flow-scripts, 즉 ORFS에 연결합니다. 핵심 변화는 LLM이 물리설계 지식을 설명하는 수준을 넘어, MCP(Model Context Protocol) client를 통해 OpenROAD 세션과 리포트를 직접 다루는 실행 경로가 공식 패키지로 고정됐다는 점입니다.

OpenROAD는 RTL-to-GDSII, 즉 register-transfer level 설계에서 layout database까지 가는 디지털 구현 flow를 공개 도구로 제공하는 프로젝트입니다. ORFS는 그 위에서 synthesis, floorplan, placement, clock tree synthesis, routing, signoff report 생성을 묶는 flow script 모음입니다. OpenROAD-MCP는 여기에 MCP server를 붙여 Claude Code, Cursor, GitHub Copilot, Cline 같은 MCP client가 `version`, `report_checks`, `read_verilog`, `global_route` 같은 OpenROAD 명령을 도구 호출로 보내게 합니다.

## 달라진 지점은 모델이 아니라 feedback loop입니다

최근 EDA 에이전트 논의는 대체로 RTL 생성, benchmark 점수, 에이전트별 pass rate에 집중했습니다. 2026년 8월 14일 EDA판이 다룬 ACE-RTL도 Verilog 생성과 CVDP benchmark 실행 경로가 중심이었습니다. OpenROAD-MCP의 새 국면은 다른 곳에 있습니다. 이 릴리스는 더 좋은 chip design agent를 주장하기보다, agent가 물리설계 도구와 대화할 때 필요한 세션·명령·리포트 인터페이스를 공개 코드와 패키지로 제공합니다.

README와 API 문서에 따르면 서버는 10개의 MCP tool을 노출합니다. `create_interactive_session`은 OpenROAD pseudo-terminal session을 만들고, `interactive_openroad_query`는 read-only 명령을 실행하며, `interactive_openroad_exec`는 설계 상태를 바꾸는 명령을 실행합니다. `get_session_history`와 `get_session_metrics`는 agent가 앞선 명령과 실행 시간을 다시 볼 수 있게 하고, `list_report_images`와 `read_report_image`는 ORFS run에서 생성된 `.webp` report image를 찾아 읽게 합니다.

이 구조가 중요한 이유는 물리설계의 실패가 자연어 설명만으로 닫히지 않기 때문입니다. 예를 들어 setup timing violation을 줄이려는 agent가 있다면 먼저 현재 design을 load하고, `report_checks`로 worst path를 읽고, constraint나 placement 상태를 바꾼 뒤 다시 report를 봐야 합니다. OpenROAD-MCP는 이 반복을 chat 안에서 시작할 수 있게 하지만, 실제로 timing을 닫거나 PPA를 개선한다는 결론은 각 flow에서 별도 검증이 필요합니다.

## v1.0.0은 Python 배포보다 TypeScript/npx 경로를 앞세웁니다

공개 changelog에서 v1.0.0은 2026년 8월 11일 릴리스로 기록되어 있습니다. 변경 항목은 Python distribution 제거, v1.0 cleanup과 test 개선, TypeScript primary 전환, dependency update, project casing fix입니다. npm registry도 `openroad-mcp`의 latest tag를 `1.0.0`으로 두고, package metadata에 Node.js 22 이상, npm 실행 파일, BSD-3-Clause license, SLSA provenance attestation을 기록합니다.

이 변화는 설치 판단에 의미가 있습니다. v0.6.0에서 TypeScript/Node.js 구현이 npm에 올라오고 `npx -y openroad-mcp`로 설치 가능한 경로가 추가됐습니다. v1.0.0은 그 흐름을 정식 1.0 계열로 정리한 릴리스입니다. 서버 자체는 npm package 또는 GHCR Docker image로 받을 수 있지만, 실제 OpenROAD 명령을 실행하려면 OpenROAD binary가 `PATH`에 있어야 하고 ORFS 리포트 이미지를 보려면 `ORFS_FLOW_PATH`가 flow directory를 가리켜야 합니다.

아키텍처 문서는 서버가 TypeScript로 작성됐고 기본 transport는 stdio이며, Streamable HTTP도 지원한다고 설명합니다. 각 OpenROAD session은 `node-pty` pseudo-terminal에서 `openroad -no_init`을 실행하는 형태입니다. 출력은 ANSI escape를 제거해 JSON text payload로 돌려주고, command history와 buffer size, execution time 같은 metadata를 함께 기록합니다.

## query와 exec를 나누지만, exec는 sandbox가 아닙니다

EDA agent를 실제 도구에 연결하면 안전 경계가 곧 제품 기능입니다. OpenROAD-MCP 문서는 Tcl command whitelist를 query와 exec로 나눕니다. `interactive_openroad_query`는 `report_*`, `get_*`, `check_*`, `sta`, `help`, `version` 같은 read-only pattern만 허용하는 default-deny 경로입니다. 반대로 `interactive_openroad_exec`는 상태 변경 명령을 실행할 수 있지만, `socket`, `load`, `glob`, `rename`, `after`, `subst` 같은 OS escape 또는 interpreter abuse 위험 명령은 막습니다.

이 설계는 물리설계 작업의 자연스러운 구분과 맞습니다. timing report를 읽는 일과 `read_lef`, `read_liberty`, `global_placement`, `detailed_route`처럼 database를 바꾸는 일은 위험도가 다릅니다. agent가 보고만 할 때는 query tool에 묶고, 설계 상태를 바꿀 때는 exec tool 호출로 드러내는 방식은 review와 audit에 도움이 됩니다.

다만 security 문서는 exec가 sandbox가 아니라고 못박습니다. HTTP mode에는 application-level authentication, CORS policy, DNS rebinding protection이 없고, localhost 또는 trusted network 안에서만 쓰라는 조건도 함께 적혀 있습니다. 따라서 팀 환경에서 이 서버를 붙일 때는 "AI agent가 OpenROAD를 쓸 수 있다"보다 "어떤 transport, host, whitelist, session cleanup, command approval 정책으로 쓸 것인가"가 먼저 결정돼야 합니다.

## 지금 할 일 / 아직 미룰 일 / 다음에 확인할 신호

지금 할 일은 작습니다. OpenROAD와 ORFS를 이미 쓰는 팀이라면 OpenROAD-MCP v1.0.0의 npm 또는 Docker 경로가 내부 agent client와 맞는지 확인하고, read-only query부터 붙여 볼 수 있습니다. 첫 검사는 version 확인, worst setup slack report, clock 목록, macro·standard cell count처럼 설계 상태를 바꾸지 않는 명령이 적합합니다.

아직 미룰 일도 분명합니다. 이 릴리스를 근거로 PPA가 좋아진다거나 routing closure 시간이 줄어든다고 결론 내리면 안 됩니다. 공개 근거는 interface, package, command boundary, report image 접근 경로를 보여 줍니다. QoR 개선은 agent prompt, OpenROAD/ORFS commit, platform, design, constraint, seed, timeout, server spec, 실패 처리 방식에 묶인 별도 실험입니다.

다음에 확인할 신호는 재현 로그입니다. 같은 OpenROAD/ORFS commit과 같은 design suite에서 agent가 명령 기록을 남기며 timing, congestion, DRC, power report를 어떻게 개선했는지 공개해야 합니다. 특히 agent가 read-only query와 state-changing exec를 어떻게 구분했는지, 잘못된 명령이 whitelist에서 막혔는지, session이 누적돼 서버 limit에 걸리지 않았는지까지 보여 주는 benchmark가 필요합니다.

## 이 릴리스가 설계 흐름에 주는 의미

OpenROAD-MCP 1.0.0의 의의는 agent가 "EDA를 안다"고 말하는 층과 "EDA tool을 조작한다"는 층을 나눠 검증할 수 있게 한 데 있습니다. LLM이 물리설계 조언을 내더라도, 그 조언이 현재 design database와 맞는지는 OpenROAD report로 다시 확인해야 합니다. MCP server는 그 확인을 agent loop 안에 넣는 배관 역할을 합니다.

이 배관은 상용 signoff flow를 대체하지 않습니다. OpenROAD/ORFS 기반의 공개 flow, 교육·연구용 design exploration, 내부 실험 자동화에서 먼저 의미가 있습니다. foundry signoff deck, proprietary IP, 상용 P&R tool을 쓰는 production flow에서는 command boundary와 데이터 반출, license, security policy를 별도로 맞춰야 합니다.

그래도 공개 EDA 생태계에는 중요한 전환입니다. 이전에는 agent 논문이나 데모가 각자 만든 wrapper와 benchmark에 갇히기 쉬웠습니다. OpenROAD-MCP처럼 공식 repository, npm package, Docker package, API 문서, security 문서가 함께 있는 인터페이스는 실험을 반복하고 실패 로그를 비교할 공통 바닥을 제공합니다. 이번 기사에서 확인한 중심 주장은 여기까지입니다.

## 이해상충과 취재 조건

중심 근거는 The-OpenROAD-Project의 공개 GitHub 릴리스, README, architecture/API/security 문서와 npm registry metadata입니다. OpenROAD-MCP는 공개 source와 package가 있는 프로젝트이므로 interface와 설치 경로는 `R2 실행 가능`으로 평가했습니다.

편집국은 이번 턴에서 OpenROAD-MCP 서버, OpenROAD binary, ORFS flow를 직접 실행하지 않았습니다. 성능, QoR, PPA, runtime, 특정 design의 closure 개선은 확인하지 않았고 기사 결론으로 쓰지 않았습니다.

## 근거 원장

| Claim | 근거 | 판정 |
|---|---|---|
| C1. OpenROAD-MCP v1.0.0은 2026년 8월 11일 공개됐고 Python distribution 제거, TypeScript primary 정리, test cleanup 등을 포함한다. | GitHub release API, CHANGELOG | `E2`: 공개 release metadata와 changelog가 일치함 |
| C2. 서버는 OpenROAD와 ORFS를 MCP client에 연결하며 session 생성, read-only query, state-changing exec, session history/metrics, ORFS report image tools를 제공한다. | README, API reference, architecture 문서 | `E2`: 공개 문서와 tool 목록이 구체적임 |
| C3. npm package `openroad-mcp` latest는 1.0.0이며 Node.js 22 이상, `npx` runtime, BSD-3-Clause license, provenance attestation을 포함한다. | npm registry metadata, server.json | `E2`: 공개 package registry와 server manifest에서 확인됨 |
| C4. OpenROAD-MCP 1.0.0이 설계 QoR, PPA, runtime을 개선한다. | 공개 독립 benchmark 없음 | 미확인: 기사 결론으로 채택하지 않음 |

근거 수준의 상한은 `E2`입니다. 중심 판단은 공개 release와 실행 가능한 package/documentation으로 확인한 interface 변화에 관한 것이며, 설계 품질 개선은 미확인 범위입니다.

## 출처

1. [The-OpenROAD-Project, OpenROAD-MCP v1.0.0 release](https://github.com/The-OpenROAD-Project/OpenROAD-MCP/releases/tag/v1.0.0)
2. [GitHub API release metadata for OpenROAD-MCP latest](https://api.github.com/repos/The-OpenROAD-Project/OpenROAD-MCP/releases/latest)
3. [The-OpenROAD-Project, OpenROAD-MCP README](https://github.com/The-OpenROAD-Project/OpenROAD-MCP)
4. [The-OpenROAD-Project, OpenROAD-MCP CHANGELOG](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-MCP/main/CHANGELOG.md)
5. [The-OpenROAD-Project, OpenROAD-MCP architecture document](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-MCP/main/ARCHITECTURE.md)
6. [The-OpenROAD-Project, OpenROAD-MCP API reference](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-MCP/main/docs/API.md)
7. [The-OpenROAD-Project, OpenROAD-MCP security model](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-MCP/main/docs/SECURITY.md)
8. [The-OpenROAD-Project, OpenROAD-MCP server manifest](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-MCP/main/server.json)
9. [npm registry metadata for openroad-mcp](https://registry.npmjs.org/openroad-mcp)
