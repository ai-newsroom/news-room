---
edition: ai
decision: publish-candidate
title: "ROCm.AI의 실제 출발선: experimental CLI와 AMD Skills로 확인한 도입 범위"
date: 2026-07-28
subject: "AMD ROCm.AI, AMD Skills commit 228980933abd97a8aa4a2656c8ea3ae9e8b590c7, ROCm CLI v0.1.0-experimental.1"
summary: "AMD가 ROCm.AI를 공개한 뒤 AMD Skills와 ROCm CLI의 실행 가능한 artifact가 확인됐습니다. 다만 CLI는 Tech Preview이며, Hyperloom·rocm-doctor 등 발표 범위의 일부는 아직 catalog에서 planned 또는 staging 상태라 production 도입 판단과 분리해야 합니다."
evidence_ceiling: E2
reproducibility: R2
conflicts: ["AMD는 ROCm.AI와 관련 code·release의 발표 및 유지관리 주체입니다. 이 기사에는 AMD의 사전 접근, 계정·hardware·credit 제공, 후원 또는 embargo가 없었습니다."]
---

AMD가 7월 23일 공개한 ROCm.AI에서 중요한 변화는 개발자가 AMD GPU용 AI stack을 agent skill과 단일 CLI로 다룰 수 있는 공개 경로가 생겼다는 점입니다. 7월 27일에는 Linux·Windows용 ROCm CLI `v0.1.0-experimental.1` binary도 공개됐습니다. 다만 발표가 묶어 설명한 설치·serving·진단·최적화 기능은 같은 성숙도가 아니므로, 지금 도입할 수 있는 artifact와 계획된 기능을 나눠 봐야 합니다.

## 세 줄 요약

- ROCm.AI는 AMD Skills, ROCm CLI, ROCm Console, Hyperloom을 한 개발 경험으로 설명하지만, 현재 공개 artifact에서 확인되는 중심은 agent instruction catalog와 experimental CLI입니다.
- ROCm CLI `v0.1.0-experimental.1`에는 Linux·Windows x86_64 archive, SHA-256 sidecar와 detached signature가 있으며, 설치 script는 archive checksum을 확인합니다.
- AMD Skills와 CLI 모두 Tech Preview입니다. Hyperloom optimizer와 `rocm-doctor` 같은 항목은 catalog에서 planned 또는 staging 상태이므로 production 자동화의 전제로 삼을 수 없습니다.

## SW 엔지니어를 위한 판단

- **지금 확인할 수 있는 것:** 고정 commit의 AMD Skills에는 설치·serving·trace 분석 절차와 helper script가 있고, 고정 tag의 ROCm CLI에는 환경 검사, runtime 설치, model serving, telemetry와 chat을 위한 code와 배포 archive가 있습니다.
- **도입 전에 확인할 것:** skill이 허용하는 shell 작업, 외부 image·model download, GPU·OS 지원 범위, `main` 대신 고정할 commit, CLI installer의 checksum·signature 정책과 rollback 절차를 검토해야 합니다.
- **아직 결론 내릴 수 없는 것:** Hyperloom의 실제 최적화 성능, fresh host에서 production까지 걸리는 시간, 여러 GPU와 model 조합의 성공률, 장기 지원 version과 API 안정성은 공개 artifact만으로 판단할 수 없습니다.

## 이 공개의 의의와 편집 판단

AMD Skills는 coding agent가 읽는 `SKILL.md`, helper script, reference와 governance card를 묶습니다. ROCm CLI는 설치와 환경 검사, model serving, telemetry를 command와 terminal UI로 노출합니다. 두 artifact가 결합되면 agent가 자연어 요청을 받아 AMD가 정한 절차를 읽고, 사용자의 허가 아래 CLI나 script를 실행하는 흐름을 만들 수 있습니다.

**편집 판단:** 이 공개의 의미는 AMD GPU가 갑자기 더 빨라졌다는 데 있지 않습니다. hardware enablement 지식을 문서 검색에서 agent가 읽을 수 있는 실행 계약으로 옮기고, 그 아래에 script 가능한 CLI를 두었다는 데 있습니다. 따라서 첫 도입 판단도 benchmark 순위보다 instruction provenance, command permission, version pinning, 실패 시 rollback을 중심으로 내려야 합니다.

