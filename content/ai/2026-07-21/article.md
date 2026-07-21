---
edition: ai
decision: publish-candidate
title: "NVIDIA Cosmos 3 Edge 4B 공개: 엣지 실행은 확인됐지만 성능 우월성은 아직 벤더 측정이다"
date: 2026-07-21
subject: "NVIDIA Cosmos 3 Edge 4B"
summary: "NVIDIA가 4B 매개변수의 MoT 기반 물리 AI 모델과 DROID 정책 체크포인트를 공개했다. 가중치·코드·측정 조건은 확인할 수 있지만 VANTAGE·RoboLab·15Hz·throughput 결과는 아직 NVIDIA 측정이며 독립 재현이 없다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["핵심 모델, 기술 보고서, 코드와 성능표의 제공·측정 주체가 모두 NVIDIA다."]
---

NVIDIA가 7월 20일 내놓은 Cosmos 3 Edge의 핵심은 거대한 물리 AI 모델을 4B 크기로 줄였다는 데 그치지 않는다. 가중치와 실행 코드, DROID 로봇 정책 경로, Jetson 조건표가 함께 공개돼 개발자와 연구자가 이제 자기 장비에서 검증을 시작할 수 있다. 다만 “가장 뛰어나다”거나 “15Hz로 동작한다”는 성능 결론은 아직 NVIDIA가 정한 조건과 측정 안에 있다.

## 세 줄 요약

- NVIDIA와 Hugging Face는 2026년 7월 20일 `Cosmos3-Edge`와 DROID 로봇용 `Cosmos3-Edge-Policy-DROID`를 공개했다. 두 모델은 각각 4B 매개변수이며, 공개 가중치와 관련 코드는 OpenMDW-1.1 조건으로 제공된다.
- 자동회귀 Reasoner와 확산 Generator를 하나의 Mixture-of-Transformers(MoT)에 넣어 텍스트·이미지·비디오·액션을 다루게 한 것이 구조상의 변화다. Edge 카드의 상세 표는 두 경로의 입출력을 나눠 적으며, 오디오는 Edge 입출력 목록에 없다.
- VANTAGE 1위, RoboLab 정책 성능, 15Hz 제어, 높은 throughput은 NVIDIA 측정이다. 서로 다른 조건의 표를 합쳐 전체 성능 우월성으로 읽을 수 없고, 제3자의 독립 재현도 아직 확인되지 않았다.

## 무엇이 바뀌었나: 4B Edge가 실제 배포 대상이 됐다

Cosmos 3의 Nano 16B와 Super 64B는 5월 말 먼저 공개됐다. 당시 기술 보고서 arXiv v1에서 Edge는 “추후 공개” 대상이었다. 이번 공개로 4B Edge 가중치와 기본 추론 예제, DROID 데이터로 후학습한 4B 로봇 정책 체크포인트, 정책 실행·후학습 경로가 실제 배포 대상에 들어왔다.

이 기사에서 확인하는 범위는 `Cosmos3-Edge`, `Cosmos3-Edge-Policy-DROID`, NVIDIA Cosmos 코드와 문서다. Nano나 Super 같은 다른 Cosmos 3 변형의 결과를 Edge 성능으로 가져오지 않는다.

## 4B MoT는 어떻게 동작하나

Edge는 전체 4B 매개변수의 Mixture-of-Transformers(MoT)다. 기술 보고서 v4에 따르면 2B dense transformer 설계를 바탕으로 28개 층, hidden dimension 2,048, attention head 16개, key-value head 8개, head dimension 128, FFN dimension 9,216을 사용한다.

입력에서 출력까지는 두 경로가 역할을 나눠 맡는다.

1. 자동회귀 tower인 Reasoner는 텍스트와 시각 토큰을 받고, 다음 토큰을 예측하는 방식으로 이해·추론 결과를 텍스트로 만든다.
2. 확산 transformer tower인 Generator는 이미지·비디오·액션 같은 연속 신호를 반복적으로 노이즈 제거(denoising)해 생성한다.
3. 두 tower는 normalization과 MLP 매개변수를 따로 두되 multimodal attention은 공유한다. “4B MoT”는 별도의 4B 모델 두 개를 차례로 실행한다는 뜻이 아니다.

