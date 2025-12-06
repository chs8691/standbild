#!/bin/bash
# Upload als Release. Vorbedingung: in hugo.toml muss baseURL = "https://standbild.kollegen.uber.space"
USER=kollegen
HOST=despina.uberspace.de             
# the directory where your web site files should go
DIR=/home/kollegen/standbild.kollegen.uber.space
hugo && rsync -avz public/ ${USER}@${HOST}:${DIR}
exit 0
