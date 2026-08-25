---
edition: ai
decision: publish-candidate
title: "Jalapeño 첫 측정 공개 - 에이전트 추론에 맞춘 OpenAI 자체 칩"
date: 2026-08-26
subject: "OpenAI Jalapeño first measured inference results and InferenceX benchmark framing, August 25 2026"
summary: "OpenAI가 자체 inference chip인 Jalapeño의 첫 측정 결과를 공개했습니다. 이 칩은 한 요청의 prefill, decode, KV cache, chip 간 통신을 따로 보지 않고, agentic workload에 필요한 낮은 token latency와 높은 전력당 처리량을 함께 맞추려는 설계입니다. 다만 공개 수치는 OpenAI가 실행한 측정이며 chip, 원 로그, 재실행 가능한 제출물은 공개되지 않았습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["OpenAI는 Jalapeño의 개발·배포 주체이며 이 기사에 쓴 발표문과 측정 결과를 작성했습니다. SemiAnalysis는 InferenceX benchmark와 공개 repository를 운영합니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

OpenAI가 2026년 8월 25일 자체 inference chip인 Jalapeño의 첫 측정 결과를 공개했습니다. 이 소식의 핵심은 새 모델이 아닙니다. 에이전트가 여러 단계를 빠르게 오가는 작업에서 latency와 전력 사용량을 함께 줄이려는 chip·system 설계입니다. OpenAI는 Jalapeño가 GPT-OSS 120B, DeepSeek R1 670B, Kimi K2.5 1T 같은 공개 모델에서 비교 시스템보다 전력당 더 많은 token을 처리하고 end-to-end latency를 낮췄다고 밝혔습니다.

이 주장을 곧바로 독립 성능 순위로 읽으면 안 됩니다. Jalapeño hardware, software stack, 원 로그, InferenceX 제출물은 기사 작성 시점에 공개되지 않았습니다. 따라서 이 기사의 중심은 “Jalapeño가 NVIDIA나 다른 accelerator보다 낫다”가 아닙니다. 확인할 수 있는 변화는 OpenAI가 에이전트형 inference workload를 기준으로 chip, memory, network, serving software를 함께 설계했고, 그 첫 vendor 측정 조건을 공개했다는 점입니다.

SW 엔지니어에게 이 변화가 중요한 이유는 agent 서비스의 병목이 초당 token 수 하나로 정해지지 않기 때문입니다. coding agent, research agent, 고객 지원 agent는 한 번 길게 답하는 대신 짧은 모델 호출, tool call, 관찰, 다음 행동을 반복합니다. 한 단계의 token latency가 작게 보여도 전체 작업에서는 계속 누적됩니다. Jalapeño 공개는 inference 비용을 볼 때 peak throughput만 보지 말고, 한 사용자에게 token이 돌아오는 속도와 전력당 처리량, 긴 agent loop의 지연을 함께 봐야 한다는 신호입니다.

## 에이전트 작업은 입력 처리와 답 생성이 모두 무겁습니다

언어 모델 inference는 크게 두 단계로 나뉩니다. prefill은 prompt를 한꺼번에 읽어 내부 상태를 만드는 단계입니다. 긴 문서, repository context, tool 결과가 들어오면 이 단계가 무거워집니다. decode는 답을 token 단위로 하나씩 만드는 단계입니다. 이때는 이전 token들의 상태인 KV cache를 계속 읽고 써야 하므로 memory bandwidth와 데이터 이동이 병목이 되기 쉽습니다.

일반적인 batch serving에서는 많은 요청을 모아 throughput을 높일 수 있습니다. 하지만 에이전트 작업은 항상 그렇게 움직이지 않습니다. agent가 command를 실행하고 결과를 본 뒤 다음 요청을 보내면, 모델 호출 사이에 외부 작업의 대기 시간이 끼어듭니다. 사용자는 각 단계의 응답을 기다리고, tool 결과는 다음 prompt의 일부가 됩니다. 그래서 높은 batch throughput만으로는 “실제 agent가 얼마나 빨리 일을 끝내는가”를 설명하기 어렵습니다.

