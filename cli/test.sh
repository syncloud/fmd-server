#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap
${BUILD_DIR}/bin/cli --help
${BUILD_DIR}/meta/hooks/install --help
${BUILD_DIR}/meta/hooks/configure --help
