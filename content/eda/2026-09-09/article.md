---
edition: eda
decision: publish-candidate
title: "Cadence EDA flow가 AWS Graviton에서도 native로 실행됩니다"
date: 2026-09-09
subject: "Cadence full front-to-back EDA flow qualification on AWS Graviton4 and Graviton5 through Cadence OnCloud, announced 2026-09-08"
summary: "Cadence는 Xcelium, Jasper, Conformal, Genus, Innovus+, Tempus를 포함한 full front-to-back EDA flow를 Arm 기반 AWS Graviton에서 native로 실행할 수 있도록 qualified했다고 밝혔습니다. 이 변화는 클라우드 EDA 용량 계획에서 x86 서버만 보던 선택지를 넓힙니다. 다만 공개 원문은 정확한 Cadence tool release, design set, PPA, runtime, license 비용, signoff correlation 수치를 제시하지 않았습니다. 성능 우월성은 벤더와 파트너의 주장으로만 다뤄야 합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Cadence, AWS, Arm은 이번 흐름의 직접 이해관계자입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

대형 SoC 설계팀이 클라우드에서 implementation과 signoff를 돌릴 때는 CPU 아키텍처도 flow를 제약합니다. Cadence는 2026년 9월 8일 Xcelium, Jasper, Conformal, Genus, Innovus+, Tempus를 포함한 full front-to-back EDA flow가 AWS Graviton에서 native로 실행되도록 qualified됐다고 밝혔습니다. Graviton은 AWS가 EC2용으로 제공하는 Arm 기반 서버 프로세서입니다.

이번 변화의 핵심은 “클라우드에서 EDA를 쓴다”는 사실 자체가 아닙니다. Cadence OnCloud는 이미 AWS, Microsoft Azure, IBM Cloud 같은 환경에서 front-end부터 back-end까지 설계 도구를 제공한다고 설명해 왔습니다. 새 발표에서 달라진 점은 실행 대상에 Arm AArch64 기반 Graviton4와 Graviton5가 들어갔다는 것입니다. Cadence는 또 Annapurna Labs가 digital implementation과 signoff 일부를 production에서 쓰고 있다고 밝혔습니다.

## x86만 보던 용량 계획에 Arm 서버가 들어옵니다

EDA workload에는 짧은 interactive 작업보다 긴 batch 작업과 반복 실행이 많습니다. Synthesis는 RTL을 gate 수준 netlist로 바꾸는 단계입니다. Place-and-route는 cell과 wire를 실제 layout 위치에 배치·배선합니다. Timing signoff는 tapeout 전에 지연과 timing constraint가 닫혔는지 확인하는 단계입니다. 이 작업들은 tapeout 직전이나 ECO가 몰리는 시점에 CPU core, memory, license를 한꺼번에 요구합니다.

그동안 많은 팀은 cloud burst를 검토할 때도 EDA tool이 지원하는 x86 instance와 기존 on-premise cluster를 먼저 기준으로 삼았습니다. Cadence 발표가 사실이라면, 같은 Cadence flow 안에서 front-end design and verification, synthesis, place-and-route, timing signoff를 Graviton instance로도 계획할 수 있습니다. 설계 flow에 새 기능이 붙었다기보다, 같은 flow를 실행할 수 있는 compute pool이 넓어진 변화입니다.

AWS는 Graviton 기반 EC2 instance가 일반 cloud workload와 HPC에 쓰인다고 설명합니다. Graviton5는 192 core와 더 큰 cache, 낮아진 inter-core latency를 갖는다고도 밝힙니다. 이 수치는 EDA 성능 검증이 아니라 서버 플랫폼 특성입니다. EDA 엔지니어에게 중요한 질문은 “Graviton이 일반적으로 싸거나 빠른가”가 아닙니다. 내 설계와 tool version, license option, memory footprint에서 같은 signoff 품질을 내는지가 핵심입니다.

## 공개된 flow 범위는 넓지만 version 조건은 따로 확인해야 합니다