## ROCm.AI는 하나의 제품명 아래 서로 다른 층을 묶습니다

AMD의 발표문은 ROCm.AI를 AI-assisted development, intelligent deployment, AI-powered optimization을 묶는 경험으로 설명합니다. 구성 요소로는 AMD Skills, ROCm CLI, ROCm Console, ROCm Hyperloom을 제시합니다. 이 설명은 제품 방향을 확인하는 P1 원문이지만, 모든 요소가 같은 날 같은 상태로 배포됐다는 증거는 아닙니다.

공개 code를 보면 첫 번째 층은 instruction입니다. AMD Skills commit `228980933abd97a8aa4a2656c8ea3ae9e8b590c7`의 catalog에는 local AI 사용·application 통합, Instinct·EPYC serving, kernel 평가와 trace 분석 skill이 실제 경로로 연결됩니다. 각 skill은 agent가 언제 활성화해야 하는지, 어떤 script와 data를 읽는지, 어느 지점에서 사용자 확인을 받아야 하는지 정의합니다.

두 번째 층은 실행입니다. ROCm CLI tag `v0.1.0-experimental.1`이 가리키는 commit `cae77819a58ee8448a14160ce989832f500e6cc4`에는 Rust workspace와 Linux·Windows installer가 있습니다. CLI 문서는 `rocm examine`, `rocm install sdk`, `rocm serve <model>`, `rocm dash`를 공개 surface로 설명합니다.

세 번째 층은 최적화 자동화입니다. 발표문은 Hyperloom이 profiling, 병목 식별, code 수정, 성능과 정확성 검증을 수행한다고 설명합니다. 그러나 AMD Skills의 고정 catalog에서는 `hyperloom-kernel-optimizer`가 planned로 표시됩니다. 공개 artifact를 실행해 그 성능을 검사할 경로가 확보되지 않았으므로, 이 기사에서는 Hyperloom의 효과를 E2 claim으로 올리지 않습니다.

## agent는 skill을 읽고 CLI와 기존 도구를 호출합니다

`serving-llms-on-instinct` skill은 AMD Instinct GPU에서 vLLM endpoint를 띄우는 절차를 정의합니다. 먼저 `amd-smi`로 GPU와 VRAM, ROCm version을 감지하고, validation script가 환경 오류를 확인합니다. 이어 model recipe와 GPU override를 합쳐 container command를 만들고, VRAM 추정 뒤 model·precision·tensor parallelism·context·port를 사용자에게 제시해 확인을 받도록 합니다.

이 흐름은 새로운 model server protocol을 만드는 것이 아닙니다. skill은 Docker, Hugging Face model, vLLM recipe와 AMD runtime을 연결하는 opinionated orchestration layer입니다. 따라서 skill 설치만으로 driver, container runtime, model license, gated model token, 충분한 VRAM이 생기지는 않습니다.

CLI는 더 낮은 실행 surface를 제공합니다. 문서상 `rocm install sdk`는 TheRock ROCm wheel과 대응 PyTorch stack을 관리 환경에 설치하고, `rocm serve qwen`은 GPU에 맞는 engine을 통해 OpenAI-compatible endpoint를 시작합니다. dashboard의 live telemetry는 Unix domain socket을 사용하므로 Linux 또는 WSL이 필요하며, 다른 환경에서는 synthetic data를 쓰는 `rocm dash --demo`만 별도로 확인할 수 있습니다.

agent와 CLI를 함께 쓸 때는 두 권한 경계를 나눠야 합니다. skill은 무엇을 해야 하는지 결정하는 instruction이고, CLI·Docker·shell은 host를 바꾸는 실행기입니다. repository를 신뢰한다는 판단이 곧 model download, driver 설치, container 삭제, shell profile 변경까지 승인한다는 뜻은 아닙니다.

