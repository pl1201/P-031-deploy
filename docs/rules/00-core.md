# RULE 00 — CỐT LÕI

Áp dụng cho mọi người, mọi file, mọi PR. Khi rule ở tầng dưới mâu thuẫn với file này, file này thắng.

---

## R00.1 — Thứ tự ưu tiên khi phải đánh đổi

```
An toàn bệnh nhân  >  Tính đúng đắn dữ liệu  >  Tính năng  >  Tốc độ  >  Vẻ đẹp code
```

Khi phân vân, chọn phương án an toàn hơn và ghi lý do vào `DEVLOG.md`.

## R00.2 — Fail closed

Nghi ngờ thì chặn, không phát hành. Không có "cảnh báo nhưng vẫn cho qua" đối với: dị ứng, tương tác thuốc mức `high`, vi phạm ngưỡng `hard`.

## R00.3 — Truy vết được

Mọi thứ đến tay người dùng phải trả lời được 3 câu hỏi:
1. Con số này ở đâu ra? → `source`
2. Vì sao chọn món này? → `applied_rule_ids` + explanation
3. Ai chịu trách nhiệm? → `reviewer_id` + `audit_log`

## R00.4 — Không tính năng ẩn

Không code path nào chạy mà không xuất hiện trong `ARCHITECTURE.md`. Thêm luồng mới → cập nhật tài liệu trong cùng PR.

## R00.5 — Nói thật về giới hạn

Trong UI, README, pitch deck và khi trả lời giám khảo: mô tả đúng những gì hệ thống làm được. Không dùng từ "chính xác tuyệt đối", "thay thế bác sĩ", "chẩn đoán", "chuẩn y khoa được chứng nhận".

## R00.6 — Quyết định phải để lại vết

Mọi quyết định kỹ thuật đáng kể ghi vào `DEVLOG.md` mục Decisions theo dạng: *bối cảnh → phương án đã cân nhắc → quyết định → hệ quả*. Tuần 6 sẽ cần nó cho slide "Challenges & Learnings".

## R00.7 — Ranh giới sở hữu

Mỗi thư mục có 1 owner (`.github/CODEOWNERS`). Sửa code người khác thì báo trước hoặc để lại comment trong PR. Không âm thầm refactor module của người khác giữa sprint.

## R00.8 — Khi bị chặn

Vướng > 90 phút → đăng vào nhóm chat kèm: đang làm gì, đã thử gì, lỗi gì. Không ai bị phán xét vì hỏi. Bị phán xét vì im lặng 2 ngày.

## R00.9 — Định nghĩa "xong"

Xem `PLAN.md` §5. Ngắn gọn: chạy được + có test + CI xanh + được review + đã ghi DEVLOG. Chưa đủ 5 thứ đó thì ticket vẫn đang mở.

## R00.10 — Thời gian là tài nguyên khan hiếm nhất

Trước khi thêm bất cứ thứ gì không có trong `TICKETS.md`, hỏi: *cái này có nằm trong 10 deliverables không? Có làm demo tốt hơn không?* Nếu cả hai đều không → đừng làm.
