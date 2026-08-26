---
edition: eda
decision: publish-candidate
title: "Jalapeño 설계 루프 공개 - AI가 칩 설계의 반복 시간을 줄였다"
date: 2026-08-26
subject: "OpenAI Jalapeño AI-assisted hardware design loop presented at Hot Chips 2026"
summary: "OpenAI는 Jalapeño를 만들 때 실제 workload, architecture simulation, XLS, RTL, QoR 측정을 빠르게 반복하는 AI 설계 루프를 사용했다고 설명했습니다. 핵심은 AI가 칩을 혼자 설계했다는 데 있지 않습니다. AI가 낸 회로 후보를 즉시 합성·검증·측정할 수 있는 통제 가능한 설계 환경을 만들고, 설계자와 함께 결과를 좁혀 간 방식에 있습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["OpenAI는 Jalapeño와 발표 자료의 당사자이고, Google·Synopsys·Cadence·Google DeepMind는 비교에 사용한 각 도구와 연구의 당사자입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

OpenAI가 자체 추론 칩 `Jalapeño`를 어떻게 설계했는지 보여 주는 발표 사진 두 장이 공개됐습니다. 첫 장은 실제 프로그램을 실행하고, 전체 구조를 시뮬레이션하고, 회로를 구현해 품질을 측정하는 과정을 계속 반복했다고 설명합니다. 둘째 장은 이 과정에서 내부 AI 모델과 `XLS`라는 하드웨어 설계 도구를 함께 사용했다고 밝힙니다.

핵심은 AI가 칩을 혼자 설계했다는 데 있지 않습니다. AI가 회로 후보를 제안하면 도구가 그 후보를 실제 회로 표현으로 바꾸고, 합성하고, 검증하고, 전력·성능·면적을 측정했습니다. 설계자는 결과를 보고 다음 후보를 고르거나 방향을 바꿨습니다. OpenAI가 강조한 것은 AI 모델의 이름이나 크기보다 이 한 바퀴를 도는 시간을 줄인 설계 환경입니다.

사진을 올린 X 게시물은 이를 `hardware-in-the-loop RSI`, 즉 하드웨어를 이용한 재귀적 자기개선의 초기 단계가 아니냐고 물었습니다. 그러나 공개 자료가 보여 주는 범위는 그보다 좁습니다. 개선된 대상은 AI 모델 자체가 아니라 칩 설계안이며, 모델이 자기 능력을 평가해 스스로 가중치나 학습 방법을 바꿨다는 근거는 없습니다. 현재로서는 `AI를 이용한 설계 공간 탐색`이라고 부르는 편이 정확합니다.

두 장은 OpenAI의 발표 자료로 보이지만 공식 프로그램상 키노트는 아닙니다. Hot Chips 2026 둘째 날 `AI 2` 세션에서 Richard Ho, Ravi Narayanaswami, Chris Leary가 발표한 `You Can Just Build Things … Chips`의 슬라이드입니다. 같은 날 공식 키노트는 Waymo의 자율주행 컴퓨팅 발표였습니다.

## 두 장의 슬라이드는 칩 성능보다 개발 방식을 설명합니다

Jalapeño의 첫 측정 결과는 이미 별도 기사에서 다뤘습니다. OpenAI는 GPT-OSS 120B, DeepSeek R1 670B, Kimi K2.5 1T를 이용한 자체 측정에서 비교 시스템보다 전력당 더 많은 작업을 처리하고 지연시간을 낮췄다고 발표했습니다. 이번 두 장의 사진이 새롭게 보여 주는 것은 그 결과에 도달한 개발 방식입니다.

첫 슬라이드의 제목은 `완성된 명세가 아니라 지속적인 수렴`입니다. 흐름은 다섯 단계로 그려져 있습니다. 제품이 풀 문제를 정하고, 실제 작업을 대표하는 프로그램을 고른 뒤, 전체 칩 구조를 시뮬레이션합니다. 이어서 RTL을 만들고 QoR을 확인하며, 설계 검증·물리 설계·성능을 함께 맞춰 갑니다.

