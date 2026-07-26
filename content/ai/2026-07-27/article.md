---
edition: ai
decision: publish-candidate
title: "MCP 2026-07-28 RC의 stateless 전환: GitHub 서버에서 확인한 배포 변화와 남은 호환성 검사"
date: 2026-07-27
subject: "Model Context Protocol 2026-07-28 release candidate와 GitHub MCP Server"
summary: "MCP 2026-07-28 RC는 protocol session과 initialize handshake를 없애고 요청마다 version·client 정보를 보내는 stateless core로 바뀝니다. GitHub MCP Server의 공개 commit에서도 stateless handler와 대응 Go SDK가 확인되지만, 최종 사양은 아직 나오지 않았고 공개 middleware에는 요청 body parsing이 남아 있습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["GitHub는 자사 MCP Server의 변경을 발표한 주체이며, Model Context Protocol 프로젝트와 공식 SDK 유지관리자도 자기 사양과 구현을 설명합니다. 이 기사에는 사전 접근, 계정·크레딧 제공, 후원 또는 embargo가 없었습니다."]
---

GitHub는 7월 23일 자사 MCP Server가 7월 28일 공개 예정인 Model Context Protocol(MCP) 사양을 미리 지원한다고 공개했습니다. 이 변화가 중요한 이유는 원격 MCP 서버를 수평 확장할 때 protocol session, `initialize` handshake, sticky routing에 의존하던 배포 구조가 달라지기 때문입니다. MCP client나 server, agent gateway를 운영하는 개발자는 “SDK가 알아서 호환된다”는 문장만 믿기보다 요청 metadata, application state, 구버전 fallback, conformance test를 분리해 확인할 필요가 있습니다.

## 세 줄 요약

- MCP `2026-07-28` release candidate(RC)는 protocol-level session과 `initialize`/`initialized` handshake를 없애고, version과 client capability를 요청마다 보내는 stateless core를 정의합니다.
- GitHub MCP Server의 7월 23일 공개 commit은 HTTP handler에 `Stateless: true`를 지정하고 `2026-07-28`을 지원하는 공식 Go SDK `v1.7.0-pre.3`을 사용합니다.
- 최종 사양은 7월 28일 공개 예정이며, GitHub의 공개 middleware는 조회한 commit에서도 POST body를 읽습니다. 따라서 hosted service의 gateway 동작과 payload inspection 제거 범위는 공개 자료만으로 확정할 수 없습니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 새 wire protocol은 각 요청을 self-contained하게 만들며, 공개 GitHub 서버 코드는 stateless HTTP handler와 대응 prerelease SDK를 실제로 연결했습니다.
- **도입 전에 확인할 것:** client와 server가 협상하는 정확한 protocol version, session에 숨겨 둔 application state, multi-round-trip request 지원, 구버전 fallback, gateway header 전달을 검사해야 합니다.
- **아직 결론 내릴 수 없는 것:** 7월 28일 최종 문서가 RC와 완전히 같은지, GitHub hosted service가 공개 repository와 같은 경로를 쓰는지, stateless 전환이 각 workload의 latency와 비용을 얼마나 줄이는지는 확인되지 않았습니다.

## 이 공개의 의의와 편집 판단

MCP는 LLM application이 외부 data와 tool을 호출하는 방식을 표준화하는 protocol입니다. 이번 RC는 tool 하나를 더하는 기능 업데이트가 아니라 client와 server가 연결을 시작하고 요청을 분산하는 base protocol을 바꿉니다. 기존 `2025-11-25` 방식에서는 `initialize` 요청 뒤 server가 발급한 `Mcp-Session-Id`를 후속 요청에 붙였지만, 새 방식에서는 요청마다 protocol version과 client metadata를 보냅니다.

**편집 판단:** 이번 변화의 핵심 가치는 Redis 하나를 없애는 데 있지 않습니다. protocol state와 application state를 분리하게 만들고, 어떤 상태가 정말 여러 tool call에 걸쳐 유지돼야 하는지 API argument와 저장소 설계로 드러내게 한다는 점이 더 중요합니다. 다만 RC를 최종 표준처럼 배포하거나 “stateless이므로 상태가 전혀 없다”고 이해하면 migration risk가 커집니다.

## 연결 handshake가 요청별 metadata로 바뀝니다

RC 문서가 제시한 이전 흐름에서는 client가 먼저 `initialize`를 보내고 server가 `Mcp-Session-Id`를 반환합니다. 이후 `tools/call` 같은 요청은 이 session ID를 포함하므로 load balancer는 같은 instance로 보내거나 여러 instance가 공유하는 session store를 사용해야 했습니다.

