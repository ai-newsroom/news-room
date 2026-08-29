---
edition: ai
decision: publish-candidate
title: "Gemini Omni 1.1 Flash 정식 출시 - 비디오 생성에 반복 편집 API를 더했습니다"
date: 2026-08-30
subject: "Google Gemini Omni 1.1 Flash, Gemini API model gemini-omni-1.1-flash, August 27 2026"
summary: "Google이 `gemini-omni-1.1-flash`를 정식 출시했습니다. 새 모델은 텍스트·이미지·비디오 입력으로 비디오를 만들고, 기존 영상을 이어 붙이며, 시작·끝 프레임 사이의 장면을 생성합니다. 360p 초안부터 4K 업스케일까지 API에서 고를 수 있습니다. 품질 평가는 Google의 자체 설명에 머물지만, changelog, 모델 카드, 개발자 문서로 API 기능과 공개된 한계는 확인할 수 있습니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Google DeepMind와 Google AI for Developers는 Gemini Omni 1.1 Flash의 개발·제공 주체이며, 이번 기사에서 사용한 발표문, changelog, 모델 카드, 개발자 문서를 작성·운영합니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Google이 2026년 8월 27일 `gemini-omni-1.1-flash`를 Gemini API의 정식 모델로 공개했습니다. 핵심 변화는 비디오 생성 모델을 한 번의 프롬프트로 클립을 뽑는 도구에 머물게 하지 않은 데 있습니다. 이 모델은 기존 영상을 이어 만들고, 시작 프레임과 끝 프레임 사이를 채우며, 해상도를 고르는 반복 편집 작업을 API로 다룹니다. 영상 편집기, 광고 소재 제작 도구, 교육용 콘텐츠 시스템을 만드는 개발자는 이제 모델 호출을 “생성” 한 단계가 아니라 작업 상태가 남는 비디오 흐름으로 설계해야 합니다.

이번 출시는 같은 Google의 Gemini 3.7 Flash처럼 코딩 에이전트 성능을 직접 겨냥한 모델 발표는 아닙니다. 하지만 SW 엔지니어에게는 다른 의미가 있습니다. 이미지 생성 API가 제품 UI 안으로 들어온 뒤에는 입력 파일, 결과 파일, 재시도, 비용 제한, 저해상도 preview가 중요해졌습니다. 비디오 생성도 이제 파일 처리와 편집 상태를 다루는 backend 기능으로 들어오고 있습니다.

## 비디오는 한 번 만들고 끝나지 않습니다

기존 비디오 생성 API는 대체로 텍스트나 이미지 하나를 넣고 몇 초짜리 결과물을 받는 방식이었습니다. 품질이 마음에 들지 않으면 프롬프트를 고쳐 다시 만들었고, 앞 결과와 새 결과를 자연스럽게 이어 붙이는 일은 별도 편집 도구나 수작업에 가까웠습니다.

Gemini Omni 1.1 Flash에서 Google이 앞세운 변화는 이 흐름을 API 작업으로 가져온 것입니다. changelog는 `gemini-omni-1.1-flash`가 기존 비디오 끝에 이어질 장면을 만드는 video extension, 두 장의 이미지를 시작·끝 프레임으로 주고 그 사이 영상을 만드는 interpolation, `360p`, `720p`, `1080p`, `4k` 해상도 선택을 지원한다고 적습니다. 기존 preview endpoint인 `gemini-omni-flash-preview`는 2026년 9월 30일에 deprecated될 예정입니다.

이 변화는 제품 설계에 직접 닿습니다. 예전에는 “비디오 생성 버튼” 하나가 중심이었다면, 이제는 storyboard를 낮은 해상도로 빠르게 확인하고, 마음에 드는 장면만 720p나 4K로 올리는 흐름이 자연스러워집니다. 앞선 작업 결과인 interaction을 이어 쓰는 UI도 만들 수 있습니다. 모델이 더 좋은 영상을 만든다는 평가보다, 개발자가 반복 편집 상태를 API 단위로 다룰 수 있게 된 점이 이번 공개의 실무적 변화입니다.

## Interactions API는 작업 상태를 남깁니다

개발자 문서에서 가장 중요한 이름은 `Interactions API`입니다. 문서는 Python, JavaScript, REST 예제로 `client.interactions.create` 또는 `/v1beta/interactions` 호출을 보여 줍니다. 응답은 단순 텍스트가 아닙니다. `steps`, `status`, `model`, `id` 같은 값을 담은 interaction 객체가 돌아오고, SDK에서는 `interaction.output_video`로 비디오 데이터를 받을 수 있습니다.