OpenAI는 Jalapeño를 이 문제에 맞췄다고 설명합니다. chip 하나의 산술 성능만 키우지 않고 chip, memory, network, software, rack-scale system을 함께 설계했다는 것입니다. 특히 model state와 KV cache를 필요한 곳에 두고, prefill과 decode 단계마다 알맞은 compute, memory, networking 조합을 쓰게 하는 방향을 강조했습니다. 이 설명은 Jalapeño를 단일 chip 제품보다 inference system으로 봐야 한다는 뜻에 가깝습니다.

## 수치는 좋지만 공개 검증 범위는 좁습니다

OpenAI는 Jalapeño를 SemiAnalysis의 InferenceX로 시험했다고 밝혔습니다. InferenceX는 agentic inference와 고정 길이 inference에서 latency, throughput, time-to-first-token, cost 같은 지표를 비교하는 공개 benchmark입니다. 공개 repository도 있어 benchmark 구성, runner, model configuration, dashboard 흐름을 확인할 수 있습니다.

OpenAI가 공개한 수치는 세 공개 모델을 기준으로 합니다. GPT-OSS 120B에서는 Jalapeño 700W와 GB200 1,200W를 비교했고, DeepSeek R1 670B와 Kimi K2.5 1T에서는 Jalapeño 700W와 GB300 1,400W를 비교했습니다. OpenAI는 세 모델 전체에서 Jalapeño가 peak throughput 기준 1.5~1.9배 더 많은 AI work per watt를 냈고, end-to-end latency는 1.7~3.6배 낮았다고 밝혔습니다.

본문에서 이 수치를 독립 측정처럼 쓰지 않는 이유는 분명합니다. InferenceX라는 benchmark 경로는 공개되어 있지만, Jalapeño는 아직 외부 팀이 살 수 있거나 빌려 쓸 수 있는 chip이 아닙니다. OpenAI의 특정 Jalapeño system, software stack, measurement log, 실패 사례, 제출 검증 기록도 공개 자료만으로는 확인할 수 없었습니다. 따라서 수치는 OpenAI가 밝힌 첫 측정 결과로 다루며, 성능 우월성에 대한 편집국 결론으로 올리지 않습니다.

## 전력당 처리량은 agent 운영 비용과 연결됩니다

Jalapeño 글에서 눈여겨볼 지표는 token per second 하나가 아닙니다. OpenAI는 “matched user experience”를 기준으로 전력당 얼마나 많은 유용한 작업을 처리하는지를 봤다고 설명합니다. 같은 token latency를 유지하면서 더 많은 요청을 처리할 수 있다면, agent 서비스는 응답성을 유지하면서 더 많은 사용자를 받을 수 있습니다.

이 기준은 한국의 AI 서비스 운영팀에도 익숙한 문제입니다. 사용자가 보는 지연시간을 낮추려면 batch를 크게 키우기 어렵습니다. batch를 키우면 throughput은 좋아져도 interactive agent의 체감 속도가 나빠질 수 있습니다. 특히 code review, 사내 문서 검색, 고객 상담처럼 여러 tool call을 거치는 agent는 한 요청의 지연이 다음 행동을 늦춥니다. 그래서 accelerator 선택 기준은 “가장 높은 peak TPS”보다 “우리가 허용하는 tail latency에서 전력과 비용 안에 동시 작업을 얼마나 넣을 수 있는가”에 가까워집니다.

OpenAI가 제시한 appendix도 이 관점을 따릅니다. 예를 들어 GPT-OSS 120B에서는 이전 비교 시스템의 min TBT에 맞췄을 때 Jalapeño가 전력당 mixed throughput을 크게 높였다고 보고했습니다. DeepSeek R1과 Kimi K2.5에서도 end-to-end latency와 time between tokens를 함께 제시했습니다. 다만 이 숫자는 OpenAI의 측정입니다. 실제 구매나 cloud 선택에는 같은 workload, 같은 quality target, 같은 concurrency, 같은 전력 산정 방식으로 다시 확인해야 합니다.

## 자체 칩은 새 모델을 빨리 올리는 데도 쓰입니다

