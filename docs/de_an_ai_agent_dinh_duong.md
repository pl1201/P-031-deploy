Đề Án Hệ Thống AI Agent Dinh Dưỡng Lâm Sàng & Cá Nhân Hóa (Phiên Bản Mở Rộng)

1. Thực Trạng, Cơ Sở Khoa Học & Đặt Vấn Đề

1.1. Thực trạng Y tế & Dinh dưỡng Lâm sàng tại Việt Nam

Gánh nặng Bệnh không lây nhiễm (NCDs): Theo thống kê của Bộ Y tế và WHO, các bệnh mãn tính như Đái tháo đường (ĐTĐ), Bệnh thận mãn tính (CKD), Tăng huyết áp, Bệnh tim mạch và Gout đang gia tăng nhanh chóng tại Việt Nam. Tỷ lệ bệnh nhân đạt mục tiêu kiểm soát đường huyết hoặc huyết áp duy trì ở mức thấp, trong đó dinh dưỡng đóng vai trò tiên quyết nhưng thường bị bỏ ngỏ.

Tình trạng tuân thủ chế độ ăn kiêng: Nghiên cứu lâm sàng cho thấy trên $70\%$ bệnh nhân mãn tính không tuân thủ được thực đơn được tư vấn sau 03 tháng rời viện. Nguyên nhân chính do:

Khẩu phần ăn được kê đơn cứng nhắc, đơn điệu, không phù hợp với khẩu vị cá nhân.

Thiếu sự đồng hành, theo dõi và phản hồi liên tục từ chuyên gia y tế.

Người bệnh dễ sa vào các tin đồn dinh dưỡng thiếu căn cứ khoa học trên không gian mạng (mạng xã hội, diễn đàn truyền miệng).

1.2. Yếu tố Văn hóa - Xã hội & Hành vi Ăn uống người Việt

Cấu trúc "Mâm cơm gia đình": Khác với văn hóa ăn theo đĩa riêng của phương Tây, người Việt Nam thường ăn chung mâm cơm gia đình. Điều này gây khó khăn cực lớn cho bệnh nhân trong việc đong đếm chính xác định lượng calo và dưỡng chất, cũng như tạo ra rào cản tâm lý "ăn biệt lập" so với các thành viên khác.

Sự đa dạng ẩm thực 3 miền:

Miền Bắc: Khẩu vị thanh nhẹ, ưu tiên luộc/hấp, dùng nước mắm nguyên chất.

Miền Trung: Khẩu vị đậm đà, thiên về mặn và cay, sử dụng nhiều loại mắm nêm, mắm ruốc (lượng muối rất cao, nguy cơ lớn cho bệnh nhân tim mạch/thận).

Miền Nam: Khẩu vị thiên ngọt, sử dụng nhiều đường và nước cốt dừa (nguy cơ cho bệnh nhân ĐTĐ và rối loạn lipid máu).

Thói quen sử dụng thực phẩm địa phương & OOV (Out-of-Vocabulary): Nhiều tên gọi rau củ, cá tôm theo từng địa phương (ví dụ: rau ngót, rau dền, cá lóc, cá quả, cá măng...) hoặc các món ăn đường phố không có trong các CSDL chuẩn quốc tế.

Hành vi kiêng khem dân gian: Tồn tại nhiều quan niệm lệch lạc như "bị ung thư phải nhịn ăn để tế bào ung thư chết đói", "bị tiểu đường bỏ hoàn toàn tinh bột", "bị thận kiêng tuyệt đối đạm"... dẫn đến suy dinh dưỡng nghiêm trọng trước khi điều trị bệnh lý chính.

1.3. Phân tích Giải Pháp Hiện Có & Khoảng Trống Công Nghệ (Market Gap)

Tiêu chí

Các ứng dụng Quốc tế (MyFitnessPal, Noom, Cronometer)

Ứng dụng/Sổ tay Nội địa hiện tại