영상 파일은 크기가 커질 수 있기 때문에 문서는 두 가지 전달 방식을 나눕니다. 작은 결과는 base64로 받을 수 있습니다. 4MB를 넘는 비디오는 `delivery="uri"`를 써서 Google-hosted URI를 받고, File API에서 상태가 `ACTIVE`가 될 때까지 polling한 뒤 내려받는 방식을 권합니다. 이는 UI에서 진행 상태, 실패 재시도, 만료 전 다운로드 같은 처리가 필요하다는 뜻입니다.

기존 영상을 편집할 때도 파일 경로가 중요합니다. 문서의 JavaScript 예제는 비디오를 File API에 올린 뒤 `files.get`으로 처리 상태를 확인하고, 그 URI와 텍스트 지시를 함께 `interactions.create`에 넘깁니다. 따라서 제품팀은 모델 프롬프트 품질만 볼 것이 아니라 업로드 용량, 파일 보존 기간, 실패 상태, 사용자별 결과 접근 권한까지 backend 설계에 넣어야 합니다.

## 해상도 선택은 초안과 최종본을 나눕니다

Omni 1.1의 해상도 옵션은 단순한 출력 품질 설정이 아닙니다. 개발자 문서는 기본값을 720p로 두고, 360p, 1080p, 4K를 선택할 수 있다고 설명합니다. 모델 페이지도 출력 비디오가 3~10초, 24 FPS 범위에서 360p부터 4K까지 가능하다고 적습니다. 1080p와 4K는 changelog 기준으로 upscaling을 사용합니다.

Google 발표문은 360p preview가 720p보다 최대 60% 빠르고 비용은 3분의 1이라고 설명합니다. 이 수치는 Google의 자체 throughput 기준이므로 독립 성능 결과로 보지는 않습니다. 그래도 API 설계상 360p 초안과 고해상도 최종본을 분리할 수 있다는 사실은 확인됩니다.

이 분리는 창작 도구에서 특히 중요합니다. 사용자는 첫 결과를 바로 최종본으로 쓰기보다 여러 방향을 빠르게 확인합니다. 개발자는 낮은 해상도 결과를 빠르게 보여 주고, 선택된 branch만 고해상도로 올리는 흐름을 만들 수 있습니다. 반대로 모든 시안을 처음부터 4K로 요청하면 비용과 대기 시간이 제품 경험을 해칠 수 있습니다.

## 모델 카드는 어려운 장면도 함께 밝힙니다

Google DeepMind의 모델 카드는 Gemini Omni Flash와 Gemini Omni 1.1 Flash를 함께 설명합니다. 입력은 text, image, audio, video이고 출력은 audio가 포함된 high-resolution video입니다. architecture는 text, vision, video, audio 입력을 native multimodal 방식으로 처리하는 transformer-based model이라고 적습니다.

모델 카드가 밝힌 한계도 기사 중심 판단에 중요합니다. Google은 편집 전반에서 완전한 consistency를 유지하는 일, 복잡한 motion이 있는 장면, 정확한 text rendering이 여전히 어렵다고 적습니다. 또 영상 편집 과정에서 사람의 speech를 바꿀 수 있는 능력은 제한하고 있으며, 안전하게 제공하는 방법을 더 파악하고 있다고 설명합니다.

따라서 이 모델을 제품에 붙일 때는 “무엇이든 영상으로 만든다”보다 “어떤 편집 실패를 사용자에게 어떻게 보여 줄 것인가”가 더 현실적인 질문입니다. 자막, 제품 로고, UI 화면처럼 텍스트 정확도가 중요한 영상은 별도 검수와 후처리가 필요합니다. 사람의 말소리나 발화 내용을 바꾸는 기능은 정책과 제품 안전 경계가 먼저 정리돼야 합니다.

## 채택 전에는 작업 경계를 먼저 재야 합니다

이번 후보의 근거 수준은 E2입니다. 출시 사실과 모델 ID는 Google AI for Developers changelog와 모델 페이지로 확인했습니다. 작동 방식은 개발자 문서의 API 예제와 모델 카드의 입력·출력·한계 설명으로 확인했습니다. 다만 영상 품질, consistency 향상, 생성 속도, 비용 절감 수치는 Google이 공개한 설명이며 이 turn에서 독립 재현하지 않았습니다.

재현성은 R1입니다. 문서에는 Python, JavaScript, REST 호출 방식과 파일 polling 절차가 공개되어 있어 실행 방법은 설명할 수 있습니다. 그러나 이 turn에서는 API key, 유료 quota, 생성 결과 파일, latency log를 확보하지 않았고 실제 비디오를 만들지 않았습니다. 공개 weight나 평가 스크립트도 제공되지 않으므로 모델 내부 동작과 품질 수치를 재현 가능한 artifact로 확인할 수는 없습니다.

