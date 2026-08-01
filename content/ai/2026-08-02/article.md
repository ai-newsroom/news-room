---
edition: ai
decision: publish-candidate
title: "OpenAI provenance API: C2PA·SynthID를 동기식으로 검사합니다"
date: 2026-08-02
subject: "OpenAI Content Provenance API and Python 2.52.0, Go 3.49.0, Ruby 0.75.0 SDK support"
summary: "OpenAI Content Provenance API는 이미지의 C2PA·SynthID와 오디오의 SynthID를 한 요청에서 검사합니다. Python 2.52.0, Go 3.49.0, Ruby 0.75.0부터 공식 SDK가 지원하지만, `not_detected`는 사람 작성 증명이나 범용 AI 판정이 아니며 이 API는 Zero Data Retention 대상이 아닙니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["OpenAI는 API, verifier와 SDK를 제공하고 동작 범위를 설명하는 주체입니다. 이 기사에는 사전 접근, 제공받은 account·credit, 후원, 광고, NDA 또는 embargo가 없었습니다."]
---

OpenAI의 Content Provenance API 공개가 SW 엔지니어에게 중요한 이유는 이미지나 오디오의 출처 신호를 수작업 웹 도구가 아니라 moderation, 게시 승인, fact-checking과 trust and safety pipeline에서 호출할 수 있게 됐기 때문입니다. 새 endpoint는 파일 하나를 받아 지원하는 C2PA Content Credentials와 SynthID watermark 결과를 같은 응답으로 돌려줍니다. 다만 이 결과는 파일의 진실성, 모든 AI 생성 여부, prompt나 작성자를 판정하지 않습니다.

## 세 줄 요약

- `POST /v1/content_provenance_checks`는 동기식 multipart 요청 하나로 검사를 끝내며, 별도 Files API upload나 background job polling이 필요하지 않습니다.
- 이미지 응답에는 C2PA와 SynthID 항목이, 오디오 응답에는 SynthID 항목이 들어가며 각 항목을 독립적으로 읽어야 합니다.
- `detected`는 지원하는 OpenAI 신호의 발견이고 `not_detected`는 신호를 찾지 못했다는 뜻일 뿐, 사람이 만들었다거나 다른 AI가 만들지 않았다는 증명이 아닙니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 공식 guide와 API schema, Python 2.52.0·Go 3.49.0·Ruby 0.75.0의 고정 tag와 공개 source에서 endpoint, multipart 입력, 결과 union type과 최소 SDK version을 확인할 수 있습니다.
- **도입 전에 확인할 것:** 조직의 endpoint access, `429` 처리, `Retry-After`, 50 MiB 파일 상한, 오디오 60초 상한, 원본 보존 정책과 Zero Data Retention 제외를 architecture와 privacy review에 반영해야 합니다.
- **아직 결론 내릴 수 없는 것:** 변환·crop·compression 뒤 signal 검출률, false positive와 false negative 분포, 지역별 availability, 실제 rate limit, latency와 비용은 공개 문서와 source inspection만으로 판단할 수 없습니다.

## 이 공개의 의의와 편집 판단

OpenAI 공식 guide는 Content Provenance API를 content review, fact-checking, labeling과 trust and safety workflow에 연결할 수 있다고 설명합니다. 7월 31일 공개된 Python 2.52.0, Go 3.49.0과 Ruby 0.75.0 release는 모두 같은 content provenance resource를 SDK에 추가했습니다. Python tag는 commit `ca693fbaa20a620ce53a48f4419a1a01444564e7`, Go tag는 `f0e6bff60a2c883de7a8cbc5492d763625f84b61`, Ruby tag는 `692e6c7cab56554e470fe414bcdd23ae7416d205`를 가리킵니다.

**편집 판단:** 이 공개의 핵심은 AI detector 하나가 더 생겼다는 데 있지 않습니다. provenance를 하나의 참·거짓 label로 압축하지 않고 C2PA manifest 상태와 SynthID watermark 결과를 분리한 API contract가 생겼다는 점이 중요합니다. 운영팀은 이를 자동 차단기의 단독 판정값으로 쓰기보다, 원본 파일과 issuer를 보존하고 사람이 검토할 queue의 근거 하나로 사용하는 편이 타당합니다.

## 파일 하나를 보내면 완료된 결과가 같은 응답으로 돌아옵니다

요청은 `file` field 하나를 가진 multipart form입니다. 공식 문서의 Python 예제는 `OpenAI()` client에서 `client.content_provenance_checks.create(file=...)`를 호출합니다. Python SDK source는 이 호출을 bearer authentication이 필요한 `/content_provenance_checks` POST로 보내며, 동기·비동기 client와 raw·streaming response wrapper를 함께 제공합니다.

