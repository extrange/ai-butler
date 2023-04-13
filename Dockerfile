FROM python:3.10-bullseye

# Doesn't work with python 3.11?
# RUN apt update && apt install -y build-essential
# RUN git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp && make

# RUN python3 -m pip install torch numpy sentencepiece

COPY requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt