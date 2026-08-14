---
edition: ai
decision: publish-candidate
title: "DeepSeek, V4 Pro 정식 출시…100만 토큰으로 에이전트의 긴 작업을 잇는다"
date: 2026-08-14
publication_kind: special
subject: "DeepSeek-V4-Pro-0813의 긴 문맥 구조와 에이전트 기술"
summary: "DeepSeek V4 Pro의 핵심은 문맥 창을 100만 토큰으로 늘린 숫자 자체가 아닙니다. CSA와 HCA로 오래된 문맥을 압축하고, 도구 사용 중에는 reasoning state를 이어 가며, 작업 난도에 따라 추론량을 조절하도록 설계했습니다. 이 구조가 긴 작업을 수행하는 에이전트에 어떤 의미가 있는지 기술 보고서를 바탕으로 분석합니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["DeepSeek 공식 문서와 기술 보고서, Hugging Face 저장소는 DeepSeek 또는 프로젝트 운영자의 1차 자료입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

DeepSeek가 2026년 8월 13일 `DeepSeek-V4-Pro` 정식판을 공개했으며, SW 개발자에게 중요한 변화는 100만 토큰이라는 숫자보다 그 긴 문맥을 실제 에이전트 작업에 쓸 수 있도록 만든 구조입니다. V4 Pro는 오래된 정보를 압축해 기억하고, 필요한 부분만 골라 읽으며, 여러 차례의 도구 호출 사이에서 추론의 흐름을 이어 가도록 설계됐습니다.

긴 문맥은 코드 저장소 전체를 읽거나 수백 개 문서를 비교하는 데 유용하지만, 기존 attention으로는 문맥이 길어질수록 계산량과 메모리가 빠르게 커집니다. V4는 이 병목을 줄이기 위해 Compressed Sparse Attention과 Heavily Compressed Attention을 섞었습니다. 보고서에 따르면 100만 토큰에서 V4 Pro의 토큰 하나 생성에 필요한 연산량은 V3.2의 27%, KV cache는 10%입니다.

여기에 `low`, `high`, `max` reasoning effort와 도구 사용 중 reasoning state를 보존하는 방식을 결합했습니다. DeepSeek가 V4 Pro를 에이전트용 모델로 강조하는 이유는 한 번에 긴 입력을 받는 능력보다, 긴 작업을 덜 잊고 필요한 계산을 골라 쓰는 능력에 있습니다.

## 세 줄 요약

- V4 Pro는 1.6조 개 파라미터 가운데 매 토큰마다 490억 개를 활성화하는 MoE 모델이며, CSA와 HCA라는 두 압축 attention을 섞어 100만 토큰 문맥의 비용을 낮췄습니다.
- 도구를 사용하는 동안에는 이전 reasoning state를 다음 호출에 넘겨 긴 작업의 사고 흐름을 유지하고, `low`, `high`, `max`로 작업별 추론량을 조절합니다.
- 기술적 의의는 큰 문맥 창 자체보다 `압축된 기억`, `이어지는 추론`, `조절 가능한 계산량`을 하나의 에이전트 운용 구조로 묶었다는 데 있습니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 공식 기술 보고서와 API 문서는 hybrid attention, 100만 토큰 문맥, reasoning effort, 도구 호출 중 reasoning state 보존 방식을 설명합니다.
- **도입 전에 확인할 것:** 코드 수정이나 장기 조사처럼 실제 업무를 여러 단계로 나눈 뒤, effort별 성공률과 지연시간, 출력 토큰, 문맥 누락을 함께 측정해야 합니다.
- **아직 결론 내릴 수 없는 것:** 연산량과 KV cache 절감 수치, 에이전트 benchmark는 DeepSeek의 자체 측정입니다. 다른 runtime과 실제 한국어 업무에서도 같은 이점이 나는지는 독립 평가가 필요합니다.

## 이 공개의 의의와 편집 판단

V4 Pro가 던지는 질문은 “모델이 얼마나 긴 글을 한 번에 읽을 수 있는가”에서 “긴 작업 동안 무엇을 어떤 형태로 기억할 것인가”로 바뀝니다. 에이전트가 코드 탐색, 테스트, 수정, 재검증을 반복하면 대화뿐 아니라 파일 내용과 명령 결과, 실패 원인도 계속 쌓입니다. 문맥 창만 넓히고 매번 모든 기록을 똑같이 읽게 하면 비용과 지연시간이 커집니다.

V4의 해법은 가까운 기록은 자세히 보고, 오래된 기록은 압축하며, 현재 질문과 관련 있는 부분을 골라 다시 읽는 것입니다. 여기에 작업 난도별 추론량과 도구 호출 사이의 상태 보존을 더했습니다.

