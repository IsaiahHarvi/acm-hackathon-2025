#!/bin/bash

TARGET_DIR="data/TorNet"
mkdir -p $TARGET_DIR
cd $TARGET_DIR

for doi in \
    https://doi.org/10.5281/zenodo.12636522 \
    https://doi.org/10.5281/zenodo.12637032 \
    https://doi.org/10.5281/zenodo.12655151 \
    https://doi.org/10.5281/zenodo.12655179 \
    https://doi.org/10.5281/zenodo.12655183 \
    https://doi.org/10.5281/zenodo.12655187 \
    https://doi.org/10.5281/zenodo.12655716 \
    https://doi.org/10.5281/zenodo.12655717 \
    https://doi.org/10.5281/zenodo.12655718 \
    https://doi.org/10.5281/zenodo.12655719
do
    zenodo_get $doi
done

for file in tornet_*.tar.gz; do
    tar -xvzf $file -C $TARGET_DIR
done
