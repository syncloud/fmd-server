#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

DISTRO=$1
ARCH=$2
SPEC=$3
if [[ -z "${DISTRO}" ]] || [[ -z "${ARCH}" ]] || [[ -z "${SPEC}" ]]; then
    echo "usage $0 distro arch spec"
    exit 1
fi

NAME=fmd-server
DOMAIN="${DISTRO}.com"
APP_DOMAIN="${NAME}.${DOMAIN}"

getent hosts $APP_DOMAIN | sed "s/$APP_DOMAIN/auth.$DOMAIN/g" | tee -a /etc/hosts
cat /etc/hosts

APP_ARCHIVE_PATH=$(realpath $(cat ${DIR}/package.name))

cd ${DIR}/test
./deps.sh
py.test -x -s ${SPEC} --distro=$DISTRO --app-archive-path=$APP_ARCHIVE_PATH --app=$NAME --arch=$ARCH
