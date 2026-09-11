---
edition: eda
decision: publish-candidate
title: "HLSFactory-Agent는 HLS 데이터셋 수집에 검증 로그를 남깁니다"
date: 2026-09-12
subject: "HLSFactory-Agent arXiv:2609.09519v1, HLS-Eval agentic flow arXiv:2609.09526v1, sharc-lab/hlsfactory-agent commit 8fac504210fae6403808b2acaad1310300dedd69"
summary: "Georgia Tech SHARC Lab 연구진은 사람이 HLS 설계 예제를 찾아 잘라내던 일을 LLM agent에 맡기는 방식을 제시했습니다. agent는 Docker 안에서 저장소를 분석하고 예제를 추출한 뒤 컴파일을 확인하며 Vitis HLS용 synth.tcl을 만듭니다. 공개 저장소와 companion HLS-Eval 논문으로 구조와 초기 결과를 추적할 수 있지만, 저자 실험을 독립 재현하지 않았고 OpenRouter API key와 Vitis HLS 접근이 필요합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["없음. 공개 arXiv 원문과 GitHub 저장소만 사용했고, 사전 briefing, 제공받은 account·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

HLS는 C/C++ 같은 높은 수준의 언어로 FPGA나 가속기 회로를 합성하는 방법입니다. AI로 이 설계 과정을 자동화하기는 쉬워 보이지만, 학습과 평가에 쓸 설계 예제를 모으는 일은 여전히 수작업에 많이 기대 왔습니다. 논문 저장소와 GitHub를 뒤져 HLS kernel을 찾고, 여러 파일에 흩어진 헤더와 testbench를 모아 독립 프로젝트로 잘라내야 하기 때문입니다. 여기에 Vitis HLS가 읽을 수 있는 `synth.tcl`도 만들어야 합니다.

2026년 9월 8일 arXiv에 올라온 HLSFactory-Agent 논문은 이 병목을 LLM agent 작업으로 옮겼습니다. 연구진은 agent가 공개 저장소를 읽고 HLS top-level function을 찾은 뒤, 설계별 폴더를 만들고 필요한 파일과 test data를 복사한다고 설명했습니다. 가능한 경우에는 Vitis HLS와 맞도록 코드도 고칩니다. 출력에는 합성 스크립트와 agent session log, HTML transcript가 남습니다. 같은 날 올라온 HLS-Eval companion 논문은 HLS agent 평가도 파일 편집과 C++ compiler self-check를 포함하는 실행 흐름으로 넓혔습니다.

핵심은 “모델이 HLS 코드를 잘 썼는가”를 한 번의 텍스트 답변만으로 보지 않는다는 점입니다. HLSFactory-Agent는 입력 저장소를 분석하고 설계 조각을 떼어 낸 뒤, 문법 확인과 합성 준비가 된 출력물로 바꿉니다. HLS-Eval agentic flow는 agent가 Docker container 안에서 shell, compiler, script를 쓰게 하고 결과 directory를 검사합니다. 평가자는 최종 코드뿐 아니라 비용, token 사용량, 반복 횟수, 실패 trace를 함께 볼 수 있습니다.

## 설계 예제 정리를 agent가 맡습니다

기존 HLS benchmark 확장은 논문과 저장소를 먼저 사람이 걸러야 했습니다. 어떤 논문이 실제 HLS 코드를 공개했는지, 저장소 안의 어느 함수가 합성 대상인지, vendor-specific type이나 project layout이 무엇인지 판단해야 합니다. 연구진은 이 작업이 오류가 잦고 repository별 engineering이 많이 든다고 설명했습니다.