Giải pháp AI Agent Dinh Dưỡng đề xuất

CSDL Thực phẩm

Phong phú món Tây (USDA DB), thiếu dữ liệu món ăn Việt Nam chi tiết

Có dữ liệu món Việt cơ bản (bảng tĩnh), thiếu biến thể 3 miền

RAG tích hợp Bảng TPTP Việt Nam (NIN) + CSDL món ăn vùng miền mở rộng

Tính năng Lâm sàng

Thiên về giảm cân/Fitness; không hỗ trợ ràng buộc y tế phức tạp (CKD, ĐTĐ)

Hướng dẫn chung chung, không cá nhân hóa theo từng chỉ số xét nghiệm

Tích hợp Guideline Y tế lâm sàng (ADA, KDIGO, BYT) & cảnh báo vi chất chi tiết

Xử lý Mâm cơm gia đình

Chỉ tính theo đĩa đơn cá nhân

Chưa có giải pháp

Giải thuật phân rã mâm cơm gia đình thành khẩu phần bệnh nhân

Cơ chế An toàn

Không có kiểm duyệt y tế (No HITL)

Tài liệu tĩnh, không tương tác

BẮT BUỘC duyệt bởi Bác sĩ/Chuyên gia (HITL Workflow)

Cảnh báo Thuốc - Thực phẩm

Rất hạn chế

Không có

Tích hợp Ma trận tương tác Thuốc - Thực phẩm (Drug-Food Interaction)

1.4. Đặt Vấn đề & Giải pháp Hệ thống

Xây dựng AI Agent Dinh Dưỡng Lâm Sàng đóng vai trò trợ lý chuyên sâu cho Chuyên gia dinh dưỡng/Bác sĩ và là người đồng hành cá nhân hóa cho Bệnh nhân, giải quyết triệt để bài toán: Ăn đúng chuẩn y khoa - Phù hợp khẩu vị Việt - Dễ tuân thủ dài hạn.

1.5. Đối tượng Người dùng

Bác sĩ / Chuyên gia Dinh dưỡng: Tiết kiệm thời gian lập thực đơn, quản lý và duyệt thực đơn hàng loạt, theo dõi tuân thủ của bệnh nhân.

Bệnh nhân cần Chế độ Dinh dưỡng Đặc thù: Bệnh nhân ĐTĐ, suy thận (các giai đoạn 1 - 5), Tăng huyết áp, Gout, Suy tim, Bệnh nhân sau phẫu thuật.

Người nhà / Người chăm sóc: Nhận gợi ý đi chợ, nấu nướng phù hợp với mâm cơm chung nhưng vẫn đáp ứng chỉ định y khoa cho người bệnh.

2. Cơ Sở Khoa Học & Khung Chuẩn Y Tế (Clinical Guidelines)

Hệ thống AI Agent được thiết kế dựa trên sự hợp nhất của các Quy chuẩn & Phác đồ điều trị dinh dưỡng chính thống:

2.1. Hướng Dẫn Lâm Sàng Quốc Tế

Đái tháo đường (ADA - American Diabetes Association): Kiểm soát chỉ số Glycemic Index (GI) và Glycemic Load (GL); phân bổ Carbohydrate tinh chế $< 40 - 50\%$ tổng năng lượng; bổ sung chất xơ $\ge 14\text{ g}/1000 \text{ kcal}$.

Bệnh thận mãn tính (KDIGO & KDOQI Guidelines):

CKD chưa lọc máu (G3a - G5): Lượng Protein giới hạn ở mức $0.6 - 0.8 \text{ g/kg/ngày}$.

Kiểm soát Kali ($< 2000 - 3000 \text{ mg/ngày}$), Phospho ($< 800 - 1000 \text{ mg/ngày}$) và Natri ($< 2000 \text{ mg/ngày}$).

