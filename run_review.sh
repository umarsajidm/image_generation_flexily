#!/bin/bash
cd /root/image_generation_flexily
streamlit run ui/review_app.py --server.port 8501 --server.headless true
