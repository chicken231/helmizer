#!/bin/bash
set -e
TAG="${1}"

if [ $# -eq 0 ]; then
    echo "error: Tag required. Exiting"
    exit 1
fi

# pyinstaller
# pyinstaller -y --workpath ./build/pyinstaller/linux/workpath --specpath ./build/pyinstaller/linux/ --distpath ./build/pyinstaller/linux/ src/helmizer.py
# mkdir -p ./build/pyinstaller/linux/releases/
# zip -9 -T -r "./build/pyinstaller/linux/releases/${TAG}.zip" ./build/pyinstaller/linux/helmizer
# unlink ./build/pyinstaller/linux/releases/current || true
# ln -s ./build/pyinstaller/linux/helmizer/helmizer ./build/pyinstaller/linux/releases/current

# docker
DOCKER_CREATE_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
printf "\n * Docker container label (timestamp): %s" "$DOCKER_CREATE_DATE"

docker build \
    -t docker.pkg.github.com/chicken231/helmizer/helmizer:${TAG} \
    -t docker.pkg.github.com/chicken231/helmizer/helmizer:latest . \
    --label "org.opencontainers.image.created=$DOCKER_CREATE_DATE" \
    --label "org.label-schema.build-date=$DOCKER_CREATE_DATE" \

echo "Push to container registry?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) docker push docker.pkg.github.com/chicken231/helmizer/helmizer:${TAG}; exit;;
        No ) echo "No further action being taken"; exit;;
    esac
done