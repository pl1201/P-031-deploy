# PITCH DECK — 10 SLIDE

> Deliverable #7 · Owner: **R4** · Thời lượng mục tiêu: 10 phút + Q&A
> Ký hiệu `[VERIFY]` = số liệu phải được xác minh (ticket DAT-00) trước khi lên slide. **Chưa verify thì gỡ khỏi slide**, đừng để bị hỏi nguồn mà ú ớ.

---

## Nguyên tắc chung

- Mỗi slide **một ý**, tối đa 30 chữ, font ≥ 24pt
- Nền tối, chữ sáng (máy chiếu hội trường lên màu tốt hơn)
- Hình > chữ. Mọi số liệu có nguồn ở footnote
- Tổng duyệt **3 lần** trước Demo Day, bấm giờ từng slide

---

## Slide 1 — Tiêu đề

**NutriCare Agent**
Trợ lý dinh dưỡng lâm sàng cho bệnh nhân mãn tính Việt Nam

*Đội [tên] · AI20K Build Cohort 2 · VMEC-10*
Live URL · QR code dẫn tới demo

**Người nói:** R2 · **20 giây**
> "Chúng em làm một trợ lý dinh dưỡng cho bệnh nhân mãn tính. Điều khác biệt không nằm ở chỗ nó thông minh hơn, mà ở chỗ nó **không được phép bịa số**."

---

## Slide 2 — Vấn đề

### Người Việt ăn mặn gấp đôi khuyến cáo

- Tiêu thụ trung bình **8,1–9,4 g muối/ngày** — khuyến cáo WHO là 5 g `[VERIFY]`
- **70–81%** lượng muối đến từ nêm nếm và nước chấm, không phải thực phẩm chế biến sẵn `[VERIFY]`
- Chỉ **16%** người dân tự nhận mình ăn mặn `[VERIFY]`
- Một bát phở bò: **3,3–4,0 g muối** — gần hết định mức cả ngày của bệnh nhân suy thận `[VERIFY]`

**Hình:** bát phở + thanh đo muối vượt ngưỡng

**Người nói:** R2 · **50 giây**
> Mở bằng con số bát phở. Cụ thể, dễ hình dung, ai trong phòng cũng vừa ăn tuần này.

---

## Slide 3 — Vì sao chưa có lời giải

| | MyFitnessPal / Noom | Sổ tay bệnh viện | NutriCare |
|---|---|---|---|
| Món ăn Việt | Thiếu | Có, nhưng tĩnh | ✅ CSDL Việt + 3 miền |
| Ràng buộc lâm sàng (CKD, ĐTĐ) | Không | Chung chung | ✅ Theo giai đoạn bệnh |
| Mâm cơm gia đình | Không | Không | ✅ Phân rã khẩu phần |
| Người duyệt | Không | — | ✅ **HITL bắt buộc** |
| Chống bịa số | Không | — | ✅ Kiến trúc tách bạch |

**Người nói:** R2 · **50 giây**
> Nhấn dòng cuối. Đó là toàn bộ luận điểm của bài.

---

## Slide 4 — Demo sản phẩm

**Slide gần như không có chữ.** Chuyển sang màn hình thật.

Kịch bản demo (3 phút, tập luyện đến mức không cần nghĩ):
1. Đăng nhập **bệnh nhân** → hồ sơ: nam 58t, ĐTĐ2 + suy thận G3b, đang dùng warfarin
2. Bấm "Lập thực đơn" → agent chạy, hiện định mức: 1950 kcal, protein 52 g, natri 2000 mg — **kèm nút "vì sao?"** mở ra rule + guideline
3. Thực đơn hiện ra, **bấm vào bát cơm → hiện nguồn NIN kèm số trang**
4. ⚠️ **Cảnh báo đỏ**: rau ngót tương tác với warfarin → agent đã tự thay bằng rau khác
5. Chuyển tài khoản **chuyên gia** → hàng chờ duyệt → sửa 120 g cơm xuống 90 g → tổng dinh dưỡng cập nhật ngay → Duyệt
6. Quay lại bệnh nhân → thực đơn hiện ra kèm dòng "Đã duyệt bởi CN. [tên] lúc [giờ]"

