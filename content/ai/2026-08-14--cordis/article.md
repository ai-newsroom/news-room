---
edition: ai
decision: publish-candidate
title: "DeepSeek·베이징대 연구진, 실행 중 앱 부품을 바꾸는 'Cordis' 설계 공개"
date: 2026-08-14
publication_kind: special
subject: "A Programming Paradigm for Spatiotemporal Composability and Cordis, draft of August 13, 2026"
summary: "DeepSeek-AI와 베이징대 소속 연구진은 2026년 8월 13일 active-revision preprint와 구현체 Cordis를 공개했습니다. Cordis는 플러그인, 서비스 의존성, 되돌릴 수 있는 등록 효과를 runtime 구조로 묶어 AI agent harness 같은 동적 앱의 유지보수 범위를 좁힐 수 있습니다. 다만 Cordis 자체가 개선안을 고르거나 스스로 학습하는 자기개선 엔진이라는 근거는 아직 없습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["논문·Cordis·DeepSeek Harness·Koishi 원문 작성자가 각 프로젝트의 당사자입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

DeepSeek-AI와 베이징대 소속 Yifan Shi, Wei Zhang, Tianyi Cui 연구진이 2026년 8월 13일 `A Programming Paradigm for Spatiotemporal Composability`라는 active-revision preprint와 구현체 Cordis를 공개했고, SW 엔지니어에게 중요한 변화는 실행 중인 앱 부품을 시험·교체·복구할 단위를 더 작게 잡는 설계가 원문과 코드로 함께 나왔다는 점입니다. 논문은 실행 중인 앱을 plugin 단위로 넣고 빼는 문제를, 부품이 남긴 변경을 회수하는 능력과 부품 사이 의존성을 다시 맞추는 능력으로 나눠 설명합니다.

AI agent harness를 만드는 팀에는 이 구분이 실무적입니다. 모델 adapter, tool registry, sandbox, approval policy, session log, agent loop가 하나의 큰 덩어리로 붙어 있으면 AI가 바꿀 수 있는 범위도 넓어지고 실패했을 때 복구할 경계도 흐려집니다. Cordis식 구성은 작은 plugin이 어떤 service를 요구하고 무엇을 등록했는지 runtime에 남겨, 교체와 rollback의 범위를 더 좁게 잡는 쪽으로 설계를 유도합니다.

이 공개가 곧 자율 자기개선 검증은 아닙니다. DeepSeek Harness는 README와 architecture 문서에서 Cordis 기반 plugin 구조를 밝히지만, 논문 결론은 self-evolving agent harness 검증을 미래 연구로 둡니다. 따라서 중심 결론은 Cordis가 AI 유지보수에 유리한 구조적 토대를 제공한다는 데서 멈추고, Cordis 자체가 개선안을 선택하거나 학습한다고 쓰지 않습니다.

## 세 줄 요약

- 논문 저장소는 2026년 8월 13일 초안을 공개했고, Cordis를 effect tracking, coeffect resolution, configuration reconciliation, hot module replacement를 제공하는 meta-framework로 설명합니다.
- DeepSeek Harness는 공개 README와 architecture 문서에서 "everything is a plugin" 구조가 Cordis로 구동되며 model adapter, tool registry, session log, agent loop까지 plugin으로 구성된다고 밝힙니다.
- 검증된 것은 구조와 구현의 공개 범위입니다. runtime overhead, 생산성 비교, 독립 benchmark, Cordis 기반 자율 자기개선 효과는 공개 원문만으로 확인되지 않습니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 논문 PDF, Cordis 코드, DeepSeek Harness 문서와 vendored Cordis API 문서로 Context, Fiber, `ctx.effect()`, `inject`, service 제공·소비, lifecycle 상태, 역순 disposer 실행을 확인할 수 있습니다.
- **도입 전에 확인할 것:** 여러분의 앱에서 외부 network message, 결제, 공유 파일, DB write처럼 context 밖으로 나간 효과를 어떻게 보상하거나 지연할지 별도 설계해야 합니다. Cordis의 language-level mediation은 sandbox가 아닙니다.
- **아직 결론 내릴 수 없는 것:** Cordis가 AI에게 더 좋은 개선안을 고르게 만든다거나, 자율 agent가 자기 harness를 안정적으로 진화시킨다는 결과는 아직 검증되지 않았습니다.