RTL은 클록이 한 번 움직일 때 레지스터와 데이터 경로가 어떻게 동작하는지 기술한 회로 표현입니다. QoR은 `Quality of Results`의 약자로, 합성과 구현을 거친 회로가 목표 주파수를 맞추는지, 면적과 전력은 어느 정도인지 같은 결과의 품질을 뜻합니다. 슬라이드의 큰 화살표는 이 과정을 `측정 → 검증 → 학습 → 변경 → 반복`으로 요약합니다.

반복 자체는 반도체 설계의 새로운 발명이 아닙니다. 기존 칩 개발도 설계, 합성, 검증, 물리 구현을 여러 번 오갑니다. OpenAI 발표에서 눈여겨볼 부분은 반복의 시작점과 범위입니다. 완성된 세부 명세를 먼저 고정한 뒤 구현을 시작하기보다, 실제 워크로드와 실행 가능한 시뮬레이션을 일찍 마련하고 애플리케이션 성능부터 회로 품질까지 한 루프에 넣었습니다.

## 실제 프로그램이 움직이는 명세가 됐습니다

첫 단계의 `vision`은 이 칩이 어떤 문제를 풀어야 하는지 정합니다. Jalapeño라면 에이전트형 추론에서 짧은 응답 지연과 높은 전력 효율을 함께 얻는 것이 큰 목표입니다. 그러나 이 목표만으로는 행렬 연산기의 크기, 메모리 구조, 데이터 이동 방식, 명령 체계를 바로 결정할 수 없습니다.

다음 단계에서 대표 프로그램을 실행하는 이유가 여기에 있습니다. 추론 모델의 attention, mixture-of-experts, 저정밀 행렬 곱처럼 실제로 자주 일어나는 계산을 프로그램으로 만들면, 설계안이 추상적인 요구사항이 아니라 실행 결과로 평가됩니다. 구조를 바꿨을 때 프로그램이 몇 cycle에 끝나는지, 어느 데이터 이동이 병목인지, 필요한 메모리 용량이 얼마나 달라지는지 일찍 볼 수 있습니다.

그다음에는 전체 architecture simulation으로 성능을 확인합니다. 이는 트랜지스터가 완성된 칩을 재는 단계가 아니라, 아직 만들고 있는 칩의 구조가 프로그램을 어떻게 실행할지 계산하는 단계입니다. 회로가 정확하게 동작하는지만 보는 기능 검증과도 다릅니다. 정확성과 예상 성능을 함께 보면서 설계 선택을 좁혀 가는 과정입니다.

슬라이드가 말하는 `명세는 반복을 통해 정밀해진다`는 표현도 이 맥락에서 읽어야 합니다. 요구사항이나 signoff 기준을 생략한다는 뜻이 아닙니다. 대표 워크로드와 측정 가능한 목표를 명세의 일부로 만들고, 구현 결과가 목표와 맞지 않을 때 세부 구조를 수정한다는 뜻입니다. 검증은 마지막 관문이 아니라 반복 과정 안에 계속 남아 있습니다.

## XLS는 AI가 다룰 수 있는 설계 표면을 만들었습니다

둘째 슬라이드의 가운데에는 `XLS hardware language`가 놓여 있습니다. XLS는 Google이 공개한 하드웨어 합성 도구 모음입니다. Rust와 비슷한 문법의 DSLX 같은 고수준 표현을 XLS의 중간 표현으로 바꾸고, 이를 다시 Verilog나 SystemVerilog 회로로 생성할 수 있습니다. 해석기, 시뮬레이션, 스케줄링, 코드 생성, 검증, 합성과 PPA 수집을 연결하는 도구도 제공합니다.