Cadence가 명시한 tool 범위는 front-end와 back-end를 모두 포함합니다. 발표문은 Xcelium Logic Simulation, Jasper Formal Verification, Conformal technologies, Genus Synthesis, Innovus+ place-and-route, Tempus Timing Signoff를 나열했습니다. Cadence는 Innovus+와 Genus가 각각 Graviton4·Graviton5 또는 Graviton5에서 시작됐고, 이후 full flow로 확장됐다고 설명했습니다.

이 말은 설계팀의 migration 검토 순서를 바꿉니다. RTL simulation과 formal verification만 Arm 서버에서 돌릴 수 있다면 implementation과 signoff는 여전히 x86 cluster를 따로 잡아야 합니다. 반대로 synthesis, place-and-route, timing signoff까지 같은 cloud architecture에서 돌릴 수 있으면 queue 분리, data movement, tool wrapper, regression farm 운영 방식이 달라집니다.

하지만 공개 원문은 정확한 tool release 번호와 supported OS image, region, instance type, memory limit, license packaging을 표로 공개하지 않았습니다. 따라서 이 기사는 “모든 Cadence version이 모든 Graviton instance에서 signoff-ready”라고 쓰지 않습니다. 공개 근거로 확인되는 것은 두 가지입니다. Cadence가 Graviton native flow qualification과 OnCloud delivery를 발표했다는 점, 그리고 제품 페이지들이 해당 tool의 flow상 역할과 OnCloud의 front-to-back cloud 제공 범위를 설명한다는 점입니다.

## 성능 개선은 아직 독립 결론으로 쓰기 어렵습니다

Cadence 발표에는 Annapurna Labs와 Arm 임원의 인용이 들어 있습니다. 두 회사는 Graviton 기반 workflow가 더 빠른 설계 cycle과 생산성, 성능·효율·확장성 이점을 준다고 말했습니다. 그러나 공개 글은 어떤 design, node, constraint, baseline x86 instance, tool option, thread 수, runtime, PPA, signoff correlation을 비교했는지 밝히지 않았습니다.

그래서 성능 관련 문장은 벤더와 파트너 주장으로만 남겨야 합니다. PPA는 power, performance, area를 뜻하며, 같은 design과 constraint에서 비교해야 의미가 있습니다. Runtime도 signoff 기준과 실패율을 같이 봐야 합니다. 정확성 기준을 낮추거나 signoff를 생략해 얻은 속도는 EDA flow 개선으로 볼 수 없습니다.

이번 발표의 실무적 의미는 더 좁고 분명합니다. Cadence 사용 조직은 다음 cloud capacity refresh나 burst 계획에서 Graviton instance를 평가 후보에 넣을 수 있습니다. 특히 AWS 내부 silicon 팀인 Annapurna Labs가 digital implementation과 signoff portion을 production에서 사용 중이라는 설명은 단순 porting보다 높은 수준의 사용 신호입니다. 다만 이것은 AWS와 Cadence가 관여한 사례이며, 독립 고객의 재현 결과는 아닙니다.

## 지금 할 일과 미룰 일을 나눠야 합니다

지금 할 일은 현재 project의 Cadence release, license feature, foundry certification, supported OS image를 Cadence support channel에서 확인하는 것입니다. 그런 다음 작은 regression design으로 x86 baseline과 Graviton run을 나눠야 합니다. runtime, memory peak, tool warning, timing report, DRC/LVS 관련 downstream 영향이 같은지 비교해야 합니다.

아직 미뤄야 할 일은 공개 발표만 보고 production signoff fleet을 Graviton으로 옮기는 결정입니다. 특히 advanced-node design에서는 signoff correlation, foundry-qualified flow, extraction과 timing corner, distributed processing option, license checkout 지연이 모두 결과를 바꿀 수 있습니다. OnCloud에서 제공되는 ready-to-use 환경과 self-managed cloud 환경도 운영 책임이 다릅니다.

