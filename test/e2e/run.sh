#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ARTIFACT_SUBDIR=$1
SPEC=$2
PROJECT=$3
if [[ -z "${ARTIFACT_SUBDIR}" ]] || [[ -z "${SPEC}" ]] || [[ -z "${PROJECT}" ]]; then
    echo "usage $0 artifact-subdir spec project"
    exit 1
fi

NAME=fmd-server
export PLAYWRIGHT_DOMAIN=bookworm.com
export PLAYWRIGHT_APP_DOMAIN=${NAME}.${PLAYWRIGHT_DOMAIN}
export PLAYWRIGHT_USER=user
export PLAYWRIGHT_PASSWORD=Password1
export PLAYWRIGHT_PROJECT=${PROJECT}
export PLAYWRIGHT_ARTIFACT_DIR="$( cd "${DIR}/../.." && pwd )/artifact/${ARTIFACT_SUBDIR}"
mkdir -p "${PLAYWRIGHT_ARTIFACT_DIR}"

${DIR}/../../apt.sh curl ca-certificates

getent hosts ${PLAYWRIGHT_APP_DOMAIN} | sed "s/${PLAYWRIGHT_APP_DOMAIN}/auth.${PLAYWRIGHT_DOMAIN}/g" | tee -a /etc/hosts
cat /etc/hosts

${DIR}/wait-app.sh ${PLAYWRIGHT_APP_DOMAIN}

cd ${DIR}
npm ci --no-audit --no-fund
npx tsc --noEmit -p tsconfig.json
npx playwright test --project="${PLAYWRIGHT_PROJECT}" "${SPEC}"
