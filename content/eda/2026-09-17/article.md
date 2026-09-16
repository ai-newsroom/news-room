---
edition: eda
decision: publish-candidate
title: "cocotb 2.1.0은 RTL 검증을 pytest 회귀 실행에 더 가깝게 옮깁니다"
date: 2026-09-17
subject: "cocotb 2.1.0 release, pytest plugin, JUnit attachment support, Verilator SAIF tracing, and Questa QIS/Qrun runner"
summary: "cocotb 2.1.0은 Python으로 쓰는 RTL 검증 testbench를 일반 Python 프로젝트의 pytest 실행, JUnit report, 병렬 실행, waveform·log 산출물 관리에 더 자연스럽게 연결합니다. 공개 release note, 문서, PyPI 배포물과 source로 기능과 조건은 추적할 수 있지만, pytest plugin은 아직 active development 상태이고 편집국은 simulator별 regression을 직접 재실행하지 않았습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음. 공개 문서, GitHub release, PyPI metadata와 공개 source만 사용했고, 사전 briefing, 제공받은 account·license·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

RTL은 register-transfer level의 약자로, clock마다 register 사이에서 data가 어떻게 움직이는지 적은 설계 표현입니다. cocotb는 이 RTL 검증 testbench를 Verilog나 SystemVerilog가 아니라 Python으로 쓰게 해 주는 공개 framework입니다. 2026년 8월 30일 공개된 cocotb 2.1.0은 새 simulator를 하나 더 붙인 단순 update에 그치지 않습니다. 이번 변화의 중심은 RTL 검증을 일반 Python test와 CI가 다루는 방식에 더 가깝게 옮기는 데 있습니다.

가장 큰 변화는 experimental pytest plugin입니다. pytest는 Python 생태계에서 test를 찾고, fixture와 marker를 적용하며, filtering과 report를 맡는 표준적인 test runner입니다. cocotb 2.1.0 문서는 이 plugin이 HDL 설계 build와 simulator 실행을 pytest fixture와 marker로 감싼다고 설명합니다. 또 `-k`와 `-m` filtering, command-line option, config file, pytest-xdist 병렬 실행을 cocotb test에 연결합니다. 기존에도 Python runner를 pytest 안에서 부를 수 있었지만, 이번 release는 검증 repository를 Python package와 비슷하게 관리할 수 있는 길을 더 공식적으로 열었습니다.

이 변화가 설계 flow에서 중요한 이유는 검증 실패가 code 한 줄의 pass/fail로 끝나지 않기 때문입니다. RTL regression에서 원인을 추적하려면 simulator log, waveform, seed, plusarg, build directory, JUnit XML 같은 산출물이 함께 남아야 합니다. cocotb 2.1.0은 generated JUnit XML에 simulator log와 waveform file을 attachment로 붙이는 기능을 추가했습니다. `COCOTB_RESULTS_ATTACHMENTS`와 `COCOTB_RESULTS_RELATIVE_TO` 환경 변수도 새로 들어갔습니다. CI에서 실패한 test를 눌렀을 때 결과 XML과 waveform·log가 같이 따라오면, 검증 엔지니어는 별도 artifact 경로를 다시 찾는 시간을 줄일 수 있습니다.

## pytest가 simulator 실행까지 맡습니다

cocotb의 전통적인 사용법은 Makefile flow에 가깝습니다. HDL source를 build하고 simulator를 띄운 뒤, Python testbench가 simulator 안의 design handle을 읽고 씁니다. cocotb 1.8부터 Python runner가 들어왔고, 2.1.0 문서도 runner를 Makefile 대체 경로로 설명합니다. 이 runner는 HDL을 simulator용으로 build하고 test를 실행합니다.

2.1.0의 pytest plugin은 이 runner를 pytest의 test 수집과 실행 방식 안으로 더 끌어옵니다. 문서에 따르면 plugin은 `hdl` fixture로 design under test를 만들고, `@pytest.mark.cocotb_runner`로 simulator를 실행하는 test function을 표시합니다. `@pytest.mark.cocotb_test`는 coroutine test를 cocotb test로 표시합니다. test 이름, module, top-level design, timescale 같은 설정은 marker와 fixture, command-line option으로 조정할 수 있습니다.