## 무엇이 실제로 바뀌었나

공개된 사건은 두 갈래입니다. 첫째, 논문 저장소는 `paper.pdf`와 README를 통해 "spatiotemporal composability"라는 동적 구성 모델을 제안합니다. 같은 저장소의 PDF metadata와 README는 초안 날짜를 2026년 8월 13일로 표시하고, active revision preprint라고 밝힙니다.

둘째, Cordis 구현체와 DeepSeek Harness가 이 설계의 실제 적용면을 보여 줍니다. Cordis 저장소는 자신을 "Meta-Framework of Spatiotemporal Composability"라고 설명하고, API 안정성이 아직 없을 수 있다고 경고합니다. DeepSeek Harness README는 `dsh`가 DeepSeek AI의 open-source agent harness이며, 모든 것을 plugin으로 구성하고 Cordis로 구동한다고 밝힙니다.

기사의 관심은 "새 프레임워크가 인기 있다"가 아닙니다. 중요한 점은 AI가 유지보수할 수 있는 앱 구조를 어떻게 나눌지에 대한 구체적 설계 언어가 생겼다는 것입니다. plugin은 기능 단위이고, context는 service 저장소이며, `inject`는 plugin이 기다릴 service 요구사항이고, `ctx.effect()`와 `ctx.on()`으로 등록한 작업은 unload 때 정리할 disposer를 남깁니다.

## Cordis 구조는 plugin 중첩만이 아닙니다

예를 들어 agent 앱에 `ctx.llm`, `ctx.tools`, `ctx.sessions`라는 service가 있고, 한 plugin이 새 model adapter를 등록한다고 보겠습니다. 그 plugin은 단순히 폴더 아래에 놓인 하위 plugin이 아니라, 자신이 제공하는 service와 요구하는 service를 context에 명시합니다. 다른 plugin은 concrete class를 import하지 않고 `inject`로 필요한 service key를 선언한 뒤, 그 service가 존재할 때만 활성화됩니다.

여기서 쉬운 말로 temporal composability는 "부품을 뺄 때 그 부품이 남긴 변경을 되돌리는 능력"입니다. listener, prompt section, tool schema, provider 등록처럼 context에 남긴 변경이 disposer와 함께 기록되고, fiber가 unload될 때 역순으로 정리됩니다. Harness의 Cordis primer도 prompt section, tool schema, adapter, provider, listener가 `ctx.effect()` 또는 `ctx.on()`으로 설치되어 reload와 teardown 때 예측 가능하게 unwind된다고 설명합니다.

spatial composability는 "service가 생기거나 사라질 때 의존 부품을 다시 맞추는 능력"입니다. Cordis의 registry 문서는 `ctx.inject(deps, callback)`을 요청 service가 사용 가능할 때 callback을 실행하는 shorthand로 설명하고, 필요한 service가 바뀌면 callback이 unload 후 다시 실행된다고 적습니다. 논문은 이 관계를 reactive coeffect라고 부릅니다. `effect`는 plugin이 환경에 만든 변경이고, `coeffect`는 plugin이 환경에서 요구하는 service와 조건입니다.

이 구조는 Context 트리, service 제공자와 소비자를 잇는 의존성 그래프, component lifecycle, 그리고 등록한 효과를 역순으로 회수하는 장치가 같이 작동해야 의미가 있습니다. Cordis 문서의 Fiber API는 fiber를 하나의 loaded plugin instance로 정의하고, lifecycle state, validated config, registered effects를 추적한다고 설명합니다. `ctx.effect()`는 즉시 실행한 effect가 만든 disposer를 모아 fiber unload 또는 disposer 호출 시 역순으로 실행합니다.

