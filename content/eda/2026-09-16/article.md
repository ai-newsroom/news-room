---
edition: eda
decision: publish-candidate
title: "PSS 3.1 초안, 검증 시나리오가 실행 코드로 바뀌는 과정을 더 자세히 적습니다"
date: 2026-09-16
subject: "Accellera Portable Test and Stimulus Standard 3.1 Draft for Public Review, August 31 2026"
summary: "Accellera가 PSS 3.1 공개 검토 초안을 2026년 8월 31일 공개했고 9월 30일까지 의견을 받습니다. 초안은 제약 언어, 재사용 library, target code 생성, address와 register 모델을 보강해 같은 검증 의도를 여러 실행 환경에 맞게 코드로 만드는 과정을 더 분명히 적습니다. 아직 최종 표준이나 도구 호환성 검증은 아닙니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["없음. 공개 Accellera 웹페이지와 공개 초안 PDF만 사용했고, 사전 briefing, 제공받은 account·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

PSS는 Portable Test and Stimulus Standard의 줄임말입니다. 검증 엔지니어가 하나의 추상 시나리오로 동작 의도를 쓰면, 도구가 simulation, emulation, silicon bring-up 같은 여러 실행 환경에 맞는 test를 만들 수 있게 하려는 표준입니다. SoC 검증에서는 같은 기능을 block 단계의 SystemVerilog testbench, SoC 단계의 embedded software, emulation 환경에서 다시 쓰고 싶을 때가 많습니다. 하지만 실제 현장에서는 언어와 실행 환경이 달라 같은 시나리오를 여러 번 옮겨 적는 일이 흔합니다.

Accellera는 2026년 8월 31일 PSS 3.1 Draft Standard를 공개 검토에 올렸고, 2026년 9월 30일까지 의견을 받습니다. Accellera는 이번 초안을 PSS 3.0 위에 쌓는 focused release라고 설명합니다. 변화가 모인 곳은 네 영역입니다. 제약을 쓰는 방법, project와 team 사이에서 나눠 쓰는 library, target code 생성 제어, address space와 register 모델입니다.

이번 초안의 의미는 PSS가 "한 번 쓴 시나리오를 여러 도구에서 실행한다"는 큰 목표를 다시 말한 데 있지 않습니다. 더 중요한 변화는 추상 시나리오가 실제 target code로 바뀌는 과정을 표준 문법 안에서 더 많이 표현하게 한 점입니다. 검증 의도를 모델에 담는 일과, 그 의도가 C나 SystemVerilog 같은 실행 코드로 바뀌는 일 사이의 빈칸을 줄이려는 수정입니다.

## 같은 검증 의도로 여러 실행 환경의 test를 만듭니다

Accellera Portable Stimulus Working Group은 PSS의 범위를 "여러 target implementation에 stimulus를 생성할 수 있는 portable test and stimulus specification language"로 설명합니다. 여기서 stimulus는 설계를 움직이게 하는 입력과 동작 순서입니다. target implementation은 simulation testbench, emulation, embedded software처럼 실제로 test가 실행되는 환경을 뜻합니다.

이 차이가 중요한 이유는 검증 재사용의 단위가 소스 코드 파일이 아니라 의도와 행위가 되기 때문입니다. 예를 들어 DMA 전송, interrupt 처리, register 접근 순서가 섞인 시나리오를 생각해 볼 수 있습니다. block 검증에서는 SystemVerilog sequence가 필요하고, SoC 검증에서는 processor에서 도는 C 코드가 필요할 수 있습니다. PSS 모델은 두 환경에 공통으로 들어가는 의도를 더 높은 층에서 적습니다. 그다음 도구가 각 target에 맞는 구현을 만들도록 하는 쪽을 겨냥합니다.

PSS 3.0은 2024년 8월 release에서 behavioral coverage를 큰 변화로 넣었습니다. 하나의 PSS specification에서 여러 scenario를 만들고 어떤 동작 공간을 덮었는지 보는 쪽에 무게가 있었습니다. 3.1 초안은 그 다음 단계에서 constraint와 realization, register 접근처럼 실제 test 생성에 가까운 부분을 다듬습니다.

## 3.1은 조건을 풀고 코드를 만드는 단계를 손봅니다

초안 PDF의 introduction은 3.1이 PSS 3.0에 비해 새 기능 추가, 오류 수정, 언어와 의미 정의 clarification, 일부 기능 제거, section 재구성을 담았다고 설명합니다. 새 기능 목록에는 `soft constraints`, `mutable attributes`, action handle의 multi-dimensional array가 들어갑니다. solve context에서 string literal formatting을 쓰는 기능과 inline non-rand action attribute 지정도 포함됩니다.

쉽게 말하면 모델 작성자가 "이 값은 가능하면 이렇게 잡되, 다른 제약 때문에 필요하면 바꿔도 된다" 같은 조건을 더 자연스럽게 표현할 수 있게 됩니다. PSS가 constrained random generation과 scenario generation에 쓰이는 언어라는 점을 생각하면, constraint는 단순한 문법 기능이 아닙니다. 어떤 시나리오가 합법인지, tool이 어떤 test 변형을 만들 수 있는지, coverage space를 어떻게 탐색할지를 정하는 기준입니다.

target code 생성 쪽 변화도 눈에 띕니다. 초안은 target-template과 triple-quoted string 처리를 명확히 하고 강화했다고 적었습니다. 새 기능 목록에는 exported functions, code generation deduplication을 위한 exec block tag, solve platform과 target platform 양쪽의 `message`도 있습니다. target-time communication과 executor 사이 synchronization도 포함됩니다.

