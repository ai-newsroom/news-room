---
edition: ai
decision: publish-candidate
title: "DeepSeek, 에이전트용 V4 Pro 정식 출시…공식 버전은 '0813'"
date: 2026-08-14
publication_kind: special
subject: "DeepSeek-V4-Pro-0813 GA release, announced August 13, 2026"
summary: "DeepSeek는 2026년 8월 13일 V4 Pro를 정식 출시했고, 공식 모델·가격 문서는 현재 버전을 DeepSeek-V4-Pro-0813으로 표시합니다. 개발팀이 봐야 할 변화는 에이전트 운용을 위한 reasoning effort, Responses API, 도구 호출, 긴 컨텍스트, 가격제 변화입니다. 다만 API 별칭과 고정 버전 endpoint, 4월 프리뷰 공개 가중치와 0813 정식판 가중치는 구분해야 합니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["DeepSeek 공식 문서와 Hugging Face 저장소는 DeepSeek 또는 프로젝트 운영자의 1차 자료입니다. 이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

DeepSeek가 2026년 8월 13일 `DeepSeek-V4-Pro`를 정식 출시로 공개했고, SW 엔지니어에게 중요한 변화는 에이전트 운용용 API 표면과 비용·버전 기록 방식이 함께 바뀐 점입니다. 일부 커뮤니티에서 보인 `DeepSeek-V4-Pro-0831` 표기는 공식 발표와 API 문서에서 확인되지 않습니다. 발행 시점에 공식 모델·가격 문서가 가리키는 현재 버전은 `DeepSeek-V4-Pro-0813`입니다.

개발팀에 더 중요한 변화는 이름보다 운용 방식입니다. V4 Pro는 앱과 웹에서는 Expert Mode로, API에서는 기존 호출명인 `deepseek-v4-pro`로 제공됩니다. 여기에 `low`, `high`, `max` reasoning effort, OpenAI Responses API 형식, Anthropic API 형식, 도구 호출, JSON 출력, 100만 토큰 컨텍스트가 묶였습니다.

이때 `deepseek-v4-pro`라는 안정된 호출명은 고정 버전 endpoint와 같은 말이 아닙니다. 공식 문서는 실제 모델 버전을 `DeepSeek-V4-Pro-0813`으로 표시하지만, `0813`을 별도 모델명처럼 직접 호출할 수 있다고 안내하지 않습니다. 재현성이 필요한 팀은 별칭만 저장하지 말고 확인 날짜와 실행 조건을 함께 남겨야 합니다.

## 세 줄 요약

- DeepSeek의 2026년 8월 13일 GA 발표는 V4 Pro를 정식 출시했고, 앱·웹 Expert Mode와 API의 `deepseek-v4-pro` 호출명을 그대로 쓴다고 밝혔습니다.
- 공식 가격·모델 문서는 현재 버전을 `DeepSeek-V4-Pro-0813`으로 표시하며, V4 Pro는 100만 토큰 컨텍스트, 최대 384K 출력, reasoning effort 조절, Responses API, Anthropic API, 도구 호출, JSON 출력을 지원 목록에 둡니다.
- 4월 프리뷰 가중치는 Hugging Face에 공개돼 있지만, 공개 저장소의 최신 커밋은 2026년 6월 22일 기술 보고서 갱신입니다. 8월 13일 GA용 `0813` 체크포인트가 새로 올라왔다고 단정할 근거는 확인하지 못했습니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** V4 Pro가 GA로 제공된 사실, API 별칭, 공식 버전 표기, reasoning effort와 호환 API 표면, 현재 가격과 2026년 8월 16일 16:00 UTC 이후 가격표는 공식 문서에서 확인할 수 있습니다.
- **도입 전에 확인할 것:** 기존 agent 회귀 평가를 `0813` 환경에서 다시 돌리고, 프롬프트·도구 정의·reasoning effort·temperature·top_p·출력 한도·캐시 적중률을 함께 기록해야 합니다.
- **아직 결론 내릴 수 없는 것:** DeepSeek가 제시한 benchmark와 production gains는 회사 자체 주장입니다. 독립 재현 없이 다른 모델보다 일반적으로 우수하다는 결론으로 올릴 수 없습니다.

## 이 공개의 의의와 편집 판단

4월 프리뷰에서 DeepSeek는 V4 계열을 공개하며 100만 토큰 컨텍스트와 MoE 구조를 앞세웠습니다. 프리뷰 문서는 V4 Pro를 전체 1.6조, 활성 490억 파라미터 모델로 설명했고, 기술 보고서와 공개 가중치 링크를 함께 제공했습니다. 이 단계의 초점은 모델 구조, 긴 컨텍스트, 공개 artifact였습니다.