**Người nói:** R4 · **3 phút**
> Có **video backup** sẵn sàng. Warm up Live URL trước 10 phút (Render free tier ngủ sau 15 phút).

---

## Slide 5 — Kiến trúc

Sơ đồ hệ thống (Mermaid, xuất từ `docs/ARCHITECTURE.md`), tô màu phân biệt:
- 🟢 **Xanh lá — Deterministic Clinical Core:** nơi mọi con số ra đời. Không gọi LLM.
- 🔵 **Xanh dương — LangGraph Agent:** gọi LLM, nhưng chỉ để *chọn* và *diễn đạt*.
- 🟠 **Cam — Human review:** chốt chặn cuối.

Stack: FastAPI · LangGraph · PostgreSQL + pgvector · Next.js · Render/Vercel

**Người nói:** R1 · **60 giây**

---

## Slide 6 — ⭐ Cách chúng em chống bịa số

**Slide quan trọng nhất của bài thuyết trình.**

> LLM chọn món. Python tính số.

```
LLM trả về:   {"food_id": 1042, "grams": 180}
                        ↓
Python tra SQL:  Gạo tẻ · NIN · Bảng TPTP VN tr.42
                        ↓
Kết quả:      234 kcal · 2 mg natri  ← LLM không hề nhìn thấy con số này
```

Schema mà LLM được phép sinh ra **không có chỗ nào để ghi kcal**. Đây là ràng buộc ở tầng kiến trúc, không phải lời dặn trong prompt — và có test tự động chặn CI nếu ai vi phạm.

**Người nói:** R1 · **80 giây**
> Đây là câu trả lời cho câu hỏi mà giám khảo chắc chắn sẽ hỏi. Nói chậm.

---

## Slide 7 — Bốn tầng an toàn

| Tầng | Chặn gì | Ví dụ |
|---|---|---|
| 1. Input Guard | Câu hỏi chỉ định y khoa | "Giảm liều insulin được không?" → từ chối, chuyển chuyên gia |
| 2. Structured Output | LLM bịa số, bịa tên món | Schema chỉ nhận `food_id` + gram |
| 3. Deterministic Validator | Vượt ngưỡng, dị ứng, tương tác thuốc | Natri 2900/2000 mg → **chặn**, sinh lại kèm lý do cụ thể |
| 4. Human Review | Phần còn lại | Chuyên gia duyệt, sửa, hoặc từ chối |

**Fail closed:** nghi ngờ thì chặn. Thà không có thực đơn còn hơn có thực đơn sai.

**Người nói:** R1 · **60 giây**

---

## Slide 8 — Evaluation & DevOps

### Đánh giá trên 60 hồ sơ mô phỏng

| Chỉ số | Kết quả | Mục tiêu |
|---|---|---|
| Thực đơn pass rules ngay lần đầu | `__%` | ≥ 70% |
| Pass sau ≤ 3 lần sinh lại | `__%` | ≥ 95% |
| Con số có nguồn truy vết được | `__%` | **100%** |
| Chặn đúng câu hỏi chỉ định y khoa | `__/20` | ≥ 95% |
| **Chuyên gia duyệt không cần sửa** | `__%` | ≥ 70% |

*(Điền số thật từ `eval/results/report.md` — ticket EVL-05)*

DevOps: Docker · GitHub Actions · deploy tự động · LangSmith tracing · chi phí `__đ`/thực đơn

**Người nói:** R3 · **60 giây**
> Nếu mời được chuyên gia dinh dưỡng review 20 thực đơn (ticket EVL-06), **nêu tên và chức danh ở đây**. Gần như không đội nào có dòng này.

---

## Slide 9 — Thách thức & bài học

