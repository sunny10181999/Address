import os
import csv
import re
from typing import List, Dict, Any
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from Tool import WikipediaSearchTool

# 1. 定义Pydantic模型
class AddressInfo(BaseModel):
    province: str = Field(description="省份名称")
    city: str = Field(description="城市名称")
    district: str = Field(description="区/县级名称")
    detailed_address: str = Field(description="详细街道地址")

# 2. 创建自定义输出解析器
class CustomAddressParser(PydanticOutputParser):
    def __init__(self):
        super().__init__(pydantic_object=AddressInfo)

    def parse(self, text: str) -> AddressInfo:
        # 尝试从文本中提取JSON格式的内容
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                json_str = json_match.group()
                # 修复常见的JSON格式错误
                json_str = json_str.replace("'", '"').replace("True", "true").replace("False", "false")
                return super().parse(json_str)
            except Exception as e:
                print(f"JSON解析错误: {e}\n尝试文本: {json_str}")

        # 尝试直接解析整个文本
        try:
            return super().parse(text)
        except Exception as e:
            print(f"完整解析失败: {e}\n原始文本: {text}")
            raise ValueError(f"无法解析地址信息: {e}")

# 3. 创建Agent函数
def process_addresses(address_list: List[str], api_key: str, output_file: str = "addresses.csv"):
    llm = ChatOpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        temperature=0.95,
        api_key=api_key
    )

    # 初始化维基百科搜索工具
    wiki_tool = WikipediaSearchTool(lang="zh", max_results=2)
    tools = [
        Tool(
            name="Wikipedia_Search",
            func=wiki_tool.run,
            description="通过维基百科获取地点的权威地址信息"
        )
    ]
    # 创建包含所有必需变量的提示模板
    template = """
    你是一名专业地址解析助手，请按以下步骤处理每一个用户给出的地址：
    步骤说明:
    1. 预处理  
       • 若地址中出现“附近/旁边/周围/对面/隔壁/路口/交叉口/地铁口”等方位或模糊词汇，先**推理并剔除**这些词，仅保留“主体地名+门牌号/道路”核心部分。  
       • 例：  
         输入：南方科技大学医院附近  
         剔除后：南方科技大学医院  
    2. 判断是否需要搜索  
       • 若剔除后的主体已包含“省/市/区/街道/门牌号”完整四级，可直接解析，**无需搜索**。  
       • 否则，使用Wikipedia_Search 获取该主体的官方或权威地址信息。
    3. 结果提取与拆分  
       • 从搜索结果中提取完整地址，按“省、市、区、详细地址”四级拆分。  
       • 直辖市：省与市同名（如“上海市、上海市”）。
    4. 最终输出  
       • JSON 格式，仅含四个字段：province / city / district / detailed_address。  
       • 不要输出 Markdown 代码块，直接给出裸 JSON
    工具列表:{tools}
    工具名称: {tool_names}
    当前地址: {input}
    请严格按照以下ReAct格式思考：
    Thought: 我需要做什么
    Action: 使用的工具名称
    Action Input: 工具的输入
    Observation: 工具返回的结果
    ... (重复多次)
    Thought: 我有最终答案了
    Final Answer: 输出JSON格式的结果
    输出格式要求：
    {format_instructions}
    
    开始处理:
    {agent_scratchpad}"""

    # 初始化解析器
    parser = CustomAddressParser()
    format_instructions = parser.get_format_instructions()

    # 创建完整提示词
    prompt = PromptTemplate(
        template=template,
        input_variables=["input", "tools", "tool_names"],
        partial_variables={"format_instructions": format_instructions}
    )

    # 获取工具名称列表
    tool_names = ", ".join([tool.name for tool in tools])

    # 创建Agent
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        return_intermediate_steps=False
    )

    # 准备CSV输出
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["省", "市", "区", "详细地址"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # 处理每个地址
        for i, address in enumerate(address_list):
            try:
                print(f"\n处理地址 [{i + 1}/{len(address_list)}]: {address}")
                # 准备Agent输入
                agent_input = {
                    "input": address,
                    "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in tools]),
                    "tool_names": tool_names
                }
                # 执行Agent
                result = agent_executor.invoke(agent_input)
                print(f"Agent输出: {result['output']}")
                # 解析输出
                parsed = parser.parse(result["output"])
                # 写入CSV
                writer.writerow({
                    "省": parsed.province,
                    "市": parsed.city,
                    "区": parsed.district,
                    "详细地址": parsed.detailed_address
                })
                print(f"成功解析: {parsed}")
            except Exception as e:
                print(f"处理地址失败: {address}\n错误: {e}")
                # 写入空行保持CSV结构
                writer.writerow({
                    "省": "ERROR",
                    "市": "ERROR",
                    "区": "ERROR",
                    "详细地址": address
                })

