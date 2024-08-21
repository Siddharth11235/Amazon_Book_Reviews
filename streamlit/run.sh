#!/usr/bin/env bash

python3 /streamlit/aggregate.py
streamlit run /streamlit/main.py --server.port=8501 --server.address=0.0.0.0
