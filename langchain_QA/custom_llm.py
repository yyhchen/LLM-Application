from typing import Any, Dict, List, Optional, Iterator
import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
import json

"""
    langchain 中自定义LLM (暂时没用得上，主要是自己构造的无法使用到 agent 中)

    [官方：如何创建自定义的 LLM类](http://www.aidoczh.com/langchain/v0.2/docs/how_to/custom_llm/)

"""


class CustomLLM(LLM):
    n: int
    base_url: str
    api_key: str
    model: str

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
    
    def _resp_process_mock(self,input:str,resp:str):
        final_answer_json = {
            "action": "Final Answer",
            "action_input": input
        }
        return f"""
                    Action: 
                    ```
                    {json.dumps(final_answer_json, ensure_ascii=False)}
                    ```
                """

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        if stop is not None:
            raise ValueError("不允许使用停用词参数。")

        # 与本地LLM交互的实际调用
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant." },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.n
            }
        )

        # 检查响应并返回结果
        response.raise_for_status()
        completion = response.json().get("choices")[0]['message']["content"]
        # return self._resp_process_mock(prompt, completion[:self.n])
        return completion[:self.n]

    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant." },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.n,
                "stream": True,
            },
            stream=True,
        )

        for line in response.iter_lines():
            if line:
                data = line.decode("utf-8")
                chunk = GenerationChunk(text=data[:self.n])
                if run_manager:
                    run_manager.on_llm_new_token(chunk.text, chunk=chunk)
                yield chunk

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model,
            "n": self.n,
            "base_url": self.base_url,
        }

    @property
    def _llm_type(self) -> str:
        return "custom_qwen2"

# 示例使用
qwenmodel = CustomLLM(n=256, base_url='http://localhost:8000/v1', api_key='token-qwen2', model='Qwen2')
result = qwenmodel("你好")
print(result)
