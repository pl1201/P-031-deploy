# UI Flow

```mermaid
flowchart TD
    START(["START"])

    START --> BS_IN["Bác sĩ nhập sau chẩn đoán<br/>kết quả cận lâm sàng · kết luận bệnh<br/>BMI · khối cơ/khối mỡ<br/>vòng eo · bắp tay · bắp chân<br/>bệnh kèm theo · thuốc đang dùng · dị ứng<br/>nhu cầu dinh dưỡng chỉ định"]

    START --> PT_IN["Người bệnh nhập<br/>ngày sinh · tên · giới tính<br/>cân nặng · chiều cao<br/>nghề nghiệp · mức độ hoạt động thể lực<br/>thực đơn / thành phần thực phẩm"]

    BS_IN --> Q1{"Đã đủ hồ sơ lâm sàng?<br/>bệnh lý + đồng mắc<br/>+ thuốc đang dùng + dị ứng"}
    Q1 -- "KHÔNG" --> STOP1(["Chưa tạo thực đơn<br/>Yêu cầu bổ sung hồ sơ"])

    Q1 -- "CÓ" --> Q2{"Đã đủ hồ sơ cá nhân?<br/>nhân trắc (BMI, khối cơ/mỡ, vòng đo)<br/>+ nhân khẩu, mức độ hoạt động"}
    PT_IN --> Q2
    Q2 -- "KHÔNG" --> STOP1

    Q2 -- "CÓ" --> Q3{"Đã có sở thích<br/>+ thực đơn/thực phẩm tham chiếu?"}
    Q3 -- "KHÔNG" --> STOP1
    Q3 -- "CÓ" --> GEN["AI xây dựng thực đơn<br/>dựa trên Lõi tính toán dinh dưỡng<br/>+ Bộ quy tắc lâm sàng<br/>+ CSDL thực phẩm &amp; món Việt"]

    GEN --> Q4{"Thực đơn đạt ngưỡng<br/>dinh dưỡng lâm sàng?"}
    Q4 -- "KHÔNG" --> FIX["Tự động điều chỉnh<br/>đổi món / sửa khẩu phần"]
    Q4 -- "CÓ" --> Q5{"Có chứa thực phẩm<br/>gây dị ứng?"}
    Q5 -- "CÓ, chứa dị ứng" --> FIX
    Q5 -- "KHÔNG" --> Q6{"Có tương tác<br/>thuốc-thực phẩm nguy hiểm?"}
    Q6 -- "CÓ" --> FIX
    FIX --> GEN
    Q6 -- "KHÔNG" --> Q7{"Chuyên gia<br/>đồng ý với thực đơn?"}

    Q7 -- "Cần sửa nhẹ" --> EDIT["Chuyên gia sửa<br/>khẩu phần/món"]
    EDIT --> APPROVE["Duyệt thực đơn"]
    Q7 -- "Đồng ý luôn" --> APPROVE
    Q7 -- "Từ chối" --> REJECT["Ghi lý do từ chối"]
    REJECT --> FIX

    APPROVE --> DOIT(["Giao thực đơn đã duyệt<br/>cho bệnh nhân!"])

    classDef terminal fill:#fff,stroke:#000,stroke-width:2px,color:#000
    classDef decision fill:#fff,stroke:#000,stroke-width:2px,color:#000
    classDef process fill:#fff,stroke:#000,stroke-width:2px,color:#000
    classDef doit fill:#000,stroke:#000,stroke-width:2px,color:#fff,font-weight:bold
    classDef doctor fill:#e6f4ea,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef patient fill:#e8f0fe,stroke:#1a56db,stroke-width:2px,color:#000

    class START,STOP1 terminal
    class Q1,Q2,Q3,Q4,Q5,Q6,Q7 decision
    class GEN,FIX,EDIT,APPROVE,REJECT process
    class DOIT doit
    class BS_IN doctor
    class PT_IN patient
```