모델 카드의 버전 요약은 Edge 전체의 입출력을 텍스트·이미지·비디오·액션으로 묶는다. 상세 표에서는 Reasoner 입력을 텍스트, 텍스트+이미지, 텍스트+비디오로 적고 출력은 텍스트로 한정한다. Generator 입력은 텍스트·이미지·액션 궤적, 출력은 이미지·비디오·액션·텍스트다.

공개 코드 문서는 별도로 `text + video` 입력과 5프레임 비디오 조건 생성 경로를 제공한다. “Edge가 비디오 입력을 지원한다”는 범위는 확인되지만, 이를 Generator 입력 표에 직접 적힌 항목이라고 설명하면 안 된다. 오디오는 Cosmos 3 계열 설명에는 등장해도 Edge 카드의 입출력 목록에는 없다.

입력 이미지는 256p 또는 480p이고, 생성 비디오는 요청별로 256p 또는 480p, 12~30fps, 50~150프레임 범위를 지정한다. 액션 입력에는 여러 embodiment 형식이 적혀 있지만 공개 Policy-DROID 체크포인트의 대상은 DROID 로봇의 8차원 액션이다. 곧바로 임의의 로봇을 제어하는 범용 정책으로 보면 공개 범위를 넘는다.

## 공개 범위와 직접 써볼 때의 판단

공개일과 출시 범위는 7월 20일 Hugging Face 발표문과 NVIDIA 모델 카드가 일치한다. 확인한 카드 revision은 Edge `6f58f6b4c91288838e60b6bcb2cc45d997e961de`, Policy-DROID `3ea407af3e156c0af3b4bb6edd85842cc9a58777`다. 구조와 학습 설명은 arXiv `2606.02800` v4(2026-06-23)와 카드가 맞물린다.

코드 쪽에서는 공개 시점을 더 세밀하게 나눠 봐야 한다. Edge 지원이 처음 나타난 고정 revision은 2026년 7월 20일 16:07:51 UTC의 `0334b6f3da2b8519e9c832175c16fd46d32d6f2a`다. 바로 전 부모 `703afe0c770997416db50895f82a547b7b2e5b65`의 README에는 `Cosmos3-Edge`가 없다.

이 commit에서 `README.md`, `inference_benchmarks.md`, `cookbooks/cosmos3/generator/action/run_policy_with_cosmos_framework.md`가 갱신됐고, Edge용 `launch_sft_vision_edge.sh`와 `launch_sft_videophy2_edge.sh` 등이 추가됐다. 2026년 7월 21일 조회 시점의 `main` HEAD는 다음 commit인 `b01cefc00920e8ecb319f15e20ce1eb8850e41ec`다. 이 commit은 Cosmos Framework Edge 예제의 480p·121프레임·24fps sampling 조건을 교정했다.

별도의 Edge GitHub Release 태그는 없었다. 따라서 최초 공개 revision과 조회 시점 `main`을 구분한다. Edge가 없던 7월 7일 `d80caad6cbc1cae8b0f15ee2f10849bbf80162d2`도 Edge 코드의 근거로 사용하지 않는다.

모델 가중치·카드와 Cosmos 저장소에는 OpenMDW-1.1이 표시돼 있다. 이 라이선스는 제공된 model materials의 사용·수정·재배포를 허용하지만, 재배포할 때 라이선스와 적용되는 저작권·출처 고지를 보존해야 한다. 제3자 권리 확인 책임과 무보증 조건은 이용자에게 남는다.

“공개 가중치”가 학습 데이터 원본 전체 공개를 뜻하지는 않는다. 모델 카드는 NVIDIA 소유 데이터와 공개 데이터를 함께 썼다고 밝힌다. 로컬 평가를 시작할 자료는 갖춰졌지만 데이터 provenance 전체를 감사할 수 있는 상태는 아니다.

근거 상한은 E2다. 모델 카드·기술 보고서(P1)와 공개 가중치·실행 코드(P2)가 연결돼 무엇이 공개됐고 어떤 인터페이스를 갖는지는 교차 확인할 수 있다. 반면 이 기사에서는 가중치를 내려받거나 GPU 추론을 실행하지 않았고, 같은 조건을 재현한 독립 기관의 기록도 찾지 못했다.

