### Thay đổi
- …

### Vì sao
- Ticket `MÃ-TICKET` — …

### Cách test
1. `make check`
2. …

### Checklist (Definition of Done — xem docs/rules/50-workflow.md §R50.3)
- [ ] `make check` xanh (ruff + format + mypy + pytest)
- [ ] Có test cho logic mới
- [ ] Không secret, không `print()`, không `except:` trần
- [ ] Đã cập nhật `.env.example` nếu thêm biến môi trường
- [ ] Đã cập nhật tài liệu nếu đổi kiến trúc/API
- [ ] Đã ghi `DEVLOG.md`
- [ ] Nếu PR chạm số liệu dinh dưỡng: mọi giá trị đều có `source` (RULE-2, xem `CLAUDE.md` §2)
