# Graph RAG

本地部署使用 `GraphRAG`

- **model:** [Qwen/Qwen2-7B-Instruct](https://huggingface.co/Qwen/Qwen2-7B-Instruct)
- **embeddings model:** [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)
- **dataset:** [cfa532/CHLAWS](https://huggingface.co/datasets/cfa532/CHLAWS/tree/main)
- **hardware:** A800-80G * 1

---

<br>
<br>


## 🛠 environments

**注意：以下三个步骤的环境最好都要单独一个环境，然后单独安装包和单独启动！！推荐使用 `python -m venv YOUR_ENV_NAME` 进行虚拟环境创建**

<br>

1. 启动 LLM 的 OpenAI 服务（推荐用vLLM，单独一个环境）

    ```bash
    python -m vllm.entrypoints.openai.api_server --model /root/private_data/models/Qwen/Qwen2-7B-Instruct --served-model-name Qwen2-7B-Instruct --gpu-memory-utilization 0.3
    ```


<br>



2. 启动 embeddings 模型的 OpenAI 服务 (目前好像仅支持 bge 系列, 推荐用 FastChat 启动, 单独一个环境)

    先下载 [FastChat 0.2.35](https://github.com/lm-sys/FastChat/releases), 解压后: 

    ```bash
    cd FastChat
    pip3 install --upgrade pip
    pip3 install -e ".[model_worker,webui]"
    ```

    再启动(建议写在一个 `.sh` 进行运行):
    ```sh
    python -m fastchat.serve.controller --host 0.0.0.0 --port 21003 &

    python -m fastchat.serve.model_worker --model-path /root/private_data/models/BAAI/bge-m3 --model-names gpt-4 --num-gpus 1 --controller-address http://0.0.0.0:21003 &

    python -m fastchat.serve.openai_api_server --host 0.0.0.0 --port 8200 --controller-address http://0.0.0.0:21003
    ```

<br>



3. 按照 [GraphRAG](https://microsoft.github.io/graphrag/posts/get_started/) 步骤进行部署:

    首先安装 `graphrag`:

    ```bash
    pip install graphrag
    ```

    然后创建 `indexer`:

    - a. 创建存放 数据集 的文件夹, 然后放入自己想要进行实验的数据集
    ```sh
    mkdir -p ./ragtest/input
    ``` 


    - b. 设置 `workspace`，使用 `graphrag.index --init` 初始化工作区
    ```sh
    python -m graphrag.index --init --root ./ragtest
    ```
    这一步会产生两个文件 `.env` 和 `settings.yaml`. 本次案例只更改 `settings.yaml`


    - c. 初始化 `workspace` 后，创建 `index pipeline`
    ```sh
    python -m graphrag.index --root ./ragtest
    ```
<img src='https://github.com/yyhchen/LLM-Application/blob/main/assets/graphrag_indexing_pipeline.png'>

<img src='https://github.com/yyhchen/LLM-Application/blob/main/assets/completed_success.png'>


    - d. running query engine

    全局搜索(global search):
    ```sh
    python -m graphrag.query \
    --root ./ragtest \
    --method global \
    "What are the top themes in this story?"
    ```
<img src='https://github.com/yyhchen/LLM-Application/blob/main/assets/graphrag_global_search.png'>

    局部搜索(local search):
    ```sh
    python -m graphrag.query \
    --root ./ragtest \
    --method local \
    "Who is Scrooge, and what are his main relationships?"
    ``
<img src='https://github.com/yyhchen/LLM-Application/blob/main/assets/image.png'>

<br>
<br>



## ❌ 常见错误

### 控制台出现：❌ Errors occurred during the pipeline run, see logs for more details.

请到当前目录下(./output/.../report)查找日志 

1. datashaper.workflow.workflow ERROR Error executing verb "cluster_graph" in create_base_entity_graph: EmptyNetworkError


**原因：** 可能是模型参数太小了，能力不够构建 KG




<br>
<br>


## ⚙️ settings.yaml

部分节选


```yaml
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat # or azure_openai_chat
  model: Qwen2-7B-Instruct
  model_supports_json: false # 模型不是很好的必须设置为false
  api_base: http://0.0.0.0:8000/v1


...


embeddings:
  async_mode: threaded # or asyncio
  llm:
    api_key: ${GRAPHRAG_API_KEY}
    type: openai_embedding # or azure_openai_embedding
    model: gpt-4    # 设置为gpt-4 (无论用任何 embeddings 模型)
    api_base: http://0.0.0.0:8200/v1

```