---
name: langgraph-node
description: Tạo hoặc sửa node, tool, edge trong LangGraph agent của dự án theo đúng chuẩn repo. Dùng khi thêm bước mới vào graph, khi viết tool cho agent, khi thiết lập structured output cho lời gọi LLM, khi cấu hình checkpointer hoặc interrupt cho HITL, hoặc khi debug vòng lặp retry.
---

# Viết node & tool cho LangGraph

## Quy tắc kiến trúc (đọc trước khi gõ dòng nào)

| Node | Có gọi LLM? |
|---|---|
| `load_profile` | ❌ |
| `compute_targets` | ❌ |
| `retrieve_context` | ❌ (embedding không tính là LLM sinh nội dung) |
| `generate_menu` | ✅ |
| `compute_nutrition` | ❌ |
| `validate` | ❌ |
| `explain` | ✅ |

Node không LLM **tuyệt đối không import** LLM client. Có test CI kiểm tra điều này.

## Mẫu node

```python
"""Node: <tên>
LLM: NO | YES
Input:  state.<...>
Output: state.<...>
Ticket: AGT-XX
"""
from src.agents.state import NutriState

async def node_name(state: NutriState) -> dict:
    # 1. Đọc từ state (không đọc biến global, không cache ngoài)
    # 2. Xử lý
    # 3. Trả về dict chỉ chứa các field cần cập nhật
    return {"field": value}
```

Node trả về **dict cập nhật một phần**, không trả về cả state.

## Mẫu node có LLM — structured output bắt buộc

```python
from pydantic import BaseModel, Field

class MenuItem(BaseModel):
    food_id: int = Field(description="ID trong bảng food_items")
    grams: float = Field(gt=0, le=2000)

class MenuSelection(BaseModel):
    breakfast: list[MenuItem]
    lunch: list[MenuItem]
    dinner: list[MenuItem]
    snacks: list[MenuItem] = []
    # KHÔNG có field kcal, protein, sodium... — đây là ràng buộc thiết kế

structured_llm = llm.with_structured_output(MenuSelection)
```

⚠️ Nếu thấy mình chuẩn bị thêm một field số dinh dưỡng vào schema của LLM → **dừng lại**. Đó là vi phạm RULE-1.

## Conditional edge

```python
def route_after_validate(state: NutriState) -> str:
    if not state["violations"]:
        return "explain"
    if state["retry_count"] >= 3:
        return "fallback"
    return "build_feedback"

graph.add_conditional_edges("validate", route_after_validate,
                            {"explain": "explain",
                             "fallback": "fallback",
                             "build_feedback": "build_feedback"})
```

Mọi vòng lặp phải có điều kiện thoát bằng bộ đếm. Không có ngoại lệ.

## Feedback cho retry

Feedback tồi: `"Thực đơn không hợp lệ, hãy thử lại."`
Feedback tốt:
```
Bản trước vi phạm:
- Natri: 2.900 mg (tối đa 2.000 mg). Đóng góp lớn nhất: nước mắm 15 ml (2.100 mg), bột canh 5 g.
- Protein: 78 g (tối đa 52 g theo CKD G4).
Hãy giữ nguyên món chính nhưng bỏ nước chấm và giảm khẩu phần thịt xuống dưới 60 g.
```

Retry mà không đưa lỗi cụ thể vào prompt chỉ là cầu may.

## Tool

```python
from langchain_core.tools import tool

@tool
def search_food(query: str, exclude_high_potassium: bool = False) -> list[dict]:
    """Tra cứu thực phẩm trong CSDL nội bộ. Trả về food_id, tên, và nguồn.
    Không trả về giá trị dinh dưỡng để LLM sao chép — chỉ trả ID để hệ thống tự tra."""
```

Docstring của tool chính là thứ LLM đọc. Viết cho LLM hiểu, không viết cho người review.

## Checkpointer & HITL

```python
from langgraph.checkpoint.postgres import PostgresSaver
graph = builder.compile(checkpointer=PostgresSaver(conn), interrupt_before=["publish"])
```

Resume:
```python
graph.invoke(Command(resume={"action": "approve", "edits": [...]}),
             config={"configurable": {"thread_id": plan_id}})
```

**Fallback nếu interrupt gây tốn hơn 2 ngày:** dùng cột `status` trong `meal_plans`, agent dừng sau `explain`, một endpoint riêng tiếp tục luồng sau khi duyệt. Ghi quyết định vào DEVLOG.

## Prompt

- Đặt trong `src/agents/prompts/`, không nhúng inline giữa logic
- Ngưỡng **truyền vào** từ `clinical_rules`, không viết cứng trong template
- Mỗi prompt có comment: ngày sửa + lý do sửa
- Sửa prompt → chạy lại eval, đừng tin cảm giác

## Checklist trước khi mở PR

- [ ] Docstring node ghi rõ `LLM: YES/NO`
- [ ] Node không-LLM không import LLM client
- [ ] Structured output không có field số dinh dưỡng
- [ ] Vòng lặp có `max_iterations`
- [ ] Có timeout và xử lý lỗi cho lời gọi LLM
- [ ] Test dùng mock, không gọi API thật trong CI
- [ ] Graph vẫn compile, `draw_mermaid()` chạy được
- [ ] Đã cập nhật sơ đồ trong `ARCHITECTURE.md` nếu graph đổi