## 7월 27일 binary release는 실제로 내려받을 수 있습니다

GitHub release `v0.1.0-experimental.1`은 7월 27일 공개됐습니다. release asset에는 Linux amd64 `tar.gz`와 Windows amd64 `zip`이 있고, 각 archive에 SHA-256 sidecar와 RSA/SHA-256 detached signature가 붙어 있습니다. Linux generic archive의 공개 checksum은 `93bafca6b3f12eba027504a09ac22f44bb0a37caf8ef032d24817b5764164733`입니다.

고정 tag의 `install.sh`는 기본 channel을 `release`로 두고 archive와 `.sha256`을 내려받아 local digest와 비교한 뒤 설치합니다. 설치 위치의 기본값은 `$HOME/.local/bin`이며, 설정에 따라 shell profile의 `PATH`도 갱신합니다. 자동화에서 사용한다면 installer를 바로 pipe로 실행하기보다 tag의 script와 checksum을 먼저 고정하고, 별도 test account나 image에서 filesystem 변화를 확인하는 편이 안전합니다.

signature는 checksum과 다른 위협을 다룹니다. checksum sidecar만 함께 바뀌면 변조를 막지 못하지만, 신뢰한 public key로 검증한 signature는 release 주체를 확인하는 데 도움이 됩니다. 다만 release trust 문서와 installer의 기본 동작을 조직 정책에 맞춰 따로 검토해야 하며, signature asset이 존재한다는 사실만으로 자신의 배포 pipeline이 이를 필수 검증한다고 가정하면 안 됩니다.

release metadata는 `prerelease: false`이고 본문은 latest stable release라는 표현을 사용합니다. 동시에 tag 이름에는 `experimental`이 들어가고 README는 API·command·behavior가 예고 없이 바뀔 수 있는 Tech Preview라고 명시합니다. production 지원 수준을 판단할 때 GitHub UI flag보다 version 이름과 README의 안정성 경고를 우선하는 편이 보수적입니다.

## AMD Skills는 설치 전에 instruction diff를 검토해야 합니다

AMD Skills는 `npx skills add amd/skills` 설치 경로와 Codex, Claude Code, Cursor, Gemini CLI 호환성을 제시합니다. 그러나 catalog README는 Tech Preview에서 skill, category, description이 자주 바뀔 수 있다고 밝힙니다. `main`을 그대로 따라가면 agent의 실행 절차가 application code 변경 없이 달라질 수 있습니다.

production 또는 공용 개발 환경에서는 catalog commit과 개별 skill path를 함께 고정해야 합니다. `SKILL.md`만 보지 말고 함께 호출하는 Python script, recipe cache, container image, network endpoint와 환경 변수 처리도 review 대상에 넣어야 합니다. federated skill은 upstream commit을 기록하는 `.federated.json`까지 확인해야 원래 code provenance를 추적할 수 있습니다.

현재 catalog는 “공개됨”과 “계획됨”을 한 표에서 구분합니다. `rocm-doctor`와 `apu-memory-tuner`의 directory가 `staging/`에 보이더라도 catalog에서 planned인 상태는 바뀌지 않습니다. staging code가 존재한다는 이유로 지원되는 interface나 production capability로 간주해서는 안 됩니다.

## 작은 sandbox 검증부터 시작할 수 있습니다

첫 검증은 AMD GPU가 없는 환경에서도 가능합니다. 고정 commit의 catalog와 plugin manifest를 읽고, 설치될 skill 목록과 `allowed-tools`, script hash, 외부 URL을 inventory로 만들 수 있습니다. ROCm CLI source는 `cargo build --release` 경로와 synthetic dashboard demo를 제공하지만, 이 기사에서는 build나 demo를 실행하지 않았습니다.

두 번째 검증은 disposable AMD host에서 수행해야 합니다. exact tag의 archive와 checksum을 별도로 내려받아 digest를 확인하고, shell profile 자동 변경을 끈 상태에서 격리 경로에 설치합니다. `rocm examine` 결과를 저장한 뒤 managed runtime 설치 전후의 driver, package, disk, network 변화를 비교합니다.

