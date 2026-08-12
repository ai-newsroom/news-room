# EDA News 공개 파일럿

> 상태: 2026-08-13 사용자 승인으로 공개 파일럿 시작

## 목표와 독자

EDA News는 반도체 설계·검증·구현·signoff·PCB·패키징 도구와 연구의 변화가 실제
workflow에 주는 영향을 설명한다. 특정 분야의 전문가는 다른 분야의 약어까지 모두 알지
못한다는 전제에서, 먼저 쉬운 흐름 설명을 제공하고 버전·조건·근거를 뒤에 붙인다.

첫 공개 파일럿의 목적은 매일 많은 글을 생산하는 것이 아니라 다음 세 경계가 함께 작동하는지
확인하는 것이다.

1. 벤더 발표와 독립 근거를 분리한다.
2. 사람의 명시적 승인을 release record로 남긴다.
3. article·evidence hash가 일치한 승인 기사만 `/eda/`에 보인다.

## 센싱 범위

공식 seed registry는 `editions/eda/sources/primary-sources.json`에 둔다.

- 벤더: Cadence, Siemens EDA, Zuken, Synopsys, Ansys, Dassault Systèmes CST,
  Keysight
- 학회·proceedings: DesignCon, DAC, DVCon, ACM Digital Library
- 연구·표준·공개 flow: arXiv cs.AR, IEEE·Accellera·Si2, OpenROAD·OpenLane,
  공개 benchmark

이 목록은 기사를 자동으로 고르는 RSS 목록이 아니다. 새로운 후보를 발견한 뒤 정확한
release note, 논문, standard, code, benchmark와 실행 artifact로 이동하기 위한 출발점이다.
블로그와 행사 소개는 제품·발표 사실의 1차 자료일 수 있지만 성능 우월성의 독립 근거가
되지는 않는다.

사용자가 적은 `CTS`는 EDA 벤더 문맥상 Dassault Systèmes의 `CST Studio Suite`로 해석했다.
다른 대상을 뜻했다면 source registry에서 명시적으로 교체한다.

## 파일럿 발행 경계

EDA runtime은 `on-demand`, `schedule.enabled=false`, `prepare-only`를 유지한다. Candidate는
`scripts/publish-eda-candidate.py`가 frontmatter, 기사 구조, 선정 점수, 중심 E2 근거,
source URL, 이해상충, release gate를 결정적으로 검증한다.

검증 성공은 공개 승인이 아니다. Materialize에는 승인자, 승인 근거와 범위를 명령행에서
모두 전달해야 한다. 생성되는 human release는 article·evidence hash와 `/eda/` route만
승인한다. 이 단계 자체는 commit, push, deploy를 하지 않는다. 이후 isolated clean
worktree에서 전체 site test를 통과한 정확히 세 파일만 finalizer가 fast-forward push한다.

자동 센싱과 정기 발행은 파일럿 품질을 확인한 뒤 별도 결정한다. 켜게 되더라도 인간 승인
요건을 바꾸려면 edition contract와 validator를 함께 바꾸고 새 정책 ID로 검토해야 한다.

## 첫 기사 결정

첫 주제는 Cadence의 2026-06-30 글 `The Feedback Loop Is the Moat`다. 기사 결론은 다음처럼
좁힌다.

- tool feedback이 agent의 다음 행동에 도움이 된다는 기술 가설은 공개 연구로 E2까지
  뒷받침한다.
- Cadence 제품 통합이 경쟁 제품보다 우월하거나 지속 가능한 moat라는 주장은 독립 비교가
  없으므로 벤더의 전략 주장으로 귀속한다.
- 상용 도구와 동일 환경을 재실행하지 않았으므로 재현성은 R1로 기록한다.

관련 article prompt와 문체 계약은 `editions/eda/editorial/`에 둔다. 독자가 기술의 핵심을
이해한 뒤 실무 적용 여부를 판단할 수 있도록 `지금 할 일 / 아직 미룰 일 / 다음 신호`를
고정한다.