이 중간층은 AI에게 중요합니다. AI가 긴 RTL 파일을 자유롭게 고치게 하면 문법상 맞더라도 합성되지 않거나, timing을 맞추지 못하거나, 미묘한 기능 오류를 만들 수 있습니다. 반대로 설계자가 정한 연산 의미와 허용 가능한 변형을 더 좁은 언어로 표현하면 AI가 탐색할 공간을 제한할 수 있습니다. 슬라이드는 이를 `통제 가능한 최적화 표면`이라고 부르며, 명확한 의미, 충분한 최적화 제어, 빠른 QoR 피드백, 견고한 검증을 조건으로 제시합니다.

예를 들어 BF16 곱셈기를 개선한다고 하겠습니다. AI는 같은 계산 결과를 내는 여러 연산 분해와 pipeline 구성을 제안할 수 있습니다. XLS 도구는 후보를 회로로 바꾸고 합성한 뒤, 목표 주파수에 맞는지와 면적이 얼마나 드는지 측정할 수 있습니다. 기능 검증을 통과하지 못한 후보는 버리고, 통과한 후보끼리 PPA를 비교합니다. PPA는 전력, 성능, 면적을 함께 보는 기준입니다.

여기서 AI의 장점은 첫 답을 잘 쓰는 능력보다 많은 후보를 만드는 속도입니다. EDA 도구의 장점은 그 후보를 칭찬하거나 비판하는 대신 합성 결과와 검증 결과로 걸러 낸다는 점입니다. 두 요소가 연결돼야 AI의 제안이 회로 개선으로 이어집니다. OpenAI의 표현대로라면 AI와 설계자는 `제안 → 측정 → 최적화`를 반복하고, 아래의 도구 체인은 `생성 → 검증 → PPA 측정`을 수행합니다.

다만 공개 XLS와 OpenAI의 내부 환경을 같은 것으로 보면 안 됩니다. 슬라이드는 내부 AI 모델과 빠른 내부 도구를 함께 표시하지만, 모델 종류, prompt, 후보 생성 방식, XLS에 가한 변경, 합성기와 물리 설계 도구의 버전을 공개하지 않았습니다. 공개된 XLS 문서는 이 접근이 가능한 기술적 바탕을 설명할 뿐, OpenAI의 결과를 그대로 재현하게 해 주지는 않습니다.

## 설계자는 목표와 경계를 정하고 결과를 선택합니다

슬라이드 왼쪽에는 `AI + DESIGNER`가 함께 적혀 있습니다. 이 표기는 장식이 아닙니다. AI가 후보를 많이 만들 수 있어도 어떤 연산을 바꿀지, 어느 정확도와 주파수를 지켜야 할지, 전력과 면적 가운데 무엇을 우선할지는 설계 목표에 따라 달라집니다. 잘못 잡은 목표를 빠르게 최적화하면 틀린 방향으로 더 빨리 갈 뿐입니다.

검증도 하나의 통과 버튼으로 끝나지 않습니다. DV는 설계 검증을 뜻하며 회로가 요구한 기능을 모든 중요한 조건에서 수행하는지 확인합니다. PD는 배치·배선, timing closure, 전력망처럼 실제 칩으로 만들기 위한 물리 설계를 뜻합니다. 논리 합성에서 좋아 보인 회로도 배치와 배선을 거치면 배선 지연이나 혼잡 때문에 이점을 잃을 수 있습니다. 첫 슬라이드가 DV, PD, performance를 함께 추적한다고 적은 이유입니다.

이 구조에서는 AI가 내놓은 후보가 설계자의 직관을 보완할 수 있습니다. 사람이 익숙한 구조를 조금씩 다듬는 동안 AI는 다른 연산 분해나 pipeline 깊이를 폭넓게 제안할 수 있습니다. 반대로 signoff 기준, 검증 범위, 변경 승인과 최종 책임은 여전히 사람과 결정적인 도구에 남습니다. 공개 자료에는 AI가 독립적으로 RTL freeze나 tapeout을 승인했다는 내용이 없습니다.

## 공개된 PPA 수치는 출발점이지 비교 결론은 아닙니다