Tim mạch & Tăng huyết áp (ESC/AHA & Chế độ ăn DASH): Natri $< 1500 - 2000 \text{ mg/ngày}$ (tương đương $< 3.8 - 5 \text{ g}$ muối ăn/ngày); ưu tiên chất béo không bão hòa.

Gout (ACR - American College of Rheumatology): Hạn chế Purine $< 150 \text{ mg/ngày}$; tránh nội tạng động vật, hải sản giàu purine, rượu bia và nước ngọt chứa Fructose high-corn syrup.

2.2. Hướng Dẫn & Quy Chuẩn Quốc Gia (Việt Nam)

Phác đồ Điều trị Dinh dưỡng Bộ Y tế Việt Nam: Các Quyết định ban hành hướng dẫn chế độ ăn bệnh viện cho từng nhóm bệnh lý (VD: Quyết định 2598/QĐ-BYT, Quyết định 3777/QĐ-BYT, Thông tư 08/2024/TT-BYT).

Bảng Thành phần Thực phẩm Việt Nam (NIN - Viện Dinh dưỡng Quốc gia): Tra cứu năng lượng, đạm, béo, đường, xơ và các vi chất ($Na, K, P, Ca, Fe...$) của trên $500+$ thực phẩm phổ biến tại Việt Nam.

2.3. Ma Trận Tương Tác Thực Phẩm - Thuốc (Drug-Food Interactions)

Warfarin / Coumadin (Thuốc chống đông): Cảnh báo khi người bệnh ăn quá nhiều rau xanh đậm chứa Vitamin K (rau muống, rau ngót, cải bắp, cải kale).

Thuốc ức chế men chuyển ACEi / ARB (Điều trị Tăng huyết áp): Cảnh báo khi phối hợp với thực phẩm giàu Kali (chuối, bưởi, nước dừa, muối thế thế Potassium).

Statins (Hạ mỡ máu): Cảnh báo tương tác nghiêm trọng với Bưởi (Grapefruit) gây tăng nồng độ thuốc trong máu.

Metformin (Điều trị Đái tháo đường): Cảnh báo nguy cơ thiếu hụt Vitamin B12 và phản ứng tiêu hóa khi dùng chung với Rượu/Cồn.

3. Bộ Dữ Liệu & Tri Thức Hệ Thống (Datasets & Knowledge Base)

Hệ thống tích hợp và chuẩn hóa các bộ dữ liệu đa nguồn:

Vietnamese Food Composition Database (NIN DB): Dữ liệu chuẩn về $500+$ thực phẩm thô và chế biến tại Việt Nam.

USDA FoodData Central: Bổ sung dữ liệu vi chất chi tiết và các nguyên liệu nhập khẩu.

Vietnamese Regional Recipe Dataset: CSDL $1000+$ công thức món ăn 3 miền, phân tích chi tiết thành phần nguyên liệu.

Clinical Nutrition Ruleset DB: CSDL quy tắc logic y tế (VD: IF CKD_Stage == 4 THEN Protein_Max = 0.6 * Weight_kg).

Drug-Food Interaction Knowledge Graph (DDID): Đồ thị tri thức về $23950+$ tương tác giữa thuốc và thực phẩm.

OOV Local Synonym Mapping: Bảng tra cứu từ đồng nghĩa địa phương (VD: Trái thơm = Dứa = Khóm; Rau ngổ = Rau ngô).

4. Quy Trình Hoạt Động Chi Tiết (Agent Workflow)

 [Hồ sơ Bệnh nhân + Chỉ số Xét nghiệm + Thuốc đang dùng]
                        │
                        ▼
       [1. Phân tích Nhu cầu & Định mức Lâm sàng]
 (Tính BMR, TDEE, Calo, Protein, Na, K, P, Purine max)
                        │
                        ▼
   [2. LangGraph Router & Hybrid RAG Retrieval]
 (Tra CSDL NIN + Guideline Y tế + Sở thích/Mâm cơm gia đình)
                        │
                        ▼
          [3. Sinh Thực Đơn Cá Nhân Hóa]
