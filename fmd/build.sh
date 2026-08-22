#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

VERSION=$1
if [[ -z "${VERSION}" ]]; then
    echo "usage $0 version"
    exit 1
fi

BUILD_DIR=${DIR}/../build/snap/fmd
mkdir -p ${BUILD_DIR}

ARCH=$(dpkg --print-architecture)
case ${ARCH} in
    amd64) FARCH=amd64 ;;
    arm64) FARCH=arm64 ;;
    armhf) FARCH=arm ;;
    *) echo "unsupported arch ${ARCH}"; exit 1 ;;
esac

${DIR}/../apt.sh wget ca-certificates unzip

${DIR}/../download-retry.sh \
    https://packages.fmd-foss.org/server/fmd-server-v${VERSION}.zip \
    ${DIR}/../build/fmd-server.zip

unzip -o -j ${DIR}/../build/fmd-server.zip \
    fmd-server-${FARCH} fmd-server-ctl-${FARCH} \
    -d ${BUILD_DIR}

mv ${BUILD_DIR}/fmd-server-${FARCH} ${BUILD_DIR}/fmd-server
mv ${BUILD_DIR}/fmd-server-ctl-${FARCH} ${BUILD_DIR}/fmd-server-ctl
chmod +x ${BUILD_DIR}/fmd-server ${BUILD_DIR}/fmd-server-ctl
