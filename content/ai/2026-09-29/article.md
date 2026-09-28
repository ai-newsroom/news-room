---
edition: ai
decision: publish-candidate
title: "Claude 생물분자 최적화 kit 공개 - 과학 모델의 GPU 병목을 줄였습니다"
date: 2026-09-29
subject: "Anthropic uplifting-biomolecular-modeling optimization kits, published 2026-09-17"
summary: "Anthropic은 Claude로 30개가 넘는 생물분자 모델의 inference 경로를 최적화했고, 그 결과를 36개 공개 kit로 배포했습니다. 공개 코드는 기존 모델 호출 방식을 크게 바꾸지 않고 `exact`, `fast`, `big` 모드로 속도와 메모리 사용량을 조절하게 해 주지만, 성능 수치는 아직 Anthropic의 자체 측정에 머뭅니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

Anthropic이 Claude로 생물분자 모델의 실행 코드를 고친 뒤, 그 결과를 공개 저장소로 냈습니다. 이번 공개의 핵심은 새 범용 모델을 내놓은 데 있지 않습니다. AlphaFold 계열 구조 예측, 단백질 설계, 유전체 모델처럼 이미 과학자가 쓰는 공개 도구의 inference 경로를 손봤다는 점이 중요합니다. 같은 입력을 더 빨리 처리하거나 더 큰 분자 시스템을 한 GPU 노드에서 돌릴 수 있게 만든 사례이기 때문입니다.

SW 엔지니어에게 이 뉴스가 의미 있는 이유는 분명합니다. 모델을 더 크게 만드는 대신 기존 모델 주변의 커널, 캐시, 실행 모드, 환경 고정을 자동으로 다듬어 비용 병목을 줄인 사례입니다. AI agent가 단순히 코드를 생성하는 데 그치지 않고, 복잡한 연구 코드의 실행 흐름을 읽어 병목을 찾은 뒤 배포 가능한 patch 묶음으로 포장했다는 점도 확인할 수 있습니다.

다만 성능 결론은 좁게 읽어야 합니다. Anthropic은 평균 약 4배 속도 개선, 동일 출력 기준 약 2배 개선, 10,000 token이 넘는 생물분자 시스템의 단일 NVIDIA GPU 노드 실행을 보고했습니다. 하지만 이 수치는 아직 Anthropic의 harness와 공개 글에 근거합니다. 제3자가 같은 hardware와 workload로 다시 잰 결과는 이 기사 작성 시점에 확인하지 못했습니다.

## 느린 부분은 모델 전체가 아니라 특정 연산이었습니다

생물분자 구조 예측 모델은 단백질이나 핵산처럼 긴 생체 분자의 3차원 구조를 추정합니다. 문제는 분자 안의 구성 요소가 서로 어떻게 맞물리는지를 계산하는 과정이 매우 비싸다는 데 있습니다. Anthropic은 현대 구조 예측 모델에서 triangle attention과 triangle multiplication이 실행 시간과 메모리의 큰 비중을 차지한다고 설명합니다.

이 두 연산은 토큰 세 개의 관계를 다룹니다. 그래서 시스템 크기가 커질수록 계산량과 메모리 요구가 빠르게 늘어납니다. Anthropic은 크기가 두 배가 되면 시간과 메모리가 8배, 세 배가 되면 27배까지 늘 수 있다고 설명했습니다. 일반적인 애플리케이션 최적화보다 GPU kernel 수준의 최적화가 필요한 이유입니다.

Anthropic은 Claude와 함께 FlashPairformer라는 custom kernel 묶음을 만들었다고 밝혔습니다. 이 kernel은 Pairformer 계열 구조 예측에서 쓰이는 triangle attention과 triangle multiplication을 빠르게 처리하도록 설계됐습니다. 원문은 NVIDIA의 cuEquivariance와 BioNeMo Inference Runtime을 분야 표준 비교 대상으로 들고, 모델 설정에 따라 triangle attention에서 평균 2.7배에서 2.9배, triangle multiplication에서 1.7배에서 3.2배 빠른 결과를 보고했습니다.

