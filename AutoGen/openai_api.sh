#!/bin/bash

python -m fastchat.serve.controller --host 0.0.0.0 --port 21003 &

python -m fastchat.serve.model_worker --model-path /home/yhchen/huggingface_model/Qwen/Qwen2-0.5B-Instruct/ --model-names gpt-4 --num-gpus 1 --controller-address http://0.0.0.0:21003 &

python -m fastchat.serve.openai_api_server --host 0.0.0.0 --port 8000 --controller-address http://0.0.0.0:21003