직접 평가한다면 먼저 같은 입력·seed·precision·runtime을 고정해야 한다. 평균 속도만 볼 것이 아니라 peak memory, 열이 오른 뒤의 지속 성능, tail latency, 정책 실패율과 안전 제약을 함께 기록해야 실제 엣지 배치 판단에 쓸 수 있다.

## benchmark를 어디까지 믿을 수 있나

### VANTAGE 1위는 아직 벤더 주장이다

NVIDIA는 Cosmos 3 Edge가 비슷한 4B 모델 중 VANTAGE-Bench 1위이며 로봇 정책 학습에서도 최고 수준이라고 주장한다. VANTAGE는 고정 카메라 영상의 event verification, VQA, pointing, localization, tracking 등 여러 하위 과제를 묶는다.

하지만 “비슷한 크기” 비교군을 어떻게 골랐는지, 종합 점수를 어떻게 합쳤는지, 제3자 제출도 같은 방식으로 검증했는지는 독립 확인하지 못했다. 판정은 `VENDOR_CLAIM_ONLY`다. 일반적인 시각 추론 1위로 확대하지 않는다.

### RoboLab의 39.7%는 Edge 4B 수치가 아니다

Edge 모델 카드는 DROID로 후학습한 정책의 RoboLab 성공률 그래프와 재현 명령을 연결한다. 다만 기술 보고서 v4 본문의 특정 지시 39.7%, 120개 과제·과제당 10회 rollout 결과는 **16B Cosmos3-Nano-Policy-DROID**의 수치다. 4B Edge 결과로 옮겨 쓸 수 없다.

Edge 정책 카드의 그래프는 별도로 기계 판독하거나 독립 실행하지 않았다. 그래서 이 기사에서는 Edge RoboLab 숫자를 인용하지 않는다.

### 15Hz는 T5000의 특정 action-chunk 조건이다

발표문은 640×360 관측과 추론당 32개 액션으로 Jetson Thor에서 15Hz 제어가 가능하다고 요약한다. 더 상세한 Policy-DROID 카드의 PyTorch loopback 표는 한 번에 한 요청을 지속 연결로 보내고, 640×540 관측을 544×736 처리 bucket으로 바꾼 조건을 적는다. 액션 chunk는 `[32, 8]`, UniPC는 4단계, guidance는 3.0, `conditioning_fps=15`다. 32개 액션을 15Hz로 소비할 수 있는 시간 예산은 2.133초다.

NVIDIA 측정에서 이 예산을 만족한 장치는 Jetson AGX Thor T5000 128GB, MAXN, 1,575MHz다. median end-to-end latency는 1.528초였고, 16회 timed request의 범위는 1.503~1.673초, 15Hz real-time factor는 1.40이었다. 같은 표의 T4000, T3000, T2000은 15Hz 예산을 충족하지 못했다.

발표문의 640×360과 상세 표의 640×540→544×736는 서로 다르다. 두 문구가 같은 측정을 가리킨다고 단정할 수 없다. 여기서 15Hz는 카메라 영상 생성 fps가 아니라 action chunk 소비 기준의 제어율이다.

### throughput은 runtime·해상도·동시성을 떼어 봐야 한다

기본 Edge 카드의 Performance Benchmark Reporting은 모든 Generator 측정을 단일 GPU 또는 단일 통합 플랫폼, batch size 1에서 했다고 명시한다. vLLM-Omni 기준 Jetson AGX Thor T5000 128GB MAXN은 832×480, 189프레임 image-to-video 생성에 137.50초, DROID `[16, 8]` 조건의 forward dynamics에 6.05초, inverse dynamics에 7.19초, Policy DROID에 6.32초를 기록했다고 NVIDIA가 보고했다.

T3000 32GB, 1,100MHz는 같은 열에서 각각 194.76초, 8.67초, 10.25초, 8.63초다. T2000의 image-to-video 101.20초는 448×256 warm run이라 480p 계열과 직접 비교하면 안 된다.

