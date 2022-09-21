#!/bin/bash
set -e

cd /opt/updating-delivery

export $(grep -v '^#' .env | xargs -d '\n')

source env/bin/activate

pip install httpie

git pull

pip install -r requirements.txt
npm ci --dev

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

./manage.py collectstatic --noinput
./manage.py migrate

systemctl reload nginx.service
systemctl restart start-burger.service

GIT_REV=$(git rev-parse --short HEAD)
if [[ $? -ne 0 ]]; then
    GIT_REV="error"
fi

http POST https://api.rollbar.com/api/1/deploy X-Rollbar-Access-Token:$ROLLBAR_ACCESS_TOKEN \
    environment=production \
    revision=$GIT_REV \
    rollbar_name=b10t \
    local_username=circle-ci \
    comment=comment \
    status=succeeded

deactivate

echo "Проект успешно обновлён."