API는 검사를 완료한 뒤 응답합니다. Files API에 먼저 올리거나 job ID를 받아 polling하는 구조가 아닙니다. 이 차이는 구현을 단순하게 만들지만, upload와 검증 시간이 caller의 request deadline 안에 들어와야 한다는 뜻이기도 합니다. 큰 media file을 web request thread에서 바로 처리할지, 별도 worker가 원본을 받아 제한된 concurrency로 호출할지는 application이 결정해야 합니다.

문서가 제시하는 지원 형식은 이미지 PNG·JPEG·WebP와 오디오 MP3·Opus·AAC·FLAC·WAV·PCM입니다. 파일당 50 MiB를 넘길 수 없고, 오디오는 decode 뒤 60초 이하여야 합니다. 한 요청에는 파일 하나만 보내며 media type을 multipart의 file part에 붙입니다.

## top-level 판정 대신 신호별 결과를 읽어야 합니다

응답 object는 `content_provenance_check`이고 `created_at`과 `results` 배열을 가집니다. 이미지에는 C2PA와 SynthID result가 들어가고 오디오에는 SynthID result가 들어갑니다. 적용되지 않는 검사는 `not_detected`로 채우는 대신 배열에서 생략하므로, client가 항상 두 항목을 가정하면 안 됩니다.

C2PA result에는 `outcome`, `validation_state`, `issuer`, `model`, `generated_at`이 있습니다. `validation_state`는 `trusted`, `valid`, `invalid`, `not_present` 가운데 하나입니다. 공식 문서에서 C2PA의 `detected`는 trusted 또는 valid manifest가 OpenAI를 issuer로 식별하고 AI-generation action을 포함할 때만 나옵니다.

세부 field는 top-level outcome보다 많은 정보를 줄 수 있습니다. 제3자 manifest, AI-generation action이 없는 manifest, invalid manifest 또는 manifest가 없는 파일은 C2PA `not_detected`가 될 수 있습니다. 그 경우에도 issuer와 validation state가 남을 수 있으므로, 단순히 `outcome == "not_detected"`만 보고 manifest가 없다고 결론 내리면 안 됩니다.

SynthID result에는 `detected` 또는 `not_detected`와 선택적인 model·generated time이 있습니다. watermark가 검출됐다는 사실은 지원하는 신호가 있다는 뜻이며, 이후 파일이 어떤 맥락에서 사용됐는지나 내용이 정확한지는 말해 주지 않습니다. `model`과 `generated_at`은 `null`일 수 있으므로 schema validation과 observability field도 optional로 다뤄야 합니다.

## 음성·이미지 provenance와 범용 AI 탐지는 다른 문제입니다

C2PA는 signed metadata이므로 편집, format 변환이나 공유 과정에서 제거될 수 있습니다. SynthID는 media 안에 들어가는 watermark이지만 crop, filter와 lossy compression 같은 변환 뒤 검출 가능성이 항상 유지된다고 공개 문서가 보증하지는 않습니다. OpenAI는 원본 파일을 가능하면 검사하고, image crop이나 format 변환을 피하며, audio는 10초에서 60초 clip을 권장합니다.

`not_detected`의 의미는 더 좁습니다. metadata가 제거되거나 tamper evidence가 있거나 watermark가 약해졌거나, legacy generation model 또는 신호 지원 전의 산출물이라면 OpenAI 생성물도 검출되지 않을 수 있습니다. 다른 회사의 AI가 만든 content는 현재 이 API의 탐지 대상이 아닙니다.

따라서 moderation rule은 세 상태 이상으로 설계하는 편이 안전합니다. 지원 신호가 검출된 경우, 적용 가능한 신호가 있지만 검출되지 않은 경우, 파일 오류나 endpoint access·rate limit 때문에 검사를 완료하지 못한 경우를 분리해야 합니다. C2PA가 invalid인 경우도 검출 실패와 같은 정상 음성 결과로 덮지 말고 별도의 manual review reason으로 남겨야 합니다.

## SDK version과 결과 schema를 함께 고정해야 합니다

공식 guide는 Python 2.52.0, Go 3.49.0, Ruby 0.75.0 이상을 요구합니다. 세 release는 모두 7월 31일 공개됐고 각 tag는 lightweight commit object로 해석됩니다. Python의 기능 commit `1d6c1180f8eaa71bfd45cae67360987b2bea3656`은 resource, request parameter, discriminated union response type과 generated API test를 추가했습니다.

Python response type은 `type` discriminator로 C2PA와 SynthID를 구분합니다. C2PA에만 `validation_state`와 `issuer`가 있고, 두 result 모두 optional `model`과 `generated_at`을 가집니다. 이 차이를 무시하고 공통 dict로 평탄화하면 invalid manifest와 watermark 부재를 같은 이유로 저장하게 됩니다.