이 방식은 검증 code를 관리하는 방법을 바꿉니다. 작은 IP block regression은 Python package test처럼 filter하고 나눠 돌릴 수 있습니다. 같은 repository 안에서 pure Python model test, cocotb RTL test, wrapper script test를 pytest가 한 번에 발견할 수도 있습니다. 검증 환경을 처음 구성하는 팀은 Makefile 변수와 simulator invocation을 따로 외울 부담을 덜 수 있습니다. 이미 pytest 기반 CI를 쓰는 팀에는 기존 report와 병렬 실행 도구를 재사용할 여지가 생깁니다.

다만 plugin은 아직 안정 API가 아닙니다. 문서는 pytest plugin이 active development 상태이며 다음 한두 release에서 breaking change가 있을 수 있다고 경고합니다. 그래서 장기 유지되는 signoff regression을 곧바로 plugin 중심으로 재작성하기보다, 새 IP나 내부 실험 flow에서 먼저 붙여 보는 쪽이 안전합니다.

## 실패한 test의 log와 waveform을 CI에서 바로 찾습니다

검증 flow에서 JUnit XML은 단순한 형식 문제가 아닙니다. Jenkins, GitLab, GitHub Actions 같은 CI가 test 결과를 읽고 실패 test를 보여 주며 trend를 계산할 때 쓰는 공통 통로입니다. cocotb 2.1.0 release note는 generated JUnit XML에 simulator가 만든 log와 waveform file을 attachment로 붙인다고 적었습니다. Jenkins xUnit schema version 2와 호환되도록 고친 점도 함께 밝혔습니다.

이 변화는 debug loop를 짧게 만듭니다. 예를 들어 Verilator나 Questa regression에서 특정 seed가 실패했다면, engineer는 실패한 test entry에서 simulator log와 waveform을 바로 볼 수 있어야 합니다. 2.1.0은 attachment 경로를 상대 경로로 바꾸는 hint도 제공합니다. CI worker의 absolute path가 매번 달라져도 report 안의 link를 더 안정적으로 만들기 위한 기능입니다.

Verilator 사용자에게는 SAIF tracing도 눈에 띕니다. SAIF는 switching activity interchange format의 약자로, simulation 중 signal toggle 정보를 전력 추정 flow로 넘길 때 쓰입니다. release note는 Verilator 5.042 이상에서 `--trace-saif`를 Makefile `EXTRA_ARGS` 또는 runner의 `build_args`에 넣어 SAIF tracing을 켤 수 있다고 설명합니다. 이 기능은 Python testbench에서 만든 stimulus를 power analysis 입력으로 이어 붙일 때 유용합니다. 다만 이 기사는 SAIF 결과의 정확도나 downstream power tool과의 일치를 재현하지 않았습니다.

## Questa와 VHDL 지원 범위도 넓어졌습니다

cocotb 2.1.0은 simulator별 runner도 보강했습니다. release note는 Questa QIS/Qrun flow용 `cocotb_tools.runner.QuestaQIS` Python Runner를 추가했고, `get_runner("questa-qisqrun")`으로 선택할 수 있다고 설명합니다. QIS/Qrun은 Siemens Questa 계열의 새 build·run 흐름을 가리키며, 기존 `vsim` 중심 flow와는 invocation 방식이 다릅니다. 조직이 Questa 2025.2 이후 flow를 쓰고 있다면 Python runner 기반 regression을 새 simulator flow와 맞추는 데 의미가 있습니다.

VHDL 쪽에서는 null-ranged array와 fixed-length string handle support가 들어갔습니다. null-ranged array는 범위가 비어 있는 배열입니다. 실제 design에서는 generic 설정이나 corner case에서 이런 object가 생길 수 있습니다. testbench가 이런 handle을 제대로 다루지 못하면 설계 자체보다 test infrastructure가 먼저 깨집니다. 2.1.0은 이런 VHDL object 접근 범위를 넓혔지만, 상용 simulator별 호환성은 각 팀 환경에서 확인해야 합니다.

지원 조건도 바뀌었습니다. PyPI metadata와 `pyproject.toml`은 cocotb 2.1.0이 Python 3.9 이상을 요구하고 `pytest>=6`를 dependency로 둔다고 보여 줍니다. release note는 Python 3.14 support가 추가됐고 Python 3.6, 3.7, 3.8 support는 제거됐다고 적었습니다. 오래된 regression farm이 Python 3.8에 묶여 있다면 upgrade 자체가 먼저 해야 할 일입니다.

