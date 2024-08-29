# AutoGen tutorial

[官方教程](https://microsoft.github.io/autogen/docs/tutorial)

---


### 1. ConversableAgent

[ConversableAgent](./ConversableAgent.ipynb)


源码中的介绍:
>(In preview) A class for generic conversable agents which can be configured as assistant or user proxy.
>
>After receiving each message, the agent will send a reply to the sender unless the msg is a termination msg.
For example, AssistantAgent and UserProxyAgent are subclasses of this class,
configured with different default settings.
>
>To modify auto reply, override `generate_reply` method.
>
>To disable/enable human response in every turn, set 
`human_input_mode` to "NEVER" or "ALWAYS".
>
>To modify the way to get human input, override `get_human_input` method.
>
>To modify the way to execute code blocks, single code block, or function call, override `execute_code_blocks`,
`run_code`, and `execute_function` methods respectively.

<br>
<br>


### 2. CodeExecutor

[CodeExecutor](./CodeExecutors.ipynb)

Agent 里面的一个参数

<br>
<br>


### 3. UserProxyAgent

[UserProxyAgent](./UserProxyAgent.ipynb)

`ConversableAgent` 的子类，通常使用`UserProxyAgent` 来与用户进行交互。

<br>
<br>



### 4. Tools

[Tools](./Tools.ipynb)


