# RULE 40 — DỮ LIỆU & RAG

> Owner: **R2**

---

## R40.1 — Phân biệt dứt khoát: dữ liệu có cấu trúc dùng SQL, văn bản dùng RAG

| Loại dữ liệu | Cách truy cập | Lý do |
|---|---|---|
| Bảng thành phần thực phẩm, công thức món, ngưỡng lâm sàng, tương tác thuốc | **SQL** | Cần con số chính xác tuyệt đối |
| Guideline BYT/ADA/KDIGO, tài liệu tư vấn, tài liệu giáo dục | **RAG (pgvector)** | Cần diễn giải và trích dẫn |

**Không bao giờ** đưa bảng thành phần thực phẩm vào vector store để LLM đọc snippet. Đó chính là cách tạo ra lỗi bịa số mà cả kiến trúc đang cố chống.

## R40.2 — Không dòng dữ liệu nào thiếu nguồn

Mọi bảng dữ liệu tri thức (`food_items`, `dishes`, `clinical_rules`, `drug_food_interactions`, `guideline_chunks`) phải có cột `source` và `source_ref` khác NULL. CI có test kiểm tra (`EVL-03`).

`source` chỉ nhận: `NIN` | `USDA` | `curated` | `estimated`.
Với `estimated`, bắt buộc kèm `confidence` và `estimation_method`.

## R40.3 — Quy trình thêm dữ liệu thực phẩm

1. Tra nguồn gốc (NIN → USDA → ước tính từ nguyên liệu)
2. Nhập vào `data/seeds/*.csv` kèm `source_ref` (tên tài liệu + trang/ID)
3. Chạy `make validate-data` (kiểm tra khoảng giá trị hợp lý)
4. PR → R2 review → merge

**Kiểm tra khoảng hợp lý tự động:** kcal/100g trong 0–900, protein 0–90 g, Na 0–20000 mg (nước mắm rất mặn nên trần cao), GI 0–110. Ngoài khoảng → CI đỏ.

## R40.4 — Bảng đồng nghĩa (OOV) là dữ liệu hạng nhất

Cột `aliases` phải phủ biến thể vùng miền: `dứa = thơm = khóm`, `lạc = đậu phộng`, `cá quả = cá lóc = cá chuối`, `mè = vừng`, `ngò = rau mùi`, `thìa là = thì là`, `bắp = ngô`, `sắn = khoai mì`, `mướp đắng = khổ qua`.

Không tra được tên → chuyển sang OOV Estimator, **không đoán bừa sang thực phẩm gần giống**.

## R40.5 — Ước tính phải trung thực

Kết quả OOV luôn: `is_estimated=true`, có `confidence` (0–1), có `estimation_method` mô tả cách suy ra, và UI hiển thị nhãn "ước tính". Không được lẫn với dữ liệu đo thật ở bất kỳ đâu.

## R40.6 — RAG: chunk có metadata đầy đủ

Mỗi chunk lưu: `source`, `title`, `page`, `condition` (bệnh lý liên quan), `organization`, `year`, `url`. Không có metadata thì không ingest — vì sẽ không trích dẫn được.

Chunk 500–800 token, overlap ~100, cắt theo ranh giới mục/đoạn chứ không cắt giữa câu.

## R40.7 — RAG: mọi câu trả lời phải trích dẫn

Câu trả lời dựa trên guideline phải kèm nguồn hiển thị cho người dùng. Không tìm được chunk liên quan → nói "chưa có tài liệu về vấn đề này trong cơ sở tri thức", **không suy đoán từ kiến thức nền của LLM**.

## R40.8 — Hybrid search

BM25 (Postgres full-text, cấu hình cho tiếng Việt) + vector similarity, hợp nhất bằng Reciprocal Rank Fusion. Chỉ dùng vector sẽ trượt các truy vấn chứa thuật ngữ chính xác ("KDIGO 2024", "G3b").

## R40.9 — Kiểm chứng số liệu trước khi công bố

Mọi số liệu đưa lên README, slide, video phải có dòng tương ứng trong `docs/REFERENCES.md` với trạng thái `verified`. Số liệu `not-found` phải bị gỡ bỏ, không được "chắc là đúng".

## R40.10 — Bản quyền và giấy phép

Ghi rõ trong `data/README.md`: mỗi nguồn dữ liệu lấy từ đâu, giấy phép gì, được dùng vào mục đích gì. Với tài liệu có bản quyền: **chỉ trích dẫn ngắn có dẫn nguồn, không sao chép nguyên khối vào repo**. Dự án học thuật vẫn phải tôn trọng quyền tác giả.

## R40.11 — Dữ liệu mô phỏng phải trông thật nhưng được đánh dấu rõ

Bệnh nhân seed dùng tên rõ ràng là giả (`BN Demo 01 — Đái tháo đường týp 2`), nhưng chỉ số lâm sàng phải hợp lý về mặt y khoa để demo có sức thuyết phục. R2 chịu trách nhiệm về tính hợp lý này.

## R40.12 — Versioning dữ liệu

Mỗi lần cập nhật seed đáng kể, tăng version trong `data/VERSION` và ghi vào DEVLOG. Kết quả eval phải ghi kèm version dữ liệu — nếu không, không so sánh được giữa các lần chạy.
