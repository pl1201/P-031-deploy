# RULE 10 — AN TOÀN LÂM SÀNG & GUARDRAILS

> Owner: **R2** (nội dung lâm sàng) + **R1** (thực thi kỹ thuật)
> Đây là file quan trọng nhất trong `docs/rules/`. Sai ở đây không phải là bug thường.

> ⚠️ **Đổi phạm vi (2026-08-05, `docs/PRD.md` v2.1):** MVP trọng tâm ĐTĐ2. R10.4/R10.5 dưới đây mô tả cơ chế **đa bệnh lý** (đã build, hoạt động đúng như mô tả) — **giữ nguyên, không sửa**.
>
> **Đã research và chốt (2026-08-05, xem DEVLOG DEC-014):** ban đầu nghi ngờ PRD v2.1 §2.2 yêu cầu gắn `needs_expert_review` cho MỌI hồ sơ có bệnh đồng mắc ngoài ĐTĐ2 — khác hành vi hiện tại (chỉ gắn cờ khi rule thật sự **xung đột**, DEC-007). Đối chiếu lại `KeHoachDuAn_VNutriCare_VMEC10_v3.docx` (chính tài liệu PRD.md ghi là "Nguồn yêu cầu chính") mục 6.4.1 "Bốn tình huống kiểm chứng" thì hành vi hiện tại của `compute_targets()` **khớp chính xác** với 4 kịch bản đặc tả gốc — kể cả ca ĐTĐ2+CKD chỉ chuyển chuyên gia khi dải ngưỡng hẹp bằng 0, không phải vì có 2 bệnh. `docs/NGHIEN_CUU_DAI_THAO_DUONG_2026.md` còn liệt kê cơ chế phát hiện xung đột này là **điểm khác biệt cạnh tranh** so với các app khác (không app nào xử lý đa bệnh lý đồng thời). Kết luận: **không sửa `compute_targets()`**, dòng PRD v2.1 §2.2 là tóm tắt quá tay, không phải quyết định lật ngược DEC-007.

---

## R10.1 — Phạm vi cho phép của hệ thống

| ✅ Được làm | ❌ Không được làm |
|---|---|
| Gợi ý thực đơn trong khuôn khổ chỉ định sẵn có | Chẩn đoán bệnh |
| Ước tính dinh dưỡng từ dữ liệu có nguồn | Kê đơn, gợi ý liều thuốc |
| Cảnh báo vượt ngưỡng theo guideline | Khuyên ngừng/đổi/giảm thuốc |
| Cảnh báo dị ứng và tương tác thuốc–thực phẩm | Diễn giải xét nghiệm thành kết luận y khoa |
| Giáo dục dinh dưỡng có trích dẫn | Tiên lượng bệnh |
| Chuyển câu hỏi tới chuyên gia phụ trách | Nói "thay thế bác sĩ" |

## R10.2 — Câu trả lời chuẩn khi guardrail kích hoạt

Dùng đúng nội dung này (có thể tinh chỉnh câu chữ, không đổi ý):

> "Mình không thể đưa ra chẩn đoán hay điều chỉnh thuốc — việc đó thuộc thẩm quyền của bác sĩ điều trị. Mình có thể giúp bạn về khẩu phần ăn trong khuôn khổ chỉ định sẵn có. Bạn muốn mình chuyển câu hỏi này tới chuyên gia dinh dưỡng đang phụ trách bạn không?"

Kèm nút hành động "Gửi câu hỏi cho chuyên gia". Guardrail phải **hữu ích**, không chỉ là bức tường.

## R10.3 — Từ khoá kích hoạt guardrail tầng 1

Nhóm phải chặn (regex + classifier, tiếng Việt có dấu và không dấu):
- Liều lượng thuốc: `liều`, `mg`, `viên`, `tiêm`, `insulin`, `đơn vị`
- Thay đổi điều trị: `ngừng thuốc`, `bỏ thuốc`, `giảm liều`, `tăng liều`, `đổi thuốc`, `có nên uống`
- Chẩn đoán: `tôi bị bệnh gì`, `có phải ung thư`, `xét nghiệm này nghĩa là`, `nguy hiểm không`
- Thay thế điều trị: `chữa khỏi`, `không cần uống thuốc nữa`, `thực phẩm chữa`

Nhóm **không được** chặn nhầm: `ăn bao nhiêu cơm`, `ăn mặn có sao không`, `rau nào tốt cho thận`, `bao nhiêu muối một ngày`.

Ngưỡng chấp nhận: chặn đúng ≥ 95%, chặn nhầm < 10% (ticket `AGT-07`).

## R10.4 — Ngưỡng lâm sàng: nguồn duy nhất là bảng `clinical_rules`

- **Cấm hardcode ngưỡng trong code Python hoặc trong prompt.** Mọi ngưỡng nằm ở DB, có `guideline_ref`.
- Chỉ **R2** được thêm/sửa ngưỡng. PR chạm `data/seeds/clinical_rules.csv` bắt buộc R2 approve.
- Mỗi rule phải trả lời được: *ngưỡng này lấy từ guideline nào, trang nào, năm nào.*

Tham chiếu ngưỡng cốt lõi (v1 — R2 xác nhận lại khi seed):

