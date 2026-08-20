#!/bin/bash -e

APP_DOMAIN=$1
if [[ -z "${APP_DOMAIN}" ]]; then
    echo "usage $0 app.domain"
    exit 1
fi

for i in $(seq 1 120); do
    CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "https://${APP_DOMAIN}/" || true)
    if [[ "${CODE}" == "200" ]]; then
        echo "${APP_DOMAIN} is up"
        exit 0
    fi
    echo "waiting for ${APP_DOMAIN}, last status ${CODE}"
    sleep 5
done

echo "${APP_DOMAIN} did not come up"
exit 1
