# REPO AUDIT — Đối chiếu repo với template AI20K

> Ngày: 27/07/2026 · Repo: `hwngkm/VMEC10_P31`
> ⚠️ **Giới hạn của báo cáo này:** repo đang ở chế độ private nên tôi không truy cập được từ ngoài (HTTP 404). Các phát hiện dưới đây dựa trên **file mà các bạn đã đưa vào Project Content**, nên danh sách có thể chưa đầy đủ. Chạy `python scripts/check_structure.py` trên máy để có kết quả chính xác 100%.

---

## 1. Ba vấn đề nghiêm trọng

### 🔴 1.1. Đường dẫn sandbox lọt vào repo

Trong Project Content có file ở đường dẫn:

```
mnt/user-data/outputs/code/data/README.md
mnt/user-data/outputs/docs/PLAN.md
```

`mnt/user-data/outputs/` là **thư mục làm việc của AI agent**, không phải thư mục dự án. Agent đã copy nguyên cả đường dẫn tuyệt đối vào repo, tạo ra một cây thư mục ma song song với cây thật.

**Vì sao nghiêm trọng:** giám khảo clone repo về sẽ thấy `mnt/user-data/...` ngay ở gốc — ấn tượng đầu tiên là dự án được ghép máy móc, không ai đọc lại. Nó cũng tạo ra file trùng lặp: `data/README.md` và `mnt/user-data/outputs/code/data/README.md` là cùng một nội dung.

**Sửa:** `git rm -r --cached mnt/` và thêm `mnt/` vào `.gitignore`.

### 🔴 1.2. Pitch deck sai vị trí

Đang ở `docs/pitch_deck.md`. Template quy định Deliverable #7 nằm ở **`presentation/pitch_deck.pptx`**.

Thư mục `presentation/` hiện chưa tồn tại trong repo. Giám khảo chấm theo checklist đường dẫn — để sai chỗ có thể bị tính là thiếu deliverable, dù nội dung đã có.

### 🔴 1.3. Thiếu `JOURNAL.md` và `WORKLOG.md`

Đây là lỗi **do tôi gây ra** ở lượt trước: tôi gộp cả hai vào một file `DEVLOG.md` cho tiện ghi chép, nhưng quên đối chiếu với template — BTC chấm Deliverable #8 và #9 theo đúng hai tên `JOURNAL.md` và `WORKLOG.md` ở gốc repo.

**Sửa:** giữ `DEVLOG.md` làm nguồn sự thật duy nhất (viết một chỗ, không chép ba lần), và dùng `scripts/sync_devlog.py` sinh tự động ra hai file kia. Đã viết sẵn script, đã test.

---

## 2. Vấn đề vừa

| # | Vấn đề | Ảnh hưởng | Cách sửa |
|---|---|---|---|
| 2.1 | `CLAUDE.md` tồn tại ở cả gốc repo và `.claude/CLAUDE.md` | Hai bản dễ lệch nhau, sửa một quên một | Giữ bản ở gốc (Claude Code đọc chỗ đó). `.claude/` chỉ để chứa `skills/` |
| 2.2 | `docs/ARCHITECTURE.md` — template chấm theo tên `docs/architecture_diagram.md` | Deliverable #3 có thể bị tính thiếu | `git mv` + cập nhật tham chiếu trong các file md |
| 2.3 | Thiếu `src/api/`, `src/models/`, `src/services/`, `src/core/` | Tiêu chí "System Design" chấm cả folder structure | Tạo sẵn kèm `.gitkeep` |
| 2.4 | Thiếu `tests/{unit,integration,eval}` | Template quy định 3 nhóm test riêng | Tạo và chuyển test hiện có vào `tests/unit/` |
| 2.5 | Thiếu `eval/`, `.github/workflows/` | Deliverable #10 + điểm DevOps | Tạo sẵn |

---

## 3. Một điểm mâu thuẫn trong chính template

Tài liệu template tự nó nói hai chỗ khác nhau về vị trí deliverable:

| Deliverable | `deliverables/checklist.md` + `README_boilerplate.md` | `chapter-09.md` |
|---|---|---|
| #7 Pitch Deck | `presentation/pitch_deck.pptx` | `docs/pitch-deck.pdf` |
| #8 Journal | `/JOURNAL.md` | `docs/journal.md` |
| #9 Worklog | `/WORKLOG.md` | `docs/worklog.md` |
| #3 Architecture | `docs/architecture_diagram.md` | `docs/architecture.md` |

**Khuyến nghị:** theo `checklist.md` và `README_boilerplate.md`, vì template **ship sẵn các file đó** (`README_boilerplate.md` ghi rõ "Template đã có sẵn, chỉ cần điền"). Để chắc chắn, tạo thêm file trỏ ở vị trí còn lại — tốn 3 dòng, loại bỏ hoàn toàn rủi ro:

```markdown
<!-- docs/journal.md -->
Nhật ký phát triển: xem [JOURNAL.md](../JOURNAL.md)
```

Và **hỏi BTC/mentor** để chốt. Đây là câu hỏi 30 giây, đừng đoán.

---

## 4. Bảng ánh xạ: file hiện tại → vị trí chuẩn

