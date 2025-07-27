#!/bin/bash

git pull
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt
python -m alembic upgrade head

python main.py
