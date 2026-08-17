---
edition: eda
decision: publish-candidate
title: "FSL 1.0 Draft는 기능안전 FMEDA를 스프레드시트 교환에서 설계 데이터 flow로 옮깁니다"
date: 2026-08-18
subject: "Accellera Functional Safety Language 1.0 Draft public review와 FMEDA 데이터 모델"
summary: "Accellera의 FSL 1.0 Draft public review가 2026년 8월 14일 끝났습니다. 초안은 FMEDA 안전 분석을 Tcl 기반 명령과 데이터 모델로 표현해 IP, SoC, 시스템 단계 사이의 추적성을 높이려 하지만, 아직 최종 표준이나 도구 호환성 검증은 아닙니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["없음"]
---

자동차, 산업 장비, 의료 기기처럼 안전 요구가 큰 칩에서는 회로가 어떻게 고장 날 수 있고 어떤 안전 메커니즘이 그 고장을 잡는지 계속 추적해야 합니다. 이 작업의 중심에는 FMEDA, 즉 Failure Modes, Effects and Diagnostic Analysis가 있습니다. 고장 모드와 영향, 진단 커버리지를 정리하는 분석입니다.

Accellera는 Functional Safety Language, 줄여서 FSL 1.0 Draft를 2026년 7월 공개했고 public review를 2026년 8월 14일까지 받았습니다. 이번 초안의 의미는 "또 하나의 안전 문서"가 아니라, FMEDA 정보를 스프레드시트와 벤더별 데이터베이스 밖으로 꺼내 EDA 도구가 읽고 주고받을 수 있는 구조로 정의했다는 데 있습니다.

## FSL이 바꾸려는 병목은 안전 분석의 재입력과 손실입니다

기능안전 분석은 한 팀에서 끝나지 않습니다. IP 공급자는 블록의 고장 모드와 안전 메커니즘을 설명하고, SoC 팀은 그 IP를 더 큰 설계 계층에 넣어 영향 범위를 다시 계산합니다. 시스템 통합자는 ISO 26262나 IEC 61508 같은 안전 표준의 목표에 맞춰 이 정보를 다시 조합합니다.

기존 flow에서는 이 정보가 표, 문서, 도구별 포맷, 수작업 변환으로 흩어지기 쉽습니다. 그래서 안전 메커니즘이 어떤 failure mode를 덮는지, 그 진단 커버리지가 추정값인지 fault injection 같은 검증 활동에서 나온 측정값인지, IP 단계의 가정이 SoC 단계에서 그대로 유효한지 추적하기 어렵습니다.

FSL draft는 이 지점을 언어와 데이터 모델로 고정하려 합니다. Accellera의 초안은 FSL을 FMEDA 작성, failure mode와 safety mechanism 모델링, safety requirement 정의, 여러 abstraction level의 design representation에 안전 데이터를 매핑하기 위한 표준화된 언어와 데이터 모델로 설명합니다.

## 설계 입력 옆에 안전 의도를 붙이는 방식입니다

FSL은 설계 RTL을 대체하지 않습니다. RTL은 회로가 어떻게 동작하는지 적고, FSL은 그 회로 또는 기능 계층에 어떤 안전 정보가 연결되는지 적습니다. 초안은 functional representation과 structural representation 모두에 안전 분석을 매핑할 수 있다고 설명합니다. Functional representation은 기능 블록 중심 표현이고, structural representation은 실제 구현 구조에 가까운 표현입니다.

작동 흐름은 다음처럼 볼 수 있습니다. 먼저 `create_fmeda`로 분석 단위를 만들고, `create_element`로 설계 또는 기능 계층의 대상을 세웁니다. 그다음 `create_fm`으로 failure mode, 즉 특정 요소가 어떻게 실패할 수 있는지를 정의합니다. `create_sm`은 parity check나 watchdog timer 같은 safety mechanism을 만들고, `assign_sm_fm`은 그 safety mechanism을 failure mode에 연결합니다.

