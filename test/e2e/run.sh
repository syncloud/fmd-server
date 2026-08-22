#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ARTIFACT_SUBDIR="${1:-e2e}"
SPEC="${2:-specs/01-smoke.spec.ts}"
PROJECT="${3:-desktop}"

NAME=fmd-server
export PLAYWRIGHT_DOMAIN="${PLAYWRIGHT_DOMAIN:-bookworm.com}"
export PLAYWRIGHT_APP_DOMAIN="${NAME}.${PLAYWRIGHT_DOMAIN}"
export PLAYWRIGHT_USER="${PLAYWRIGHT_USER:-user}"
export PLAYWRIGHT_PASSWORD="${PLAYWRIGHT_PASSWORD:-Password1}"
export PLAYWRIGHT_PROJECT="${PROJECT}"
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