8월 정식판의 초점은 제품 운용에 더 가깝습니다. GA 발표는 agent upgrade, reasoning effort, Responses API, Codex용 설정, 앱·웹 Expert Mode, API 제공을 한 묶음으로 제시합니다. 공식 가격·모델 문서도 `deepseek-v4-pro`가 JSON 출력, 도구 호출, Responses API, Anthropic API를 지원한다고 표시합니다.

편집 판단: 이 출시는 benchmark 순위보다 에이전트 runtime에 연결하기 쉬운 표면을 넓힌 사건으로 보는 편이 정확합니다. 간단한 분류나 요약은 낮은 reasoning effort로, 일반 코드 수정과 agent workflow는 high로, 긴 조사와 검증 작업은 max로 나눠 시험할 수 있습니다. 다만 실제 품질과 비용은 팀의 workload와 캐시 적중률에서 다시 측정해야 합니다.

## 입력에서 출력까지의 동작을 어떻게 바꿔야 하나

reasoning effort는 한 모델을 작업 난이도별로 운용하는 knob입니다. 공식 thinking mode 문서는 OpenAI Chat Completions 형식에서 `reasoning_effort`를 `low`, `high`, `max`로 줄 수 있고, Responses API 형식에서는 `reasoning.effort`에 `none`, `low`, `high`, `max`를 쓴다고 설명합니다. 기본 thinking mode는 켜져 있고 기본 effort는 high입니다.

이 기능은 비용 절감 버튼으로만 보면 안 됩니다. effort를 낮추면 쉬운 작업의 지연시간과 출력 토큰을 줄일 가능성이 있지만, 실패 비용이 큰 코드 변경이나 다단계 도구 호출에서는 품질 저하가 더 비쌀 수 있습니다. 따라서 agent runner는 task class별로 effort를 고정하고, 실패율·수정 횟수·출력 토큰·캐시 적중률을 함께 봐야 합니다.

Responses API 지원은 기존 OpenAI 형식 client를 붙일 때 의미가 큽니다. DeepSeek 문서는 base URL을 `https://api.deepseek.com`으로 두고 Responses API 형식 호출을 지원한다고 설명합니다. 동시에 일부 필드는 부분 지원 또는 미지원입니다. 예를 들어 `tools`는 function과 web_search 중심으로, `previous_response_id`와 conversation 저장은 지원하지 않는 stateless API로 문서화돼 있습니다.

## API 별칭은 재현성을 보장하지 않습니다

공식 가격·모델 문서의 모델 행은 호출명을 `deepseek-v4-pro`로, 모델 버전을 `DeepSeek-V4-Pro-0813`으로 분리해 보여 줍니다. GA 발표도 API 모델 이름은 바뀌지 않는다고 적었습니다. 이 조합은 운영에는 편하지만 실험 기록에는 부족합니다.

재현성이 필요한 팀은 실행 로그에 최소 여섯 가지를 남겨야 합니다. 테스트 날짜, 공식 문서에서 확인한 버전 표기, 호출한 모델 별칭, 프롬프트와 system/developer message, 도구 schema와 approval policy, reasoning effort와 sampling 설정입니다. 여기에 regression suite의 입력 commit, expected output, 실패 판정 기준까지 묶어야 나중에 alias가 다른 backend를 가리켜도 원인을 좁힐 수 있습니다.

`0813`을 직접 호출하는 endpoint가 있다는 뜻으로 쓰면 안 됩니다. 발행 시점에 공식 문서는 `deepseek-v4-pro` 호출명과 `DeepSeek-V4-Pro-0813` 버전 표기를 보여 주지만, `DeepSeek-V4-Pro-0813`을 모델명으로 호출하라고 안내하지 않습니다. provider가 고정 버전 endpoint를 제공한다고 확인되기 전까지는 별칭 기반 API로 취급하는 편이 안전합니다.

## 새 가격제는 현재 가격보다 비싸질 수 있습니다

공식 가격표의 현재 V4 Pro 가격은 100만 토큰당 cache-hit 입력 0.003625달러, cache-miss 입력 0.435달러, 출력 0.87달러입니다. 2026년 8월 16일 16:00 UTC부터는 peak/off-peak 가격제가 적용됩니다. 한국 시간으로는 2026년 8월 17일 01:00입니다.