이 연결이 중요한 이유는 진단 커버리지 값을 어디에 둘지까지 언어가 다루기 때문입니다. FSL draft의 `assign_sm_fm` 명령은 permanent, transient, latent fault에 대한 estimated diagnostic coverage와 measured diagnostic coverage를 구분합니다. estimated는 분석이나 가정에서 온 값이고, measured는 fault injection 또는 verification activity 결과에서 온 값입니다. 같은 "커버리지 90%"라도 출처와 신뢰도가 다르다는 사실을 flow 안에 남길 수 있습니다.

## 이전 white paper의 데이터 모델이 draft LRM으로 올라왔습니다

이번 초안은 갑자기 나온 형식이 아닙니다. Accellera Functional Safety Working Group의 2023년 white paper는 FMEDA process, design representation, mapping, conceptual data model을 먼저 정리했습니다. 그 문서는 FMEDA evaluation과 "as-is" exchange라는 두 사용 사례를 나눴습니다. 전자는 안전 분석을 작성하면서 데이터 모델을 채우는 방식이고, 후자는 이미 만들어진 FMEDA 표나 요약을 교환하는 방식입니다.

2026년 FSL draft는 이 논의를 Language Reference Manual에 가까운 형태로 올렸습니다. 목차만 봐도 `create_fmeda`, `create_te`, `create_sm`, `create_element`, `create_fm`, `create_fme`, `create_sreq`, 여러 `assign_*` 명령, ISO 26262와 IEC 61508 관련 failure rate와 metric 정의 명령이 들어갑니다. 여기서 TE는 technology element, SM은 safety mechanism, SREQ는 safety requirement로 읽을 수 있습니다.

설계 flow 관점에서 새 국면은 자동화가 가능한 최소 단위가 생겼다는 점입니다. 안전 엔지니어가 표 하나를 넘기는 대신, failure mode와 design element의 관계, safety mechanism과 diagnostic coverage의 관계, requirement와 metric의 관계를 도구가 파싱할 수 있는 명령 단위로 주고받을 수 있습니다. 이것이 실제로 통하려면 각 벤더 도구가 같은 의미로 읽고 쓰는 conformance가 필요하지만, 초안 자체는 그 검사의 기준점을 제공합니다.

## 지금 할 일 / 아직 미룰 일 / 다음에 확인할 신호

지금 할 일은 FSL을 기존 safety flow의 포맷 후보로 검토하는 것입니다. 특히 IP 공급자와 SoC 통합자 사이에서 FMEDA, safety mechanism, failure mode effect, safety requirement를 어떤 표와 필드로 주고받는지 목록화하면 FSL 명령과 데이터 객체에 매핑되는 부분을 빨리 찾을 수 있습니다.

아직 미룰 일도 있습니다. FSL 1.0 Draft는 public review가 끝난 초안이지 최종 표준으로 ratify된 문서가 아닙니다. 또한 공개 자료만으로는 상용 EDA 도구의 import/export 호환성, 기존 FMEDA spreadsheet 변환 품질, ISO 26262 audit에서의 수용 방식, 실제 fault injection 결과와의 round-trip 검증을 확인할 수 없습니다. 따라서 "FSL을 쓰면 안전 signoff가 자동화된다"는 결론은 아직 강합니다.

다음에 확인할 신호는 세 가지입니다. Accellera가 public review 의견을 반영한 최종 1.0 표준을 언제 승인하는지, vendor-neutral 예제 repository나 conformance suite를 공개하는지, 주요 EDA·functional safety 도구가 같은 FMEDA를 FSL로 내보내고 다시 읽는 round-trip 결과를 제시하는지입니다.

## 이 draft가 설계 조직에 주는 의미