이 수치는 독립 benchmark가 아닙니다. 그래서 기사에서는 “Anthropic이 보고했다”는 범위를 넘겨 쓰지 않습니다. 그러나 어떤 병목을 겨냥했는지, 공개 코드가 어떤 실행 구조로 묶였는지는 원문과 저장소에서 확인됩니다.

## 공개 저장소는 모델마다 따로 붙이는 kit입니다

Anthropic이 공개한 `uplifting-biomolecular-modeling` 저장소에는 36개 optimization kit가 들어 있습니다. 각 kit는 하나의 upstream 생물분자 모델 옆에 붙습니다. 저장소 설명에 따르면 각 kit는 upstream release를 `stock/`에 고정해 두고, 최적화 코드는 `opt/`, 실행 환경은 `environment/`, 변경 내용은 `CHANGES.md`, 정확한 upstream version과 pin은 `STOCK.md`에 나눠 둡니다.

이 구성은 중요합니다. 연구 코드는 논문 구현, weight downloader, GPU library, Python package version이 서로 얽혀 있어 재현이 자주 깨집니다. Anthropic은 kit가 upstream 호출 방식을 가능한 한 유지하면서, 실행할 때 이름이 붙은 모드를 켜는 방식으로 최적화를 넣었다고 설명합니다. 34개 kit는 upstream의 Python 환경 안에서 작동하고, 두 foundry kit는 별도 interpreter에 작은 file overlay를 설치합니다.

모드는 네 가지로 나뉩니다. `off`는 고정된 upstream release를 그대로 실행합니다. `exact`는 출력은 같게 유지하면서 더 빠르게 도는 모드입니다. `fast`는 upstream의 seed 간 변동 안에 드는 작은 수치 차이를 허용해 더 빠르게 도는 모드입니다. `big`은 가장 낮은 peak GPU memory를 목표로 하며, 다른 모드가 담지 못하는 큰 입력을 처리하기 위한 모드입니다.

이 구조는 agent가 만든 코드를 연구자가 바로 믿어야 한다는 뜻이 아닙니다. 오히려 반대입니다. `ACTIVE` 또는 `NOT ACTIVE` 로그를 찍고, mode 이름이 맞지 않으면 에러로 끝내며, 각 kit마다 stock version과 변경점을 나눠 둔 것은 “무엇이 켜졌는지”를 검증하기 위한 장치입니다. 과학 코드에서 AI가 만든 최적화를 받아들이려면 이런 추적성이 먼저 필요합니다.

## Claude가 한 일은 커널 작성만이 아니었습니다

Anthropic은 Claude에게 모든 모델에 같은 kernel만 넣은 것이 아니라, 개별 모델의 실행 경로도 보게 했다고 설명합니다. 예로 든 변화는 중복 계산 캐시, 항상 같은 값으로 끝나는 dead branch 단순화, memory를 아끼는 실행 방식입니다. 이런 변화가 구조 예측, 단백질 설계, 단백질 언어 모델, 유전체 모델에 걸쳐 적용됐다는 점이 이번 공개의 기술적 중심입니다.

여기서 눈에 띄는 것은 작업 범위입니다. Anthropic은 생물분자 모델링 경험은 있지만 inference 최적화나 kernel engineering 경험은 없던 기술 직원 두 명의 감독 아래 Claude가 4주가 채 안 되는 기간에 30개가 넘는 공개 모델을 가속했다고 밝혔습니다. 기존에는 모델마다 숙련된 engineer가 몇 주씩 들여야 했던 작업이었습니다.

다만 이 주장은 “Claude가 스스로 일반적인 최적화 engineer를 대체했다”는 결론으로 넓힐 수 없습니다. 대상은 Anthropic이 고른 생물분자 모델이고, 작업자는 Claude Science 안에서 구조화된 harness를 썼으며, 공개된 수치는 Anthropic의 측정입니다. 그래도 공개 repository가 있어 최소한 어떤 파일과 실행 모드로 이 결과를 주장하는지는 추적할 수 있습니다.