실무 판단은 분명합니다. Gemini Omni 1.1 Flash는 비디오 모델을 제품 backend에 넣을 때 필요한 상태 관리와 반복 편집 기능을 공식 API로 넓혔습니다. 다만 채택 전에는 자기 서비스의 평균 클립 길이, preview 해상도, 고해상도 전환 비율, 파일 저장 정책, 저작권·초상권 검수, 실패 재시도 비용을 작은 pilot에서 먼저 재야 합니다.

## 이해상충과 취재 조건

Google DeepMind와 Google AI for Developers는 Gemini Omni 1.1 Flash의 개발·제공 주체이며, 이번 기사에서 사용한 발표문, changelog, 모델 카드, 개발자 문서를 작성·운영합니다. 성능과 품질 개선 표현은 발표 주체의 주장으로 다루고, 중심 결론은 공개 문서가 서로 확인하는 모델 ID, API 기능, 입력·출력, 한계, deprecation 일정에 제한했습니다.

사전 briefing, 제공받은 account·credit·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 2차 요약은 후보 발견에만 사용했고, 기사 사실은 열린 공식 발표문, Gemini API changelog, 모델 카드, 모델 페이지, 개발자 문서로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Google은 2026년 8월 27일 `gemini-omni-1.1-flash`를 Gemini API의 정식 모델로 출시했고, preview endpoint인 `gemini-omni-flash-preview`는 2026년 9월 30일 deprecated될 예정입니다. | E2 · P1 | Gemini API changelog와 모델 페이지로 확인했습니다. 실제 계정별 availability는 확인하지 않았습니다. |
| C2. `gemini-omni-1.1-flash`는 video extension, first-and-last-frame interpolation, `360p`, `720p`, `1080p`, `4k` resolution control을 지원합니다. | E2 · P1 | Gemini API changelog와 Omni 개발자 문서로 확인했습니다. 1080p와 4K는 upscaling 기반입니다. |
| C3. Omni 개발자 문서는 `Interactions API`를 통해 text-to-video, image-to-video, video editing, URI delivery, File API polling 흐름을 제공합니다. | E2 · P1 | Google AI for Developers 문서의 Python, JavaScript, REST 예제로 확인했습니다. 편집국은 API를 실행하지 않았습니다. |
| C4. 모델 페이지는 `gemini-omni-1.1-flash`의 입력을 text, image, 최대 10초 video로, 출력을 3~10초 video와 24 FPS로 설명합니다. | E2 · P1 | Gemini API 모델 페이지로 확인했습니다. audio 입력 지원 범위는 모델 카드와 문서 표면에서 다르게 표현될 수 있어 기사에서는 제품 설계상 핵심인 text·image·video 중심으로 설명했습니다. |
| C5. 모델 카드는 Gemini Omni Flash가 text, image, audio, video data로 학습됐고, native multimodal transformer architecture를 사용한다고 설명합니다. | E2 · P1 | Google DeepMind 모델 카드로 확인했습니다. 학습 데이터 원본, 학습 로그, model weight는 공개되지 않았습니다. |
| C6. 모델 카드는 consistency, complex motion, accurate text rendering이 여전히 어려우며, 사람의 speech를 바꾸는 능력은 현재 제한한다고 적습니다. | E2 · P1 | Google DeepMind 모델 카드의 known limitations와 safety 설명으로 확인했습니다. 제한 정책의 세부 enforcement 방식은 공개 문서만으로 재현할 수 없습니다. |
| C7. 360p preview가 최대 60% 빠르고 720p 비용의 3분의 1이라는 수치는 Google 발표문에 있는 자체 throughput 기준입니다. | E1 · P0 | 발표문으로 확인했지만 독립 benchmark가 아니므로 기사 중심 결론이나 순위 판단에 사용하지 않았습니다. |

## 출처

1. Google, `Gemini Omni 1.1 Flash lets you build with more control`: https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-omni-1-1-flash/
2. Google AI for Developers, Gemini API release notes: https://ai.google.dev/gemini-api/docs/changelog
3. Google DeepMind, `Gemini Omni Flash` model card: https://deepmind.google/models/model-cards/gemini-omni-flash/
4. Google AI for Developers, `Gemini Omni Flash` model page: https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash
5. Google AI for Developers, `Generate and edit videos with Gemini Omni Flash`: https://ai.google.dev/gemini-api/docs/omni