둘째 슬라이드는 AI가 개선한 building block으로 BF16 곱셈기 56%, FP4 dot 연산 21%, FP32 누산기 10%를 제시합니다. 이어서 block 수준에서는 Matrix Unit 면적 10%, SIMD Unit 면적 8%를 줄였다고 적습니다. 큰 변경을 RTL freeze 당일까지 반영할 수 있었다는 설명도 있습니다.

여기서 숫자를 읽을 때는 범위를 나눠야 합니다. 10%와 8%는 슬라이드가 면적 개선이라고 명시합니다. 반면 56%, 21%, 10%의 building block 수치는 `measured PPA wins` 아래에 있지만, 전력·성능·면적을 어떤 식으로 합친 값인지 사진만으로 확인되지 않습니다. 따라서 BF16 곱셈기 면적이 56% 줄었다고 바꿔 쓰면 원문보다 강한 주장이 됩니다.

비교 조건도 공개되지 않았습니다. 공정 node, cell library, 전압과 온도, 목표 clock, 합성·배치·배선 단계, baseline을 최적화한 방법, 실패한 후보 수를 알 수 없습니다. `optimized human baseline`이라는 표현은 있지만 인간 설계에 쓴 시간과 도구, AI 쪽 계산 비용도 제시되지 않았습니다. 공개 사진은 OpenAI가 이런 개선을 보고했다는 사실을 확인하게 해 주지만, 다른 팀이 같은 수치를 재현하거나 다른 EDA 방법과 직접 비교하기에는 부족합니다.

그럼에도 이 수치가 의미 없는 것은 아닙니다. 블록 하나의 개선이 Matrix Unit과 SIMD Unit의 면적 감소로 이어졌다고 공개한 점은 후보 생성과 측정 루프가 실제 Jalapeño RTL에 연결됐음을 보여 줍니다. 다만 기술적 의미는 56%라는 가장 큰 숫자보다, 기능 검증과 QoR 측정을 충분히 빠르게 만들어 늦은 시점까지 설계를 바꿀 수 있었다는 개발 방식에 있습니다.

## 기존 AI EDA와 다른 점은 AI의 존재보다 루프의 범위입니다

AI를 칩 설계에 쓴 사례는 이미 있습니다. Google DeepMind의 AlphaChip은 강화학습으로 칩의 큰 블록을 어디에 배치할지 탐색했고 TPU 설계에 사용됐습니다. Synopsys DSO.ai와 Cadence Cerebrus는 합성·배치·배선 과정의 많은 설정과 실행 결과를 탐색해 PPA 목표를 맞추는 방향을 앞세웠습니다.

OpenAI 슬라이드가 보여 주는 차이는 `AI를 처음 썼다`는 데 있지 않습니다. 공개 설명상 루프의 위쪽에는 실제 추론 워크로드와 전체 architecture simulation이 있고, 아래쪽에는 XLS, RTL, QoR, DV, PD가 있습니다. 애플리케이션이 원하는 성능과 회로 구현 결과를 더 짧은 경로로 연결하려는 구성이 특징입니다.

하지만 어느 접근이 더 낫다고 비교할 자료는 없습니다. AlphaChip은 floorplanning이라는 특정 문제를 깊게 다루고, 상용 EDA 제품은 실제 구현 flow의 넓은 제약을 처리합니다. OpenAI는 자체 칩과 자체 워크로드를 함께 통제할 수 있다는 조건에서 루프를 만들었습니다. 여러 고객의 서로 다른 PDK, IP, tool flow를 지원해야 하는 EDA 벤더와는 문제의 경계가 다릅니다.

## 이것은 아직 재귀적 자기개선이 아닙니다

재귀적 자기개선은 AI가 자기 능력을 높일 변경을 만들고, 그 변경의 효과를 평가한 뒤, 개선된 시스템이 다시 다음 개선을 수행하는 과정을 뜻합니다. 이번 공개에서 반복되는 것은 칩 설계 후보입니다. AI 모델이 회로를 제안하고 EDA 결과를 받지만, 그 결과로 모델의 가중치나 학습 알고리즘이 자동으로 바뀌었다는 내용은 없습니다.

