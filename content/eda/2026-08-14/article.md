---
edition: eda
decision: publish-candidate
title: "ACE-RTL 공개는 EDA 에이전트 평가를 말솜씨에서 실행 로그로 옮깁니다"
date: 2026-08-14
subject: "NVIDIA ACE-RTL 공개 코드와 CVDP 1.1.0 benchmark 실행 경로"
summary: "NVIDIA가 ACE-RTL 코드와 CVDP 연동 실행 절차를 공개해 RTL 생성·수정·디버그 에이전트를 일부 재실행 가능한 방식으로 평가할 길이 열렸습니다. 다만 97.1% pass rate와 Siemens Fuse 통합 효과는 벤더·저자 보고 범위에 머뭅니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["중심 자료 일부는 NVIDIA와 Siemens가 자기 모델·도구 통합을 설명한 벤더 원문입니다.", "CVDP benchmark와 ACE-RTL 저자 일부는 NVIDIA 소속이며, 편집국은 NVIDIA Inference API key와 동일 실행 비용을 투입해 결과를 재실행하지 않았습니다.", "Siemens Fuse EDA AI Agent의 상세 제품 문서와 상용 도구 실행 환경에는 접근하지 못했습니다."]
---

AI가 RTL 코드를 한 번 그럴듯하게 쓰는지보다 더 중요한 기준이 생기고 있습니다. RTL은 레지스터 전송 수준(register transfer level)의 하드웨어 동작 서술로, 실제 회로 합성과 검증의 출발점입니다. NVIDIA의 ACE-RTL 공개는 에이전트가 코드를 쓰고, 시뮬레이터나 테스트 하네스의 실패를 읽고, 다시 고치는 과정을 코드와 benchmark로 일부 확인할 수 있게 했습니다.

## 세 줄 요약

- NVIDIA는 ACE-RTL을 공개하면서 RTL 생성, 수정, 테스트벤치, assertion, 디버깅 과제를 CVDP benchmark와 연결하는 실행 절차를 제시했습니다.
- NVIDIA 기술 글은 Nemotron 3 Ultra를 ACE-RTL agent에 넣었을 때 CVDP 9개 과제군 평균 pass rate 97.1%, 반복당 평균 6,629 token을 썼다고 보고했습니다.
- 이 수치는 저자·벤더 보고 결과입니다. 공개 코드는 재실행 가능성을 높이지만, 편집국은 같은 API key, 모델 endpoint, 비용, seed, 전체 로그로 독립 재현하지 않았습니다.

## EDA 엔지니어를 위한 판단

- **지금 할 일:** RTL AI 도구를 평가할 때 demo 영상보다 benchmark 행, test harness, simulator preflight, 실패 로그, 반복 횟수, token 사용량이 남는지 먼저 확인할 만합니다.
- **아직 미룰 일:** ACE-RTL 결과만으로 특정 상용 EDA agent가 verification closure 전체를 자동화한다고 결론 내리는 일입니다.
- **다음에 확인할 신호:** 같은 CVDP 1.1.0 데이터셋과 공개 runner에서 여러 모델·agent가 남긴 원 로그, 실패 행, 비용, runtime을 비교하는 독립 결과입니다.

### 이번 공개가 이전 EDA 에이전트 기사와 다른 점

전날 EDA판은 Cadence가 말한 "검증 가능한 피드백 루프"를 다뤘습니다. 그때 중심 질문은 EDA agent가 simulation, formal, coverage 도구의 피드백을 어떻게 받아야 하는가였습니다.

이번 주제의 새 사실은 그 질문을 일부 실행 가능한 형태로 옮긴 공개 artifact입니다. ACE-RTL repository는 generator, reflector, coordinator라는 세 역할을 두고, CVDP라는 Verilog benchmark에 연결하는 스크립트와 실행 조건을 공개합니다. Generator는 RTL을 만들거나 고치고, reflector는 시뮬레이션 실패와 mismatch를 읽어 수정 방향을 제안하며, coordinator는 이전 시도와 실패 정보를 다음 반복에 남깁니다.

이 차이는 실무적으로 큽니다. "agent가 tool feedback을 쓴다"는 말은 발표 자료만으로도 할 수 있습니다. 그러나 어떤 dataset 파일을 쓰고, 어떤 simulator가 필요하며, 결과가 어느 디렉터리에 남는지까지 공개되면 평가자는 적어도 같은 과제를 다시 돌려 보거나 실패 조건을 좁혀 물을 수 있습니다.

### CVDP는 작은 Verilog prompt보다 실제 흐름에 더 가깝게 만들려는 benchmark입니다