편집 판단: V4 Pro의 기술적 의의는 100만 토큰을 모델 사양에서 에이전트의 작업 기억으로 바꾸려는 시도에 있습니다. 세 구성 요소가 함께 작동한다면 에이전트는 더 긴 작업을 수행하면서도 모든 과거 토큰에 같은 비용을 지불하지 않아도 됩니다. 다만 이 판단은 설계가 겨냥한 방향에 관한 것이며, DeepSeek가 제시한 성능 우위를 독립적으로 확인했다는 뜻은 아닙니다.

## 100만 토큰에서 가장 먼저 무너지는 것은 기억 비용입니다

일반적인 Transformer attention은 새 토큰을 만들 때 앞에 있는 많은 토큰과 관계를 계산합니다. 문맥이 길어질수록 비교해야 할 대상과 과거 key·value를 저장하는 KV cache가 커집니다. 에이전트가 수십 차례 도구를 호출하면 이 기록에는 질문과 답변뿐 아니라 코드, 로그, 검색 결과까지 들어갑니다.

V4는 모든 과거 정보를 같은 해상도로 보관하지 않습니다. 작업 장면으로 바꾸면 최근에 수정한 코드와 오류 메시지는 원문에 가깝게 두고, 오래된 탐색 기록은 묶어서 요약하며, 현재 문제와 관련 있는 묶음만 다시 꺼내 보는 방식입니다. 이 역할을 CSA와 HCA가 나눠 맡습니다.

### CSA: 압축한 뒤 관련 있는 기록만 고릅니다

Compressed Sparse Attention은 먼저 여러 토큰의 key·value를 하나의 압축 항목으로 만듭니다. 그런 다음 작은 indexer가 현재 query와 관련도가 높은 압축 항목 top-k를 고릅니다. 모든 과거 토큰을 다시 읽지 않고, 압축된 기록 가운데 필요한 부분만 attention 계산에 넣는 구조입니다.

압축하면 세부 정보가 사라질 수 있습니다. 이를 보완하기 위해 CSA는 최근 토큰을 압축하지 않은 sliding window로 함께 봅니다. 방금 나온 함수명이나 오류 줄처럼 가까운 정보는 자세히 유지하고, 먼 정보는 검색 가능한 묶음으로 관리합니다.

### HCA: 더 오래된 문맥은 훨씬 강하게 압축합니다

Heavily Compressed Attention은 CSA보다 많은 토큰을 하나의 key·value 항목으로 합칩니다. 관련 항목을 top-k로 다시 고르는 대신, 훨씬 작아진 전체 요약을 봅니다. V4는 CSA와 HCA layer를 교차 배치해 중간 거리의 선택적 기억과 아주 긴 거리의 압축 기억을 함께 사용합니다.

이 hybrid attention이 100만 토큰을 가능하게 한 핵심입니다. DeepSeek의 기술 보고서는 같은 길이에서 V4 Pro가 V3.2 대비 단일 토큰 추론 FLOPs의 27%, KV cache의 10%를 사용한다고 보고합니다. 이는 실제 서비스 비용을 직접 뜻하는 가격표가 아니라 모델 내부 attention의 계산·메모리 측정입니다.

## 긴 문맥이 에이전트의 ‘이어지는 생각’이 되는 과정

긴 문맥 창만 있다고 에이전트가 긴 작업을 잘 수행하는 것은 아닙니다. 도구를 한 번 호출할 때마다 이전 판단을 버리면, 모델은 같은 파일을 다시 읽고 같은 가설을 다시 세우게 됩니다.

V4는 도구 호출이 이어지는 동안 `reasoning_content`를 다음 요청에 다시 넣도록 API를 설계했습니다. 예를 들어 에이전트가 테스트 실패 원인을 추론한 뒤 파일 검색 도구를 호출했다면, 검색 결과뿐 아니라 그 전에 세운 가설도 다음 단계에 전달합니다. 공식 API 문서는 tools를 사용한 요청에서 이 필드를 빠뜨리면 400 오류가 난다고 명시합니다.

일반 대화에서는 이전 reasoning content를 계속 쌓지 않습니다. 도구 호출이 없는 대화는 새 사용자 메시지가 오면 이전 추론을 문맥에서 제외하고, 장기 작업의 도구 연쇄에서는 유지합니다. 모든 상황에서 기억을 늘리는 것이 아니라, 상태의 연속성이 필요한 경로에만 비용을 쓰는 선택입니다.

기술 보고서는 도구 호출 형식도 XML 기반의 전용 schema로 학습해 문자열 escaping 실패를 줄였다고 설명합니다. 공개 API에서는 OpenAI·Anthropic 호환 형식을 사용하지만, 모델을 학습시킬 때부터 도구 이름과 인자를 구조적으로 다루었다는 점이 에이전트 성능의 한 축입니다.

## reasoning effort는 단순한 속도 스위치가 아닙니다

