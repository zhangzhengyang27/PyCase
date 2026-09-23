"""环检测：用 DFS 判定有向图中是否存在环。

课程配套示例。dictionary.txt 是练习用的词表数据文件（与脚本同目录），
运行时演示「逐行读取数据文件并统计」的最小用法。
"""
from pathlib import Path


def has_cycle(graph: dict[str, list[str]]) -> bool:
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node: str) -> bool:
        if node in in_stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        in_stack.add(node)
        for nxt in graph.get(node, []):
            if dfs(nxt):
                return True
        in_stack.discard(node)
        return False

    return any(dfs(n) for n in graph)


if __name__ == "__main__":
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": ["A"],  # D -> A 形成环
    }
    print("图中存在环:", has_cycle(graph))

    # 顺带演示读取同目录的数据文件（兄弟文件随目录整体物化）
    words = Path(__file__).with_name("dictionary.txt").read_text(encoding="utf-8").split()
    print(f"词表共 {len(words)} 个词，最长: {max(words, key=len)}")
