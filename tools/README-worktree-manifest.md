# 읽기 전용 worktree 보존 manifest

> 상태: fixture와 현재 dirty worktree에서 설치를 검증하는 capability experiment.
> 다음 10개 work turn의 성과 관찰은 아직 끝나지 않았다.

`worktree_manifest.py`는 turn 시작 시점에 이미 존재한 Git 변경을 보존하고, 이번 turn에
허용한 새 변경 경로만 분리해 설명하기 위한 도구다. reset, stash, checkout, add, commit,
파일 생성·수정·삭제를 하지 않는다. Git에는 `--no-optional-locks`와
`GIT_OPTIONAL_LOCKS=0`을 함께 적용해 status의 선택적 index refresh도 막는다.

## 1. capture 범위

`capture`는 `git status --porcelain=v1 -z --untracked-files=all`을 기준으로 다음을 JSON
stdout에 기록한다.

- 변경된 tracked path의 XY status, worktree SHA-256·크기·mode·mtime, index object id·mode·stage
- 모든 non-ignored untracked file의 SHA-256·크기·mode·mtime
- rename/copy의 원래 path, symlink라면 link target의 hash
- repository root와 HEAD object id
- capture 시간, 외부 호출 수와 내부 read-only Git 명령 수

중첩 untracked directory는 `--untracked-files=all`이 반환한 각 파일로 펼쳐 기록한다. Git이
ignored로 분류한 `.coco-agents/`, build output, dependency cache는 범위 밖이다. clean tracked
file도 시작 manifest에는 없지만 turn 도중 수정되면 post manifest의 새 changed path로
나타나므로 명시적 allowance가 없으면 위반이다.

파일을 hash하는 동안 inode·mode·size·mtime이 달라지면 조용히 불완전한 manifest를 만들지
않고 capture를 실패시킨다. tracked deletion은 `kind: missing`으로 기록한다. submodule은
gitlink와 directory metadata만 기록하고 내부 worktree를 재귀 hash하지 않는다.

## 2. turn 사용법

manifest 파일은 저장소 밖의 임시 디렉터리에 둔다. 아래 두 호출이 한 turn의 보존 증거다.

```bash
turn_manifest_dir="$(mktemp -d)"
python3 tools/worktree_manifest.py capture --repo . > "$turn_manifest_dir/pre.json"

# 승인된 repository 작업

python3 tools/worktree_manifest.py compare-live \
  --repo . \
  --before "$turn_manifest_dir/pre.json" \
  --allow-new 'tools/new-file.py' \
  --allow-new 'tools/new-fixtures/'
```

exact allowance는 해당 path 하나만 허용한다. 끝이 `/`인 allowance만 그 하위 path를
허용한다. 절대 경로, `..`, `.git` allowance는 거부한다. 시작 때 이미 변경돼 있던 path는
allowance와 일치해도 수정·삭제할 수 없으며 pre/post status, index, worktree fingerprint가
같아야 한다.

`compare-live`는 post manifest와 comparison을 stdout에 함께 내고 다음을 분리한다.

- `preexisting_preserved`: 시작 변경 가운데 status·index·내용·metadata가 같은 path
- `preexisting_changed`, `preexisting_missing`: 보존 위반
- `allowed_new`: 이번 turn allowance에 맞는 새 changed/untracked path
- `unexpected_new`: allowance에 없는 새 changed/untracked path
- HEAD 변경 여부, 시작 path 설명률, 위반 수, 사용하지 않은 allowance

비교가 통과하면 exit 0, 보존 위반이나 계약 오류가 있으면 exit 2다. `compare` subcommand로
저장된 pre/post manifest 둘을 비교할 수도 있다.

## 3. 이 실험의 관찰 기록

fixture 통과는 “반복적인 수동 확인을 줄였다”는 증거가 아니다. 다음 10개 work turn마다
result evidence에 아래 값만 기록한다.

```yaml
worktree_manifest_experiment:
  turn: 1
  before_entry_count: 0
  accounted_preexisting_count: 0
  explanation_rate: 1.0
  preservation_violations: 0
  unexpected_new: 0
  manual_invocations: 2
  capture_or_compare_error: null
  evaluation_omitted_path_count: 0 # 후속 독립 평가가 있을 때 갱신
```

10개 turn 뒤 다음처럼 결정한다.

- **retain:** 시작 변경 포착·설명률 100%, 보존 위반 0, 평가상 누락 0이고 기존의 개별
  status·hash 명령보다 수동 명령 수가 줄거나 동일한 비용으로 더 완전한 증거를 제공한다.
- **adjust:** 누락·쓰기 위반은 없지만 실행 시간이나 report 크기, 수동 명령 수가 과도하다.
  한 가지 좁은 조정만 다시 측정한다.
- **rollback:** path 누락, worktree 또는 index 쓰기, 기존 변경 손상 가운데 하나라도
  발생하거나 수동 절차보다 검증 비용만 증가한다. helper 사용을 중단하고 기존
  `git status --porcelain=v1 -uall`과 개별 hash 확인으로 돌아간다.

원 manifest와 실패 report는 원인을 확인할 때까지 보존한다. 도구는 자동으로 allowance를
늘리거나 위반을 승인하지 않는다.

## 4. 검증

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_worktree_manifest.py
```

fixture는 공백이 있는 repository와 path, staged 뒤 worktree가 수정된 tracked file,
여러 단계의 untracked directory, 허용된 새 하위 path, 예상 밖 새 path, 기존 content 변경,
기존 path 삭제, index-only 상태 변경과 위험한 allowance를 포함한다. capture 전후에는 임시
repository의 `.git`을 포함한 전체 파일·directory fingerprint가 같은지도 검사한다.
