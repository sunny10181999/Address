# Address
一个简易版的地址抽取工具
## 一个基于 Streamlit + LangChain 的地址解析工具：上传含地址的 csv，即可调用维基百科与大模型自动补全省-市-区-街道四级信息并下载结果
## 文件速览：
## 1.main.py：前端入口。负责页面布局、文件上传、调用解析函数、展示与下载结果 csv。
## 2.Address_choice.py：解析核心。读取地址列表 → 构造 LangChain Agent → 按规则推理/搜索维基百科 → 拆分为四级地址 → 写入结果 csv。
## 3.Tool.py：维基百科搜索工具，为 Agent 提供权威地址摘要【需要科学上网】。
## 4.地址.csv：原始数据文件；parsed_addresses.csv:处理后的文件。
