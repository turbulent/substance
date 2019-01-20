#!/bin/bash -eux

rm -f dist/*
python3 setup.py sdist bdist_wheel
sleep 5
twine upload dist/*
echo "Released."
