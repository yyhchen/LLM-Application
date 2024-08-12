# Chainlit

类似 chatgpt 的前端显示界面

---


<br>
<br>



## 📦 environments

`python >= 3.8`


```bash
pip install chainlit
```


<br>


检测是否安装成功，在终端输入:
```bash
chainlit hello
```

如下图所示：

![chainlit hello](/assets/chainlit_hello.png)



<br>
<br>
<br>




## 🔌 本地部署 Chatbot

1. 启动 LLM 的 OpenAI 服务（推荐用vLLM）

```bash
python -m vllm.entrypoints.openai.api_server --model /home/yhchen/huggingface_model/Qwen/Qwen2-0.5B-Instruct --served-model-name Qwen2-0.5B-Instruct --port 8080
```

> 注意，因为 `chainlit` 默认启动的端口是 `8000`, 所以本地使用 vLLM 启动 API 服务时，需要指定为其他端口，如 `8080`

<br>
<br>

2. 启动 `chainlit`

在启动之前，需要在 `app.py` 同级目录下创建一个 `.env` 文件，并写入以下内容： 

```sh
OPENAI_API_KEY="vllm"
```

<br>

在 `app.py` 相应地方也加上:
```python
client = AsyncOpenAI(
    api_key="vllm",
    base_url="http://0.0.0.0:8080/v1",
)
```

<br>

最后执行以下命令启动网页:

```sh
chainlit run app.py -w
```

> 注意： 加 `-w` 是为了方便开发时，直接调试而不需要重新启动服务


效果如下所示：
![openai format chatbot demo](/assets/chainlit_openaidemo.png)