HLSFactory-Agent는 이 단계를 두 층으로 나눕니다. 먼저 indexing script가 FPGA, EDA, architecture venue의 논문 metadata에서 `high-level synthesis`, `HLS` 같은 keyword를 찾아 후보 논문을 모읍니다. 대상은 DAC, ICCAD, ASP-DAC, DATE, MLCAD, GLVLSI, HOST, TCAD와 FPGA·architecture venue까지 넓게 잡았습니다. 논문은 이 방법으로 1984년부터 2026년까지 2,517개의 후보 publication을 모았다고 보고했습니다. 다만 연구진은 이 목록에도 사람이 다시 볼 항목이 많다고 적었습니다.

그다음 agent가 실제 repository를 처리합니다. agent는 source tree를 읽고 HLS kernel이나 top-level function을 찾은 뒤 설계별 출력 directory를 만듭니다. 필요한 source, header, utility, test data를 복사하고, testbench가 없으면 만들거나 기존 testbench를 보존합니다. 마지막에는 target part와 source list를 담은 `synth.tcl`을 생성합니다.

이 구조는 EDA flow에서 중요합니다. 데이터셋 수집이 단순 crawling에서 끝나지 않고, 이후 합성 도구가 받을 수 있는 작은 설계 단위로 이어집니다. agent의 산출물은 논문 링크 목록이 아니라 downstream HLS benchmark나 QoR model 학습으로 넘길 수 있는 설계 package입니다.

## 작은 실험이지만 실패 기준은 분명합니다

연구진은 26개 공개 repository를 대상으로 초기 실험을 했고, agent가 271개 candidate design을 뽑았다고 보고했습니다. 이 가운데 130개는 Vitis HLS synthesis를 통과했고 141개는 실패했습니다. 다섯 repository에서는 설계가 나오지 않았습니다.

이 수치는 HLS 설계 자동화가 이미 해결됐다는 뜻이 아닙니다. 오히려 유용한 지점은 실패를 어떻게 세는지 명확하다는 데 있습니다. 논문은 Tcl 오류, header 누락, target part 문제, 지원하지 않는 construct, timeout 때문에 합성까지 가지 못하면 실패로 계산했다고 설명했습니다. agent가 “그럴듯한 kernel”을 찾았더라도 standalone Vitis HLS design으로 만들지 못하면 통과로 보지 않았습니다.

공개 저장소도 이 흐름을 뒷받침합니다. `sharc-lab/hlsfactory-agent` 저장소는 core agent code, Docker image build 경로, example batch run과 analysis script, HLS source indexing script를 포함합니다. README는 실행에 Python 3.12, Docker, Git, OpenRouter API key, Vitis HLS가 필요하다고 적었습니다. example workflow는 predefined repository를 clone하고 agent를 Docker 안에서 실행한 뒤 `exp/run_base/runs/`에 결과를 씁니다.

## HLS-Eval은 평가를 실행 로그까지 넓힙니다

같은 연구진의 HLS-Eval agentic flow 논문은 설계 agent를 평가하는 쪽의 변화를 보여 줍니다. 기존 HLS-Eval은 HLS code generation과 editing benchmark를 제공했지만, 이번 논문은 mini-swe-agent 기반 flow를 붙여 agent가 Docker 안에서 Bash와 C/C++ compiler를 사용하게 했습니다. 평가 뒤에는 제공된 testbench나 header가 바뀌지 않았는지도 확인합니다. 이는 agent가 test를 고쳐 점수를 얻는 경로를 막기 위한 장치입니다.

초기 결과에서 연구진은 gpt-oss-120b가 단순 HLS generation task에서 pass@10 기준 benchmark를 포화시켰다고 보고했습니다. 더 작은 gpt-oss-20b도 sample을 10개로 늘리면 synthesis pass rate가 크게 올라갔다고 설명했습니다. 이 결과는 “모델이 충분히 강하다”보다 “기존 쉬운 benchmark만으로는 agentic HLS 능력을 재기 어려워졌다”는 쪽에 가깝습니다. 연구진도 더 복잡한 benchmark와 trace 분석이 필요하다고 결론냈습니다.

## 설계팀이 바로 바꿀 수 있는 일과 아직 남은 일

