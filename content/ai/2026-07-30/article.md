---
edition: ai
decision: publish-candidate
title: "MCP 2026-07-28 최종판: RC에서 바뀐 identity wire와 안정판 SDK의 도입 경계"
date: 2026-07-30
subject: "Model Context Protocol 2026-07-28 final, Go SDK v1.7.0, TypeScript SDK v2.0.0"
summary: "MCP 2026-07-28이 최종 사양과 안정판 Go·TypeScript SDK로 공개됐습니다. 다만 RC의 serverInfo 위치와 clientInfo 필수 조건이 최종판에서 바뀌었고, Go와 TypeScript의 새 protocol 활성화 방식도 달라서 RC 구현을 version 문자열만 바꿔 배포하면 안 됩니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["Model Context Protocol 프로젝트와 공식 SDK 유지관리자는 자기 사양·release·conformance artifact를 설명합니다. 이 기사에는 사전 접근, 계정·credit 제공, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

Model Context Protocol(MCP) `2026-07-28` 최종판 공개에서 개발자에게 중요한 변화는 stateless 설계가 문서의 약속을 넘어 고정된 schema와 안정판 SDK에 들어갔다는 점입니다. MCP는 LLM application이 외부 data와 tool을 호출하는 message contract입니다. 이번에는 release candidate(RC) 뒤에 wire contract, 즉 network에서 주고받는 JSON field의 모양도 실제로 바뀌었으므로 prerelease 구현을 그대로 두고 version 문자열만 최종판으로 올리면 호환성 오류가 날 수 있습니다.

## 세 줄 요약

- MCP 프로젝트는 7월 28일 commit `5f5440bb26a62e2cf3440b92da5a667efa03b267`에 `2026-07-28` 최종 tag를 만들고 versioned specification과 JSON Schema를 공개했습니다.
- RC에서는 `server/discover` 결과 body의 `serverInfo`와 request별 `clientInfo`가 필수였지만, 최종판은 server identity를 모든 result의 `_meta`로 옮기고 `clientInfo`를 선택 field로 바꿨습니다.
- Go SDK `v1.7.0`과 TypeScript server `2.0.0`은 안정판이지만 modern protocol 활성화 방식이 다르며, 새 spec용 공식 conformance package는 확인한 commit에서 `0.2.0-alpha.10`입니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 최종 spec tag, versioned schema, Go와 TypeScript의 안정판 source와 migration guide를 고정 commit에서 검사할 수 있습니다.
- **도입 전에 확인할 것:** RC type을 다시 생성하고, `serverInfo`를 security decision에 쓰지 않으며, SDK별 negotiation 기본값과 legacy fallback, HTTP·stdio entry point, conformance version을 명시적으로 고정해야 합니다.
- **아직 결론 내릴 수 없는 것:** 여러 언어 SDK와 실제 host·server 조합이 모두 같은 final wire를 처리하는지, migration이 workload latency·장애율·운영 비용을 얼마나 바꾸는지는 공개 artifact만으로 확정할 수 없습니다.

## 이 공개의 의의와 편집 판단

7월 27일 확인한 RC 단계에서는 stateless handler와 prerelease SDK가 공개돼 있었지만 최종 spec 자체는 아직 없었습니다. 7월 28일에는 spec release가 prerelease가 아닌 stable로 바뀌었고, `schema/2026-07-28/` 경로와 Go·TypeScript 안정판이 함께 생겼습니다. 이제 구현자는 움직이는 `draft` 대신 날짜가 고정된 schema를 code generation, gateway validation, contract test의 기준으로 삼을 수 있습니다.

**편집 판단:** 이번 공개의 실질적인 가치는 “MCP가 stateless가 됐다”는 설명을 반복하는 데 있지 않습니다. RC와 final 사이에도 interoperability를 깨뜨릴 수 있는 field 이동이 있었고, 안정판 SDK를 설치하는 일과 새 wire를 실제로 활성화하는 일이 같은 동작이 아니라는 점을 배포 판단에 반영할 수 있게 됐다는 데 있습니다. production 전환의 단위는 package version 하나가 아니라 `spec revision + SDK tag + negotiation policy + conformance scenario`의 묶음이어야 합니다.

## RC 뒤에 identity field가 실제로 바뀌었습니다