Jalapeño가 훗날 더 빠른 AI를 돌리고, 그 AI가 다음 세대 Jalapeño를 더 잘 설계하는 장기적인 순환은 상상할 수 있습니다. OpenAI도 2세대 칩을 개발 중이고 3세대 구상을 시작했다고 밝혔습니다. 그러나 세대 간 선순환과 한 시스템 안의 재귀적 자기개선은 같은 말이 아닙니다. 다음 세대의 설계 속도, AI 개입 범위, 모델 개선 방식이 공개되기 전에는 RSI라고 단정할 수 없습니다.

현재 확인되는 변화만으로도 충분히 중요합니다. AI가 설계자 대신 최종 결정을 내리지 않아도, 후보를 만드는 비용을 낮추고 측정 결과를 빨리 돌려주면 사람이 시험할 수 있는 설계의 수가 늘어납니다. 칩 개발에서 한 번의 합성과 검증이 오래 걸린다면 AI가 빠르게 코드를 써도 이점이 작습니다. 반대로 피드백이 빠르고 실패가 자동으로 걸러지면 작은 팀도 더 많은 선택지를 검토할 수 있습니다.

## EDA 팀에 남는 교훈은 모델보다 피드백 시간입니다

이번 발표가 보여 주는 설계 원칙은 특정 AI 모델을 도입하라는 조언과 다릅니다. 먼저 실제 workload를 실행 가능한 형태로 만들고, 설계 목표를 측정값으로 정의해야 합니다. 다음으로 AI가 바꿀 수 있는 회로 표현과 금지된 영역을 나눠야 합니다. 마지막으로 기능 검증, 합성, PPA 측정이 같은 자동화 경로에서 빠르게 돌아야 합니다.

이 조건이 없으면 AI는 검토할 RTL을 더 많이 만들 뿐입니다. 후보 수가 늘어날수록 검증 부채도 함께 늘어납니다. 반대로 각 후보가 같은 constraint와 같은 도구 버전에서 평가되고, 결과와 변경 이력이 남는다면 설계자는 무엇이 왜 좋아졌는지 비교할 수 있습니다. AI 도입의 성패를 code generation 수보다 `검증을 통과한 유효 후보 한 개를 얻는 데 걸린 시간`으로 재는 편이 낫습니다.

OpenAI의 두 슬라이드가 흥미로운 이유도 여기에 있습니다. AI가 사람처럼 칩을 이해한다는 선언이 아니라, AI의 제안을 회로와 측정값으로 바꾸는 좁고 반복 가능한 통로를 만들었다는 보고이기 때문입니다. 공개되지 않은 내부 모델보다 더 오래 남을 가능성이 큰 기술은 이 피드백 구조입니다.

## 이해상충과 취재 조건

OpenAI는 Jalapeño와 Hot Chips 발표의 당사자입니다. OpenAI 발표문은 설계 기간, AI 활용, Jalapeño 구조와 자체 측정 결과를 확인하는 1차 자료이지만, 공개하지 않은 내부 AI 모델과 PPA 결과를 독립적으로 증명하지는 않습니다. X 게시물은 발표 현장의 슬라이드 사진을 찾는 출발점으로 사용했고, 게시자가 붙인 RSI 해석은 OpenAI의 주장과 분리했습니다.