CVDP는 Comprehensive Verilog Design Problems의 약자입니다. 여러 줄짜리 Verilog 함수 하나를 맞히는 대신, RTL 생성, 기존 모듈 재사용, 코드 수정, lint와 QoR 개선, 테스트벤치 자극 생성, checker 생성, assertion 생성, 디버깅 같은 과제를 나눠 다룹니다.

NVIDIA의 CVDP 논문은 13개 범주와 783개 문제를 설명합니다. 공개 Hugging Face dataset은 현재 749개 행으로 표시되며, CVDP repository README는 초기 공개에서 일부 datapoint와 reference solution이 test harness 문제, 라이선스, 데이터 오염 방지 이유로 빠졌다고 설명합니다. 따라서 "논문 전체 benchmark가 그대로 완전 공개됐다"가 아니라, 공개된 하위 집합과 실행 framework가 있다는 쪽이 정확합니다.

ACE-RTL README는 실행 조건도 구체적으로 적습니다. Python 패키지, `git`, `make`, `curl` 외에 선택한 CVDP 행에 따라 `iverilog`, `vvp`, `verilator`, `yosys` 같은 공개 simulator와 합성 도구가 필요합니다. 일부 행은 Cadence Xcelium/IMC 같은 상용 도구를 요구할 수 있습니다. 기본 hosted model은 `nvidia/nemotron-3-ultra-550b-a55b`이고, API key는 환경변수에서 읽도록 되어 있습니다.

### 97.1%는 제품 순위가 아니라 한 agent 설정의 저자 보고 결과입니다

NVIDIA 기술 글은 같은 ACE-RTL pipeline에 GLM 5.2, Kimi K2.6, Nemotron 3 Ultra를 넣어 비교했다고 설명합니다. 그 글에서 보고한 평균 pass rate는 Nemotron 3 Ultra 97.1%, Kimi K2.6 95.2%, GLM 5.2 92.1%입니다. 반복당 평균 token은 Nemotron 3 Ultra가 6,629개, GLM 5.2가 9,156개, Kimi K2.6이 22,579개였다고 합니다.

이 숫자는 유용하지만, 해석 범위가 좁습니다. 같은 agent pipeline으로 모델 효과를 보려는 비교라는 점은 장점입니다. 반대로 benchmark 선정, sampling, endpoint 상태, token 계산 방식, 실패 로그, 비용, 상용 행 포함 여부를 독립 주체가 같은 조건으로 확인한 결과는 아직 확인하지 못했습니다. 따라서 이 수치는 "Nemotron 3 Ultra가 모든 RTL 업무에서 가장 좋다"가 아니라 "NVIDIA가 공개한 CVDP 조건에서 ACE-RTL과 결합했을 때 이렇게 보고했다"로 읽어야 합니다.

### Siemens 발표는 흐름 적용 범위를 보여 주지만, 검증 근거는 별도입니다

Siemens는 DAC 2026 발표에서 Fuse EDA AI Agent가 NVIDIA NeMo Gym, OpenShell, Nemotron model, CUDA-X와 결합해 semiconductor와 PCB 설계 흐름에서 자기 검증형 agentic workflow를 제공한다고 밝혔습니다. 발표문은 Catapult, Questa One, Veloce, Solido, Aprisa, Calibre, Tessent, Innovator3D IC, Xpedition까지 넓은 제품군을 언급합니다.

여기서 실무적으로 볼 부분은 "self-verifying"이라는 말 자체가 아닙니다. 실제 확인해야 할 것은 agent가 어떤 deterministic EDA engine을 언제 부르고, 어떤 결과를 통과 조건으로 삼으며, 실패하면 어떤 로그와 권한 기록을 남기는지입니다. Siemens 발표는 제품 방향과 적용 범위를 확인하는 `E1` 근거입니다. 하지만 10배 turnaround 개선이나 5~10배 token cost 절감 같은 수치는 공개 benchmark와 독립 재현이 없으므로 제품 전체 성능 결론으로 쓰지 않습니다.

## 확인된 것과 확인되지 않은 것

| 구분 | 확인된 것 | 확인되지 않은 것 |
|---|---|---|
| 공개 artifact | ACE-RTL repository, CVDP benchmark repository, CVDP dataset changelog와 실행 절차가 공개되어 있습니다. | 편집국이 동일 모델 endpoint와 비용으로 전체 결과를 재실행하지 않았습니다. |
| benchmark 범위 | CVDP는 RTL 생성·수정·검증·디버깅을 여러 범주로 나눕니다. | 모든 논문 datapoint와 reference solution이 공개된 것은 아닙니다. 일부 행은 상용 도구가 필요할 수 있습니다. |
| NVIDIA 결과 | ACE-RTL + Nemotron 3 Ultra의 CVDP 평균 pass rate와 token 사용량이 NVIDIA 기술 글에 보고됐습니다. | 독립 주체가 같은 조건에서 97.1%를 재현했다는 로그는 확인하지 못했습니다. |
| Siemens 제품 흐름 | Siemens는 Fuse EDA AI Agent와 NVIDIA 기술 통합을 DAC 2026에서 발표했습니다. | Siemens 상용 flow의 상세 release note, 고객별 설정, 전체 runtime·비용·실패율은 공개 자료만으로 검증할 수 없습니다. |