Reasoner의 엣지 수치는 raw Transformers eager mode의 예비 측정이다. T5000 128GB MAXN에서 텍스트 1,705-token 입력은 prefill 8,717 tok/s·decode 37.3 tok/s·E2E 3.60초, 이미지 911-token 입력은 4,845 tok/s·42.6 tok/s·3.17초, 비디오 1,263-token 입력은 6,032 tok/s·41.8 tok/s·3.25초라고 NVIDIA가 적었다. 데이터센터 vLLM serving 표와는 runtime·workload·metric이 달라 직접 비교할 수 없다.

“높은 throughput”도 조건부다. 단일 RTX PRO 6000에서 50 input/100 output/1 video-fps workload의 vLLM serving은 client concurrency 1에서 1.98 req/s, 64에서 10.27 req/s였다. 요청 지연은 각각 503.44ms와 6,188.90ms로 늘었다. 총 처리량과 단일 요청 지연을 분리해서 봐야 하며, 이 값들은 모두 독립 재현이 없는 NVIDIA 측정이다.

## 어디에 쓸 수 있고, 무엇이 아직 미확인인가

가장 직접적인 적용 후보는 단일 GPU나 Jetson Thor급 장치에서 시각 이해, 짧은 영상 예측, forward/inverse dynamics, DROID 계열 정책을 연구하려는 팀이다. 가중치·예제·라이선스가 함께 있어 로컬 평가의 출발점은 마련됐다. 다만 공개 자료만으로 다음까지 확인된 것은 아니다.

- VANTAGE 비교군과 종합 점수 산정이 다른 제출에도 같은 방식으로 적용됐는지, Edge 결과가 독립 기관에서 재현됐는지 확인하지 못했다.
- 4B Edge-Policy-DROID의 정확한 RoboLab 수치와 반복 분산을 텍스트 근거로 확인하지 못했다. 보고서의 39.7%는 Nano 16B 결과다.
- 15Hz 홍보 문구의 640×360과 상세 정책 카드의 640×540→544×736가 왜 다른지 설명이 없다.
- 학습 corpus는 집계 수준으로만 공개됐고 NVIDIA 소유 데이터가 포함된다. 데이터별 provenance, 라이선스, 중복 제거 결과 전체를 감사할 수 없다.
- 모델 카드는 Linux와 BF16만 테스트했다고 밝힌다. FP4·FP8·FP16, 다른 운영체제, 비 NVIDIA 가속기에서의 작동과 품질은 확인되지 않았다.
- 모델 카드가 경고한 장시간·고해상도의 temporal inconsistency, 불안정한 물체·카메라 움직임, 부정확한 물리 상호작용, action-state drift가 남아 있다. 물리 simulator나 안전 인증된 제어기로 취급할 수 없다.

## 기술 판단: 공개 artifact는 가치가 있지만 우월성은 미확인이다

이번 공개의 검증 가능한 가치는 “물리 AI 전반의 최고 성능”이 아니다. 4B MoT 가중치와 코드, DROID 정책 경로, 장치별 조건표가 한꺼번에 열렸다는 점이다. 후속 검증을 설계할 만한 정보가 충분하고 주장별 한계를 구분할 수 있으므로 판정은 `publish-candidate`다.

성능 우월성은 E3 독립 근거가 생길 때까지 확정하지 않는다. 재검토 계기는 고정 revision의 독립 VANTAGE/RoboLab 결과, 동일 Jetson 조건의 공개 실행 로그, 640×360과 상세 표 해상도 차이에 대한 정정, 모델 카드·라이선스 변경이다. `nvidia/cosmos`가 별도 Edge release tag를 내거나 조회 시점 `main` 이후 관련 경로를 바꾸는 경우도 다시 확인한다.

## 이해상충과 취재 조건

NVIDIA는 모델·GPU·runtime을 공급하면서 기술 보고서 작성, benchmark 측정, 모델 카드 게시까지 맡았다. Hugging Face 발표문에도 NVIDIA 계정과 NVIDIA 소속 저자가 참여했다. 엣지 수치가 NVIDIA 하드웨어에 한정돼 제품 판매 이해와 분리하기 어렵다.

