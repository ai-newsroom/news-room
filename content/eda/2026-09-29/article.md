---
edition: eda
decision: publish-candidate
title: "Yosys 0.69, 오래된 합성 옵션을 정리하고 SV 2023 입력 경로를 추가했습니다"
date: 2026-09-29
subject: "Yosys 0.69 release, tag v0.69 commit 9f75ca1f9834a39a863915b5dae0c7b1e33533bc, CHANGELOG and verific frontend source"
summary: "Yosys 0.69는 `abc`, FPGA별 합성 pass, 공통 `synth` 옵션에 남아 있던 오래된 이름과 우회 옵션을 정리했습니다. 공개 합성 flow를 유지하는 팀은 CI script와 board별 wrapper를 먼저 점검해야 합니다. Verific frontend에는 SystemVerilog 2023을 명시하는 `-sv2023` 경로가 들어갔지만, 이 기능은 Verific을 포함한 빌드와 라이선스 조건이 있어야 쓸 수 있습니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["없음"]
---

Yosys 0.69는 오픈소스 RTL 합성 flow에 오래 남아 있던 명령 이름과 옵션을 정리한 릴리스입니다. RTL 합성은 Verilog나 SystemVerilog로 쓴 회로 설명을 gate 수준 netlist로 바꾸는 단계입니다. 이번 변경은 PPA가 좋아졌다는 발표가 아닙니다. 합성 script가 어떤 명령을 계속 쓸 수 있는지, 최신 SystemVerilog를 어떤 입력 경로로 읽을 수 있는지를 가르는 변화입니다.

릴리스 노트와 `CHANGELOG`는 0.68에서 0.69로 넘어오며 여러 항목이 제거됐다고 적었습니다. 대상은 `abc` pass의 sum-of-products 관련 파라미터, `coolrunner2`와 `greenpak4` 합성 pass, `nlutmap` pass, 여러 `synth` 계열 옵션입니다. `abc`는 조합 논리를 최적화하고 technology mapping을 할 때 Berkeley ABC를 연결해 쓰는 pass입니다. 따라서 영향을 받는 곳은 Yosys 본체를 한 번 직접 호출하는 명령보다, `synth_*`, `abc`, board별 wrapper, CI 회귀 script를 여러 해 쌓아 온 공개 FPGA와 ASIC 실험 flow입니다.

## 오래된 옵션이 남은 자동화부터 깨질 수 있습니다

Yosys script는 보통 `read -sv`, `hierarchy`, `proc`, `opt`, `memory`, `techmap`, `abc`처럼 pass를 차례로 실행합니다. 프로젝트가 특정 FPGA family나 실험용 mapping flow를 오래 유지했다면, 예전 옵션이 script 안에 남아 있을 수 있습니다. 0.69에서 제거된 항목이 들어 있으면 새 버전이 같은 결과를 내기 전에 명령 해석 단계에서 멈출 수 있습니다. 그래서 먼저 확인할 것은 결과 차이가 아니라 실행 실패 여부입니다.

이번 정리는 합성 품질을 한 방향으로 개선했다는 뜻이 아닙니다. 공개 원문은 어떤 옵션과 pass가 제거됐는지를 말하지만, 특정 design set에서 area, timing, runtime이 어떻게 달라졌는지는 제시하지 않습니다. 따라서 기사에서 말할 수 있는 중심 변화는 "0.69로 올릴 때 합성 자동화의 호환성 검사를 해야 한다"는 데 있습니다.

## SV 2023 옵션은 Verific 경로에서 쓰입니다

같은 릴리스는 `verific` frontend에 `-sv2023` 옵션을 추가했습니다. SystemVerilog 2023은 IEEE 1800-2023 계열의 언어 기능을 가리킵니다. frontend는 RTL 파일을 읽고 elaboration한 뒤 Yosys 내부 표현으로 넘기는 입구입니다. 공개 source의 help 문자열은 `verific {-vlog95|-vlog2k|-sv2005|-sv2009|-sv2012|-sv2017|-sv2023|-sv}` 형태를 보여 줍니다. 실제 argument 처리에서도 `-sv2023`을 Verific의 `SYSTEM_VERILOG_2023` 모드로 넘깁니다.

다만 이 문장을 "Yosys 무료 기본 빌드가 모든 SystemVerilog 2023 설계를 처리한다"는 뜻으로 읽으면 안 됩니다. Yosys README는 자체적으로 Verilog-2005와 SystemVerilog 일부를 지원한다고 설명합니다. 산업용 SystemVerilog와 VHDL parser가 필요하면 Tabby CAD Suite 평가 라이선스를 받으라고도 안내합니다. 공개 source도 `read -sv2023` 같은 높은 수준의 `read` 명령이 Verific을 쓰지 않는 경우에는 내부적으로 `read_verilog -sv` 쪽으로 낮춰 호출하는 경로를 갖고 있습니다. 즉 0.69의 새 플래그는 Verific을 포함한 빌드에서 언어 모드를 명시할 수 있게 한 변화입니다.