`2026-07-28` RC에서는 `initialize`와 protocol-level session이 제거됩니다. HTTP 요청은 `MCP-Protocol-Version`, `Mcp-Method`, 필요하면 `Mcp-Name` 같은 header를 사용하며, JSON-RPC `_meta`에는 client 정보와 capability가 들어갑니다. server capability를 미리 알아야 하는 client는 새 `server/discover` method를 호출할 수 있습니다.

이 구조에서는 같은 client의 연속 요청이 서로 다른 server instance로 가도 protocol 자체는 처리할 수 있습니다. gateway도 routing에 필요한 method와 name을 표준 header에서 읽을 수 있습니다. 다만 “ordinary round-robin load balancer로 확장할 수 있다”는 설명은 protocol state에 관한 결론이며, database transaction, browser session, 장기 task처럼 application이 유지해야 하는 상태까지 사라진다는 뜻은 아닙니다.

여러 호출에 걸친 상태가 필요하면 tool이 `browser_id`나 `job_id` 같은 명시적 handle을 반환하고 client가 다음 호출의 argument로 다시 보내는 방식이 필요합니다. 이때 handle의 authorization 범위, 만료, 재시도 idempotency, 다른 tenant와의 격리는 application 책임으로 남습니다.

## 공개 GitHub 서버에서는 stateless handler가 확인됩니다

GitHub의 변경 공지는 자사 MCP Server가 차기 사양을 이미 지원하며 Redis session, `initialize` 시 database write, 요청마다 수행하던 database read를 없앴다고 설명합니다. 또한 logging과 secret scanning에 필요한 값을 새 표준 header에서 얻어 모든 payload를 미리 검사하지 않아도 된다고 적었습니다.

공개 repository의 7월 23일 commit `eb088dfe9d854dab6453a8d4ae5871a5ced20974`를 확인하면 두 구현 사실은 직접 볼 수 있습니다. `go.mod`는 공식 MCP Go SDK `v1.7.0-pre.3`을 가리키고, HTTP handler는 `mcp.StreamableHTTPOptions{Stateless: true}`로 server를 만듭니다. 요청마다 새 MCP server instance를 만드는 비용을 줄이기 위해 schema cache를 공유한다는 주석도 있습니다.

그러나 공개 code snapshot만으로 변경 공지의 모든 운영 효과를 확인할 수는 없습니다. 같은 commit의 `pkg/http/middleware/mcp_parse.go`는 routing 최적화와 secret-scanning context를 만들기 위해 POST body를 읽고 JSON-RPC method, tool name, argument를 parsing한 뒤 body를 복원합니다. 이는 GitHub가 설명한 hosted gateway의 deep packet inspection 제거와 대상 경로가 다를 수 있으며, 공개 server에 후속 변경이 아직 반영되지 않았을 수도 있습니다.

따라서 확인 가능한 결론은 “공개 GitHub MCP Server가 stateless SDK 경로를 사용한다”까지입니다. hosted service에서 Redis read가 몇 회 줄었는지, body inspection이 어느 계층에서 완전히 사라졌는지, latency가 얼마나 개선됐는지는 공개 log나 benchmark가 없어 판단하지 않습니다.

## SDK 지원은 stable과 prerelease를 구분해야 합니다

GitHub MCP Server가 고정한 Go SDK `v1.7.0-pre.3`은 이름 그대로 prerelease입니다. 7월 17일 release note는 `2026-07-28`을 대상으로 spec compliance 수정, stateless server의 request cancellation option, `server/discover` 조건 검사를 포함한다고 설명합니다. tag가 가리키는 commit은 `827f90ba0c13edb546028df42fadc9f1211a4ff2`입니다.

Go SDK 문서는 `v1.7.0+`이 `2026-07-28`과 이전 protocol version을 지원한다고 적습니다. 하지만 7월 27일 확인한 GitHub 서버는 정식 `v1.7.0`이 아니라 `pre.3`을 사용합니다. 다른 언어 SDK도 release 상태와 opt-in 방식이 같다고 가정하면 안 됩니다.

MCP 사양 repository의 RC tag `2026-07-28-RC`는 commit `9d700ed62dcf86cb77475c9b81930611a9182f46`을 가리키며, release note는 최종판 전 변경 가능성을 명시합니다. production migration에서는 “7월 28일을 지원한다”는 feature matrix와 “안정판으로 배포해도 된다”는 release maturity를 별도 항목으로 관리해야 합니다.

## conformance suite로 wire behavior를 따로 검사할 수 있습니다

공식 conformance repository는 client와 server가 사양에 맞게 통신하는지 검사하는 실행 가능한 test framework를 공개합니다. 7월 23일 commit `a865118206d4d8cc8dbc5f5201607839281d0c3b`의 README는 `--spec-version 2026-07-28` option과 draft suite를 설명하며, `2025-11-25`까지는 stateful lifecycle, `2026-07-28`은 request별 `_meta`를 사용하는 stateless lifecycle로 구분합니다.