RC tag `9d700ed62dcf86cb77475c9b81930611a9182f46`의 TypeScript schema에서 `RequestMetaObject`의 `io.modelcontextprotocol/clientInfo`는 required였습니다. 같은 RC의 `DiscoverResult`에는 `serverInfo`가 body field로 들어 있었습니다. RC를 기준으로 type을 만들거나 `server/discover` response를 strict validation한 client라면 이 모양을 전제로 code가 굳어질 수 있습니다.

최종 tag `5f5440bb26a62e2cf3440b92da5a667efa03b267`에서는 두 조건이 달라졌습니다. `clientInfo`에는 `?`가 붙어 optional이 됐고, `serverInfo`는 `DiscoverResult` body에서 빠져 공통 `ResultMetaObject`의 `io.modelcontextprotocol/serverInfo`로 이동했습니다. 최종 changelog도 client가 request마다 자신을 식별하는 것과 server가 result마다 자신을 식별하는 것을 각각 `SHOULD`로 설명합니다.

이 변경은 7월 16일 merge된 spec PR `#3002`에서 추적할 수 있습니다. PR은 handshake 제거로 사라진 server identity를 response `_meta`에 복원하면서 client와 server identity가 self-reported이고 검증되지 않았다고 명시합니다. display, logging, debugging에는 쓸 수 있지만 behavior나 security decision의 입력으로 신뢰하지 말라는 범위도 함께 적었습니다.

따라서 identity를 authorization, tenant routing, feature entitlement에 사용하면 안 됩니다. 신뢰 경계에는 검증된 token claim, mTLS identity, gateway가 보존한 인증 context처럼 별도 mechanism을 사용해야 합니다. `serverInfo`는 관찰용 label이고 authentication proof가 아닙니다.

## 안정판 SDK도 같은 switch로 켜지지 않습니다

Go SDK tag `v1.7.0`은 signed annotated tag가 commit `bc72835f62eb94d0fb484439f886b6885b075f36`을 가리킵니다. release note는 새 client가 먼저 `server/discover`를 호출하고 실패하면 legacy `initialize`로 fallback한다고 설명합니다. Streamable HTTP server가 `2026-07-28` request를 받으려면 `StreamableHTTPOptions.Stateless = true`가 필요하며, 그렇지 않으면 새 revision request를 거부합니다.

TypeScript SDK는 package 구조와 활성화 방식이 다릅니다. `@modelcontextprotocol/server@2.0.0` tag가 가리키는 commit은 `cc4b41617ce3601b1290d67216ea0b194a3cd9ac`이고, package는 Node.js `>=20`을 요구합니다. v2 migration guide는 hand-constructed `Client`, `Server`, `McpServer`가 기본으로 2025-era protocol을 계속 사용하며 `2026-07-28` byte를 자동으로 내보내지 않는다고 명시합니다.

TypeScript client는 `versionNegotiation: { mode: 'auto' }`를 켜야 `server/discover` probe 뒤 legacy fallback을 수행합니다. HTTP server는 `createMcpHandler`, stdio server는 `serveStdio` entry를 사용해야 modern revision을 제공합니다. 따라서 dependency를 v2로 올렸다는 사실만으로 traffic이 final protocol로 바뀌었다고 판단하면 안 됩니다.

TypeScript v2 release에는 RC와 final의 identity 차이를 맞춘 commit `f4137630c05dc9a4fb14d4d3777f5cb167bd6313`도 포함됩니다. release note는 이전 v2 shape가 final server의 `DiscoverResult`를 거부한 뒤 legacy handshake를 시도해 modern-only server 연결이 실패할 수 있었다고 기록합니다. RC build를 썼다면 generated type, response cache key, mock fixture와 gateway log parser를 함께 갱신해야 합니다.

v1을 즉시 제거할 필요는 없습니다. official README는 TypeScript v1.x가 v2 release 뒤 최소 6개월 동안 bug fix와 security update를 받는다고 적습니다. 이 기간을 dual-era test와 단계적 rollout에 사용할 수 있지만, 지원 약속이 application의 자동 호환성을 보장하는 것은 아닙니다.

## negotiation 실패를 legacy로 오인하지 않아야 합니다

TypeScript `auto` mode는 2025-only server를 위한 fallback을 제공하지만 모든 실패를 legacy 증거로 취급하지 않습니다. migration guide는 HTTP `401`·`403`, `5xx`, HTTP probe timeout을 authentication 또는 infrastructure failure로 surface하고 legacy handshake로 조용히 내리지 않는다고 설명합니다. 반면 일부 legacy stdio server는 `initialize` 전 알 수 없는 request에 응답하지 않으므로, SDK는 별도 sibling process에서 probe한 뒤 fallback합니다.

