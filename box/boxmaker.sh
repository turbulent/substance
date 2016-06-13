#!/bin/bash -e

packer build -force substance-base.packer.json
packer build -force substance-box.packer.json