문서에 나온 server 검사는 다음 형태입니다.

```bash
npx @modelcontextprotocol/conformance server --url http://localhost:3000/mcp
```

client 검사는 실행할 client command와 scenario 또는 suite를 지정합니다. 다만 조회한 main snapshot의 `package.json` version은 `0.2.0-alpha.9`이고, 저장소의 latest 정식 release는 더 이전 version입니다. CI에 넣을 때는 main branch를 그대로 따라가지 말고 검증한 package version이나 commit을 고정해야 합니다.

이 기사에서는 GitHub hosted endpoint나 별도 MCP server를 대상으로 conformance suite를 실행하지 않았습니다. 공개 code와 test 절차가 있어 재현 상태는 `R2 실행 가능`으로 기록하지만, 특정 배포가 suite를 통과했다고 주장하지 않습니다.

## migration은 protocol과 application을 나눠 진행해야 합니다

먼저 access log에서 `initialize`, `Mcp-Session-Id`, sticky cookie, session store read/write가 실제로 어디에 사용되는지 찾습니다. 단순 handshake인지, tool별 authorization이나 사용자별 state까지 묶여 있는지 구분하지 않고 session store를 제거하면 tenant isolation이나 연속 작업이 깨질 수 있습니다.

그다음 application state를 명시적 handle로 옮깁니다. handle은 추측하기 어려운 값이어야 하고, 호출 주체와 scope를 다시 검증하며, 만료와 revoke 경로를 가져야 합니다. 재시도 가능한 tool이라면 같은 요청이 두 번 실행돼도 안전한 idempotency contract를 함께 정해야 합니다.

gateway에서는 새 header를 보존하고 allowlist에 추가해야 합니다. 동시에 header 값만 믿어 authorization을 생략해서는 안 됩니다. `Mcp-Method`와 `Mcp-Name`은 routing과 관측을 돕지만 tool argument의 schema validation, 사용자 권한, secret scanning을 대신하지 않습니다.

마지막으로 새 client와 구형 server, 구형 client와 새 server를 각각 검사합니다. Go SDK가 backward compatibility를 제공하더라도 custom transport, proxy, client-side cache, multi-round-trip request는 별도의 실패 지점입니다. conformance suite와 실제 deployment smoke test를 분리해 실행하고, fallback이 일어났을 때 negotiated version을 log에 남기는 편이 좋습니다.

## 최종 사양과 운영 수치는 아직 기다려야 합니다

- 최종 `2026-07-28` 사양은 기사 작성 시점에 공개되지 않았습니다. RC 이후 schema나 error code가 바뀔 가능성이 남아 있습니다.
- GitHub hosted MCP Server의 source revision, topology, Redis metric, gateway configuration과 latency 결과는 공개되지 않았습니다.
- GitHub 변경 공지는 payload 사전 검사가 사라졌다고 설명하지만 공개 repository의 고정 commit에는 body-parsing middleware가 남아 있습니다. 두 경로가 같은 배포인지 확인할 자료가 없습니다.
- 공식 conformance code는 공개돼 있지만 이 기사에서는 GitHub server나 SDK를 실행해 통과 결과를 만들지 않았습니다.
- stateless core는 protocol session을 없앱니다. 장기 작업, browser, transaction, authorization 같은 application state까지 자동으로 해결하지 않습니다.

## 도입 판단: 7월 28일에는 upgrade보다 inventory가 먼저입니다

현재 구형 session flow가 안정적으로 동작한다면 날짜만 보고 즉시 전환할 필요는 없습니다. 먼저 SDK별 정식 release 여부, 지원하는 protocol version, fallback behavior, 제거 예정 capability를 표로 만들고, session store의 data가 protocol bookkeeping인지 application state인지 분류해야 합니다.

새 원격 server를 설계한다면 stateless path를 기본 후보로 삼을 근거는 충분합니다. 다만 명시적 state handle, request별 authorization, idempotency, observability를 함께 설계해야 수평 확장의 이점을 실제 운영 안전성으로 연결할 수 있습니다. 최종 사양 공개 뒤 RC와 diff를 확인하고 고정 version으로 conformance test를 통과시키는 것이 production 전환의 최소 조건입니다.

## 이해상충과 취재 조건

GitHub는 자사 MCP Server의 변경을 발표하고 공개 repository를 운영합니다. Model Context Protocol project와 공식 Go SDK·conformance suite의 유지관리자는 자기 사양과 구현의 범위를 설명합니다. 각 발표의 성능·호환성 해석에는 선택된 공개 범위가 영향을 줄 수 있습니다.