세 번째 검증에서 작은 공개 model 하나를 고정해 endpoint health와 rollback을 검사합니다. model ID, container image digest, ROCm·driver version, GPU, VRAM, engine, context와 port를 기록합니다. 여기까지 통과한 뒤에만 coding agent가 skill을 자동 선택하고 host 변경 command를 제안하도록 범위를 넓히는 편이 좋습니다.

성능 검증은 별도입니다. 발표문의 “faster to build”나 Hyperloom 최적화 효과를 확인하려면 fresh-host setup 시간, 수작업 intervention 수, 성공률, serving latency·throughput, 품질 동등성, 전력과 비용을 같은 조건에서 측정해야 합니다. 공개 발표와 code 존재만으로 이 수치를 채울 수는 없습니다.

## 공개 자료가 허용하는 결론은 Tech Preview 평가까지입니다

- ROCm CLI release asset은 Linux와 Windows x86_64에 한정되며, 모든 AMD GPU·OS 조합의 동작을 보증하지 않습니다.
- live dashboard telemetry는 문서상 Linux 또는 WSL을 요구합니다. Windows binary가 있다는 사실과 모든 dashboard 기능의 Windows 지원은 같은 claim이 아닙니다.
- 이 기사에서는 AMD GPU에서 CLI를 설치하거나 model을 serving하지 않았고, 공개 code와 release artifact만 검사했습니다.
- Hyperloom의 benchmark, 지원 workload, 반복 수, 실패 분포와 공개 실행 artifact는 확인하지 못했습니다.
- AMD Skills의 일부 항목은 planned 또는 staging이며, Tech Preview catalog는 자주 바뀔 수 있습니다.
- release의 `prerelease` metadata, stable 표현, experimental tag와 Tech Preview 경고가 완전히 같은 성숙도 신호를 주지 않습니다.

## 도입 판단: instruction과 실행기를 따로 승인해야 합니다

AMD hardware를 검토 중인 팀이라면 ROCm.AI를 production 자동화로 바로 채택하기보다 evaluation track으로 넣을 근거는 충분합니다. 공개 skill과 CLI가 있어 자연어 안내를 실제 command와 연결하는 구조, 지원 범위, 실패 처리를 inspect할 수 있기 때문입니다.

도입 순서는 AMD Skills commit pinning과 instruction review, ROCm CLI exact-tag sandbox 설치, 고정 model의 endpoint smoke test, agent 권한 확대 순서가 적절합니다. 각 단계의 rollback을 독립적으로 유지하면 skill update가 문제인지, CLI나 runtime change가 문제인지 구분할 수 있습니다.

Hyperloom과 planned skill은 별도 gate에 남겨야 합니다. 공개 실행 artifact와 같은 조건의 benchmark가 나오기 전에는 “자동 최적화가 production tuning 비용을 줄인다”는 결론을 내리지 않습니다. 현재 확인된 변화는 AMD가 agent-readable instruction과 experimental execution surface를 공개했다는 데 있습니다.

## 이해상충과 취재 조건

AMD는 ROCm.AI를 발표하고 AMD Skills와 ROCm CLI repository, release asset을 운영합니다. 기능 범위와 성숙도 설명은 개발 주체가 선택한 공개 자료이며, 독립적인 production 운영 결과는 아닙니다.

이 기사에는 AMD의 사전 briefing, hardware·cloud account·credit 제공, 후원, 광고, NDA 또는 embargo가 없었습니다. 공개 발표, GitHub release metadata, 고정 commit의 README·skill·installer·release trust 문서만 확인했습니다. binary를 실행하거나 AMD GPU에서 model serving과 성능 측정을 수행하지 않았습니다.

## 근거 원장