## AI 유지보수에는 변경 범위를 좁히는 장점이 있습니다

AI에게 전체 앱을 "고쳐 보라"고 시키면 문제는 code size만이 아닙니다. 어떤 module이 어떤 runtime service를 전제로 하는지, 변경이 어느 listener와 resource를 남기는지, 실패했을 때 어디까지 되돌릴 수 있는지가 자연어 문서에 흩어집니다. Cordis식 앱은 plugin tree, service key, `inject` 관계, lifecycle 상태, 등록된 effect metadata를 구조화해 AI에게 보여 줄 수 있습니다.

이 구조가 유리한 첫 번째 지점은 이해 범위입니다. model adapter 교체라면 AI는 `ctx.llm` provider와 그 consumer 계약을 보면 됩니다. tool 실행 정책을 바꾼다면 `ctx.tools` service, `tools/*` event, approval이나 sandbox 관련 plugin을 따로 볼 수 있습니다. DeepSeek Harness architecture 문서는 model adapter, tool registry, session log, agent loop 자체가 모두 plugin이라 configuration에서 교체 가능하다고 설명합니다.

두 번째 지점은 비교 시험입니다. 같은 interface의 provider를 둘 이상 만들고 configuration layer에서 하나를 교체하면, consumer 전체를 고치지 않고 adapter 구현을 나란히 시험할 수 있습니다. 논문은 loader가 entry의 `url`, `config`, `isolate`, `intercept`, `disabled` 같은 필드를 보고 incremental reconciliation을 수행한다고 설명합니다. 실패한 hot reload는 module cache를 복구하고 stale entry를 backup으로 다시 세우는 transactional reload 절차도 제시합니다.

세 번째 지점은 rollback의 기준입니다. `ctx.effect()`가 등록한 disposer는 LIFO 순서로 실행되므로, plugin이 context 안에서 만든 listener, resource, service 등록은 제거 순서가 정해집니다. 이것은 source control의 `git revert`와 같은 코드 변경 rollback은 아니지만, running process 안에서 "이 plugin episode가 context에 남긴 것"을 회수하는 토대가 됩니다.

## LLM의 자기회귀와 agent 자기변형은 다른 문제입니다

여기서 용어를 분리해야 합니다. LLM의 자기회귀는 다음 token을 이전 token 조건에서 순차 생성하는 모델 동작입니다. Cordis가 말하는 recursive composition은 component가 하위 component를 만들고 Context 트리 안에 붙이는 구조입니다. agent의 자기변형 또는 자기진화는 agent가 자기 tool, prompt, policy, adapter 같은 harness 부품을 생성·교체하는 더 큰 workflow입니다.

Cordis는 두 번째 문제, 즉 component가 component를 만들고 실행 중 교체되는 구조를 다룹니다. 세 번째 문제의 안전한 기반이 될 수는 있지만, 어떤 변경안을 채택할지 판단하거나 학습 데이터를 축적해 자기 성능을 높이는 엔진은 아닙니다. 논문도 conclusion에서 self-evolving agent harness 적용을 "future validation" 방향으로 둡니다.

DeepSeek Harness와의 관계도 이 선에서 읽어야 합니다. Harness README는 Cordis가 `dsh` 아래의 plugin framework라고 밝히고, architecture 문서는 sandbox와 approval policy까지 base layer의 plugin으로 언급합니다. 이 사실은 DeepSeek Harness가 Cordis를 채택했다는 근거입니다. 하지만 Harness가 Cordis 덕분에 자율 자기개선 성능을 검증했다는 근거는 아닙니다.

## 보장되는 것과 보장되지 않는 것

논문은 preservation, recovery exactness, ordering, progress, confluence 같은 형식 성질을 제시합니다. 대략 말하면 well-formed registry에서 lifecycle 규칙이 구조를 보존하고, 독립성이 성립하는 effect들은 fiber 제거 후 해당 fiber의 기여를 회수하며, provider가 떠날 때 consumer teardown 순서를 맞추고, acyclic precedence와 유한성 같은 조건에서 quiescent state에 도달한다는 주장입니다.

