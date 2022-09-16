#!/bin/bash
set -e

cd /opt/updating-delivery

source env/bin/activate

git pull

pip install -r requirements.txt
npm ci --dev

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

./manage.py collectstatic --noinput
./manage.py migrate

systemctl reload nginx.service
systemctl restart start-burger.service

deactivate

echo "Проект успешно обновлён."