| Claim | 판정 | 출처/근거 | 등급 | 한계·재확인 조건 |
|---|---|---|---|---|
| ROCm.AI는 AMD Skills, ROCm CLI·Console과 Hyperloom을 한 개발 경험으로 제시합니다 | AMD 발표로 확인하고 공개 artifact 범위와 분리 | AMD ROCm.AI 발표, AMD Skills commit `228980933abd97a8aa4a2656c8ea3ae9e8b590c7`, ROCm CLI release | P1+P2 / E2 / R2 | 발표의 통합 경험 전체를 실행하지 않았으며 Hyperloom 공개 artifact는 미확인 |
| ROCm CLI `v0.1.0-experimental.1`은 Linux·Windows x86_64 archive와 checksum·signature sidecar를 공개했습니다 | GitHub release asset과 tag로 확인 | release tag, commit `cae77819a58ee8448a14160ce989832f500e6cc4`, checksum asset | P2 / E2 / R2 | binary 미실행, 지원 GPU·OS 전체 조합 미검증 |
| installer는 archive SHA-256을 검사하고 기본적으로 `$HOME/.local/bin`과 shell `PATH`를 다룹니다 | 고정 tag의 script로 확인 | `install.sh` at `cae77819a58ee8448a14160ce989832f500e6cc4` | P2 / E2 / R2 | 실제 설치를 실행하지 않았고 signature 강제 정책은 별도 검토 필요 |
| AMD Skills에는 실제 catalog skill과 planned·staging 항목이 함께 존재합니다 | README와 repository tree로 확인 | AMD Skills README·skill·staging tree at `228980933abd97a8aa4a2656c8ea3ae9e8b590c7` | P2 / E2 / R2 | catalog가 Tech Preview라 후속 commit에서 상태 변경 가능 |
| production 도입은 instruction pinning, sandbox CLI, 고정 model smoke test, agent 권한 확대를 나눠야 합니다 | 편집 판단 | 위 release·skill·installer claim에서 파생 | 편집 판단 / E2 / R2 | 조직별 hardware, 보안 정책과 workload로 다시 검증 필요 |

## 출처

1. AMD, “ROCm.AI: The AI-Native Developer Experience for Building on AMD”, 2026-07-23, 조회 2026-07-28: https://www.amd.com/en/blogs/2026/rocm-ai-the-ai-native-developer-experience-for-building.html
2. ROCm CLI `v0.1.0-experimental.1` release, 2026-07-27: https://github.com/ROCm/rocm-cli/releases/tag/v0.1.0-experimental.1
3. ROCm CLI source, tag commit `cae77819a58ee8448a14160ce989832f500e6cc4`: https://github.com/ROCm/rocm-cli/tree/cae77819a58ee8448a14160ce989832f500e6cc4
4. ROCm CLI README at the tag commit: https://github.com/ROCm/rocm-cli/blob/cae77819a58ee8448a14160ce989832f500e6cc4/README.md
5. ROCm CLI Linux installer at the tag commit: https://github.com/ROCm/rocm-cli/blob/cae77819a58ee8448a14160ce989832f500e6cc4/install.sh
6. ROCm CLI release trust 문서 at the tag commit: https://github.com/ROCm/rocm-cli/blob/cae77819a58ee8448a14160ce989832f500e6cc4/docs/release-trust.md
7. Linux amd64 generic archive SHA-256 sidecar: https://github.com/ROCm/rocm-cli/releases/download/v0.1.0-experimental.1/rocm-cli-linux-amd64.tar.gz.sha256
8. AMD Skills, commit `228980933abd97a8aa4a2656c8ea3ae9e8b590c7`: https://github.com/amd/skills/tree/228980933abd97a8aa4a2656c8ea3ae9e8b590c7
9. AMD Skills catalog README at the fixed commit: https://github.com/amd/skills/blob/228980933abd97a8aa4a2656c8ea3ae9e8b590c7/README.md
10. `serving-llms-on-instinct` skill at the fixed commit: https://github.com/amd/skills/blob/228980933abd97a8aa4a2656c8ea3ae9e8b590c7/skills/serving-llms-on-instinct/SKILL.md
11. AMD Skills staging `rocm-doctor` at the fixed commit: https://github.com/amd/skills/tree/228980933abd97a8aa4a2656c8ea3ae9e8b590c7/staging/rocm-doctor
