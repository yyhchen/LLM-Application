# AutoGen

本地LLM部署 + AutoGen

- [AutoGen Getting-Started](https://microsoft.github.io/autogen/docs/Getting-Started)

- [paper](https://arxiv.org/abs/2308.08155)

---

<br>
<br>


## 📦 environments
python >=3.8 & <3.13

安装 `AutoGen`
```sh
pip install pyautogen
```


<br>
<br>
<br>


## 🔨 One of demo Guide

<img src="https://github.com/yyhchen/LLM-Application/blob/main/assets/autogen_speaker.png">

构建一个简单的 StateFlow 模型，定制一个 Speaker，定义如下 Agent：
- Initializer：发送任务启动工作流程
- Coder：编写代码从 互联网检索论文（这个是真可以～）
- Executor：执行代码
- Scientist：阅读论文并写总结

<br>

### API

先启动 API, 运行 [openai_api.sh](https://github.com/yyhchen/LLM-Application/tree/main/AutoGen/openai_api.sh):

```sh
bash openai_api.sh
```

<br>

### AutoGen案例

[autogen.ipynb](https://github.com/yyhchen/LLM-Application/tree/main/AutoGen/autogen.ipynb) 改编自 [AutoGen官网案例](https://microsoft.github.io/autogen/docs/topics/groupchat/customized_speaker_selection) 

