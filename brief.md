# 🍏 TÀI LIỆU TÓM TẮT DỰ ÁN (PROJECT BRIEF)

**Tên dự án:** VNutriCare AI Agent
**Thời gian triển khai:** 5 tuần
**Định hướng công nghệ:** Neuro-Symbolic AI (LangGraph + Deterministic Engine)

## 1. Tổng Quan & Bối Cảnh (Context)

VNutriCare là trợ lý AI cá nhân hoá dinh dưỡng lâm sàng, được thiết kế đặc thù cho bệnh nhân Tăng huyết áp và Tim mạch tại Việt Nam. Dự án ra đời nhằm giải quyết gánh nặng dịch tễ khổng lồ khi có tới 26,2% người trưởng thành (khoảng 17 triệu người) mắc tăng huyết áp. Hệ thống tuân thủ nghiêm ngặt chế độ ăn DASH (Dietary Approaches to Stop Hypertension), siết chặt lượng Natri dưới 2000 mg/ngày. Đồng thời, hệ thống tính toán tăng cường Kali từ rau củ để hỗ trợ giãn mạch. Mọi thực đơn bắt buộc phải có sự phê duyệt của bác sĩ (Human-in-the-Loop) trước khi hiển thị cho người bệnh.

## 2. Vấn Đề Cần Giải Quyết (Pain Points)

- **Ảo giác LLM (Hallucination) đe dọa tính mạng:** Ngưỡng sai số an toàn y khoa là dưới 10%, nhưng các mô hình ngôn ngữ lớn hiện tại có sai số định lượng lên tới ~36%. VNutriCare loại bỏ rủi ro AI tự "bịa" ra hàm lượng muối (Natri) bằng Lõi tính toán luật cứng[cite: 1390].
- **Tương tác Thuốc - Thực phẩm nguy hiểm:** Bệnh nhân tim mạch dùng thuốc liên tục. Ví dụ, thuốc huyết áp nhóm ACEi gây giữ Kali. Nếu AI gợi ý ăn nhiều thực phẩm giàu Kali (như chuối, cà chua), bệnh nhân có thể bị tăng Kali máu dẫn đến rối loạn nhịp tim. NutriCareAgent sẽ lập tức nhận diện và chặn đứng thực đơn này.
- **Khoảng trống thị trường:** Các app phổ thông (MyFitnessPal) chỉ tập trung giảm cân, thiếu bộ lọc vi chất sinh tử (Natri, Kali) và sai lệch khi tính toán món ăn phức hợp Việt Nam.

## 3. Chân Dung Người Dùng (Target Audience)

| Nhóm Đối Tượng                                | Vai Trò & Phạm Vi Phục Vụ                                                                                                                |
| :-------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| **Bệnh nhân Tim mạch / Huyết áp & Người nhà** | Nhận thực đơn chuẩn DASH, cảnh báo tương tác thuốc. Mọi hồ sơ trong giai đoạn này là dữ liệu mô phỏng 100% để tránh rào cản y đức (IRB). |
| **Bác sĩ Tim mạch / Chuyên gia Dinh dưỡng**   | Người vận hành cốt lõi (Human-in-the-Loop). Chịu trách nhiệm duyệt, sửa thực đơn nháp do AI phác thảo nhằm giảm tải thời gian khám bệnh. |

## 4. Kiến Trúc AI: Phân Tuyến An Toàn (Safe Routing)

Để đảm bảo an toàn tuyệt đối, hệ thống áp dụng kiến trúc lai chia thành 3 tuyến biệt lập:

- **Tuyến A (Lõi Sinh Số - Deterministic Engine):** Code luật cứng bằng Python/SQL, tra cứu Bảng thành phần thực phẩm VN 2007. KHÔNG dùng AI ở tuyến này. Mọi con số dinh dưỡng tính ra là chính xác 100%.
- **Tuyến B (Bóc Tách - LLM Parser):** LLM đóng vai trò nhận diện ý định và trích xuất thực thể (Món ăn, Định lượng, Tên thuốc). KHÔNG được tự sinh con số.
- **Tuyến C (Diễn Đạt - LLM Generation):** Sử dụng RAG (vietnamese-bi-encoder) để truy xuất hướng dẫn lâm sàng. Giải thích lý do chọn món và hướng dẫn chế biến giảm Natri, chỉ hoạt động trên thực đơn đã được chuyên gia duyệt.

## 5. Phạm Vi Triển Khai (Sprint 5 Tuần)

Dự án áp dụng chiến lược "Cắt tỉa khắt khe" để kịp tiến độ bảo vệ:

- **In Scope (Bắt buộc làm):** \* Bộ dữ liệu mô phỏng (~60 ca tĩnh)[cite: 1407].
  - Lõi tính toán chuẩn DASH (Tuyến A).
  - Luồng Agent LangGraph gọi API LLM (Tuyến B & C) - Không tự fine-tune LLM từ đầu.
  - Giao diện UI duyệt thực đơn cho Bác sĩ (HITL).
  - Bộ từ điển cảnh báo tương tác Thuốc Tim mạch - Thực phẩm (~80 cặp làm thủ công).
  - Chỉ số cận lâm sàng cốt lõi tập trung vào Chỉ số huyết áp (Tâm thu/Tâm trương) và Bilan lipid máu (Cholesterol toàn phần, LDL, HDL, Triglyceride).
- **Out of Scope (Đã loại bỏ):** \* Thuật toán đa bệnh lý (Constraint Programming) - Đã lược bỏ do scope lại 1 bệnh.
  - Nhận diện ảnh mâm cơm (Computer Vision) do sai số >10%.
  - Dữ liệu thiết bị đeo (Wearables, Apple Health).

## 6. Tiêu Chí Đánh Giá Nghiệm Thu (KPIs)

- **Bảo chứng dữ liệu (RQ1):** 100% giá trị dinh dưỡng hiển thị phải truy vết được về CSDL gốc.
- **Độ chính xác tương tác thuốc (RQ5):** >90% độ nhạy trong việc bắt trúng kịch bản (Red-team) tương tác nguy hiểm giữa thuốc ACEi và thực phẩm giàu Kali.
- **Hiệu suất Bác sĩ (RQ2):** Thời gian duyệt thực đơn trung bình < 2 phút/lượt.