이 변화는 PSS 모델이 추상 설명에서 끝나지 않고 실행 코드의 모양까지 더 많이 통제하도록 합니다. 여러 action이 같은 helper code를 반복해서 만들지 않게 하거나, target에서 실행되는 코드가 필요한 시점에 메시지와 동기화를 다루게 하는 식입니다. 검증팀 입장에서는 모델 재사용만이 아니라 생성된 test code의 읽기 쉬움, 중복, platform별 glue code 관리도 판단 대상이 됩니다.

## register와 address 모델은 SoC 검증 장면을 더 직접 다룹니다

PSS 3.1 초안은 address space와 register layer도 보강했습니다. 새 기능 목록에는 register base type과 target code에서 register를 symbolic representation으로 다루는 기능이 들어갑니다. overlapping action 사이에서 address claim을 공유하는 문법, memory access descriptor를 확장할 수 있는 hook도 포함됩니다. 초안은 이 memory access descriptor 인자 추가가 backward compatible하지 않다고도 밝힙니다.

SoC 검증에서 register 접근은 단순한 read/write 호출이 아닙니다. 어떤 peripheral의 programmer's view를 모델링하고, address map과 register collection을 따라가야 합니다. 여러 실행 주체가 같은 memory나 register resource를 건드릴 때 충돌도 막아야 합니다. PSS가 이 층을 더 명확히 하면, test intent와 firmware-like target code 사이의 연결이 좋아질 수 있습니다.

다만 이 기사는 "PSS 3.1을 지원하면 검증 효율이 몇 퍼센트 오른다"는 결론을 내리지 않습니다. 공개 초안은 표준 문법과 의미를 설명하는 P1 원문입니다. 특정 tool이 이 초안을 얼마나 빨리 구현하는지, 기존 PSS 3.0 model이 어떤 수정 없이 동작하는지, 서로 다른 vendor tool이 같은 target code를 만드는지는 별도 확인 대상입니다.

## 지금은 초안을 검토하고 도구 호환성은 나중에 봐야 합니다

지금 할 일은 PSS를 쓰는 검증팀이 3.1 초안의 변경 목록을 자기 model coding rule과 맞춰 보는 것입니다. `soft constraints`, target-template, exec block tag, register base type처럼 model 작성 방식에 영향을 줄 수 있는 항목은 style guide와 generator template을 바꿀 수 있습니다. 공개 검토 기간이 2026년 9월 30일까지이므로, 실제 model에서 막히는 표현이나 backward compatibility 문제는 working group에 의견으로 낼 수 있습니다.

아직 미룰 일은 3.1을 최종 표준이나 검증 flow 전환 근거로 보는 것입니다. 초안 PDF 자체가 draft for public review이고, Accellera notices는 표준 문서가 자발적 사용 대상이라고 밝힙니다. Accellera가 내용의 정확성을 독립 시험하거나 검증하지 않는다는 한계도 적고 있습니다. vendor support matrix, parser release note, conformance example이 나오기 전에는 tool 호환성을 단정하기 어렵습니다.

다음에 확인할 신호는 세 가지입니다. Accellera가 public review 의견을 반영해 3.1 최종 표준을 승인하는지, 주요 verification tool이 3.1 문법과 register 모델 지원 범위를 release note에 공개하는지, 같은 PSS 3.1 model이 simulation과 emulation 또는 embedded target에서 같은 의도로 실행되는 공개 예제가 나오는지입니다.

## 이해상충과 취재 조건

이 기사는 Accellera의 공개 웹페이지, 공개 검토 목록, PSS 3.1 draft PDF, Portable Stimulus Working Group 페이지를 확인했습니다. Accellera, EDA 벤더, tool 공급자로부터 사전 briefing, 비공개 draft, license, account, hardware, 광고, 후원, NDA, embargo를 제공받지 않았습니다. 편집국은 PSS parser나 상용 verification tool에서 3.1 문법을 실행하지 않았습니다.

## 근거 원장

| claim | 근거 | 등급 | 확인한 내용 | 한계 |
|---|---|---|---|---|
| C1 | https://www.accellera.org/ | E1 | Accellera는 PSS 3.1 Draft Standard 공개 검토가 열렸고, 공개 검토 기간이 2026년 9월 30일까지라고 공지했습니다. | 발표와 상태 확인 근거이며 tool 구현을 검증하지 않습니다. |
| C2 | https://www.accellera.org/downloads/drafts-review | E1 | Drafts Under Public Review 페이지는 Portable Stimulus Standard Draft 3.1의 상태와 date modified 2026-08-31을 표시합니다. | 목록 페이지는 변경 세부를 설명하지 않습니다. |
| C3 | https://www.accellera.org/images/downloads/drafts-review/PSS%203.1%20Public%20Review%20Draft%202026.08.28.pdf | E2 | 초안 PDF는 PSS 3.1 Draft for Public Review, August 31 2026이며, PSS 3.0 대비 새 기능 목록과 backward incompatible memory access descriptor 변경을 설명합니다. | draft 문서이며 최종 표준이 아닙니다. |
| C4 | https://www.accellera.org/activities/working-groups/portable-stimulus | E2 | Working Group 페이지는 PSS의 목적, 여러 target implementation으로 stimulus를 생성하는 범위, PSS 3.0의 behavioral coverage 추가 배경을 설명합니다. | working group 설명은 표준 적용 결과나 vendor 호환성 검증이 아닙니다. |

## 출처

- https://www.accellera.org/
- https://www.accellera.org/downloads/drafts-review
- https://www.accellera.org/images/downloads/drafts-review/PSS%203.1%20Public%20Review%20Draft%202026.08.28.pdf
- https://www.accellera.org/activities/working-groups/portable-stimulus