이 보장은 전제가 있습니다. 논문은 `ctx.effect()` callback이 inverse를 제공하고, 그 inverse가 실제로 원래 effect를 되돌린다는 것은 component 작성자의 의무라고 선을 긋습니다. 서로 독립인 effect, 비순환 의존 관계, 유한한 component 집합과 transition 길이 같은 조건도 들어갑니다. runtime이 작성자의 inverse 정확성을 자동 증명하는 것은 아닙니다.

system boundary도 중요합니다. 논문 discussion은 외부로 emission된 데이터가 context 밖에 있으면 tracking과 recovery 대상이 아니라고 설명합니다. 이미 보낸 network packet, 결제 요청, 외부 공유 파일, 다른 process가 읽고 쓰는 경로는 Cordis context 안의 disposer만으로 원상복구되지 않습니다. 그런 작업은 출력 commit 지연, 보상 transaction, 별도 audit log, idempotency key가 필요합니다.

보안도 별도입니다. Cordis는 dependency declaration과 interception으로 component가 어떤 context service를 proxy-mediated 방식으로 접근하는지 통제할 수 있지만, 악성 code가 host runtime 객체에 직접 접근할 수 있으면 language-level access control은 충분하지 않습니다. 논문은 untrusted component에는 process, virtualized container, 별도 runtime 같은 sandbox boundary가 필요하다고 설명합니다.

## 어떤 앱 설계에 적용할 수 있나

Cordis식 설계는 plugin이 많고 실행 중 교체가 필요한 앱에 잘 맞습니다. agent harness, IDE extension host, chatbot framework, tool runner, workflow engine처럼 service provider와 consumer가 계속 바뀌는 시스템이 해당합니다. 작은 plugin과 명시적 dependency를 유지할수록 AI가 읽고 시험하고 되돌릴 수 있는 단위도 작아집니다.

반대로 모든 것을 Cordis로 만들 필요는 없습니다. 권한, sandbox, audit, 검증, release gate, rollback orchestration은 작은 안정 core에 남기는 편이 안전합니다. AI가 바꿀 수 있는 영역은 model adapter, prompt section, tool provider, workflow step, UI node처럼 계약이 좁고 교체 결과를 시험하기 쉬운 외곽으로 제한하는 편이 합리적입니다.

Koishi 사례는 참고할 만하지만 과장하면 안 됩니다. 논문은 Koishi가 Cordis 위에 지어진 open-source chatbot framework이며 4,000개가 넘는 community plugin을 가진 생산 시스템이라고 설명합니다. 동시에 이 사례가 TypeScript 단일 생태계의 관찰 사례이고, 대조 실험이나 overhead·생산성 비교가 없으며, Koishi는 논문이 설명하는 Cordis v4가 아니라 Cordis v3를 사용한다고 한계를 밝힙니다.

## 이 공개의 의의와 편집 판단

확인된 사실은 세 가지입니다. 2026년 8월 13일자 active-revision preprint가 공개됐고, Cordis 구현체가 별도 공개 저장소로 있으며, DeepSeek Harness가 Cordis 기반 plugin architecture를 공식 문서에서 채택하고 있습니다. 여기에 Cordis API 문서와 논문 PDF는 `ctx.effect()`, `inject`, fiber lifecycle, loader reconciliation처럼 엔지니어가 직접 확인할 수 있는 구현 표면을 제공합니다.

편집 판단: AI가 유지보수할 앱을 설계할 때 Cordis의 핵심 가치는 "스스로 똑똑해지는 runtime"이 아니라 "AI가 바꿀 수 있는 범위를 작게 만들고, 그 범위의 의존성과 정리 절차를 구조화하는 runtime"입니다. 이 차이는 제품 설계에 바로 이어집니다. 안정 core와 교체 가능한 외곽을 나누고, 외곽 plugin이 만든 effect와 요구 coeffect를 명시하면 AI가 변경 영향, 시험 대상, rollback 경계를 더 좁게 판단할 수 있습니다.