FSL의 가장 현실적인 가치는 기능안전 검토를 설계 flow 밖의 문서 작업으로만 두지 않게 만드는 데 있습니다. RTL, netlist, IP-XACT, SysML 같은 설계 표현 자체와는 별개로, safety intent가 어떤 설계 요소와 failure mode에 붙는지 추적할 수 있으면 변경 영향 분석이 쉬워집니다. 예를 들어 IP 내부 safety mechanism이 바뀌었을 때 해당 failure mode effect와 상위 SoC safety requirement가 어디까지 영향을 받는지 도구가 추적할 여지가 생깁니다.

다만 표준 형식이 생긴다고 안전 판단이 자동으로 맞아지는 것은 아닙니다. Failure rate, diagnostic coverage, latent fault 분류, requirement의 충분성은 여전히 공정, 설계 구조, fault model, verification strategy에 묶입니다. FSL은 그 판단을 담는 그릇과 연결선을 표준화하려는 시도입니다. 그릇 안의 값이 맞는지는 별도의 verification과 review가 필요합니다.

## 이해상충과 취재 조건

중심 근거는 Accellera의 FSL 1.0 Draft PDF, Drafts Under Public Review 페이지, Functional Safety Working Group 페이지, 2023년 white paper입니다. Accellera working group에는 EDA 벤더와 반도체·IP 회사 참여자가 포함될 수 있으므로 표준의 방향에는 생태계 이해관계가 반영됩니다.

편집국은 Accellera, EDA 벤더, 도구 공급자에게서 사전 브리핑, 라이선스, 비공개 draft, 고객 사례를 제공받지 않았습니다. 공개 문서만으로 언어 구조와 표준화 의도를 확인했으며, FSL parser나 vendor tool의 round-trip 동작은 실행하지 않았습니다.

## 근거 원장

| Claim | 근거 | 판정 |
|---|---|---|
| C1. Accellera는 FSL 1.0 Draft를 공개했고 public review는 2026년 8월 14일까지 진행됐다. | Accellera home, Drafts Under Public Review | `E1`: 표준 기구의 공개 상태와 날짜 확인 |
| C2. FSL draft는 FMEDA, failure mode, safety mechanism, safety requirement, design representation mapping을 위한 언어와 데이터 모델을 정의한다. | FSL 1.0 Draft PDF | `E2`: 초안 본문과 명령 목록에서 범위 확인 |
| C3. `assign_sm_fm`은 safety mechanism을 failure mode에 연결하며 estimated diagnostic coverage와 measured diagnostic coverage를 구분한다. | FSL 1.0 Draft PDF | `E2`: 명령 syntax와 argument 설명에서 직접 확인 |
| C4. 2023년 white paper는 FMEDA 데이터 모델과 authoring/exchange 사용 사례를 먼저 제시했고, 2026년 draft는 이를 언어 명령으로 구체화했다. | Functional Safety White Paper 2023, FSL 1.0 Draft PDF | `E2`: WG 산출물 간 구조적 연속성 확인 |
| C5. FSL이 상용 도구 간 완전한 호환성과 safety signoff 자동화를 이미 보장한다. | 공개 conformance 결과 없음 | 미확인: 기사 결론으로 채택하지 않음 |

근거 수준의 상한은 `E2`, 재현성은 `R1`입니다. 언어와 데이터 모델은 공개 초안으로 설명 가능하지만, 실행 가능한 reference parser, conformance suite, vendor round-trip 로그를 확인하지 못했습니다.

## 출처

1. [Accellera, Functional Safety Draft Standard Available for Public Review](https://www.accellera.org/)
2. [Accellera, Drafts Under Public Review](https://www.accellera.org/downloads/drafts-review)
3. [Accellera, Functional Safety Language Standard Version 1.0 Draft PDF](https://www.accellera.org/images/downloads/drafts-review/FSL-1.0-draft.pdf)
4. [Accellera, Functional Safety Working Group](https://www.accellera.org/activities/working-groups/functional-safety)
5. [Accellera, Functional Safety Working Group White Paper, 2023-12-13](https://www.accellera.org/images/downloads/standards/functional-safety/Functional_Safety_White_Paper_20231213.pdf)
