# EDA판 일일 자동 발행과 발행 후 개선

> 상태: 2026-08-13 사용자의 명시적 승인으로 활성화

## 운영 결과

EDA판은 매일 07:00 `Asia/Seoul`에 시작하는 단일 발행 실행의 세 번째 판이다. 시사판의
공개 확인과 AI판의 발행 또는 `no-publish` 결정이 끝난 뒤에만 EDA 후보를 만든다. 하루
최대 한 편이며 이미 같은 Seoul 날짜의 EDA 기사가 있으면 다시 만들지 않는다.

주요 EDA 벤더, 표준 기구, DesignCon·DAC·DVCon과 논문·공개 artifact를 조사한다. 고정 URL
체크리스트를 기계적으로 순회하지 않고 source registry를 발견 seed로 사용한다. 최근 EDA
기사 title·subject를 읽어 같은 발표를 새 기사처럼 반복하지 않는다.

## 고정 안전 경계

- 후보 총점은 7 이상, 중심 주장은 `E2` 이상이어야 한다.
- 중심 분석에는 서로 다른 HTTPS 원문이 최소 두 개 필요하다. 같은 발표를 옮긴 검색 결과와
  2차 기사 둘은 세지 않는다.
- 벤더 발표, 저자 보고, 독립 확인과 미확인 범위를 기사에서 분리한다.
- 뉴스 설명·기술 이해·기술적 의미와 검증 과제의 세 의미 층은 작성 지침과 회고에서
  확인하되 특정 소제목으로 강제하지 않는다.
- 허용된 frontmatter, 검증 부록,
  claim-source ledger, 이해상충 일치,
  publication ID, route 중복과 artifact hash를 결정적으로 확인한다.
- 첫 검증 실패에는 기존 주제·주장·수치·source를 보존하는 형식 복구 턴을 한 번만 허용한다.
- 두 번째 검증도 실패하면 content materialize, commit, push, deploy 없이 중단한다.
- `no-publish`는 공개 route를 만들지 않으며 같은 날짜 재실행에서 보존한다.
- 자동 권한은 `eda-auto-publish-v1`에만 적용하며 AI판·시사판으로 상속하지 않는다.
- 전체 repository test, site test와 production build가 성공한 정확히 세 파일만 finalizer가
  fast-forward push한다.
- Pages 배포 뒤 공개 URL의 HTTP 상태, 제목, 발행 ID와 자동 출고 표식을 확인한다.

## 원문 두 개의 의미

원문 둘은 숫자를 채우기 위한 중복 링크가 아니다. 중심 판단의 서로 다른 부분을 독자가
직접 검사할 수 있는 조합이어야 한다.

- 공식 제품 발표 + 연결 논문
- release note + manual 또는 support matrix
- 학회 논문 + 공개 코드·benchmark
- 표준 변경 원문 + 구현 또는 conformance artifact

공식 발표 하나로 출시 사실만 확인되고 실제 변화를 분석할 두 번째 원문이 없다면 자동
기사는 만들지 않는다. 이 규칙은 매일 빈칸을 억지로 채우는 것보다 `no-publish`를 택하게
하는 최소 품질 경계다.

## 실행 경계

기사 생성 턴은 `var/runs/eda` 아래 후보와 evidence 또는 `no-publish` 결정만 쓴다. 모델은
Git, 공개 content·decision 경로, deploy, schedule과 self-improvement 상태를 수정하지 않는다.
결정적 publisher가 통과한 후보만 다음 세 파일로 materialize한다.

```text
content/eda/<publication-id>/article.md
decisions/eda/<publication-id>/evidence.json
decisions/eda/<publication-id>/release.json
```

`scripts/publish-eda-candidate.py`도 외부 Git 동작을 하지 않는다. 상위 일일 entrypoint가 전체
검증을 마친 뒤 공통 finalizer와 공개 verifier를 순서대로 호출한다.

## 발행 후 자가개선 피드백

09:30 회고 routine은 시사·AI·EDA 중 공개 검증이 성공한 판의 article과 evidence·release를
읽는다. EDA판에서는 다음을 특히 확인한다.

1. 벤더 주장을 편집국 결론처럼 확대했는가.
2. 원문 두 개가 실제로 서로 다른 근거 역할을 하는가.
3. 뉴스 설명·쉽고 심층적인 기술 이해·기술적 의미와 검증 과제가 고정 판단 상자나 반복
   경고 없이 전달되는가.
4. 중요한 벤더·학회·논문 신호를 반복적으로 놓쳤는가.
5. 후보 생성·검증·배포에서 같은 실패나 수작업이 되풀이되는가.

회고는 하루 최대 한 건의 근거 있는 개선 proposal을 자동 생성할 수 있다. 그러나 자기
평가 직후 프롬프트나 코드를 직접 고치지 않는다. 실제 변경은 사람 승인, 별도 worker,
독립 review와 제한 finalization을 거친다. 효과는 해당 판의 이후 발행 3회에서 관찰한다.
