"""dataclass：声明式数据模型。"""
from dataclasses import dataclass, field


@dataclass(order=True, frozen=True)
class Student:
    sort_index: float = field(init=False, repr=False)
    name: str
    score: float

    def __post_init__(self):
        object.__setattr__(self, "sort_index", -self.score)  # 分数降序


students = [
    Student("小明", 92.5),
    Student("小红", 88.0),
    Student("小刚", 95.0),
]
for rank, s in enumerate(sorted(students), 1):
    print(f"第{rank}名 {s.name} {s.score}")

# frozen=True 不可变：修改会抛 FrozenInstanceError
try:
    students[0].score = 0
except Exception as e:
    print("不可变校验:", type(e).__name__)