## 이 공개의 의의와 편집 판단

**편집 판단:** 이번 공개의 의미는 특정 모델의 97.1% 숫자보다, EDA agent 평가가 "그럴듯한 RTL 출력"에서 "tool feedback을 읽고 다시 실행해 남긴 로그"로 이동하고 있다는 점입니다. ACE-RTL과 CVDP 1.1.0은 완전한 독립 benchmark는 아니지만, 최소한 공개 행과 runner를 기준으로 모델·agent·비용을 따져 물을 수 있는 발판을 제공합니다.

이 흐름은 EDA 조직의 구매·도입 질문도 바꿉니다. "AI가 RTL을 잘 쓰는가"만으로는 부족합니다. 어떤 과제를 통과했는지, open-source simulator로 재현되는 행과 상용 도구가 필요한 행이 어떻게 나뉘는지, 실패한 datapoint를 숨기지 않는지, token 비용과 runtime이 설계 규모에 따라 어떻게 커지는지를 봐야 합니다.

## 이해상충과 취재 조건

중심 자료 일부는 NVIDIA가 자기 모델, benchmark, repository를 설명한 원문입니다. Siemens 발표도 자기 EDA 제품군과 NVIDIA 통합을 설명하는 벤더 원문입니다. CVDP와 ACE-RTL 저자에는 NVIDIA 소속 연구자가 포함됩니다.

편집국은 NVIDIA나 Siemens의 지원을 받지 않았고, 상용 EDA license나 NVIDIA Inference API key를 제공받지 않았습니다. 이 때문에 공개 코드·문서·dataset 구조는 확인했지만, benchmark 결과를 독립 재현했다고 쓰지 않습니다.

## 근거 원장

| Claim | 근거 | 판정 |
|---|---|---|
| C1. ACE-RTL은 RTL 생성·검증·반복 수정을 위한 generator, reflector, coordinator 구조와 CVDP 연동 실행 절차를 공개했다. | ACE-RTL GitHub README, ACE-RTL 논문 | `E2`: 코드와 실행 절차가 공개된 P2/P1 근거 |
| C2. CVDP는 RTL 생성, 수정, verification, debugging 등 여러 Verilog 설계 과제를 다루며, 공개 dataset은 논문 설명보다 일부 제한이 있다. | CVDP 논문, CVDP GitHub README, Hugging Face dataset·CHANGELOG | `E2`: benchmark 방법과 공개 artifact 확인 |
| C3. ACE-RTL + Nemotron 3 Ultra가 CVDP 9개 과제군 평균 97.1% pass rate와 반복당 평균 6,629 token을 기록했다. | NVIDIA Technical Blog | `E2`: 조건이 설명된 저자·벤더 보고, 독립 재현 없음 |
| C4. Siemens는 Fuse EDA AI Agent에 NVIDIA NeMo Gym, OpenShell, Nemotron, CUDA-X를 결합한 self-verifying EDA workflow를 발표했다. | Siemens 공식 발표 | `E1`: 발표 사실과 제품 방향 확인, 성능 주장은 미확인 |

근거 수준의 상한은 `E2`, 재현성은 `R2`입니다. 공개 코드와 benchmark 실행 경로가 있어 재실행은 가능하지만, 이 기사 작성 과정에서 전체 benchmark를 재실행하지 않았습니다.

## 출처

1. [NVIDIA Technical Blog, *NVIDIA Nemotron 3 Ultra Leads Open Models on Accuracy and Efficiency in Agentic RTL Coding* (2026-07-26)](https://developer.nvidia.com/blog/nvidia-nemotron-3-ultra-leads-open-models-on-accuracy-and-efficiency-in-agentic-rtl-coding/)
2. [NVlabs/ACE-RTL GitHub repository](https://github.com/NVlabs/ACE-RTL)
3. [Deng 외, *ACE-RTL: When Agentic Context Evolution Meets RTL-Specialized LLMs*](https://arxiv.org/abs/2602.10218)
4. [NVlabs/cvdp_benchmark GitHub repository](https://github.com/NVlabs/cvdp_benchmark)
5. [Pinckney 외, *Comprehensive Verilog Design Problems*](https://arxiv.org/abs/2506.14074)
6. [nvidia/cvdp-benchmark-dataset](https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset)
7. [Siemens, *Siemens advances self-verifying AI workflows for EDA* (2026-07-26)](https://news.siemens.com/en-us/siemens-nvidia-dac-2026/)