## 큰 분자 시스템은 먼저 메모리 한계에 막혔습니다

이번 공개가 단순한 속도 기사에 그치지 않는 이유는 `big` 모드 때문입니다. 구조 예측 모델은 입력이 길어질수록 메모리가 먼저 막힙니다. Anthropic은 Claude가 만든 low-memory 모드로 10,000 token이 넘는 생물분자 시스템을 단일 NVIDIA GPU 노드에서 정확하게 예측할 수 있었다고 설명했습니다.

원문은 인간 mitochondrial complex I, TRiC chaperone complex, proteasome, bacterial ribosome 같은 큰 시스템을 예로 듭니다. 또 31,000 token에서 70,000 token이 넘는 viral capsid와 protein compartment 예측도 실행했지만, 이 경우 구조가 무너졌다고 밝혔습니다. 실행은 가능해졌지만 모델이 그 크기에서 일반화했다고 말할 수는 없다는 뜻입니다.

이 구분이 중요합니다. 메모리 최적화는 “계산을 시작할 수 있게 하는 변화”이고, 생물학적으로 맞는 예측은 별도 검증입니다. Anthropic은 interface 정확도 기준으로 DockQ 0.23 이상을 사용했다고 설명하지만, wet lab 검증이나 독립 구조 평가가 모든 결과를 확인한 것은 아닙니다.

## 제품 팀도 baseline과 mode 기록을 봐야 합니다

이번 공개는 생물학 연구 도구 이야기이지만, AI agent를 제품 개발에 붙이는 팀에도 직접적인 질문을 던집니다. Agent가 코드베이스를 읽고 성능 병목을 줄인다면, patch 자체만으로는 부족합니다. 어떤 baseline에서 무엇을 바꿨는지 설명하는 기록이 함께 있어야 합니다. Anthropic 저장소가 `stock/`, `opt/`, `environment/`, `STOCK.md`, `CHANGES.md`를 분리한 이유가 여기에 있습니다.

또 하나의 교훈은 모드 설계입니다. 속도와 정확도를 하나의 스위치로 묶으면 운영자가 무엇을 포기했는지 알기 어렵습니다. `exact`, `fast`, `big`처럼 출력 동일성, 작은 수치 차이, 메모리 절약을 나눠 두면 연구자는 자기 workload에 맞춰 위험을 고를 수 있습니다.

한국의 AI·바이오·제약 연구팀에는 비용 면에서도 의미가 있습니다. 이전 Anthropic protein design 캠페인은 target 하나에 최대 10,000달러, 약 2,500 NVIDIA H100 GPU hour를 허용했습니다. 이번 글에서는 한 NVIDIA H200과 24시간 wall time, 더 짧은 prompt, sub-agent 없는 설정으로 이전과 비슷한 in silico score를 냈다고 설명합니다. 이 역시 자체 측정이지만, GPU 접근이 제한된 팀에는 어떤 부분을 직접 재측정해야 하는지 알려 주는 신호입니다.

## 아직 남은 검증은 분명합니다

이 기사의 중심 근거 수준은 E2입니다. 공식 발표와 공개 저장소가 있고, code artifact와 실행 안내가 열려 있습니다. 직접 실행까지 확인한 것은 아니므로 재현성은 R2로 둡니다. 공개 코드는 재실행 가능하지만, 각 kit는 GPU, model weights, container나 Python 환경, upstream license 조건을 요구합니다.

가장 큰 빈칸은 독립 benchmark입니다. 같은 kit를 제3자가 같은 GPU, 같은 입력, 같은 upstream version으로 실행해 Anthropic의 속도와 정확도 주장을 재확인해야 합니다. `fast` 모드의 작은 수치 차이가 실제 연구 결론에 영향을 주는지도 분야별로 다시 봐야 합니다. `big` 모드가 10,000 token 안팎에서 유용하다는 주장과 70,000 token급에서 실행만 됐다는 주장은 서로 다르게 다뤄야 합니다.

