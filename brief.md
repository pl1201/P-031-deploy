# 🍏 TÀI LIỆU TÓM TẮT DỰ ÁN (PROJECT BRIEF)

**Tên dự án:** VNutriCare AI Agent
**Thời gian triển khai:** 6 tuần
**Định hướng công nghệ:** Neuro-Symbolic AI (LangGraph + Deterministic Engine)

> Bản cập nhật theo `docs/PRD.md` v2.2 (2026-08-06) — trọng tâm MVP đã chuyển sang **đái tháo đường type 2 (ĐTĐ2)**, dùng dữ liệu thực tế NHANES 2021-2023 (de-identified). Xem `CLAUDE.md` §1 để biết lý do đổi phạm vi.

## 1. Tổng Quan & Bối Cảnh (Context)

VNutriCare là trợ lý AI cá nhân hoá dinh dưỡng lâm sàng, trọng tâm MVP là bệnh nhân **đái tháo đường type 2** tại Việt Nam. Hệ thống tuân thủ nguyên tắc kiểm soát carbohydrate, chỉ số đường huyết (GI/GL) và phân bổ bữa ăn theo hướng dẫn ADA. Cơ chế đa bệnh lý sẵn có (tăng huyết áp, bệnh thận mạn, gout) vẫn hoạt động như một modifier chồng lên ĐTĐ2, không phải bệnh chính riêng lẻ — xem DEC-007/DEC-014 trong `DEVLOG.md`. Mọi thực đơn bắt buộc phải có sự phê duyệt của chuyên gia dinh dưỡng/bác sĩ (Human-in-the-Loop) trước khi hiển thị cho bệnh nhân.

## 2. Vấn Đề Cần Giải Quyết (Pain Points)

- **Ảo giác LLM (Hallucination) đe dọa tính mạng:** Ngưỡng sai số an toàn y khoa là dưới 10%, nhưng các mô hình ngôn ngữ lớn hiện tại có sai số định lượng đáng kể khi tự tính dinh dưỡng. VNutriCare loại bỏ rủi ro AI tự "bịa" ra hàm lượng carbohydrate/natri bằng lõi tính toán luật cứng (RULE-1, xem `CLAUDE.md` §2).
- **Carbohydrate ẩn trong món Việt:** Cơm, bún, phở, bánh mì, nước ngọt và thực phẩm đóng gói khiến bệnh nhân ĐTĐ2 khó kiểm soát đường huyết nếu không có chỉ số GI/GL rõ ràng cho từng món.
- **Khoảng trống thị trường:** Các app phổ thông (MyFitnessPal) chỉ tập trung đếm calo, thiếu chỉ số GI/GL, không kiểm tra tương tác thuốc-thực phẩm và sai lệch khi tính món ăn phức hợp Việt Nam.

## 3. Chân Dung Người Dùng (Target Audience)

| Nhóm Đối Tượng                                | Vai Trò & Phạm Vi Phục Vụ                                                                                                                |
| :--------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| **Bệnh nhân ĐTĐ2 & người chăm sóc**           | Nhận thực đơn cá nhân hoá theo ngưỡng carb/GI/GL, cảnh báo tương tác thuốc. Dữ liệu phát triển/kiểm thử dùng NHANES de-identified, không dữ liệu bệnh nhân thật. |
| **Bác sĩ / Chuyên gia dinh dưỡng**            | Người vận hành cốt lõi (Human-in-the-Loop). Chịu trách nhiệm duyệt, sửa thực đơn nháp do AI phác thảo (RULE-3 — không có đường tắt tới bệnh nhân). |

## 4. Kiến Trúc AI: Phân Tuyến An Toàn (Safe Routing)

Để đảm bảo an toàn tuyệt đối, hệ thống áp dụng kiến trúc lai chia thành 3 tuyến biệt lập (xem `docs/ARCHITECTURE.md` cho chi tiết luồng graph):

- **Tuyến A (Lõi Sinh Số - Deterministic Engine):** Code luật cứng bằng Python/SQL, tra cứu Bảng thành phần thực phẩm VN 2007/2017. KHÔNG dùng LLM ở tuyến này (`src/clinical/**` cấm import LLM client, có test chặn).
- **Tuyến B (Bóc Tách - LLM Parser/Selector):** LLM chỉ trả về `food_id`/`dish_id` + gram, KHÔNG được tự sinh số dinh dưỡng.
- **Tuyến C (Diễn Đạt - LLM Generation):** RAG truy xuất hướng dẫn lâm sàng, giải thích lý do chọn món và hướng dẫn chế biến, chỉ hoạt động trên thực đơn đã được chuyên gia duyệt.

## 5. Phạm Vi Triển Khai (MVP 6 Tuần)

Xem đầy đủ tại `docs/PRD.md` §4 và `CLAUDE.md` §7 (danh sách không-mục-tiêu chi tiết).

- **In Scope (Bắt buộc làm):**
  - Dữ liệu bệnh nhân thực tế NHANES 2021-2023 (de-identified, public-use).
  - Lõi tính toán ngưỡng ĐTĐ2 (carb %, GI/GL, phân bổ bữa, HbA1c) — Tuyến A.
  - Luồng Agent LangGraph gọi API LLM (Tuyến B & C) — không tự fine-tune LLM.
  - Giao diện UI duyệt thực đơn cho chuyên gia (HITL).
  - Bộ từ điển cảnh báo tương tác thuốc-thực phẩm liên quan ĐTĐ2 (curated, có nguồn).
  - Cơ chế đa bệnh lý hiện có (CKD/gout/THA làm modifier) — giữ nguyên, không thu hẹp.
- **Out of Scope (đã loại bỏ khỏi MVP):**
  - Computer vision/OCR nhận diện ảnh mâm cơm.
  - Tính năng điều trị mới chuyên biệt cho CKD, gout, THA nặng (không phải cắt cơ chế đa bệnh lý sẵn có).
  - Dữ liệu thiết bị đeo (Wearables, HealthKit/Health Connect), fine-tuning, multi-tenant/HIS-EMR.

## 6. Tiêu Chí Đánh Giá Nghiệm Thu (KPIs)

- **Bảo chứng dữ liệu (RQ1):** 100% giá trị dinh dưỡng hiển thị phải truy vết được về CSDL gốc (`source`/`source_ref`).
- **HITL (RQ2):** Mọi thực đơn dừng ở trạng thái chờ duyệt trước khi tới bệnh nhân; đo thời gian duyệt trung bình của chuyên gia.
- **Tương tác thuốc-thực phẩm (RQ5):** Độ nhạy bắt trúng kịch bản (red-team) tương tác nguy hiểm liên quan ĐTĐ2 trong danh mục curated.