SDK update에는 별개의 retry 변화도 있습니다. Python 2.52.0 release note는 client가 최대 2분의 `Retry-After`를 존중하도록 고쳤다고 기록합니다. provenance endpoint 문서도 `429 rate_limit_exceeded`에서 `Retry-After`를 따르라고 안내하므로, application의 전체 timeout이 2분보다 짧다면 SDK의 sleep에만 맡기지 말고 job deadline과 retry budget을 명시해야 합니다.

## privacy와 access 실패를 정상 음성 결과와 분리해야 합니다

공개 browser verifier는 업로드한 파일을 OpenAI 신호 검사에 처리하며, 법적으로 필요한 경우가 아니면 저장하지 않고 model training에 사용하지 않는다고 설명합니다. API에는 별도의 data-control 경계가 있습니다. 공식 API guide는 content provenance check가 Zero Data Retention 대상이 아니라고 명시합니다.

Zero Data Retention을 필수로 전제한 pipeline이라면 endpoint가 기술적으로 호출된다는 사실만으로 도입하면 안 됩니다. 원본 media가 어떤 지역과 account를 거쳐 전송되는지, 자체 object store의 retention과 audit log에는 무엇을 남길지, API response의 issuer·model·timestamp가 개인정보나 조사 기록으로 취급되는지를 검토해야 합니다.

오류도 provenance 판정과 분리해야 합니다. 문서는 malformed, unsupported 또는 blocked file에는 `400`, endpoint access가 없는 organization에는 `404`, rate limit에는 `429`가 올 수 있다고 설명합니다. 이 상태를 모두 `not_detected`로 변환하면 검사를 수행하지 못한 파일을 신호가 없는 파일로 잘못 승인할 수 있습니다.

## 도입 canary는 원본·변환본과 fail-closed 경계를 함께 봐야 합니다

첫 canary는 production content가 아닌 합성 fixture로 구성합니다. C2PA manifest가 trusted 또는 valid인 지원 OpenAI image, C2PA가 없는 image, invalid manifest image와 지원 audio fixture를 나눕니다. 실제 OpenAI 산출물을 fixture로 사용할 때는 생성 model, 시각과 원본 hash를 같이 고정해야 합니다.

각 원본에서 format 변환, crop, screenshot, compression과 audio transcoding을 별도 파생물로 만듭니다. 목적은 검출률을 미리 가정하는 것이 아니라 어떤 변환에서 signal이 사라지는지 자체 publishing path를 기준으로 측정하는 것입니다. 변환본의 결과는 원본 provenance를 대체하지 않으므로 두 hash와 transformation log를 함께 보존해야 합니다.

client contract test는 결과 배열의 순서와 길이를 고정하지 않고 `type`으로 분기해야 합니다. `issuer`, `model`, `generated_at`이 없는 경우와 C2PA `invalid`를 fixture에 포함합니다. `400`, `404`, `429`, timeout과 server error가 application의 `unknown` 또는 review queue로 가고 `not_detected`로 합쳐지지 않는지도 확인해야 합니다.

마지막으로 retry와 비용을 관찰합니다. 요청 수, media type, byte size, duration, status, retry count와 latency를 기록하되 원본 media나 credential을 application log에 복제하지 않습니다. 실제 rate limit과 가격을 문서에서 확인하지 못했으므로 canary 결과 없이 throughput capacity나 월 비용을 계산하지 않습니다.

## 공개 artifact로 확인할 수 있는 최소 절차

아래 절차는 API key 없이 SDK interface와 tag identity를 검사합니다. endpoint의 runtime 결과를 재현하는 절차는 아니며, 실제 호출 전에는 조직 access와 data policy를 별도로 확인해야 합니다.

```bash
git ls-remote https://github.com/openai/openai-python.git refs/tags/v2.52.0
git ls-remote https://github.com/openai/openai-go.git refs/tags/v3.49.0
git ls-remote https://github.com/openai/openai-ruby.git refs/tags/v0.75.0

curl -fsSL https://developers.openai.com/api/docs/guides/content-provenance.md \
  | shasum -a 256
```

2026년 8월 2일 확인한 guide Markdown의 SHA-256은 `368645d44bb8c2a7c28d5b1c40efe236db635bdead823787c900ed18bde2a204`입니다. 공식 문서는 갱신될 수 있으므로 이 hash는 문서 정본을 영구 고정하는 값이 아니라 이번 판단이 읽은 snapshot을 식별하는 값입니다. SDK tag commit과 release URL은 별도로 고정해야 합니다.

실제 API canary는 공식 guide의 multipart 호출을 사용하되 production 원본과 분리된 fixture 하나부터 시작해야 합니다. 편집국은 인증된 endpoint를 호출하거나 detector 결과를 측정하지 않았습니다. 따라서 이 기사는 API contract와 공개 구현의 존재를 E2로 다루지만 검출 정확도, latency, access 범위나 비용을 재현했다고 주장하지 않습니다.