그래도 이번 공개는 중요한 기사 후보가 됩니다. 모델 능력 발표가 아니라, frontier model이 기존 과학 소프트웨어의 병목을 찾고 그 결과를 version pin과 실행 모드가 있는 공개 kit로 남긴 사례이기 때문입니다. 개발자가 오늘 가져갈 질문은 단순합니다. 우리 팀의 agent 산출물도 baseline, 실행 환경, mode, 변경점, 실패 시 동작을 이 정도로 남기고 있는가입니다.

## 이해상충과 취재 조건

이 글은 공개 웹 문서만 읽어 작성했습니다. Anthropic, OpenAI, Google, Qwen, DeepSeek, Mistral 또는 다른 공급자로부터 계정, 크레딧, 장비, 브리핑, 엠바고 자료를 제공받지 않았습니다. 이해상충은 확인된 바 없습니다.

## 근거 원장

| claim_id | 주장 | 근거 | 등급 | 한계 |
| --- | --- | --- | --- | --- |
| C1 | Anthropic은 2026년 9월 17일 Claude가 30개가 넘는 생물분자 모델의 inference 경로를 최적화했고 그 코드를 공개했다고 밝혔습니다. | Anthropic research post, GitHub repository | E2 | 개발사 자체 발표와 자체 측정입니다. |
| C2 | 공개 저장소에는 36개 optimization kit가 있고, 각 kit는 upstream release, 최적화 코드, 실행 환경, 변경 내용, pin 정보를 나눠 둡니다. | GitHub repository README | E2 | 저장소는 reference release이며 Anthropic은 유지보수와 PR 수용 계획이 없다고 밝힙니다. |
| C3 | kit는 `off`, `exact`, `fast`, `big` 모드로 stock 실행, 동일 출력 가속, 작은 수치 차이를 허용한 가속, 낮은 peak memory 실행을 구분합니다. | GitHub repository README | E2 | 실제 효과는 모델별 README와 hardware에서 다시 확인해야 합니다. |
| C4 | Anthropic은 triangle attention과 triangle multiplication이 구조 예측 모델의 주요 병목이며 FlashPairformer가 이를 빠르게 처리한다고 설명했습니다. | Anthropic research post, GitHub repository | E2 | 비교 수치는 Anthropic 측정이며 독립 재현은 확인하지 못했습니다. |
| C5 | Anthropic은 평균 약 4배 속도 개선, 동일 출력 기준 약 2배 개선, 10,000 token 초과 시스템의 단일 GPU 노드 실행을 보고했습니다. | Anthropic research post | E2 | 원자료 로그와 제3자 재실행 결과는 기사 작성 시점에 확인하지 못했습니다. |
| C6 | NVIDIA cuEquivariance와 BioNeMo Inference Runtime은 Anthropic이 비교 대상으로 든 공개 kernel/runtime 경로입니다. | Anthropic research post, NVIDIA GitHub repositories | E1 | 이 기사는 NVIDIA runtime 성능을 독립 평가하지 않습니다. |

## 출처

- Anthropic, “How Claude is uplifting biomolecular modeling,” 2026-09-17. https://www.anthropic.com/research/claude-uplifts-biomolecular-modeling
- Anthropic, `anthropics/uplifting-biomolecular-modeling`, GitHub repository, accessed 2026-09-28. https://github.com/anthropics/uplifting-biomolecular-modeling
- Anthropic, technical report PDF linked from the research post, accessed 2026-09-28. https://www-cdn.anthropic.com/e96b5807039a88168733d9687afe41dfbbd5de13.pdf
- NVIDIA, `cuEquivariance`, GitHub repository, accessed 2026-09-28. https://github.com/nvidia/cuequivariance
- NVIDIA BioNeMo, `BioNeMo-Inference-Runtime`, GitHub repository, accessed 2026-09-28. https://github.com/NVIDIA-BioNeMo/BioNeMo-Inference-Runtime