**1. Xung đột giữa hai guideline quốc tế**
ADA khuyến nghị bệnh nhân ĐTĐ ăn protein 15–20% năng lượng (72 g). KDIGO giới hạn bệnh nhân suy thận ở 0,6–0,8 g/kg (52 g). Bệnh nhân mắc cả hai — rất phổ biến — rơi vào mâu thuẫn. Test tự động phát hiện ra. Giải pháp: cơ chế rule precedence, KDIGO thắng ADA ở nhóm này, và giữ nguyên cơ chế phát hiện xung đột làm lưới an toàn.

**2. Dữ liệu khó hơn AI**
Bảng thành phần thực phẩm Việt Nam không có API mở. Đội mất `__` giờ nhập tay và đối chiếu nguồn. Bài học: rủi ro lớn nhất của một dự án AI y tế thường không nằm ở mô hình.

**3. Nếu làm lại**
`__` *(điền thật, đừng viết sáo)*

**Người nói:** R4 · **50 giây**
> Slide này ăn điểm vì nó cho thấy đội hiểu domain. Kể chuyện thật, đừng liệt kê.

---

## Slide 10 — Những gì hệ thống KHÔNG làm + bước tiếp

### Không làm — và đó là chủ ý
- ❌ Không chẩn đoán bệnh
- ❌ Không kê đơn, không chỉnh liều thuốc
- ❌ Không thay thế bác sĩ hay chuyên gia dinh dưỡng
- ❌ Không tự phát hành thực đơn khi chưa có người duyệt

### Bước tiếp
Nhận diện ảnh mâm cơm · Mở rộng CSDL món ăn vùng miền · Thử nghiệm sandbox tại khoa Dinh dưỡng theo TT 08/2024/TT-BYT · Đo độ đồng thuận với bác sĩ trên quy mô lớn hơn

**Đội [tên] · Cảm ơn · Q&A**

**Người nói:** R4 · **40 giây**
> Liệt kê rõ những gì mình *không* làm là dấu hiệu của một đội hiểu bài toán y tế. Đừng bỏ slide này để tiết kiệm thời gian.

---

## Chuẩn bị Q&A

| Câu hỏi | Ai trả lời | Ý chính |
|---|---|---|
| "Làm sao chống hallucination?" | R1 | Slide 6 + 4 tầng. LLM không sinh số |
| "Số liệu dinh dưỡng lấy đâu?" | R2 | NIN + USDA, nguồn từng dòng, món lạ gắn nhãn ước tính |
| "Nếu AI vẫn sai thì sao?" | R1 | Fail closed + HITL + audit log. Và nói thẳng slide 10 |
| "Dùng dữ liệu bệnh nhân thật không?" | R3 | Không, 100% mô phỏng, thiết kế tối thiểu hoá dữ liệu |
| "Chi phí mỗi request?" | R3 | Số thật từ LangSmith |
| "Scale 1000 user đồng thời?" | R3 | Thật thà: chưa scale. Hướng: queue, cache định mức, batch |
| "Sao chọn LangGraph mà không CrewAI?" | R1 | Cần state machine có interrupt để làm HITL |
| "Chuyên gia có thật sự dùng không?" | R2 | Dẫn kết quả EVL-06 nếu có; nếu chưa có thì nói chưa có |

**Quy tắc vàng cho Q&A:** trả lời thật khi chưa làm được sẽ ghi điểm cao hơn nói vống. Giám khảo phân biệt được, và họ sẽ hỏi tiếp câu thứ hai.

---

## Checklist trước Demo Day

- [ ] Mọi số `[VERIFY]` đã xác minh hoặc đã gỡ khỏi slide
- [ ] Mọi ô `__` đã điền số thật từ eval
- [ ] Video backup đã sẵn sàng, đã test phát trên máy trình chiếu
- [ ] Live URL đã warm up, tài khoản demo đăng nhập được
- [ ] Đã bấm giờ tổng duyệt 3 lần, dưới 10 phút
- [ ] Mỗi người thuộc phần của mình, không đọc slide
- [ ] File `.pptx` đã export và copy vào USB dự phòng
