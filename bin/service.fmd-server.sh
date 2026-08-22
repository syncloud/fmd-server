#!/bin/bash -e

/bin/rm -f ${SNAP_DATA}/fmd.sock

exec ${SNAP}/fmd/fmd-server serve --config ${SNAP_DATA}/config/fmd-server.yml