이 기사에는 NVIDIA나 Hugging Face의 사전 열람, 비용 지원, 장비 제공이 없었고 공개 원문만 사용했다. 실제 가중치 다운로드와 GPU 재현 실험도 수행하지 않았다.

## 근거 원장

| Claim | 판정 | 출처/근거 | 등급 | 한계·재확인 조건 |
|---|---|---|---|---|
| 2026-07-20에 4B Edge와 4B Policy-DROID가 공개됐다 | 확인 | 발표문·두 모델 카드 | P1 / E2 / R1 | 카드 revision 고정 필요, 공개 범위 변경 시 재확인 |
| Edge는 자동회귀·확산 tower를 결합한 4B MoT다 | 확인 | arXiv v4·모델 카드·발표문 | P1 / E2 / R1 | 구현 parameter audit는 하지 않음 |
| 텍스트·이미지·비디오·액션 입출력과 가중치·코드가 공개됐다 | 확인 | 모델 카드·Cosmos 저장소 | P1+P2 / E2 / R2 | 코드 최초 공개 `0334b6f`, 조회 시점 `main` `b01cefc`; 상세 카드에서 Reasoner·Generator 입력 표면이 분리됨; Edge 카드에 오디오 입출력은 없음; 학습 데이터 전체 공개 아님 |
| 비슷한 4B 중 VANTAGE 1위다 | NVIDIA 주장 | 발표문·모델 카드 benchmark 그림 | P1 / E1 / R1 | 비교군·종합 산식·독립 재현 미확인 |
| Edge 후학습 정책이 RoboLab 최고 수준이다 | NVIDIA 주장 | 발표문·Edge Policy-DROID 카드 | P1 / E1 / R1 | Edge 수치의 텍스트 원장 미확인; Nano 39.7%와 혼동 금지 |
| Jetson Thor에서 32-action policy가 15Hz를 만족한다 | 조건부 NVIDIA 측정 | 발표문·Policy-DROID PBR | P1 / E1 / R1 | T5000 한 조건만 충족; 두 문서의 입력 해상도 불일치; 독립 재현 없음 |
| Edge가 높은 생성·reasoning throughput을 낸다 | 조건부 NVIDIA 측정 | Edge PBR | P1 / E1 / R1 | 단일 플랫폼·batch 1 또는 특정 concurrency; 해상도·runtime별 직접 비교 금지 |

## 출처

1. Hugging Face·NVIDIA, “Introducing Cosmos 3 Edge”, 2026-07-20: https://huggingface.co/blog/nvidia/cosmos3edge
2. NVIDIA, `nvidia/Cosmos3-Edge` model card, revision `6f58f6b4c91288838e60b6bcb2cc45d997e961de`, 공개 2026-07-20, 조회 2026-07-21: https://huggingface.co/nvidia/Cosmos3-Edge
3. NVIDIA, `nvidia/Cosmos3-Edge-Policy-DROID` model card, revision `3ea407af3e156c0af3b4bb6edd85842cc9a58777`, 공개 2026-07-20, 조회 2026-07-21: https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID
4. NVIDIA 외, “Cosmos 3: Omnimodal World Models for Physical AI”, arXiv:2606.02800, v4 2026-06-23: https://arxiv.org/abs/2606.02800
5. NVIDIA, `nvidia/cosmos`, Edge 지원 최초 공개 commit `0334b6f3da2b8519e9c832175c16fd46d32d6f2a`, 2026-07-20 16:07:51 UTC: https://github.com/NVIDIA/cosmos/commit/0334b6f3da2b8519e9c832175c16fd46d32d6f2a
6. NVIDIA, `nvidia/cosmos`, 조회 시점 `main` HEAD `b01cefc00920e8ecb319f15e20ce1eb8850e41ec`, 2026-07-21 06:53:04 UTC: https://github.com/NVIDIA/cosmos/commit/b01cefc00920e8ecb319f15e20ce1eb8850e41ec
7. OpenMDW, “OpenMDW License Agreement, version 1.1”, 조회 2026-07-21: https://openmdw.ai/license/1-1/