정식 API는 reasoning effort를 `low`, `high`, `max`로 제공합니다. `low`는 짧고 단순한 판단, `high`는 일반적인 코드 수정과 계획, `max`는 긴 조사나 어려운 추론에 배분할 수 있습니다. 기본값은 `high`입니다.

기술 보고서를 보면 이 차이는 같은 출력을 임의로 길게 만드는 옵션에 그치지 않습니다. DeepSeek는 서로 다른 context window와 길이 penalty를 적용한 specialist를 별도로 훈련한 뒤 세 reasoning mode를 통합했다고 설명합니다. `max`는 더 많은 test-time compute를 쓰도록 학습된 경로입니다.

따라서 높은 effort가 항상 좋은 기본값은 아닙니다. 짧은 분류나 형식 변환에서는 추가 추론이 지연시간과 출력량만 늘릴 수 있습니다. 반대로 여러 파일을 고치고 테스트 결과에 따라 계획을 바꾸는 작업에서는 중간 가설을 검토하는 계산이 실패 횟수를 줄일 수 있습니다. 비교해야 할 것은 요청 한 번의 토큰 수가 아니라 작업 완료까지 든 총 시간과 재시도 횟수입니다.

## mHC와 Muon은 큰 모델을 안정적으로 학습시키는 기반입니다

V4 Pro는 전체 1.6조 개 파라미터 가운데 토큰마다 490억 개를 활성화하는 MoE 모델입니다. 긴 문맥용 attention만 바꿔서는 이 규모의 모델을 안정적으로 훈련하기 어렵습니다. DeepSeek는 층 사이의 residual connection을 확장한 mHC와, 대부분의 행렬 parameter를 갱신하는 Muon optimizer를 함께 도입했습니다.

Manifold-Constrained Hyper-Connections는 층 사이에 여러 residual 경로를 두되, 신호를 섞는 행렬을 음수가 없고 각 행과 열의 합이 1인 범위로 제한합니다. 이 제약은 깊은 층을 지나며 신호가 과도하게 커지거나 서로 상쇄되는 위험을 줄입니다. 더 넓은 residual 경로의 표현력을 사용하면서 학습 안정성을 확보하려는 설계입니다.

Muon은 gradient update 행렬을 직교화에 가깝게 다듬어 학습의 수렴과 안정성을 높이는 optimizer입니다. V4는 embedding과 normalization 같은 일부 parameter에는 AdamW를 유지하고, 나머지 주요 module에 Muon을 사용합니다. mHC와 Muon은 사용자가 API에서 직접 조절하는 기능은 아니지만, 거대한 MoE와 새로운 attention을 실제로 훈련할 수 있게 만든 기반입니다.

## benchmark는 설계의 가능성을 보여 주지만 결론은 아닙니다

기술 보고서에서 V4 Pro Max는 지식·수학·코딩·에이전트 benchmark에서 이전 공개 모델보다 높은 결과를 제시합니다. 100만 토큰 retrieval 평가에서는 128K까지 비교적 안정적이고 그 이후 성능 저하가 나타나지만, 1M에서도 정보를 찾는 능력이 유지된다고 보고합니다.

조건을 함께 봐야 합니다. 코드 에이전트 평가는 DeepSeek의 내부 harness에서 bash와 파일 편집 도구, 최대 500 interaction step, 최대 512K context를 사용했습니다. reasoning effort 비교도 mode마다 생성한 총 토큰 수가 다릅니다. 따라서 benchmark는 hybrid attention과 추가 test-time compute가 어떤 가능성을 보였는지 설명하지만, 모든 에이전트 runtime에서 같은 순위가 나온다는 보장은 아닙니다.

이 기사는 모델을 직접 실행하거나 API benchmark를 재현하지 않았습니다. 재현성 상태는 R2이며, 성능 수치는 DeepSeek 기술 보고서의 자체 평가로 한정합니다.

## 버전과 공개 가중치는 짧게 구분하면 됩니다

공식 모델·가격 문서가 표시하는 현재 서비스 버전은 `DeepSeek-V4-Pro-0813`입니다. 일부 커뮤니티에서 보인 `0831` 표기는 공식 자료에서 확인되지 않았습니다. API에서는 기존처럼 `deepseek-v4-pro`를 호출하면 됩니다. 이전 실행과 비교해야 한다면 사용 날짜와 reasoning effort 같은 조건을 함께 기록하는 편이 좋습니다.

4월 프리뷰 가중치와 기술 보고서는 공개됐지만, Hugging Face 저장소에는 8월 13일 정식판을 별도 `0813` checkpoint로 올린 기록이 확인되지 않습니다. 따라서 공개 가중치와 현재 API 서비스가 같은 checkpoint라고 전제해서는 안 됩니다.