이 기사에는 GitHub나 MCP project의 사전 열람, 비용 지원, 계정·credit 제공, embargo가 없었습니다. 공개 changelog, RC 사양, release note와 고정 commit의 code만 확인했습니다. hosted infrastructure, 비공개 benchmark, production log에는 접근하지 않았습니다.

## 근거 원장

| Claim | 판정 | 출처/근거 | 등급 | 한계·재확인 조건 |
|---|---|---|---|---|
| MCP `2026-07-28` RC는 protocol session과 `initialize` handshake를 제거하고 request별 metadata와 `server/discover`를 사용합니다 | 사양·schema artifact로 확인 | MCP RC blog·draft specification·RC tag `9d700ed62dcf86cb77475c9b81930611a9182f46` | P1+P2 / E2 / R2 | 최종 사양 공개 뒤 RC diff 재확인 필요 |
| GitHub MCP Server는 stateless HTTP handler와 공식 Go SDK `v1.7.0-pre.3`을 연결했습니다 | 공개 code로 확인 | GitHub changelog·server commit `eb088dfe9d854dab6453a8d4ae5871a5ced20974`의 `handler.go`와 `go.mod` | P1+P2 / E2 / R2 | hosted service가 같은 commit과 topology를 쓰는지는 미공개 |
| Go SDK prerelease는 새 protocol과 이전 version compatibility를 구현합니다 | release note·code로 확인 | Go SDK `v1.7.0-pre.3`, commit `827f90ba0c13edb546028df42fadc9f1211a4ff2` | P1+P2 / E2 / R2 | prerelease이며 다른 언어 SDK에 일반화할 수 없음 |
| conformance framework는 `2026-07-28` stateless lifecycle을 선택해 client와 server를 검사할 수 있습니다 | 공개 test code와 CLI 문서로 확인 | conformance commit `a865118206d4d8cc8dbc5f5201607839281d0c3b` | P2 / E2 / R2 | 기사에서 실행하지 않았고 main snapshot package는 alpha |
| GitHub 공지는 payload 사전 검사 제거를 설명하지만 공개 server commit의 middleware는 POST body를 parsing합니다 | 두 공개 artifact의 범위 차이 확인 | GitHub changelog·`mcp_parse.go` at `eb088dfe9d854dab6453a8d4ae5871a5ced20974` | P1+P2 / E2 / R2 | hosted gateway와 공개 middleware가 같은 계층인지 미확인 |
| migration은 protocol state와 application state를 분리하고 version negotiation·fallback·authorization을 각각 검증해야 합니다 | 편집 판단 | 위 사양과 구현 claim에서 파생 | 편집 판단 / E2 / R2 | 조직별 workload와 threat model로 검증 필요 |

## 출처

1. GitHub, “GitHub MCP Server supports the next MCP specification”, 2026-07-23, 조회 2026-07-27: https://github.blog/changelog/2026-07-23-github-mcp-server-supports-the-next-mcp-specification/
2. Model Context Protocol Blog, “The 2026-07-28 MCP Specification Release Candidate”, 2026-05-21, 조회 2026-07-27: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
3. Model Context Protocol draft specification, 조회 2026-07-27: https://modelcontextprotocol.io/specification/draft
4. MCP specification RC release `2026-07-28-RC`, commit `9d700ed62dcf86cb77475c9b81930611a9182f46`: https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28-RC
5. GitHub MCP Server, commit `eb088dfe9d854dab6453a8d4ae5871a5ced20974`, `pkg/http/handler.go`: https://github.com/github/github-mcp-server/blob/eb088dfe9d854dab6453a8d4ae5871a5ced20974/pkg/http/handler.go
6. GitHub MCP Server, 같은 commit의 `go.mod`: https://github.com/github/github-mcp-server/blob/eb088dfe9d854dab6453a8d4ae5871a5ced20974/go.mod
7. GitHub MCP Server, 같은 commit의 `pkg/http/middleware/mcp_parse.go`: https://github.com/github/github-mcp-server/blob/eb088dfe9d854dab6453a8d4ae5871a5ced20974/pkg/http/middleware/mcp_parse.go
8. MCP Go SDK `v1.7.0-pre.3`, commit `827f90ba0c13edb546028df42fadc9f1211a4ff2`: https://github.com/modelcontextprotocol/go-sdk/releases/tag/v1.7.0-pre.3
9. MCP conformance framework, commit `a865118206d4d8cc8dbc5f5201607839281d0c3b`: https://github.com/modelcontextprotocol/conformance/tree/a865118206d4d8cc8dbc5f5201607839281d0c3b