(Đề xuất khẩu phần 3 bữa + Phân rã mâm cơm gia đình + Xử lý OOV)
                        │
                        ▼
      [4. Safety Guardrails & Interaction Check]
 (Kiểm tra vượt ngưỡng vi chất + Tương tác Thuốc-Thực phẩm)
                        │
                        ▼
      [5. Quy trình Phê duyệt HITL (Bác sĩ/Chuyên gia)]
          ├─► Refused/Edit ──► [Agent Tái điều chỉnh]
          └─► Approved
                        │
                        ▼
         [6. Gửi Thực đơn đến Bệnh nhân/Người nhà]
                        │
                        ▼
       [7. Nhật Ký Ăn Uống & Adaptive Feedback]
    (Bệnh nhân log bữa ăn ──► Agent phân tích xu hướng)


4.1. Giải thuật Phân rã "Mâm Cơm Gia Đình" (Family Meal Decomposition)

Đầu vào: Mâm cơm chung gồm 3 món: Thịt kho tàu, Canh rau ngót nấu thịt băm, Đậu phụ luộc.

Phân tích Agent:

Tính toán tổng năng lượng và vi chất mâm cơm chung.

Trích xuất định lượng riêng cho bệnh nhân ĐTĐ + CKD Stage 3:

Thịt kho tàu: Lấy $2$ miếng thịt lẻ ($50 \text{ g}$), gạt bỏ nước kho (tránh dư thừa Natri và Đường).

Canh rau ngót: Lấy $1$ bát con phần cái, hạn chế múc nhiều nước canh (tránh dư Natri và Kali).

Đậu phụ luộc: $1$ miếng ($40 \text{ g}$) để bổ sung đạm thực vật thanh nhẹ.

Đầu ra: Thực đơn gia đình giữ nguyên, hướng dẫn gắp/định lượng riêng cho bệnh nhân.

5. Ràng Buộc, An Toàn Y Tế & Tuân Thủ Pháp Lý (Guardrails & Compliance)

5.1. Con Người Can Thiệp Bắt Buộc (HITL - Human-in-the-Loop)

Luồng phê duyệt cứng: Toàn bộ thực đơn được sinh ra cho bệnh nhân có chẩn đoán y khoa KHÔNG được gửi trực tiếp cho bệnh nhân ngay lập tức, mà phải chuyển vào hàng chờ (Queue) của Bác sĩ/Chuyên viên dinh dưỡng phụ trách.

Chuyên gia có thể phê duyệt nhanh bằng 1-Click hoặc chỉnh sửa định lượng trực tiếp trên giao diện Dashboard trước khi phát hành thực đơn.

5.2. Safety Guardrails & Chống Ảo Giác (Hallucination Mitigation)

Groundedness Enforcement: Chỉ sử dụng dữ liệu thành phần dinh dưỡng từ CSDL đã được xác thực (NIN / USDA). Khi LLM sinh ra một món ăn ngoài CSDL, Agent sẽ kích hoạt mô-đun OOV Estimator (phân tích theo thành phần nguyên liệu cấu thành) thay vì tự bịa số liệu.

Deterministic Bounds Checker: Dùng code Python thuần (Pydantic / Rules Engine) để thẩm định lại output của LLM.

Ví dụ: Nếu LLM sinh thực đơn có tổng Natri là $3000 \text{ mg}$ cho bệnh nhân Tăng huyết áp ($Limit \le 2000 \text{ mg}$), Rules Engine sẽ reject ngay lập tức và yêu cầu LLM sinh lại (Regenerate).

5.3. Bảo Mật Dữ Liệu Cá Nhân & Y Tế (PII / PHI Compliance)

Tuân thủ Nghị định 13/2023/NĐ-CP của Việt Nam về Bảo vệ dữ liệu cá nhân và các nguyên tắc bảo mật thông tin y tế (HIPAA/GDPR standard).