이 구분은 운영 관측에도 필요합니다. `server/discover` 실패율을 하나의 metric으로 합치면 “구버전 peer”와 “인증 설정 오류”, “server 장애”, “CORS 문제”를 분리할 수 없습니다. rollout dashboard에는 negotiated era, transport, probe result, HTTP status 또는 JSON-RPC error code, fallback 여부를 별도 field로 남기는 편이 좋습니다.

modern-only pin은 fail-closed canary에 적합합니다. 먼저 test environment에서 `2026-07-28`을 pin해 final wire가 아니면 실패하게 만들고, production의 초기 단계에서는 `auto`로 실제 peer 분포와 fallback 비율을 측정할 수 있습니다. 전체 traffic 전환 전에는 legacy path를 제거하지 않고 rollback switch로 유지하는 편이 안전합니다.

## conformance artifact는 아직 alpha line입니다

공식 conformance repository의 7월 28일 commit `49103de6ed70804e940637bf3e9e29e4a3f54e64`는 Go, C#, Rust, Python SDK를 `2026-07-28` mode로 실행하기 위한 per-spec-version override를 추가했습니다. 같은 commit의 package version은 `0.2.0-alpha.10`입니다. repository의 latest stable release로 확인되는 `v0.1.16`은 3월 27일 공개본이므로 새 revision 검사를 위해 latest stable이라는 이름만 따라가면 부족합니다.

이 기사는 conformance suite를 특정 server에 실행하지 않았습니다. 공개 code와 scenario가 있어 재현 상태는 `R2 실행 가능`으로 기록하지만, 어느 SDK나 hosted server가 suite를 통과했다고 주장하지 않습니다. CI에서는 `main`이나 `latest` 대신 검증한 package version 또는 commit을 고정하고, 사용 언어의 server·client 양쪽 결과와 wire transcript를 보존해야 합니다.

최소 contract test에는 final `server/discover` shape, request별 required `_meta`, optional `clientInfo`, result `_meta`의 optional `serverInfo`, `resultType`, error code `-32020`부터 `-32022`, legacy fallback을 포함해야 합니다. HTTP와 stdio는 probe와 cancellation 동작이 다르므로 같은 fixture 이름을 쓰더라도 transport별 expected result를 나누는 편이 좋습니다.

## 작은 rollout 단위로 final wire를 검증할 수 있습니다

먼저 RC schema로 생성된 type과 fixture를 찾아 final versioned schema로 다시 만듭니다. `DiscoverResult.serverInfo` 접근, `clientInfo` required assertion, `_meta`를 제거하는 serializer, identity를 security policy에 연결한 code를 별도 review 대상으로 표시합니다.

다음으로 SDK별 modern activation을 명시합니다. Go server는 `Stateless: true` 여부를 config와 test에서 확인하고, TypeScript는 client `versionNegotiation`, HTTP `createMcpHandler`, stdio `serveStdio` 사용을 검사합니다. package install 성공과 negotiated protocol version을 서로 다른 health signal로 기록해야 합니다.

그다음 canary client와 server를 각각 modern-only로 고정해 schema와 error behavior를 확인합니다. 이후 `auto` client로 legacy peer fallback을 측정하고, 인증 실패나 `5xx`가 fallback으로 숨지 않는지 검사합니다. rollback은 traffic을 legacy path로 되돌리거나 modern negotiation을 끄는 configuration change로 준비합니다.

마지막으로 application state를 점검합니다. protocol-level session이 사라져도 browser job, transaction, approval flow 같은 application state는 사라지지 않습니다. explicit handle의 tenant binding, 만료, revoke, retry idempotency를 검증한 뒤에만 session store와 sticky routing을 제거해야 합니다.

## 적용 범위와 확인하지 못한 것

이 기사는 official GitHub API와 fixed commit의 source, final website 문서를 읽어 schema와 release metadata를 비교했습니다. package를 설치하거나 sample server를 띄우지 않았고, conformance suite도 실행하지 않았습니다. 따라서 code와 test path의 존재는 확인했지만 runtime success, latency, throughput, memory, 장애 복구와 실제 host compatibility는 측정하지 않았습니다.