## benchmark 또는 재현 결과

편집국은 Cordis나 DeepSeek Harness를 로컬에서 실행해 benchmark를 재현하지 않았습니다. 재현성 상태는 R2입니다. 이유는 논문 PDF, Cordis 코드, Harness 코드와 문서, Koishi 코드가 공개되어 구조와 API를 독자가 직접 열람·실행할 수 있지만, 기사에서는 runtime overhead나 생산성 개선을 실험 결과로 주장하지 않기 때문입니다.

확인한 실행 artifact 범위는 공개 저장소의 현재 HEAD입니다. `cordiverse/paper` HEAD는 `948a07b369c62adb3b12e102458be5c18dfb69b9`, `cordiverse/cordis` HEAD는 `8cc9e33fab69e2d0476d126baaf2acb24e6a6ab4`, `deepseek-ai/deepseek-harness` HEAD는 `47f943859bef60e4160492346772ded9b24f765a`, `koishijs/koishi` HEAD는 `fb6e2c092242c0387f07f36e21082d5715c48449`였습니다. 이 값은 2026년 8월 14일 UTC에 확인한 snapshot입니다.

## 적용 범위와 확인하지 못한 것

논문은 active-revision preprint입니다. 발행 시점에 arXiv, DOI, 학회 게재, 동료평가 여부는 다시 확인해야 합니다. 이 기사는 논문이 공개한 설계와 코드 artifact를 근거로 삼았고, peer review가 끝난 연구 결과처럼 쓰지 않았습니다.

형식 모델은 보존, 복구 정확성, 의존 순서, 진행성과 합류성을 다루지만 inverse 정확성, effect 독립성, 비순환 의존 관계 같은 전제가 있습니다. Cordis runtime은 component 작성자가 준 disposer나 inverse가 외부 세계까지 정확히 되돌리는지 자동 증명하지 않습니다. context 밖으로 이미 나간 network message, 결제, 외부 공유 파일은 자동 rollback 대상이 아닙니다.

DeepSeek Harness의 Cordis 채택과 자율 자기개선 효과 검증도 분리해야 합니다. Harness 문서는 Cordis 기반 plugin 구조와 swappable capability를 확인시켜 주지만, AI가 자기 harness를 지속적으로 고쳐 성능을 높였다는 독립 실험은 아닙니다. 논문 결론도 이 검증을 미래 연구로 남겼습니다.

## 독자가 내릴 수 있는 기술 판단

agent harness나 plugin-heavy 앱을 설계하는 팀은 Cordis를 바로 도입하지 않더라도 설계 체크리스트로 쓸 수 있습니다. 기능을 plugin 단위로 나누고, plugin이 요구하는 service를 선언하게 하며, listener·resource·provider 등록을 반드시 disposer와 묶는지 확인해야 합니다. AI가 수정할 수 있는 영역은 이 계약을 만족하는 외곽 plugin으로 제한하는 편이 좋습니다.

Cordis 도입을 검토한다면 첫 실험은 성능 benchmark가 아니라 failure rehearsal이어야 합니다. model adapter를 교체하다 import error를 내고, tool provider를 unload하고, sandbox provider를 바꿨을 때 어떤 consumer가 내려가고 어떤 state가 남는지 로그로 확인해야 합니다. 그다음에 latency, memory, HMR 시간, developer workflow 개선을 여러분의 workload에서 따로 측정해야 합니다.

## 이해상충과 취재 조건

논문 저장소, Cordis, DeepSeek Harness, Koishi 문서는 각 프로젝트의 작성자와 운영자가 제공한 1차 근거입니다. 이 자료들은 공개 사실, 코드 구조, 문서화된 API, 논문 저자의 주장과 한계를 확인하는 데 적합하지만, Cordis의 생산성 개선이나 자율 자기개선 효과에 대한 독립 검증은 아닙니다.