다음에 확인할 신호는 세 가지입니다. Cadence가 tool release와 support matrix를 공개하거나 고객별로 확인 가능한 문서를 제공하는지, Annapurna 외부 고객의 조건 있는 benchmark가 나오는지, 같은 design에서 x86과 Graviton의 timing·power·route 결과가 signoff 허용 오차 안에 드는지입니다. 그 전까지는 “성능 우월성”보다 “지원되는 compute 선택지가 넓어졌다”는 뜻으로 읽는 편이 안전합니다.

## 이해상충과 취재 조건

Cadence, AWS, Arm은 이번 흐름의 직접 이해관계자입니다. Cadence는 tool과 OnCloud를 판매하고, AWS는 Graviton과 EC2를 제공하며, Arm은 Graviton의 기반 CPU architecture ecosystem에 이해관계를 갖습니다. 이 기사는 이들의 성능·생산성 표현을 독립 검증으로 쓰지 않았습니다.

이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 웹 원문만 사용했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Cadence는 full front-to-back EDA flow를 AWS Graviton에서 native 실행하도록 qualified했다고 발표했습니다. | E2 · P1 · R1 | Cadence 공식 blog가 발표 날짜, Graviton native qualification, flow 범위를 제시합니다. 정확한 release note와 support matrix는 공개 글에서 확인하지 못했습니다. |
| C2. 공개 flow 범위에는 Xcelium, Jasper, Conformal, Genus, Innovus+, Tempus가 포함됩니다. | E2 · P1 · R1 | Cadence 발표가 제품 목록을 명시했고, Innovus+와 Genus 제품 페이지가 synthesis, implementation, signoff flow에서 맡는 역할을 설명합니다. |
| C3. Cadence OnCloud는 front-to-back EDA cloud flow와 peak capacity를 제공한다고 설명합니다. | E2 · P1 · R1 | Cadence OnCloud 제품 페이지가 managed cloud service와 full front-to-back design flow 제공을 설명합니다. 실제 계정과 project별 제공 범위는 확인하지 않았습니다. |
| C4. AWS Graviton은 Arm 기반 EC2 processor family이며, AWS는 Graviton5의 192 core, larger cache, lower inter-core latency를 플랫폼 특성으로 설명합니다. | E2 · P1 · R1 | AWS Graviton 원문에서 processor family와 Graviton5 특성을 확인했습니다. 이는 EDA 성능 검증이 아니라 infrastructure 조건입니다. |
| C5. Annapurna Labs와 Arm의 성능·생산성 발언은 이해관계자의 보고이며 독립 benchmark가 아닙니다. | E1 · P0/P1 · R0 | Cadence 발표문 속 인용으로 확인됩니다. design, node, baseline, PPA, runtime 조건이 공개되지 않아 편집국 결론으로 확대하지 않았습니다. |

## 출처

1. Cadence, `Accelerate Chip Design with Arm Architecture: Cadence EDA Tools on AWS Graviton`: https://community.cadence.com/cadence_blogs_8/b/corporate-news/posts/accelerate-chip-design-with-arm-architecture-cadence-eda-tools-on-aws-graviton
2. Cadence, `Cadence Cloud Portfolio | Cadence OnCloud`: https://www.cadence.com/en_US/home/solutions/cadence-oncloud.html
3. AWS, `AWS Graviton Processors`: https://aws.amazon.com/ec2/graviton/
4. Arm, `Arm Neoverse for cloud and AI data centers`: https://www.arm.com/products/cloud-datacenter
5. Cadence, `Innovus+ Synthesis and Implementation System`: https://www.cadence.com/en_US/home/tools/digital-design-and-signoff/soc-implementation-and-floorplanning/innovus-plus-synthesis-implementation-system.html
6. Cadence, `Genus Synthesis Solution`: https://www.cadence.com/en_US/home/tools/digital-design-and-signoff/synthesis/genus-synthesis-solution.html