Jalapeño 공개에서 또 하나 중요한 대목은 OpenAI가 chip을 “AI가 프로그래밍하기 쉬운 대상”으로 만들었다고 설명한 부분입니다. OpenAI는 engineer가 local tensor, 명시적 communication, predictable synchronization으로 작업을 설명할 수 있게 했고, AI가 그 작업을 system 위에 배치하고 schedule하는 최적화를 도울 수 있다고 적었습니다.

이 말은 chip 설계의 검증된 성능 수치라기보다 software stack의 방향을 보여 줍니다. 새 모델 family가 나오면 attention, mixture-of-experts, quantization, KV cache layout, routing 방식이 달라지고 kernel도 바뀝니다. hardware가 특정 모델 하나에만 잘 맞으면 다음 모델에서 이점을 잃을 수 있습니다. OpenAI는 GPT-Astra를 쓰는 Codex로 원래 생산 계획에 없던 세 open-weight model을 두 달 안에 높은 성능으로 올렸다고 밝혔습니다.

기사에서 확인할 수 있는 의미는 “AI가 chip programming을 완전히 자동화했다”가 아닙니다. OpenAI가 일부 GPT-OSS attention과 mixture-of-experts block에서 AI가 만든 구현이 인간 expert가 쓴 기존 구현보다 1.5~1.8배 빨랐다고 했지만, 이 수치는 선택된 block에 한정됩니다. 전체 모델, 전체 workload, 장기 유지보수 비용까지 입증하는 자료는 아닙니다. 더 넓은 결론을 내려면 공개 kernel, compiler path, benchmark script, 실패한 후보와 사람이 개입한 지점을 봐야 합니다.

## 아직은 개발자가 고를 수 있는 accelerator가 아닙니다

Jalapeño는 당장 개발자가 클라우드에서 선택할 수 있는 instance type이 아닙니다. OpenAI는 올해 말까지 자체 compute infrastructure 안에 배포를 시작할 계획이라고 밝혔고, production qualification, software 성숙화, scale 운영 준비, 더 많은 모델 검증이 남았다고 적었습니다. 또 training과 inference 전반에서 NVIDIA와 다른 partner accelerator를 계속 넓게 쓰겠다고 했습니다.

따라서 제품팀의 당장 할 일은 Jalapeño를 구매 후보에 넣는 것이 아닙니다. 오히려 inference 평가표를 고치는 쪽에 가깝습니다. agent 서비스를 운영한다면 prompt 길이, output 길이, tool call 횟수, concurrency, time-to-first-token, time between tokens, tail latency, 전력 또는 cloud cost를 함께 기록해야 합니다. hardware vendor가 어떤 수치를 내놓든, 자기 workload의 병목이 prefill인지 decode인지, KV cache memory인지, network communication인지 확인해야 비교가 가능합니다.

이 관점은 특정 chip 하나를 넘어섭니다. OpenAI가 자체 chip을 만들었다는 사실보다 더 넓은 변화는 frontier lab이 모델, serving software, accelerator, data center를 하나의 제품 원가 구조로 다루기 시작했다는 점입니다. 모델 API 가격이 내려가거나 agent latency가 줄어드는 배경에는 모델 개선뿐 아니라 serving stack의 구조가 있습니다. 사용자는 API만 보지만, 실제 성능과 비용은 그 아래 system에서 정해집니다.

## 공개 자료로 확인한 범위는 첫 측정과 설계 설명까지입니다

이 기사에서 확인한 중심 주장은 공개된 OpenAI 발표문, OpenAI의 full-stack 전략 글, SemiAnalysis InferenceX dashboard와 GitHub repository로 한정합니다. OpenAI는 Jalapeño가 공개 모델 세 종류에서 전력당 처리량과 latency를 개선했다고 밝혔고, chip·memory·network·software를 함께 설계한 이유를 설명했습니다. SemiAnalysis 쪽 자료는 InferenceX가 공개 benchmark와 repository를 갖고 있으며 agentic inference 지표를 다룬다는 사실을 확인하는 데 썼습니다.