| Bệnh lý | Chất | Ngưỡng | Nguồn |
|---|---|---|---|
| ĐTĐ2 | Carbohydrate | 45–55% năng lượng, ưu tiên GI thấp/TB | ADA/EASD |
| ĐTĐ2 | Chất xơ | ≥ 14 g/1000 kcal | ADA |
| THA / tim mạch | Natri | < 2000 mg/ngày (< 5 g muối) | WHO/AHA |
| CKD G3–G5 chưa lọc | Protein | 0,6–0,8 g/kg/ngày | KDIGO/KDOQI |
| CKD | Natri / Kali / Phospho | < 2000 mg / theo giai đoạn / theo giai đoạn | KDIGO |
| Gout | Purine | < 150 mg/ngày | ACR |
| Chung | Năng lượng | 30–35 kcal/kg/ngày (điều chỉnh theo BMI, mục tiêu) | BYT / Viện Dinh dưỡng |

## R10.5 — Đa bệnh lý luôn chọn ngưỡng nghiêm ngặt hơn

Bệnh nhân ĐTĐ2 + CKD G4: protein lấy theo CKD (chặt hơn), carb lấy theo ĐTĐ. Khi hai rule cùng một chất → `min(threshold)` cho giới hạn trên, `max(threshold)` cho giới hạn dưới. Phải có unit test riêng cho quy tắc này.

## R10.6 — Dị ứng là ràng buộc cứng tuyệt đối

Không bao giờ hạ dị ứng xuống mức cảnh báo. Phải kiểm cả **nguyên liệu ẩn**:

| Dị ứng | Nguyên liệu ẩn cần bắt |
|---|---|
| Hải sản | nước mắm, mắm tôm, mắm nêm, dầu hào, bột ngọt từ cá, bánh phồng tôm |
| Đậu nành | nước tương, tương hột, đậu phụ, dầu đậu nành, chao |
| Lạc | dầu lạc, tương đậu phộng, muối vừng lạc, nem chua rán |
| Gluten | mì, bánh mì, nước tương lên men lúa mì, chả cá có bột |
| Sữa | bơ, phô mai, sữa đặc trong cà phê, bánh flan |

## R10.7 — Cảnh báo tương tác thuốc phải hành động được

Cảnh báo tồi: "Bưởi có thể tương tác với thuốc."
Cảnh báo tốt: "Bạn đang dùng Atorvastatin. Bưởi và nước ép bưởi làm tăng nồng độ thuốc trong máu, tăng nguy cơ tác dụng phụ trên cơ. **Nên tránh hoàn toàn** trong thời gian dùng thuốc. Đã thay bưởi bằng cam trong thực đơn này." *(Nguồn: …)*

Mỗi cảnh báo cần: thuốc cụ thể + thực phẩm cụ thể + cơ chế ngắn gọn + hành động + nguồn.

## R10.8 — Disclaimer

Bắt buộc hiển thị ở: mỗi màn hình có thực đơn, mỗi API response chứa dữ liệu dinh dưỡng, mỗi file PDF export, footer của app.

Nội dung chuẩn:

> ⚕️ Thông tin dinh dưỡng mang tính tham khảo, không thay thế chỉ định của bác sĩ hoặc chuyên gia dinh dưỡng. Thực đơn này đã được duyệt bởi {tên chuyên gia} lúc {thời điểm}. Nếu có triệu chứng bất thường, hãy liên hệ cơ sở y tế.

## R10.9 — Dữ liệu bệnh nhân

- v1 được dùng NHANES 2021–2023 public-use, de-identified cho phát triển và kiểm thử theo PRD v2.2 và NCHS Data User Agreement. Không được tái định danh hoặc tuyên bố dữ liệu này đại diện dân số Việt Nam.
- Bộ benchmark trong `eval/datasets/` phải là dữ liệu mô phỏng; expected output phải được tính/review độc lập với system under test.
- Không đưa SEQN, mã định danh nguồn hoặc PII/PHI vào UI, prompt hay log. Dataset ngoài NHANES chỉ được dùng sau khi license, provenance và trạng thái de-identification được xác minh.
- Prompt gửi LLM: chỉ tuổi, giới, cân nặng, chiều cao, mã bệnh + giai đoạn, chỉ số xét nghiệm, danh sách thuốc. **Không định danh.**
- Log không chứa PHI. Logger phải có filter che tự động.

## R10.10 — Khi hệ thống không chắc

Thà nói không biết:

> "Món này chưa có trong cơ sở dữ liệu của mình. Mình ước tính dựa trên nguyên liệu tương tự, độ tin cậy trung bình. Bạn nên xác nhận lại với chuyên gia trước khi dùng con số này."

**Không bao giờ** đưa ra con số nghe có vẻ chính xác cho thứ mình đang đoán.

## R10.11 — Checklist trước khi merge bất kỳ PR nào chạm lâm sàng

- [ ] Ngưỡng lấy từ `clinical_rules`, không hardcode
- [ ] Có `guideline_ref` cho mọi ngưỡng mới
- [ ] Đa bệnh lý đã được xét
- [ ] Dị ứng vẫn là hard constraint
- [ ] Có unit test cho case biên
- [ ] R2 đã approve
