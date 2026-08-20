#!/bin/bash -e

export FMD_DATABASEDIR=${SNAP_DATA}/db

exec ${SNAP}/fmd/fmd-server-ctl "$@"