이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 웹 문서, 공개 GitHub 저장소, 공개 PDF만 사용했습니다. 검색 결과와 저장소 인기 신호는 발견 신호로만 보았고 중심 주장에는 사용하지 않았습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. DeepSeek-AI와 베이징대 소속 연구진은 2026년 8월 13일 `A Programming Paradigm for Spatiotemporal Composability` 초안을 공개했습니다. | E2 · P1 · R2 | 논문 PDF의 저자·소속, PDF metadata, 논문 저장소 README로 확인했습니다. active-revision preprint이며 peer review 상태는 확인되지 않았습니다. |
| C2. 논문은 temporal composability를 component 제거 시 side effect를 되돌리는 능력, spatial composability를 dependency를 선언하고 변화에 반응해 관리하는 능력으로 정의합니다. | E2 · P1 · R2 | 논문 abstract와 introduction, paper README로 확인했습니다. 정의 자체의 채택 가능성은 별도 학계 검증 문제가 남습니다. |
| C3. Cordis 구현은 `ctx.effect()`, fiber lifecycle, `inject`, service 제공·소비, loader reconciliation, hot module replacement를 통해 논문 모델의 runtime 대응물을 제공합니다. | E2 · P1/P2 · R2 | 논문 implementation 절, Cordis README, DeepSeek Harness의 generated Cordis API 문서로 확인했습니다. 편집국은 Cordis test suite를 실행하지 않았습니다. |
| C4. DeepSeek Harness는 Cordis 기반 plugin architecture를 사용하며 model adapter, tool registry, session log, agent loop 등을 plugin으로 구성한다고 문서화합니다. | E2 · P1/P2 · R2 | DeepSeek Harness README, Cordis primer, architecture 문서로 확인했습니다. 이는 채택 사실의 근거이지 자율 자기개선 효과 검증은 아닙니다. |
| C5. Koishi 사례는 Cordis 기반 production ecosystem 사례로 제시되지만 단일 TypeScript 생태계 관찰 사례이고 overhead·생산성 대조 실험은 없습니다. | E2 · P1/P2 · R2 | 논문 case study와 Koishi README로 확인했습니다. Koishi README는 3,000개 이상 plugin을, 논문은 4,000개 이상 community plugin을 언급하며 기준 시점과 Cordis v3/v4 차이가 있습니다. |
| C6. 중심 편집 판단은 Cordis가 AI가 좁은 범위를 이해·시험·교체·복구하기 좋은 구조를 제공하지만, Cordis 자체가 자기개선 엔진은 아니라는 것입니다. | E2 · derived · R2 | C1-C5와 논문 conclusion의 future validation 문단에서 파생했습니다. 자율 개선안 선택, 학습, 성능 향상은 주장하지 않았습니다. |

## 출처

- Cordis paper repository: https://github.com/cordiverse/paper
- Cordis paper PDF: https://raw.githubusercontent.com/cordiverse/paper/948a07b369c62adb3b12e102458be5c18dfb69b9/paper.pdf
- Cordis implementation repository: https://github.com/cordiverse/cordis
- Cordis core README at checked commit: https://raw.githubusercontent.com/cordiverse/cordis/8cc9e33fab69e2d0476d126baaf2acb24e6a6ab4/packages/core/README.md
- DeepSeek Harness repository: https://github.com/deepseek-ai/deepseek-harness
- DeepSeek Harness Cordis primer: https://deepseek-harness.github.io/deepseek-harness/reference/cordis-primer/
- DeepSeek Harness architecture document at checked commit: https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/47f943859bef60e4160492346772ded9b24f765a/docs/architecture.md
- DeepSeek Harness generated Cordis Fiber API: https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/47f943859bef60e4160492346772ded9b24f765a/docs/cordis-api/fiber.md
- DeepSeek Harness generated Cordis Registry API: https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/47f943859bef60e4160492346772ded9b24f765a/docs/cordis-api/registry.md
- Koishi repository: https://github.com/koishijs/koishi
