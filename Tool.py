import wikipediaapi

class WikipediaSearchTool:
    """
    用维基百科 REST API 搜索并返回格式化文本
    """
    def __init__(self, lang: str = "zh", max_results: int = 3,user_agent: str = "address_parser/1.0"):
        self.lang = lang
        self.max_results = max_results
        self.wiki = wikipediaapi.Wikipedia(
            language=self.lang,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent=user_agent
        )

    def run(self, query: str) -> str:
        try:
            # 先按标题精确搜索
            page = self.wiki.page(query)
            if page.exists():
                # 返回前 800 字符，避免太长
                summary = page.summary[:800].strip()
                return f"标题: {page.title}\nURL: {page.fullurl}\n摘要:\n{summary}"
            # 模糊搜索
            search_res = self.wiki.search(query, results=self.max_results)
            if not search_res:
                return "维基百科未找到相关条目"

            lines = []
            for title in search_res[: self.max_results]:
                p = self.wiki.page(title)
                if p.exists():
                    lines.append(
                        f"- [{p.title}]({p.fullurl})\n  {p.summary[:200]}..."
                    )
            return "\n\n".join(lines) if lines else "维基百科未找到相关条目"
        except Exception as e:
            return f"维基百科搜索错误: {e}"