## 작은 regression부터 붙여 볼 만합니다

지금 할 일은 새 기능을 test infrastructure 개선으로 분리해 보는 것입니다. 작은 IP block에서 pytest plugin을 켜고, simulator log와 waveform attachment가 CI에서 어떻게 보이는지 확인할 가치가 있습니다. Verilator 5.042 이상을 쓰는 팀은 SAIF tracing이 기존 waveform·coverage 설정과 충돌하지 않는지도 작은 design으로 확인할 수 있습니다.

아직 미룰 일은 signoff regression 전체를 pytest plugin으로 한 번에 옮기는 결정입니다. plugin은 experimental 상태이고, 문서가 breaking change 가능성을 직접 밝힙니다. 또 편집국은 Questa QIS/Qrun, Verilator SAIF, VHDL null-ranged array case를 실제 simulator에서 재실행하지 않았습니다. 따라서 이 기사의 결론은 “flow를 바꿀 수 있는 공개 기능이 나왔다”이지 “모든 simulator에서 검증됐다”가 아닙니다.

다음에 확인할 신호는 세 가지입니다. 첫째, cocotb 2.2나 이후 release에서 pytest plugin API가 안정화되는지입니다. 둘째, 주요 CI template와 downstream library가 attachment와 plugin flow를 기본값으로 받아들이는지입니다. 셋째, 상용 simulator와 open-source simulator가 같은 test repository에서 일관된 JUnit, waveform, seed 재현성을 보이는지입니다.

## 이해상충과 취재 조건

이 기사는 cocotb 2.1.0 release note, 공식 문서, GitHub release, PyPI metadata, 공개 source file만 확인했습니다. 사전 briefing, 제공받은 account, license, hardware, 광고, 후원, NDA, embargo는 없었습니다. 편집국은 package를 설치하거나 simulator별 regression을 직접 실행하지 않았습니다.

## 근거 원장

| claim | 근거 | 등급 | 확인한 내용 | 한계 |
|---|---|---|---|---|
| C1 | https://docs.cocotb.org/en/v2.1.0/release_notes.html | E2 | cocotb 2.1.0은 2026년 8월 30일 release됐고 pytest plugin, JUnit attachment, Verilator SAIF tracing, Questa QIS/Qrun runner, Python 3.14 support 등을 추가했습니다. | release note는 project maintainer의 원문이며, 성능 개선을 독립 입증하지 않습니다. |
| C2 | https://docs.cocotb.org/en/v2.1.0/pytest_plugin.html | E2 | pytest plugin은 fixture, marker, config, filtering, reporting, pytest-xdist 병렬 실행 연결을 제공합니다. | 문서가 active development와 breaking change 가능성을 밝힙니다. |
| C3 | https://docs.cocotb.org/en/v2.1.0/runner.html | E2 | Python runner는 HDL build와 test 실행을 담당하며 pytest와 함께 쓸 수 있습니다. | simulator별 실제 동작은 각 환경에서 확인해야 합니다. |
| C4 | https://pypi.org/project/cocotb/2.1.0/ | E2 | PyPI metadata는 version 2.1.0, Python 3.9 이상, `pytest>=6`, BSD-3-Clause license, wheel·sdist 배포를 확인합니다. | 배포물 metadata는 실행 성공을 보장하지 않습니다. |
| C5 | https://github.com/cocotb/cocotb/releases/tag/v2.1.0 | E2 | GitHub release는 2.1.0 release note, PyPI link, source archive를 연결합니다. tag object는 `a4824476ab10f20b4c6b87df6c7a067090903c1a`로 확인했습니다. | 편집국은 source build와 regression을 재실행하지 않았습니다. |

## 출처

- https://docs.cocotb.org/en/v2.1.0/release_notes.html
- https://docs.cocotb.org/en/v2.1.0/pytest_plugin.html
- https://docs.cocotb.org/en/v2.1.0/runner.html
- https://docs.cocotb.org/en/v2.1.0/simulator_support.html
- https://docs.cocotb.org/en/v2.1.0/platform_support.html
- https://github.com/cocotb/cocotb/releases/tag/v2.1.0
- https://pypi.org/project/cocotb/2.1.0/
- https://raw.githubusercontent.com/cocotb/cocotb/v2.1.0/pyproject.toml
- https://raw.githubusercontent.com/cocotb/cocotb/v2.1.0/src/cocotb_tools/_pytest/plugin.py
