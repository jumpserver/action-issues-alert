#!/bin/bash -eix

WEB_HOOK=${INPUT_HOOK}
REPO=${INPUT_REPO-$GITHUB_REPOSITORY}
TYPE=${INPUT_TYPE-all}
INACTIVE_DAY=${INPUT_INACTIVE-30}
RECENT_DAY=${INPUT_RECENT-2}

python /check_inactive_issues.py "${REPO}" --hook "${WEB_HOOK}" --type "${TYPE}" \
    --inactive "${INACTIVE_DAY}" --recent "${RECENT_DAY}"