## 적용 범위와 확인하지 못한 것

이번 검증은 OpenAI의 공개 API guide, 공개 browser verifier 설명, Python·Go·Ruby SDK release와 고정 source에 한정합니다. browser verifier page는 browser surface에서 열렸지만 command-line HTTP 요청은 bot protection으로 `403`을 받았고, 파일을 upload해 결과를 만들지는 않았습니다.

인증된 Content Provenance API도 호출하지 않았습니다. 조직별 access, 실제 error body, rate limit, latency, 가격, regional processing과 data retention 세부값은 확인하지 못했습니다. SDK generated test는 request surface와 response type을 검사하지만 production verifier의 detection quality를 시험하지 않습니다.

C2PA와 SynthID의 공개 원리와 OpenAI endpoint가 보고하는 field는 확인했지만, 변환 강건성이나 false positive 비율을 독립 실험으로 검증하지 않았습니다. OpenAI는 detected signal의 false positive가 드물다고 설명하지만, 독립 benchmark가 없어 이를 편집국의 정량 결론으로 승격하지 않습니다.

이 API는 지원하는 OpenAI provenance signal 검사기입니다. 범용 AI detector, deepfake 판별기, 사실 검증기, 저작권 판정기, 생성 prompt 복원기 또는 개인 식별 도구가 아닙니다. high-stakes workflow에서는 결과 하나로 자동 제재하지 않고 원본·맥락·다른 근거와 사람 검토를 함께 사용해야 합니다.

## 이해상충과 취재 조건

OpenAI는 검사 대상 신호를 발행하는 제품 주체이면서 verifier, API와 세 SDK를 제공하고 동작 범위를 설명하는 주체입니다. 공식 guide와 code는 endpoint contract, version과 공개 implementation의 1차 근거이지만 false positive·false negative, availability와 운영 비용의 독립 검증은 아닙니다.

이 기사에는 OpenAI, C2PA 또는 Google DeepMind의 사전 briefing, 제공받은 API account·credit, media fixture, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 문서, 공개 browser surface와 GitHub release·source만 사용했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. OpenAI는 file 하나를 동기식으로 검사하는 `POST /v1/content_provenance_checks`와 Python 2.52.0·Go 3.49.0·Ruby 0.75.0 SDK 지원을 공개했습니다. | E2 · P1/P2 · R2 | 공식 guide, 세 release와 exact tag commit을 대조했습니다. 인증된 production endpoint는 호출하지 않았습니다. |
| C2. image result는 C2PA와 SynthID, audio result는 SynthID를 포함하며 top-level outcome 없이 신호별 result를 독립적으로 해석합니다. | E2 · P1/P2 · R2 | 공식 schema와 Python discriminated union type을 확인했습니다. 실제 media의 결과와 배열 순서는 측정하지 않았습니다. |
| C3. `not_detected`는 지원 신호 부재의 증거일 뿐 사람 작성이나 다른 AI 미사용의 증명이 아닙니다. | E2 · P1/P2 · R1 | 공식 guide와 verifier 설명이 같은 제한을 명시합니다. 독립 false-negative benchmark는 확인하지 못했습니다. |
| C4. 지원 파일은 50 MiB 이하이고 audio는 60초 이하이며, API는 Zero Data Retention 대상이 아닙니다. | E2 · P1 · R1 | 공식 API guide의 availability·data-control 경계를 확인했습니다. 지역별 처리와 실제 retention 기간은 공개 문서에서 확인하지 못했습니다. |
| C5. Python 2.52.0 source는 multipart resource와 C2PA·SynthID response type, generated API test를 포함합니다. | E2 · P2 · R2 | 기능 commit과 release tag의 source·test를 확인했습니다. Test는 mock API surface를 검증하며 production detector 정확도를 검증하지 않습니다. |

## 출처

1. OpenAI Content Provenance API guide: https://developers.openai.com/api/docs/guides/content-provenance
2. OpenAI 공개 content verifier: https://openai.com/research/verify/
3. OpenAI Python SDK 2.52.0 release: https://github.com/openai/openai-python/releases/tag/v2.52.0
4. Python SDK content provenance 기능 commit `1d6c1180f8eaa71bfd45cae67360987b2bea3656`: https://github.com/openai/openai-python/commit/1d6c1180f8eaa71bfd45cae67360987b2bea3656
5. Python SDK response type at tag commit `ca693fbaa20a620ce53a48f4419a1a01444564e7`: https://github.com/openai/openai-python/blob/ca693fbaa20a620ce53a48f4419a1a01444564e7/src/openai/types/content_provenance_check.py
6. OpenAI Go SDK 3.49.0 release: https://github.com/openai/openai-go/releases/tag/v3.49.0
7. OpenAI Ruby SDK 0.75.0 release: https://github.com/openai/openai-ruby/releases/tag/v0.75.0