가격도 바뀝니다. 2026년 8월 17일 01:00 KST부터 V4 Pro의 off-peak cache-miss 입력은 100만 토큰당 0.66달러, 출력은 1.98달러입니다. 현재 가격 0.435달러와 0.87달러보다 높습니다. 긴 문맥이 기술적으로 저렴해진 것과 API 가격이 낮아지는 것은 다른 문제입니다.

## 독자가 내릴 수 있는 기술 판단

V4 Pro를 평가할 때 첫 질문은 “100만 토큰을 넣을 수 있는가”가 아니라 “우리 작업에서 오래된 정보를 제대로 되찾는가”여야 합니다. 저장소 탐색, 수정, 테스트, 재수정으로 이어지는 시나리오를 만들고 중간 근거를 잊거나 같은 탐색을 반복하는지 확인해야 합니다.

두 번째는 effort별 전체 작업 비용입니다. `low`, `high`, `max`로 같은 작업을 수행하고 첫 응답의 속도뿐 아니라 완료율, 재시도, 도구 호출 오류, 총 출력 토큰을 비교해야 합니다.

세 번째는 runtime의 context 관리입니다. 도구 호출 사이에서 `reasoning_content`를 정확히 되돌려 보내지 않으면 V4가 설계한 interleaved thinking을 활용할 수 없습니다. 모델 교체만으로 장기 에이전트가 완성되는 것이 아니라, 상태 전달 계약까지 맞아야 합니다.

## 이해상충과 취재 조건

이 기사에 사용한 DeepSeek API 문서, 기술 보고서, Hugging Face 저장소는 DeepSeek 또는 프로젝트 운영자의 1차 자료입니다. 구조와 공개 artifact를 설명하는 데는 적합하지만, DeepSeek의 성능 우월성을 독립 검증하는 자료는 아닙니다.

이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 기술 보고서와 문서만 사용했으며 커뮤니티 표기는 사실 확인을 위한 질문으로만 다뤘습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. DeepSeek는 2026년 8월 13일 V4 Pro 정식판을 발표했고 현재 서비스 버전을 `DeepSeek-V4-Pro-0813`으로 표시합니다. | E2 · P1 | GA 발표와 모델·가격 문서로 확인했습니다. `0831`은 공식 자료에서 확인되지 않았습니다. |
| C2. V4 Pro는 CSA와 HCA를 교차 사용해 긴 문맥을 압축하며, 보고서는 1M에서 V3.2 대비 단일 토큰 FLOPs 27%, KV cache 10%를 제시합니다. | E2 · P1/P2 | DeepSeek 기술 보고서의 설계와 자체 측정입니다. 독립 재현 수치가 아닙니다. |
| C3. mHC는 residual mapping을 제약해 깊은 층의 신호 전달 안정성을 높이고, Muon은 주요 module의 학습에 사용됩니다. | E2 · P2 | 기술 보고서의 architecture와 optimizer 절로 확인했습니다. API 사용자가 직접 조절하는 기능은 아닙니다. |
| C4. V4는 도구 호출 중 reasoning state를 유지하고 API는 `low`, `high`, `max` effort를 지원합니다. | E2 · P1/P2 | 기술 보고서와 thinking mode 문서로 확인했습니다. 실제 효과는 runtime이 상태 전달 계약을 지킬 때 평가해야 합니다. |
| C5. V4 Pro는 1.6T total, 49B active parameter MoE이며 32T token 이상으로 pre-training됐습니다. | E2 · P2 | 기술 보고서와 공개 모델 자료의 프로젝트 자체 설명입니다. |
| C6. V4 Pro의 핵심 의의는 압축된 긴 문맥, 이어지는 도구 추론, 조절 가능한 test-time compute를 에이전트 운용에 결합한 데 있습니다. | E2 · derived | C2-C5에서 도출한 편집 판단입니다. 다른 runtime에서의 성능 우위를 뜻하지 않습니다. |
| C7. 프리뷰 공개 가중치와 API의 0813 서비스 버전은 동일 checkpoint로 확인되지 않았으며, 8월 17일 KST부터 API 가격이 변경됩니다. | E2 · P1/P2 | 공식 가격표와 Hugging Face commit 기록으로 확인했습니다. 가격과 저장소 상태는 이후 바뀔 수 있습니다. |

## 출처

- DeepSeek V4 Pro 정식 출시 발표: https://api-docs.deepseek.com/news/news260813/
- DeepSeek V4 기술 보고서: https://arxiv.org/abs/2606.19348
- DeepSeek thinking mode 문서: https://api-docs.deepseek.com/guides/thinking_mode/
- DeepSeek 모델·가격 문서: https://api-docs.deepseek.com/quick_start/pricing/
- DeepSeek V4 프리뷰 발표: https://api-docs.deepseek.com/news/news260424/
- DeepSeek V4 Pro Hugging Face 저장소: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
- DeepSeek V4 Pro commit 기록: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/commits/main