Go와 TypeScript를 비교 대상으로 삼았지만 Python, Rust, C#, Kotlin, Swift 등 다른 official SDK의 final 지원 수준을 포괄적으로 판정하지 않았습니다. GitHub MCP Server 같은 hosted deployment가 어느 exact stable SDK와 configuration을 현재 사용하는지도 공개 자료만으로 확정하지 않습니다.

최종 spec의 identity field는 self-reported입니다. article이 고정한 것은 field 위치와 normative 범위이지, peer가 적어 보낸 name·version의 진실성이 아닙니다. 해당 값을 보안 판단에 사용하려면 별도의 인증 근거가 필요합니다.

## 이해상충과 취재 조건

Model Context Protocol 프로젝트와 official SDK 유지관리자는 자기 specification, code, release와 conformance 상태를 설명합니다. GitHub는 MCP 프로젝트와 GitHub MCP Server의 참여 주체이며 release hosting도 제공합니다. 이 기사에는 vendor나 프로젝트의 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. `2026-07-28` final spec과 versioned schema가 stable tag `5f5440bb26a62e2cf3440b92da5a667efa03b267`에 공개됐습니다. | E2 · P1/P2 · R2 | Official release와 fixed schema를 확인했습니다. Schema validator나 code generator는 실행하지 않았습니다. |
| C2. RC의 required `clientInfo`와 body `serverInfo`는 final에서 optional request metadata와 optional result metadata로 바뀌었습니다. | E2 · P2 · R2 | RC·final `schema.ts`와 merged PR `#3002`를 직접 비교했습니다. 다른 비공식 구현의 반영 상태는 확인하지 않았습니다. |
| C3. Go `v1.7.0`과 TypeScript server `2.0.0`은 stable source를 제공하지만 modern protocol의 기본 negotiation과 server entry가 다릅니다. | E2 · P1/P2 · R2 | Signed Go tag, TypeScript tag, exact migration docs와 package metadata를 확인했습니다. Package를 설치하거나 endpoint를 실행하지 않았습니다. |
| C4. 새 revision용 conformance source는 공개됐지만 확인한 7월 28일 commit의 package version은 `0.2.0-alpha.10`입니다. | E2 · P2 · R2 | Fixed commit의 package metadata와 release 목록을 확인했습니다. Suite 통과 결과는 만들지 않았습니다. |

## 출처

1. Model Context Protocol final specification `2026-07-28`: https://modelcontextprotocol.io/specification/2026-07-28
2. MCP `2026-07-28` key changes: https://modelcontextprotocol.io/specification/2026-07-28/changelog
3. MCP stable release tag `2026-07-28`: https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28
4. MCP final schema at commit `5f5440bb26a62e2cf3440b92da5a667efa03b267`: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/5f5440bb26a62e2cf3440b92da5a667efa03b267/schema/2026-07-28/schema.ts
5. MCP RC schema at commit `9d700ed62dcf86cb77475c9b81930611a9182f46`: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/9d700ed62dcf86cb77475c9b81930611a9182f46/schema/draft/schema.ts
6. Spec PR `#3002`: https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3002
7. Go SDK `v1.7.0`: https://github.com/modelcontextprotocol/go-sdk/releases/tag/v1.7.0
8. Go SDK protocol guide at commit `bc72835f62eb94d0fb484439f886b6885b075f36`: https://github.com/modelcontextprotocol/go-sdk/blob/bc72835f62eb94d0fb484439f886b6885b075f36/docs/protocol.md
9. TypeScript server `2.0.0`: https://github.com/modelcontextprotocol/typescript-sdk/releases/tag/%40modelcontextprotocol%2Fserver%402.0.0
10. TypeScript `2026-07-28` migration guide at commit `cc4b41617ce3601b1290d67216ea0b194a3cd9ac`: https://github.com/modelcontextprotocol/typescript-sdk/blob/cc4b41617ce3601b1290d67216ea0b194a3cd9ac/docs/migration/support-2026-07-28.md
11. TypeScript server package metadata at commit `cc4b41617ce3601b1290d67216ea0b194a3cd9ac`: https://github.com/modelcontextprotocol/typescript-sdk/blob/cc4b41617ce3601b1290d67216ea0b194a3cd9ac/packages/server/package.json
12. Conformance commit `49103de6ed70804e940637bf3e9e29e4a3f54e64`: https://github.com/modelcontextprotocol/conformance/tree/49103de6ed70804e940637bf3e9e29e4a3f54e64