Mã hóa toàn bộ dữ liệu định danh bệnh nhân (PII) và chỉ số sức khỏe (PHI) cả khi lưu trữ (at rest) và trên đường truyền (in transit).

6. Kiến Trúc Kỹ Thuật (Tech Stack)

Thành phần System

Công nghệ / Giải pháp Lựa chọn

Trách nhiệm chính

Core LLM

Claude 3.5 Sonnet / GPT-4o / Gemini Pro

Trích xuất thông tin, suy luận lập kế hoạch thực đơn, tương tác tự nhiên

Orchestration Framework

LangGraph

Quản lý luồng Stateful Agent (State machine), xử lý rẽ nhánh HITL, retry loop

Retrieval System (RAG)

Qdrant / Milvus + Hybrid Search (BM25 + Dense Vectors)

Tra cứu nhanh Guideline y tế, CSDL món ăn Việt Nam & quy tắc tương tác

Rules & Validation Engine

Python Pydantic + Custom Guardrail Functions

Kiểm tra cứng các ngưỡng vi chất ($Na, K, P$, Calo), chặn chỉ định điều trị y khoa

Backend API Service

FastAPI (Python)

Xử lý logic nghiệp vụ, tích hợp Agent, quản lý bất đồng bộ (Async)

Frontend Platform

Next.js (React), TailwindCSS, Shadcn UI

Web app đa nền tảng, phân quyền giao diện (Bệnh nhân vs Bác sĩ)

Database Systems

PostgreSQL + pgvector

Lưu trữ hồ sơ người dùng, nhật ký ăn uống, Audit trail y tế

Cloud & Security

AWS / GCP (Docker, Kubernetes)

Hạ tầng đám mây, mã hóa dữ liệu, đảm bảo sẵn sàng cao

7. Lộ Trình Phát Triển Tính Năng (Detailed Roadmap)

7.1. Giai đoạn 1: MVP (Minimum Viable Product)

Triển khai ứng dụng Web App cơ bản trên Cloud.

Phân quyền $2$ nhóm người dùng: Bệnh nhân | Người chăm sóc và Chuyên gia Dinh dưỡng.

Nhập hồ sơ bệnh lý cơ bản (ĐTĐ Type 2, Tăng huyết áp) và chỉ số cơ thể ($BMI$, TDEE).

Agent gợi ý thực đơn tuần kèm ước tính Calo/Macro có trích dẫn nguồn từ CSDL NIN.

Ghi nhật ký ăn uống bằng văn bản hoặc chọn món có sẵn.

Đính kèm Disclaimer pháp lý và Cảnh báo dị ứng thực phẩm cơ bản.

7.2. Giai đoạn 2: Nâng Cao & Chuẩn Lâm Sàng (Advanced Features)

Sơ đồ HITL hoàn chỉnh: Dashboard cho phép Chuyên gia duyệt/chỉnh sửa thực đơn hàng loạt.

Mô-đun Phân rã Mâm cơm Gia đình: Gợi ý cách ăn mâm cơm chung phù hợp với bệnh nhân.

Phân tích Tương tác Thuốc - Thực phẩm: Cảnh báo tự động dựa trên đơn thuốc bệnh nhân đang uống (sử dụng DDID).

Cảnh báo Ngưỡng an toàn realtime: Cảnh báo đỏ khi tổng lượng Natri/Muối hoặc Đường vượt mức cho phép trong ngày.

Personalized Memory: Ghi nhớ thói quen ăn uống, món ăn không thích, nguyên liệu có sẵn trong tủ lạnh.

Smart Shopping List: Tự động quy đổi thực đơn tuần thành danh sách nguyên liệu cần mua ngoài chợ/siêu thị.

Xử lý OOV tiên tiến: Phân tích dinh dưỡng món ăn lạ/món địa phương dựa trên công thức cấu thành.

Tích hợp OCR / Image Recognition: Chụp ảnh mâm cơm để tự động nhận diện món ăn và ước tính khẩu phần.