Google XLS 문서와 저장소는 XLS의 언어·중간 표현·코드 생성·검증·PPA 도구 범위를 확인하는 자료입니다. AlphaChip, DSO.ai, Cerebrus 자료는 각 연구·제품의 당사자가 작성한 원문이므로 접근 범위를 비교하는 데만 사용했습니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. OpenAI는 Hot Chips 2026의 AI 2 세션에서 Jalapeño의 개발 과정을 발표했습니다. | E2 · P1/S2 · R1 | Hot Chips 공식 프로그램의 세션·발표자 정보와 현장 슬라이드 사진을 대조했습니다. 공식 slide deck 전체는 공개 여부를 확인하지 못했습니다. |
| C2. OpenAI는 실제 workload, architecture simulation, RTL·QoR, DV·PD·performance를 연결해 `측정 → 검증 → 학습 → 변경 → 반복`하는 개발 흐름을 제시했습니다. | E2 · S2/P1 · R1 | 현장 슬라이드 사진의 흐름과 OpenAI가 초기 설계부터 tapeout까지 9개월 동안 구현·측정·검증 루프를 줄였다고 밝힌 공식 글이 서로 맞습니다. 내부 workflow와 실행 log는 공개되지 않았습니다. |
| C3. OpenAI는 내부 AI 모델, 빠른 도구, XLS를 이용해 회로 후보를 생성·검증하고 PPA를 측정했다고 설명했습니다. | E2 · S2/P2 · R1 | 슬라이드 사진과 XLS 공식 문서·공개 저장소로 도구의 공개 기능을 확인했습니다. OpenAI가 사용한 모델, prompt, XLS 변경 사항, 상용 EDA 도구와 version은 공개되지 않았습니다. |
| C4. OpenAI는 BF16 mul 56%, FP4 dot 21%, FP32 acc 10%의 building-block PPA 개선과 Matrix Unit 면적 10%, SIMD Unit 면적 8% 개선을 보고했습니다. | E1 · S2 · R0 | 수치는 현장 슬라이드 사진에 표시돼 있습니다. 앞의 세 수치가 PPA를 어떻게 계산한 것인지와 node·library·corner·baseline·signoff 단계가 공개되지 않아 vendor report 이상으로 일반화하지 않았습니다. |
| C5. AlphaChip, DSO.ai, Cerebrus도 AI로 physical design이나 implementation flow를 탐색합니다. | E2 · P1 · R1 | Google DeepMind, Synopsys, Cadence의 공식 설명으로 각 접근 범위를 확인했습니다. 서로 다른 design과 flow의 PPA 수치를 직접 비교하지 않았습니다. |
| C6. 이번 공개는 AI가 칩 설계안을 개선하는 인간 참여형 loop를 보여 주지만, AI가 자기 모델이나 학습법을 자동으로 개선하는 RSI를 입증하지는 않습니다. | E2 · derived · R1 | C1-C4와 OpenAI 공식 글에서 파생한 판단입니다. 공개 자료에는 모델 weight update, 자기 평가를 통한 model selection, 무인 tapeout 승인 과정이 없습니다. |

## 출처

1. X, Beff Jezos가 공개한 Hot Chips 발표 사진: https://x.com/beffjezos/status/2092418951586390137
2. Hot Chips 2026 공식 프로그램: https://hc2026.hotchips.org/
3. OpenAI, `Jalapeño’s first results show industry-leading speed and efficiency in AI inference`: https://openai.com/index/jalapeno-first-results/
4. OpenAI, `OpenAI and Broadcom introduce Jalapeño, a custom chip for AI inference`: https://openai.com/index/openai-broadcom-jalapeno-inference-chip/
5. Google, XLS 공식 문서: https://google.github.io/xls/
6. Google, XLS 공개 저장소: https://github.com/google/xls
7. Google DeepMind, `How AlphaChip transformed computer chip design`: https://deepmind.google/blog/how-alphachip-transformed-computer-chip-design/
8. Synopsys, DSO.ai 공식 발표: https://news.synopsys.com/2020-03-11-Synopsys-Advances-State-of-the-Art-in-Electronic-Design-with-Revolutionary-Artificial-Intelligence-Technology?asPDF=1
9. Cadence, `Cerebrus Intelligent Chip Explorer` white paper: https://www.cadence.com/content/dam/cadence-www/global/en_US/documents/tools/digital-design-signoff/cerebrus-wp.pdf
