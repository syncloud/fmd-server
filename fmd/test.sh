#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

VERSION=$1
if [ -z "${VERSION}" ]; then
    echo "usage $0 version"
    exit 1
fi

BUILD_DIR=${DIR}/../build/snap/fmd

OUT=$(${BUILD_DIR}/fmd-server version)
echo "fmd-server version: ${OUT}"
echo "${OUT}" | grep -q "${VERSION}"

CTL=$(${BUILD_DIR}/fmd-server-ctl version)
echo "fmd-server-ctl version: ${CTL}"
echo "${CTL}" | grep -q "${VERSION}"