## 업그레이드 전에는 script부터 검색해야 합니다

지금 할 일은 간단합니다. Yosys를 0.69나 2026년 9월 말 이후 OSS CAD Suite nightly로 올리는 팀은 repository의 `.ys` script, Makefile, CI job에서 제거된 option 이름을 검색해야 합니다. 특히 `-retime`, `-noabc9`, `-abc2`, `-abc`, `nlutmap`, `coolrunner2`, `greenpak4`가 남아 있다면 새 flow에서 실패하는지 먼저 작은 design으로 확인하는 편이 안전합니다.

아직 미룰 일도 있습니다. 이 릴리스만 보고 timing closure 전략이나 signoff 기준을 바꿀 근거는 없습니다. 공개 원문으로 확인할 수 있는 것은 pass 목록과 frontend 옵션입니다. design, library, constraint, seed, runtime hardware를 고정한 QoR 비교는 제공하지 않습니다. `-sv2023`도 Verific이 포함된 환경에서 확인해야 하므로, 무료 OSS CAD Suite 사용자가 바로 모든 SV 2023 문법을 기대할 근거로 삼을 수 없습니다.

다음에 확인할 신호는 세 가지입니다. 첫째, OSS CAD Suite와 주요 open-source flow가 Yosys 0.69를 받아들이며 제거된 옵션을 어떻게 고치는지입니다. 둘째, 공개 benchmark script에서 같은 design과 constraint로 0.68과 0.69를 비교한 로그가 나오는지입니다. 셋째, Verific 기반 flow가 실제 SV 2023 설계 예제로 `-sv2023`을 쓰고, 기본 `read_verilog -sv` 경로와 어떤 차이가 나는지 공개하는지입니다.

## 이해상충과 취재 조건

이 기사는 Yosys의 공개 릴리스 노트, tag, `CHANGELOG`, README와 `verific` frontend source만 확인해 작성했습니다. YosysHQ, EDA 벤더, FPGA 벤더, foundry, PDK 배포자로부터 계정·라이선스·브리핑·자료를 제공받지 않았습니다. 편집국은 Yosys 0.69를 빌드하거나 예제 design으로 합성 결과를 재현하지 않았습니다.

## 근거 원장

| claim_id | 주장 | 근거 | 등급 | 한계 |
| --- | --- | --- | --- | --- |
| C1 | Yosys 0.69는 2026년 9월 9일 공개됐고 tag `v0.69`는 commit `9f75ca1f9834a39a863915b5dae0c7b1e33533bc`를 가리킨다. | GitHub release와 tag API | E2 | GitHub 공개 metadata 확인이며, 릴리스 빌드를 직접 설치하지 않았다. |
| C2 | 0.69 `CHANGELOG`는 `abc` pass의 sum-of-products 관련 파라미터, `coolrunner2`와 `greenpak4` 합성 pass, `nlutmap` pass, 여러 `synth` 옵션 제거를 적었다. | Yosys `CHANGELOG` at `v0.69` | E2 | 제거 항목의 실제 사용자 영향은 각 project script에 따라 다르다. |
| C3 | `verific` frontend source는 help와 argument parsing 양쪽에서 `-sv2023`을 SystemVerilog 2023 모드로 다룬다. | Yosys `frontends/verific/verific.cc` at `v0.69` | E2 | Verific 포함 빌드와 라이선스 조건이 필요하며, 편집국은 실행하지 않았다. |
| C4 | Yosys README는 기본 지원 범위와 산업용 SystemVerilog·VHDL parser 접근 조건을 구분한다. | Yosys `README.md` at `v0.69` | E2 | 제품·라이선스 안내는 배포자 설명이며, 개별 사용자의 entitlement를 확인하지 않는다. |
| C5 | 이번 릴리스는 script 호환성 점검에는 직접적인 의미가 있지만, PPA나 runtime 개선을 입증하지 않는다. | C1-C4에서 파생한 편집 판단 | E2 | 공개 benchmark와 독립 재현 로그가 없으므로 성능 결론으로 확대하지 않았다. |

## 출처

- Yosys 0.69 release: https://github.com/YosysHQ/yosys/releases/tag/v0.69
- Yosys `v0.69` tag object: https://api.github.com/repos/YosysHQ/yosys/git/tags/14c55bfd9941046244300f92bb707ff99be2c5b2
- Yosys `CHANGELOG` at `v0.69`: https://raw.githubusercontent.com/YosysHQ/yosys/v0.69/CHANGELOG
- Yosys `frontends/verific/verific.cc` at `v0.69`: https://raw.githubusercontent.com/YosysHQ/yosys/v0.69/frontends/verific/verific.cc
- Yosys `README.md` at `v0.69`: https://raw.githubusercontent.com/YosysHQ/yosys/v0.69/README.md