재현성 상태는 R1입니다. benchmark 방법과 공개 harness 경로는 설명할 수 있지만, Jalapeño hardware와 OpenAI의 제출·측정 log가 없어 편집국이나 독자가 같은 조건으로 다시 돌릴 수 없습니다. 그래서 이 글은 OpenAI가 공개한 첫 측정 결과를 기술적 사건으로 다루되, Jalapeño가 모든 inference workload에서 더 낫다거나 비교 시스템보다 일반적으로 우월하다고 결론 내리지 않습니다.

## 이해상충과 취재 조건

OpenAI는 Jalapeño와 관련 측정 결과의 당사자입니다. OpenAI 발표문은 chip 설계, 공개한 수치, 배포 계획을 확인하는 1차 자료이지만, OpenAI의 성능 우월성을 독립적으로 증명하지는 않습니다. SemiAnalysis는 InferenceX benchmark와 공개 repository의 운영 주체이며, benchmark 방법과 공개 surface를 확인하는 근거로 썼습니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 2차 기사는 후보 발견과 비교 후보 확인에만 사용했고, 기사 사실은 열린 공식 원문과 공개 repository로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. OpenAI는 2026년 8월 25일 Jalapeño의 첫 measured inference result를 공개했고, 이를 OpenAI의 첫 custom inference chip이라고 설명했습니다. | E1 · P1 | OpenAI 발표문과 full-stack 전략 글로 확인했습니다. 발표 사실과 OpenAI의 설명 범위입니다. |
| C2. OpenAI는 Jalapeño를 chip, memory, network, software, rack-scale system을 함께 설계한 inference system으로 설명하며, prefill과 decode의 병목과 KV cache data movement를 줄이는 방향을 제시했습니다. | E2 · P1 | OpenAI 발표문으로 확인했습니다. chip 세부 spec, compiler, memory hierarchy 전체는 공개되지 않았습니다. |
| C3. OpenAI는 Jalapeño를 InferenceX에서 GPT-OSS 120B, DeepSeek R1 670B, Kimi K2.5 1T로 시험했고, 세 모델에서 1.5~1.9배 높은 peak AI work per watt와 1.7~3.6배 낮은 end-to-end latency를 보고했습니다. | E2 · P1 | OpenAI 발표문과 appendix 수치로 확인했습니다. Jalapeño hardware, 원 로그, 제출 검증 기록은 공개되지 않아 독립 성능 결론으로 쓰지 않았습니다. |
| C4. InferenceX는 agentic inference와 fixed-sequence inference의 latency, throughput, TTFT 같은 지표를 다루는 공개 benchmark이며 GitHub repository를 공개합니다. | E2 · P1/P2 | SemiAnalysis InferenceX dashboard와 GitHub repository로 확인했습니다. 공개 repository가 Jalapeño 측정값 자체를 재현하게 해 주지는 않습니다. |
| C5. OpenAI는 Jalapeño를 올해 말 자체 compute infrastructure 안에 배포하기 시작할 계획이라고 밝혔고, production qualification과 software 성숙화가 남았다고 설명했습니다. | E1 · P1 | OpenAI 발표문으로 확인했습니다. 외부 cloud SKU, 가격, 일반 제공 일정은 확인되지 않았습니다. |
| C6. OpenAI는 일부 GPT-OSS attention과 mixture-of-experts block에서 AI-generated implementation이 기존 human-expert implementation보다 1.5~1.8배 빨랐다고 밝혔습니다. | E2 · P1 | OpenAI 발표문으로 확인했습니다. 선택된 block에 한정된 vendor 수치이며 전체 모델 성능이나 자동화 일반론으로 확대하지 않았습니다. |

## 출처

1. OpenAI, "Jalapeño’s first results show industry-leading speed and efficiency in AI inference": https://openai.com/index/jalapeno-first-results/
2. OpenAI, "The full stack behind abundant intelligence": https://openai.com/index/the-full-stack-behind-abundant-intelligence/
3. SemiAnalysis InferenceX, "Agentic Inference Benchmarks": https://inferencex.semianalysis.com/inference
4. GitHub, `SemiAnalysisAI/InferenceX`: https://github.com/SemiAnalysisAI/InferenceX
