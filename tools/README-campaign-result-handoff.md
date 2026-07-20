# Campaign result 인계 사전검사

> 상태: 고정 fixture에서 설치를 검증한 capability experiment.
> 다음 10개 work turn의 성공 관찰은 아직 끝나지 않았다.

campaign_result_handoff.py는 conductor가 이미 지정받은 한 run의 result.json만 원자적으로
기록하고 즉시 다시 읽어 인계 계약을 검사한다. 다른 run이나 inbox·campaign 상태를 탐색하지
않으며, 네트워크·Git·publish·commit·push·deploy 기능이 없다.

## 경로와 계약

호출자는 repository root, campaign_run_ 뒤 32자리 소문자 16진수 run id, 절대 result
경로를 모두 제공해야 한다. 보조 명령은 다음 경로와 byte 단위로 같은 정규화 경로만 허용한다.

    <repo>/.coco-agents/campaigns/runs/<run-id>/result.json

다른 run, 다른 파일명, 상대 경로의 이탈, symlink인 run 디렉터리·result 파일은 실패한다.
run 디렉터리를 자동 생성하지 않는다. write는 stdin JSON을 쓰기 전에 완전히 파싱하고
top-level 및 follow-up 계약을 검사한다. 같은 run 디렉터리의 임시 파일을 flush·fsync한 뒤
os.replace하고, 지정된 result.json만 다시 열어 존재·regular file·UTF-8·JSON·계약과
SHA-256을 확인한다. 실패한 사전검사에서는 target이나 임시 파일을 만들지 않는다.

    python3 tools/campaign_result_handoff.py write \
      --repo /absolute/path/to/news-room \
      --run-id campaign_run_0123456789abcdef0123456789abcdef \
      --result-path /absolute/path/to/news-room/.coco-agents/campaigns/runs/campaign_run_0123456789abcdef0123456789abcdef/result.json \
      < /path/outside/repository/result-contract.json

    python3 tools/campaign_result_handoff.py verify \
      --repo /absolute/path/to/news-room \
      --run-id campaign_run_0123456789abcdef0123456789abcdef \
      --result-path /absolute/path/to/news-room/.coco-agents/campaigns/runs/campaign_run_0123456789abcdef0123456789abcdef/result.json

성공 report의 checks.read_back_parse_confirmed, result_path, result_sha256,
instrumentation.duration_ms를 해당 turn의 result evidence에 남긴다. 실패는 exit 2와
result_path_mismatch, result_missing, invalid_json, contract_fields_mismatch 같은 고정
error code를 반환한다.

## 10-turn 관찰과 결정

fixture 통과만으로 가설을 입증하지 않는다. 다음 10개 work turn마다 아래 관찰 한 줄을
result evidence에 남긴다.

    campaign_result_handoff_experiment:
      turn: 1
      result_missing: 0
      designated_path_parse_confirmed: true
      verification_duration_ms: 0.0
      other_campaign_state_files_modified: 0
      helper_error: null

10개 turn 뒤 result_missing 합계, parse 확인률, duration 중앙값을 수동 절차 baseline과
비교한다.

- **retain:** 누락 0, 지정 경로 parse 확인률 100%, 다른 상태 수정 0, 중앙값 2초 이하다.
- **adjust:** 누락·충돌은 없지만 report 또는 호출 방식의 작은 마찰만 관찰됐다.
- **rollback:** 누락이 다시 발생하거나 중앙값이 2초를 넘거나 다른 .coco-agents 상태를
  수정한다. helper를 제거하고 직접 기록 후 수동 JSON parse로 돌아간다.

## Fixture 검증

    PYTHONDONTWRITEBYTECODE=1 python3 tools/test_campaign_result_handoff.py

fixture는 잘못된 run 경로, 누락 파일, 깨진 JSON, 필수 필드 누락과 올바른 중첩 계약을
고정한다. 정상 write 뒤 immediate read-back, 임시 파일 정리, 다른 campaign fixture 파일의
불변성, 11회 subprocess verify의 중앙값 오버헤드도 검사한다.
