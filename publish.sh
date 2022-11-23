#!/usr/bin/env bash

GH_REPO_USER=sarumaj
GH_REPO=MyCampusMobile
GH_USER=sarumaj
GH_TOKEN=$(git config --global --list | grep url | sed -E 's|.*:(.*)@.*|\1|g')
GH_TARGET=main
ASSETS_PATH=bin
VERSION=$(cat main.py | grep '__version__ = ' | sed -rE 's|.*"([0-9]+\.[0-9]+\.[0-9]+\w?)".*|\1|g')

if [[ ! -z $(git tag --list $VERSION) ]]
then
git add -u
git commit -m "$VERSION release" --no-verify
git tag "v${VERSION}"
git push --follow-tags
git push origin "v${VERSION}" 
fi

rel_id=$(
    curl \
        --silent --user "$GH_USER:$GH_TOKEN" \
        -X GET https://api.github.com/repos/${GH_REPO_USER}/${GH_REPO}/releases/tags/v${VERSION} \
    | jq -r '.id'
)
echo Found release ${rel_id}

if [[ $rel_id -eq null ]]
then
    echo Creating release
    response=$(
        curl \
            --silent --user "$GH_USER:$GH_TOKEN" \
            -X POST https://api.github.com/repos/${GH_REPO_USER}/${GH_REPO}/releases \
            --data '{
                "tag_name": "v'$VERSION'",
                "target_commitish": "'$GH_TARGET'",
                "name": "v'$VERSION'",
                "body": "version release: '$VERSION'",
                "draft": false,
                "prerelease": false
            }')
    rel_id=$( jq -r '.id' <<<$response)
else 
    echo Updating release ${release_id}
    response=$(
        curl \
            --silent --user "$GH_USER:$GH_TOKEN" \
            -X PATCH https://api.github.com/repos/${GH_REPO_USER}/${GH_REPO}/releases/$rel_id \
            --data '{
                "tag_name": "v'$VERSION'",
                "target_commitish": "'$GH_TARGET'",
                "name": "v'$VERSION'",
                "body": "version release: '$VERSION'",
                "draft": false,
                "prerelease": false
            }')
fi
echo Result: ${response}


for i in $ASSETS_PATH/* ; do
    file_name=$(basename $i)
    echo uploading ${file_name}
    curl \
        --user "$GH_USER:$GH_TOKEN" \
        -X POST https://uploads.github.com/repos/${GH_REPO_USER}/${GH_REPO}/releases/${rel_id}/assets?name=${file_name} \
        --header 'Content-Type: application/octet-stream' \
        --upload-file "./${ASSETS_PATH}/${file_name}" 2>&1 >/dev/null
done