| Hiện tại | Chuyển tới | Lý do |
|---|---|---|
| `mnt/user-data/outputs/**` | 🗑️ xoá | Rác sandbox |
| `docs/pitch_deck.md` | `presentation/pitch_deck.md` | Deliverable #7 |
| `docs/ARCHITECTURE.md` | `docs/architecture_diagram.md` | Deliverable #3 |
| `.claude/CLAUDE.md` | 🗑️ xoá (giữ bản gốc repo) | Trùng lặp |
| `DEVLOG.md` | giữ nguyên + sinh `JOURNAL.md`, `WORKLOG.md` | Deliverable #8, #9 |
| `code/src/**` (nếu có) | `src/**` | Không lồng thêm một tầng `code/` |
| `code/tests/**` (nếu có) | `tests/unit/**` | |
| `docs/00_ASSESSMENT.md`, `PLAN.md`, `TICKETS.md`, `TEAM.md`, `rules/` | giữ nguyên | Tài liệu bổ sung, hợp lệ |

---

## 5. Cấu trúc đích

```
VMEC10_P31/
├── README.md                      ← Deliverable #2
├── JOURNAL.md                     ← Deliverable #8  (sinh tự động)
├── WORKLOG.md                     ← Deliverable #9  (sinh tự động)
├── DEVLOG.md                      ← nguồn sự thật, đội ghi hằng ngày
├── CLAUDE.md                      ← rules cho AI coding agent
├── Dockerfile · docker-compose.yml · .env.example · .gitignore
├── pyproject.toml · Makefile
├── .github/workflows/ci.yml       ← CI/CD
├── .claude/skills/                ← chỉ chứa skills, KHÔNG chứa CLAUDE.md
├── src/                           ← Deliverable #1
│   ├── main.py · config.py
│   ├── agents/{graph,state}.py · nodes/ · tools/
│   ├── clinical/                  ← lõi deterministic của dự án
│   ├── api/routes/ · models/ · services/ · core/
├── tests/{unit,integration,eval}/
├── data/{README.md,seeds/}
├── scripts/{check_structure.py,sync_devlog.py,reorganize_repo.sh,validate_data.py}
├── eval/{datasets,scripts,results/report.md}   ← Deliverable #10
├── presentation/pitch_deck.md → .pptx          ← Deliverable #7
└── docs/
    ├── architecture_diagram.md    ← Deliverable #3
    ├── 00_ASSESSMENT.md · PLAN.md · TICKETS.md · TEAM.md · INDEX.md
    ├── REPO_AUDIT.md              ← file này
    ├── rules/ · adr/
```

---

## 6. Cách sửa — 15 phút

```bash
# 1. Nhánh riêng, không đụng develop
git checkout -b chore/reorganize-repo
git status                                  # phải sạch

# 2. Copy 3 script vào scripts/
#    check_structure.py · sync_devlog.py · reorganize_repo.sh

# 3. Xem trước sẽ thay đổi gì (KHÔNG sửa gì cả)
bash scripts/reorganize_repo.sh

# 4. Đọc kỹ danh sách, rồi chạy thật
bash scripts/reorganize_repo.sh --apply

# 5. Kiểm tra lại
python scripts/check_structure.py           # mục tiêu: 0 lỗi

# 6. Commit
git add -A
git commit -m "chore: sắp xếp lại repo theo template AI20K"
git push -u origin chore/reorganize-repo
```

Script chạy **dry-run mặc định**, dùng `git mv` nên giữ được lịch sử file, và idempotent — chạy lại nhiều lần không hỏng.

---

## 7. Chặn tái diễn

Thêm vào `.github/workflows/ci.yml` để CI tự chặn:

```yaml
  structure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Kiểm tra cấu trúc repo
        run: python scripts/check_structure.py
      - name: Kiểm tra dữ liệu seed
        run: python scripts/validate_data.py
```

Sau đó không ai vô tình commit `mnt/`, `.venv/`, hay đặt pitch deck sai chỗ được nữa.

---

## 8. Bài học về quy trình

Đây là hệ quả trực tiếp của việc **để agent tự sắp xếp file mà không có ai kiểm tra đầu ra**. Agent copy nguyên đường dẫn tuyệt đối vào repo — một người nhìn 5 giây là thấy sai, nhưng không ai nhìn.

Hai quy tắc nên chốt luôn:

1. **Mọi thay đổi cấu trúc repo phải qua PR có người review.** Không agent nào được push thẳng.
2. **CI kiểm tra cấu trúc** — vì con người sẽ quên, còn CI thì không.

Ghi việc này vào `DEVLOG.md` §4 (Sự cố & bài học). Nó là nguyên liệu tốt cho slide 9 "Challenges & Learnings" — thật hơn nhiều so với những bài học chung chung.

---

## 9. Việc tôi chưa kiểm tra được

Vì repo private, những mục sau chưa xác nhận được — hãy tự kiểm tra:

- [ ] `.env` có bị commit nhầm không? → `git log --all --full-history -- .env`
- [ ] Có API key nào trong lịch sử commit không? → cài `gitleaks` và quét
- [ ] `.ai-log/` đã có dữ liệu chưa (Deliverable #4)?
- [ ] `.github/workflows/ci.yml` của template còn nguyên hay bị xoá?
- [ ] `pyproject.toml` đã đổi tên dự án chưa, hay vẫn là tên template?
- [ ] Branch `develop` đã tạo chưa, branch protection đã bật chưa?
- [ ] File nào >10MB không? → `git ls-files | xargs -I{} du -h {} | sort -rh | head`

**Cách nhanh nhất để tôi rà giúp:** chạy lệnh dưới rồi dán kết quả vào chat.

```bash
git ls-files | sort
```