HLS dataset을 새로 모으는 팀은 수작업 기준표를 agent trace와 합성 통과 기준으로 바꿔 볼 수 있습니다. 후보 repository를 찾는 단계, standalone design으로 자르는 단계, C++ compile과 Vitis HLS synthesis를 통과시키는 단계를 분리하면 어느 병목에서 시간이 드는지 볼 수 있습니다.

아직 미뤄야 할 결정은 agent가 만든 dataset을 곧바로 신뢰 가능한 training corpus로 쓰는 일입니다. 논문은 26개 repository의 초기 결과를 보고했고, 실패 원인도 다양합니다. vendor-specific code, generated code, 복잡한 dependency가 많은 저장소에서는 agent가 kernel을 찾더라도 standalone project로 만들지 못할 수 있습니다.

다음에 확인할 신호는 세 가지입니다. 첫째, HLSFactory-Agent가 Vitis HLS를 Docker 안에서 더 직접적인 feedback으로 쓰는지입니다. 둘째, 추출된 design이 HLSFactory나 HLS-Eval benchmark에 실제로 병합되는지입니다. 셋째, 같은 repository set에서 다른 model과 prompt가 designs-per-dollar, designs-per-minute, synthesis pass rate를 어떻게 바꾸는지입니다.

## 이해상충과 취재 조건

이 기사는 공개 arXiv 원문, 공개 GitHub 저장소, raw README만 확인했습니다. 저자나 벤더의 사전 briefing, 제공받은 account, license, hardware, 광고, 후원, NDA, embargo는 없었습니다. 편집국은 저장소를 clone하거나 OpenRouter API와 Vitis HLS로 저자 실험을 재실행하지 않았습니다.

## 근거 원장

| claim | 근거 | 등급 | 확인한 내용 | 한계 |
|---|---|---|---|---|
| C1 | https://arxiv.org/abs/2609.09519 | E2 | HLSFactory-Agent 논문은 2026년 9월 8일 제출됐고, agent가 HLS design을 repository에서 추출해 Vitis HLS-compatible project로 package한다고 설명했습니다. | 저자 보고이며 독립 재현은 아닙니다. |
| C2 | https://github.com/sharc-lab/hlsfactory-agent | E2 | 저장소는 agent code, Docker image, batch run, analysis script, source indexing script를 공개합니다. HEAD는 `8fac504210fae6403808b2acaad1310300dedd69`로 확인했습니다. | 실행에는 OpenRouter API key와 Vitis HLS가 필요합니다. |
| C3 | https://arxiv.org/html/2609.09519 | E2 | 논문은 26개 repository에서 271개 candidate design, 130개 synthesis pass, 141개 fail을 보고했습니다. | repository subset과 model 선택은 저자 설정입니다. |
| C4 | https://arxiv.org/abs/2609.09526 | E2 | companion HLS-Eval 논문은 mini-swe-agent 기반 agentic evaluation flow와 C++ compiler self-verification, trace logging을 설명했습니다. | agentic flow의 구현 세부와 결과는 저자 보고입니다. |
| C5 | https://github.com/sharc-lab/HLS-Eval | E2 | HLS-Eval 저장소는 HLS code generation/editing benchmark와 framework, benchmark data와 experiment directory를 공개합니다. HEAD는 `9eb7addc7103b44d25eee61fc356e3f50cfc28e9`로 확인했습니다. | 이번 agentic 결과를 편집국이 재실행하지 않았습니다. |

## 출처

- https://arxiv.org/abs/2609.09519
- https://arxiv.org/html/2609.09519
- https://github.com/sharc-lab/hlsfactory-agent
- https://raw.githubusercontent.com/sharc-lab/hlsfactory-agent/master/README.md
- https://arxiv.org/abs/2609.09526
- https://arxiv.org/html/2609.09526
- https://github.com/sharc-lab/HLS-Eval
- https://raw.githubusercontent.com/sharc-lab/HLS-Eval/main/README.md