새 가격표에서 V4 Pro의 off-peak 가격은 cache-hit 입력 0.022달러, cache-miss 입력 0.66달러, 출력 1.98달러입니다. peak 가격은 각각 0.044달러, 1.32달러, 3.96달러입니다. DeepSeek가 말한 off-peak 50% 할인은 peak 대비 절반이라는 뜻이지, 현재 가격보다 싸다는 뜻이 아닙니다.

현재가와 비교하면 off-peak도 cache-hit 입력은 약 6.1배, cache-miss 입력은 약 1.5배, 출력은 약 2.3배입니다. agent workload는 긴 system prompt와 도구 결과를 반복해서 넣기 때문에 cache-hit 비중이 비용을 크게 좌우합니다. 가격 변경 뒤에는 평균 토큰 단가가 아니라 실제 캐시 적중률과 출력 토큰 분포로 다시 계산해야 합니다.

## 공개 가중치는 프리뷰와 0813을 나눠 봐야 합니다

4월 프리뷰 발표는 V4 계열을 open-sourced라고 설명했고, Hugging Face 공개 가중치 링크를 제공했습니다. `deepseek-ai/DeepSeek-V4-Pro` 저장소도 MIT 라이선스, safetensors 파일, README, inference 코드, 기술 보고서 링크를 공개합니다. 따라서 "V4 Pro 계열의 프리뷰 가중치는 공개돼 있다"는 확인된 사실입니다.

하지만 이 말은 "0813 정식판 가중치가 새로 공개됐다"와 다릅니다. Hugging Face API로 확인한 `deepseek-ai/DeepSeek-V4-Pro`의 `main` 최신 commit은 2026년 6월 22일 `Update technical report`입니다. 저장소 metadata의 현재 `sha`도 같은 commit을 가리킵니다. 2026년 8월 13일 GA 이후 `DeepSeek-V4-Pro-0813` 체크포인트나 커밋이 공개됐다는 기록은 확인되지 않았습니다.

따라서 로컬 실행과 API 결과를 같은 모델로 가정하면 안 됩니다. 공개 저장소의 무접미사 `DeepSeek-V4-Pro`와 API 문서의 `DeepSeek-V4-Pro-0813`은 이름이 이어져 있지만, 동일 checkpoint라고 확인된 것은 아닙니다. 로컬 평가를 한다면 Hugging Face commit과 config, API 평가를 한다면 공식 버전 표기와 호출 날짜를 따로 기록해야 합니다.

## benchmark 또는 재현 결과

이 기사는 DeepSeek API를 호출하거나 모델을 로컬에서 실행해 benchmark를 재현하지 않았습니다. 재현성 상태는 R2입니다. 이유는 GA 발표, 가격·모델 문서, API guide, Hugging Face 모델 저장소와 commit 목록처럼 독자가 직접 열람 가능한 원문과 artifact가 있지만, 성능 수치를 독립 재현하지 않았기 때문입니다.

DeepSeek가 발표한 production gains와 benchmark 표는 회사 자체 평가로만 다뤘습니다. 본문은 V4 Pro가 다른 frontier 모델보다 낫다는 결론을 내리지 않습니다. 실제 도입 판단은 기존 agent regression, latency, cost, tool-call failure, 한국어 업무 입력을 포함한 팀별 평가로 좁혀야 합니다.

## 적용 범위와 확인하지 못한 것

확인한 범위는 2026년 8월 14일 UTC에 접근 가능한 공식 문서와 공개 Hugging Face 저장소입니다. 가격은 DeepSeek 공식 문서가 제품 가격이 바뀔 수 있고 최신 가격을 정기적으로 확인하라고 적은 항목이므로, 발행 직전과 실제 도입 직전에 다시 봐야 합니다.

확인하지 못한 것은 세 가지입니다. 첫째, `DeepSeek-V4-Pro-0831`이라는 표기가 공식적으로 존재한다는 근거는 찾지 못했습니다. 둘째, API 별칭이 특정 backend commit에 고정된다는 보장은 공식 문서에서 확인하지 못했습니다. 셋째, 8월 13일 GA에 맞춘 `0813` 공개 가중치가 Hugging Face에 새로 올라왔다는 근거도 확인하지 못했습니다.

## 독자가 내릴 수 있는 기술 판단

도입 전에 할 일은 명확합니다. 첫째, 기존 agent regression을 `deepseek-v4-pro` 현재 환경에서 다시 실행하고, 실패 유형을 effort별로 나눠 봅니다. 단순 분류, 일반 코드 수정, 복잡한 조사·검증을 같은 설정으로 평가하면 운영 knob의 의미가 사라집니다.

둘째, 모델 별칭 이외의 실행 조건을 로그에 남깁니다. 공식 문서 확인 날짜, `DeepSeek-V4-Pro-0813` 버전 표기, 프롬프트, 도구 정의, approval policy, reasoning effort, sampling 설정, 최대 출력, 입력 commit을 함께 저장해야 합니다.

셋째, 2026년 8월 17일 01:00 KST부터 바뀌는 비용을 실제 캐시 적중률로 다시 계산합니다. 특히 agent가 긴 컨텍스트를 반복 투입한다면 cache-hit 입력 단가 상승과 출력 단가 상승이 전체 비용을 다르게 흔듭니다.

## 이해상충과 취재 조건

이 기사에 사용한 DeepSeek API 문서와 Hugging Face 저장소는 DeepSeek 또는 프로젝트 운영자의 1차 자료입니다. 출시·지원·가격·버전·공개 artifact 상태를 확인하는 데는 적합하지만, DeepSeek의 성능 우월성이나 production gains를 독립 검증하는 자료는 아닙니다.

이 기사에는 사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 웹 문서, 공개 API 문서, 공개 Hugging Face metadata만 사용했습니다. 커뮤니티 표기는 발견 질문으로만 취급했고, 모델명·출시일·가격·가중치 공개 여부의 근거로 쓰지 않았습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. DeepSeek는 2026년 8월 13일 V4 Pro GA를 발표했고 앱·웹 Expert Mode와 API에서 제공한다고 밝혔습니다. | E1 · P1 | DeepSeek GA 발표로 확인했습니다. 출시 사실과 회사 발표 내용의 근거이며 성능 우월성의 독립 검증은 아닙니다. |
| C2. 공식 모델·가격 문서는 `deepseek-v4-pro` 호출명과 `DeepSeek-V4-Pro-0813` 모델 버전을 분리해 표시합니다. | E2 · P1 | 가격·모델 문서의 표로 확인했습니다. `0813`을 직접 호출할 수 있는 고정 endpoint는 확인하지 못했습니다. |
| C3. V4 Pro는 reasoning effort, Responses API, Anthropic API, JSON 출력, 도구 호출, 1M 컨텍스트, 최대 384K 출력을 공식 지원 목록에 둡니다. | E2 · P1 | 가격·모델 문서와 thinking mode, Responses API guide로 확인했습니다. 일부 Responses API 항목은 부분 지원 또는 미지원입니다. |
| C4. 2026년 8월 16일 16:00 UTC 이후 V4 Pro off-peak 가격도 현재 가격보다 cache-hit 입력 약 6.1배, cache-miss 입력 약 1.5배, 출력 약 2.3배 높습니다. | E2 · derived | 공식 가격표의 현재가와 예정 off-peak 가격을 직접 나눠 계산했습니다. 가격은 변동 가능성이 있어 재확인이 필요합니다. |
| C5. 4월 프리뷰 기준 V4 Pro는 1.6T total, 49B active parameter MoE 모델이고 프리뷰 가중치와 기술 보고서가 공개됐습니다. | E2 · P1/P2 | 4월 프리뷰 발표, Hugging Face README, 모델 metadata로 확인했습니다. 프리뷰 artifact 범위에 대한 주장입니다. |
| C6. Hugging Face `deepseek-ai/DeepSeek-V4-Pro`의 최신 main commit은 2026년 6월 22일 기술 보고서 갱신이며, 8월 13일 GA용 `0813` 공개 checkpoint는 확인되지 않았습니다. | E2 · P2 | Hugging Face API의 commit 목록과 모델 metadata로 확인했습니다. 저장소 밖의 비공개 또는 다른 공개 경로는 확인 범위 밖입니다. |
| C7. 중심 편집 판단은 GA가 에이전트 운용 표면을 넓혔지만, API 별칭·비용·공개 가중치 상태를 별도 관리해야 한다는 것입니다. | E2 · derived | C1-C6에서 파생한 판단입니다. 성능 우월성이나 production gains는 DeepSeek 주장으로만 제한했습니다. |

## 출처

- DeepSeek V4 Pro GA 발표: https://api-docs.deepseek.com/news/news260813/
- DeepSeek 모델·가격 문서: https://api-docs.deepseek.com/quick_start/pricing/
- DeepSeek thinking mode 문서: https://api-docs.deepseek.com/guides/thinking_mode
- DeepSeek Responses API 문서: https://api-docs.deepseek.com/guides/responses_api
- DeepSeek V4 프리뷰 발표: https://api-docs.deepseek.com/news/news260424/
- DeepSeek V4 Pro Hugging Face 저장소: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
- DeepSeek V4 Pro Hugging Face commit 목록: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/commits/main
