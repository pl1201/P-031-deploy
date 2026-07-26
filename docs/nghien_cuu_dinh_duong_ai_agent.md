Nghiên cứu Toàn diện Xây dựng Hệ thống AI Agent Dinh dưỡng Lâm sàng Cá thể hóa cho Bệnh nhân Mãn tính tại Việt Nam

1. Tổng quan Nghiên cứu Y học Lâm sàng, Y học Cộng đồng và Công nghệ AI trong Dinh dưỡng Bệnh Mãn tính

Sự gia tăng bùng nổ của các bệnh lý mãn tính không lây như đái tháo đường tuýp 2, bệnh tim mạch, bệnh thận mạn tính và gout đang đặt ra thách thức nghiêm trọng cho hệ thống y tế công cộng. Liệu pháp Dinh dưỡng Y khoa (Medical Nutrition Therapy - MNT) đã được xác nhận là can thiệp nền tảng giúp kiểm soát chuyển hóa, ngăn ngừa biến chứng và tối ưu hóa chi phí điều trị. Trong môi trường bệnh viện, việc tầm soát và đánh giá tình trạng dinh dưỡng được thực hiện bằng các công cụ chuẩn hóa như NRS-2002, MUST, SGA hoặc MNA nhằm phát hiện sớm nguy cơ suy dinh dưỡng, giảm tỷ lệ tử vong và rút ngắn thời gian nằm viện. Tuy nhiên, việc duy trì MNT khi bệnh nhân xuất viện đối mặt với rào cản lớn do thiếu hụt lực lượng bác sĩ chuyên khoa dinh dưỡng và khả năng tự quản lý khẩu phần của người bệnh còn hạn chế.

Sự ra đời của Trí tuệ nhân tạo (AI) và các Mô hình Ngôn ngữ Lớn (LLMs) mở ra phương thức mới trong việc cá thể hóa tư vấn dinh dưỡng ở quy mô lớn. Khung kiến trúc NutriGen đã chứng minh khả năng ứng dụng LLM kết hợp với kỹ thuật Prompt Engineering và cơ sở dữ liệu USDA FoodData Central để khởi tạo thực đơn cá thể hóa dựa trên mục tiêu năng lượng và sở thích cá nhân. Thực nghiệm cho thấy mô hình Llama 3.1 8B và GPT-3.5 Turbo đạt mức sai số tuyệt đối về năng lượng tiêu chuẩn ở mức rất thấp, tương ứng là $1.55\%$ và $3.68\%$, thể hiện khả năng bám sát ngân sách calo do người dùng thiết lập. Đồng thời, các hệ thống Đa Agent (Multi-Agent Systems - MAS) kết hợp thị giác máy tính và xử lý ngôn ngữ tự nhiên đã thiết lập chu trình hỗ trợ khép kín: từ nhận diện món ăn qua ảnh chụp, ước tính dinh dưỡng, cập nhật ngân sách khẩu phần còn lại, đến tự động điều chỉnh thực đơn cho bữa ăn tiếp theo theo thời gian thực. Thử nghiệm trên tập dữ liệu SNAPMe ghi nhận hệ thống Đa Agent đạt độ tối ưu kế hoạch (Plan Optimality) ở mức $0.75$ với độ trễ phản hồi khoảng 65 giây. Ngoài ra, kiến trúc ChatDiet đã áp dụng phương pháp khám phá suy luận nguyên nhân - kết quả để trích xuất mô hình nhân duyên cá nhân từ dữ liệu người dùng, giúp tạo ra các khuyến nghị dinh dưỡng có khả năng giải thích dựa trên phản ứng chuyển hóa riêng biệt.

Mặc dù có nhiều triển vọng, việc áp dụng trực tiếp các mô hình LLM thương mại hoặc mã nguồn mở nguyên bản vào tư vấn dinh dưỡng lâm sàng chứa đựng rủi ro y khoa nghiêm trọng. Phân tích thực nghiệm trên phác đồ dinh dưỡng cho bệnh nhân đái tháo đường tuýp 2 chỉ ra rằng các LLM nguyên bản thường mắc lỗi lệch định lượng hệ thống. Các mô hình này có xu hướng đưa ra thực đơn có tổng năng lượng thấp hơn mức khuyến cáo, giảm nghiêm trọng lượng carbohydrate và xơ, đồng thời phân bổ đạm không ổn định. Phân tích Bland-Altman ghi nhận khoảng giới hạn đồng thuận rất rộng đối với các đa chất then chốt, khẳng định AI-generated diets chưa thể thay thế sự giám sát của chuyên gia dinh dưỡng. Việc tích hợp kỹ thuật Bổ trợ Truy xuất Kiến thức (Retrieval-Augmented Generation - RAG) dựa trên các hướng dẫn lâm sàng giúp cải thiện rõ rệt tính chính xác, giảm thiểu hiện tượng ảo giác thông tin và nâng cao sự nhất quán trong khuyến nghị.

2. Khung Pháp lý và Guidelines Dinh dưỡng Lâm sàng Quốc tế và Việt Nam

Việc xây dựng hệ thống tri thức y khoa cho AI Agent đòi hỏi sự tổng hợp khắt khe các hướng dẫn lâm sàng từ các tổ chức y tế quốc tế và hệ thống quy định pháp lý, quy trình kỹ thuật do Bộ Y tế Việt Nam ban hành.

Khung hướng dẫn quốc tế thiết lập các tiêu chuẩn định lượng cụ thể nhằm kiểm soát bệnh lý mãn tính. Hiệp hội Đái tháo đường Hoa Kỳ (ADA) và Hiệp hội Nghiên cứu Đái tháo đường Châu Âu (EASD) khuyến nghị chế độ ăn kiểm soát chỉ số đường huyết (GI) từ thấp đến trung bình, kiểm soát nghiêm ngặt carbohydrate theo từng bữa ăn và theo dõi HbA1c định kỳ 3 tháng/lần. Hiệp hội Tim mạch Hoa Kỳ (AHA) và Tổ chức Y tế Thế giới (WHO) ấn định mức tiêu thụ Natri dưới $2000 \text{ mg/ngày}$ (tương đương dưới $5\text{ g}$ muối/ngày) ở người trưởng thành để dự phòng và điều trị tăng huyết áp, biến cố mạch máu nào và suy tim. Tổ chức Cải thiện Kết quả Bệnh Thận Toàn cầu (KDIGO) đề xuất hạn chế protein ở bệnh nhân suy thận mạn chưa lọc máu ở mức $0.6 - 0.8 \text{ g/kg cân nặng/ngày}$, kết hợp kiểm soát kali, phốt pho và natri theo từng giai đoạn bệnh. Hội Chuyển hóa và Dinh dưỡng Lâm sàng Châu Âu (ESPEN) và Hoa Kỳ (ASPEN) quy định chuẩn hóa quy trình sàng lọc nguy cơ dinh dưỡng bắt buộc cho bệnh nhân nhập viện.

Tại Việt Nam, Bộ Y tế đã thể chế hóa hoạt động dinh dưỡng lâm sàng qua hệ thống văn bản pháp lý chặt chẽ. Thông tư 08/2024/TT-BYT và Văn bản hợp nhất quy định 100% người bệnh nội trú và ngoại trú phải được sàng lọc nguy cơ dinh dưỡng trong vòng 36 giờ sau khi nhập viện; người bệnh không có nguy cơ cần được sàng lọc lại sau mỗi 7 ngày. Đối với người bệnh suy dinh dưỡng nặng hoặc thuộc cấp chăm sóc I, bác sĩ điều trị bắt buộc phải hội chẩn với khoa Dinh dưỡng để xây dựng phác đồ can thiệp. Quyết định 2598/QĐ-BYT và Quyết định 3777/QĐ-BYT ban hành quy trình kỹ thuật khám nhân trắc, đánh giá khối cơ, lớp mỡ dưới da và phát hiện lâm sàng các dấu hiệu thiếu hụt vi chất. Quyết định 9484/QĐ-BYT (Phụ lục XV) quy định danh mục kỹ thuật dinh dưỡng lâm sàng, bao gồm đo chuyển hóa năng lượng cơ bản gián tiếp, nhận định khẩu phần 24 giờ, xây dựng công thức nuôi dưỡng qua sonde hoặc đường tĩnh mạch, và phục hồi chức năng nuốt.

Bảng 1: Tổng hợp Khung Hướng dẫn Lâm sàng cho Các Bệnh lý Mãn tính

Bệnh lý Mãn tính

Tổ chức ban hành Guidelines

Khuyến nghị Năng lượng & Đa chất

Khuyến nghị Vi chất & Hạn chế

Chỉ số Theo dõi Lâm sàng

Đái tháo đường Tuýp 2

ADA, EASD, Viện Dinh dưỡng

Năng lượng $30 - 35 \text{ kcal/kg/ngày}$; Carb $45 - 55\%$ (GI thấp/trung bình); Protein $15 - 20\%$; Lipid $20 - 25\%$

Chất xơ $> 14\text{ g}/1000 \text{ kcal}$; Hạn chế đường tinh chế; Cho phép dùng chất tạo ngọt an toàn

Glucose máu lúc đói, HbA1c (1 lần/3 tháng), SGA/MNA

Tăng huyết áp & Tim mạch

AHA, WHO, Bộ Y tế

Năng lượng điều chỉnh theo BMI; Lipid $< 25 - 30\%$ (Chất béo bão hòa $< 7\%$)

Natri $< 2000 \text{ mg/ngày}$ ($< 5\text{ g}$ muối/ngày); Tăng cường Kali từ thực phẩm tự nhiên

Huyết áp tâm thu/tâm trương, BMI, Chu vi vòng bụng

Bệnh thận mạn tính (CKD)

KDIGO, ESPEN, Bộ Y tế

Năng lượng $30 - 35 \text{ kcal/kg/ngày}$; Protein $0.6 - 0.8 \text{ g/kg/ngày}$ (chưa lọc máu)

Natri $< 2000 \text{ mg/ngày}$; Kiểm soát Kali, Phốt pho và dịch vào/ra

eGFR, Creatinine, Albumin/Prealbumin, Điện giải đồ

Gout & Tăng Uric máu

Bộ Y tế, Viện Dinh dưỡng

Năng lượng duy trì BMI chuẩn; Protein vừa phải (ưu tiên nguồn ít purin); Lipid vừa phải

Purin khẩu phần $< 150 \text{ mg/ngày}$; Kiêng cồn và Fructose công nghiệp; Nước $2 - 2.5 \text{ lít/ngày}$

Axit Uric huyết thanh, BMI, Tỷ lệ sụt cân

3. Phân tích Văn hóa - Xã hội, Hành vi Tiêu dùng và Đặc điểm Ẩm thực Địa phương

Sự thành công của hệ thống AI Agent Dinh dưỡng phụ thuộc vào khả năng tương thích với bối cảnh văn hóa và hành vi ăn uống thực tế của người Việt Nam. Ẩm thực Việt Nam mang tính tổng hợp và cộng đồng cao, thể hiện rõ nhất qua tập quán sinh hoạt gia đình.

Thói quen "ăn chung mâm" là đặc trưng văn hóa sâu sắc, nơi các thành viên quây quần quanh mâm cơm, cùng chia sẻ các đĩa thức ăn chung và sử dụng chung bát nước chấm. Nếp sống này củng cố tình cảm gia đình nhưng tạo ra rào cản kỹ thuật phức tạp cho việc cá thể hóa dinh dưỡng. Người bệnh gặp khó khăn lớn trong việc định lượng chính xác khối lượng thực phẩm đã tiêu thụ từ các đĩa thức ăn chung. Đồng thời, văn hóa "kính trên nhường dưới" cùng quan niệm truyền thống xem sức khỏe đo bằng số bát cơm ăn được khiến bệnh nhân thường xuyên nạp thừa tinh bột và chất đạm do sự chăm sóc của người thân. Ngoài ra, việc dọn chung nước chấm mặn khiến bệnh nhân tăng huyết áp hay bệnh thận thụ động tiêu thụ lượng Natri vượt quá chỉ định lâm sàng.

Dữ liệu điều tra dịch tễ cho thấy mức tiêu thụ muối của người Việt Nam đang ở ngưỡng báo động. Trung bình một người trưởng thành tiêu thụ từ $8.1\text{ g}$ đến $9.4\text{ g}$ muối/ngày (nam giới lên tới $10.5\text{ g/ngày}$, nữ giới $8.3\text{ g/ngày}$), gần gấp đôi ngưỡng khuyến cáo $5\text{ g/ngày}$ của WHO. Về nguồn gốc, $70\% - 81\%$ lượng muối đến từ thói quen nêm nếm gia vị (nước mắm, bột canh, hạt nêm, mì chính) trong quá trình chế biến và chấm thêm tại bàn ăn; $11\% - 20\%$ đến từ thực phẩm chế biến sẵn; và chỉ khoảng $7\% - 10\%$ có sẵn trong thực phẩm tự nhiên. Khảo sát thực tế trong các món ăn phổ biến ghi nhận một bát phở bò chứa $3.3\text{ g} - 4.0\text{ g}$ muối, một bát bún cá chứa tới $6.2\text{ g}$ muối và một gói mì ăn liền chứa $4.2\text{ g} - 5.0\text{ g}$ muối. Mặc dù $89.2\%$ người nấu ăn luôn cho gia vị mặn khi chế biến và $70\%$ thường xuyên chấm thêm mắm muối khi ăn, chỉ có $16\%$ người dân tự nhận thức bản thân ăn mặn. Đây là yếu tố nguy cơ hàng đầu dẫn đến tỷ lệ $20\%$ người trưởng thành mắc tăng huyết áp, gây ra các biến cố tim mạch và suy thận mạn. Để giải quyết thực trạng này, Chính phủ và Bộ Y tế đã phê duyệt Chiến lược Quốc gia phòng chống bệnh không lây nhiễm và Chương trình Sức khỏe Việt Nam với mục tiêu giảm $30\%$ lượng muối tiêu thụ trung bình, đưa mức tiêu thụ xuống dưới $7\text{ g/ngày}$.

Song song với hành vi tiêu dùng, AI Agent phải tích hợp bản đồ ẩm thực ba miền và kế thừa tri thức y học cổ truyền Việt Nam. Y học cổ truyền từ thời Tuệ Tĩnh và Hải Thượng Lãn Ông đã đề cao nguyên lý "ăn uống trị bệnh", sử dụng các thực phẩm tự nhiên, dễ tìm như tía tô, hành, đậu xanh, đậu đen, vừng, lạc, khế, sấu để cân bằng âm dương và hỗ trợ điều trị.

Bảng 2: Phân tích Ẩm thực 3 Miền và Chiến lược Can thiệp Dinh dưỡng

Vùng miền

Đặc trưng Ẩm thực & Gia vị Chủ đạo

Yếu tố Nguy cơ Bệnh lý Mãn tính

Chiến lược Can thiệp của AI Agent

Miền Bắc

Vị thanh nhẹ, cân bằng, ít cay/béo; sử dụng nước mắm loãng, mắm tôm, rau củ và thủy sản nước ngọt

Nạp Natri tiềm ẩn qua bột canh, mì chính và nước dùng bún/phở

Tính toán Natri trong nước dùng; khuyến nghị tách riêng bát nước chấm; thay gia vị mặn bằng thảo mộc tươi (hành, tía tô)

Miền Trung

Vị đậm đà, mặn sắn, cay nồng; sử dụng mắm nêm, mắm tôm chua, ớt bột

Nguy cơ cao về Tăng huyết áp, Bệnh tim mạch, Ung thư dạ dày và Gout

Đề xuất sản phẩm thay thế mắm giảm natri; kiểm soát lượng ớt bột; khuyến nghị nhóm thực phẩm kiềm hóa giảm axit uric

Miền Nam

Vị ngọt, béo; sử dụng phổ biến đường tinh chế, nước cốt dừa, hải sản

Nguy cơ Tăng kháng Insulin, Béo phì, Đái tháo đường Tuýp 2 và Tăng Triglyceride

Nhận diện đường ẩn trong món kho/nấu; thay thế bằng chất tạo ngọt GI thấp; giảm tỷ lệ nước cốt dừa trong công thức chế biến

4. Kiến trúc AI Agent, Hệ thống Bộ Dữ liệu Tích hợp và Khung Guardrails An toàn Y tế

Khảo sát hệ sinh thái ứng dụng y tế hiện tại tại Việt Nam như eDoctor, Nutrihome, YouMed hay GeneStory cho thấy các giải pháp chủ yếu dừng lại ở đặt lịch khám, quản lý hồ sơ sức khỏe cá nhân, tư vấn từ xa hoặc phân tích di truyền đơn lẻ. Khoảng trống công nghệ hiện nay là sự thiếu hụt một hệ thống AI Agent hỗ trợ dinh dưỡng theo chu trình khép kín, có khả năng phân rã món ăn phức hợp Việt Nam, kiểm tra tương tác thuốc - thực phẩm và tự động cân bằng thực đơn theo thời gian thực.

Để vận hành chính xác, hệ thống AI Agent phải tích hợp đồng bộ bốn bộ dữ liệu cốt lõi:

Vietnamese Food Composition Database (VNFCD): do Viện Dinh dưỡng phát hành, kết hợp với cơ sở dữ liệu USDA FoodData Central để cung cấp chỉ số dinh dưỡng chi tiết của thực phẩm thô và món ăn chín.

Diet-Drug Interaction Database (DDID): bao gồm $23950$ bản ghi tương tác được chuẩn hóa giữa $1516$ loại thuốc, $270$ thực phẩm và $1068$ thảo dược. Bộ dữ liệu này giúp AI phát hiện kịp thời các tương tác nguy hiểm, ví dụ như tương tác giữa thuốc chống đông máu Warfarin với rau xanh đậm giàu Vitamin K, hoặc thuốc chế ngự men chuyển (ACEi) với thực phẩm giàu Kali.

Vietnamese Recipe & Allergy Dataset: Bộ dữ liệu Công thức Món ăn Việt Nam tích hợp cảnh báo dị ứng (hải sản, đậu nành, lạc, gluten).

Clinical Nutrition Knowledge DB: Cơ sở dữ liệu Tri thức Lâm sàng tích hợp mã bệnh ICD-10, chỉ số sinh hóa và quy trình kỹ thuật theo Thông tư 08/2024/TT-BYT và Quyết định 2598/QĐ-BYT.

Kiến trúc AI Agent được thiết kế theo mô hình Multi-Agent Controller phân công nhiệm vụ chuyên biệt. Vision Agent tiếp nhận ảnh chụp bữa ăn và ước tính thể tích. Ingredient Decomposition Agent đảm nhận bài toán phân rã món ăn phức hợp. Nghiên cứu thực nghiệm chứng minh các LLM lớn như Llama-3 70B và GPT-4o đạt độ chính xác cao trong việc tách món ăn phức hợp thành các nguyên liệu đơn lẻ với F1-Score lần lượt là $0.894$ và $0.842$, vượt trội so với Mixtral 8x7B ($F1 = 0.690$). Agent này phân rã các món ăn như "Phở bò" hoặc "Bún riêu" thành từng định lượng nguyên liệu thô để tra cứu chính xác vào VNFCD. Phản hồi từ Agent này được chuyển sang Clinical Guardrail Agent để kiểm tra chéo với hồ sơ bệnh lý, kết quả xét nghiệm sinh hóa và thuốc đang điều trị qua cơ sở dữ liệu DDID. Cuối cùng, Planning & Re-balancing Agent tiến hành cập nhật ngân sách dinh dưỡng còn lại trong ngày. Nếu bữa sáng bệnh nhân tiêu thụ lượng Natri vượt ngưỡng cho phép, agent sẽ tự động điều chỉnh giảm Natri ở bữa trưa và tối để đảm bảo an toàn chuyển hóa.

Nhằm đảm bảo hệ thống vận hành an toàn tuyệt đối trước khi ứng dụng lâm sàng, đề án triển khai khung kiểm thử an toàn đa tầng tích hợp các bộ benchmark y tế tiên tiến. Đánh giá tri thức y khoa cơ bản được thực hiện qua MedQA và MedMCQA dựa trên các câu hỏi trắc nghiệm lâm sàng USMLE. Đánh giá kỹ năng lâm sàng thực tế được thực hiện qua khung MedQA-CS (mô phỏng kỳ thi OSCE), kiểm tra tương tác giữa MedStuLLM (mô phỏng sinh viên y khoa) và MedExamLLM (mô phỏng giám khảo) trên 4 giai đoạn: thu thập thông tin, khám thực thể, giao tiếp và chẩn đoán. Năng lực tương tác đa lượt trong môi trường lâm sàng thực tế được đánh giá qua MedArena với sự tham gia chấm điểm của hội đồng bác sĩ. Khung M-LEAF đánh giá hệ thống trên 8 trụ cột an toàn (độ chính xác, minh bạch suy luận, an toàn tương tác thuốc, giảm ảo giác). Khung RAGAS đo lường độ trung thực và độ liên quan của thông tin do RAG truy xuất từ văn bản Bộ Y tế.

Bảng 3: So sánh Hiệu năng Mô hình AI và Các Khung Benchmark An toàn

Mô hình AI / Framework Benchmark

Cấu trúc & Quy mô

Chỉ số Hiệu năng (Accuracy / F1)

Độ lệch Calo (Caloric MAE)

Vai trò Chức năng trong AI Agent System

Llama-3.1 (8B)

8B Parameters (Mã nguồn mở)

N/A

$1.55\%$ (Độ lệch thấp nhất)

Lập kế hoạch thực đơn và tính toán ngân sách calo tức thì

GPT-3.5 Turbo

Proprietary API

N/A

$3.68\%$ (Độ trễ thấp)

Xử lý tương tác hội thoại/chat thời gian thực

DeepSeek V3

MoE Architecture

N/A

$10.45\%$ (Chậm, sai số cao)

Cần tối ưu RAG trước khi dùng cho tính toán định lượng

Llama-3 (70B)

70B Parameters

$F1 = 0.894$ ($95\%$ CI: $0.84 - 0.95$)

N/A

Tối ưu cho phân rã món ăn phức hợp thành nguyên liệu thô

GPT-4o

Multimodal Proprietary

$F1 = 0.842$ ($95\%$ CI: $0.79 - 0.89$)

N/A

Phân tích hình ảnh bữa ăn và giao tiếp lâm sàng phức tạp

Med-PaLM 2

Fine-tuned Medical LLM

$86.5\%$ trên MedQA

N/A

Đóng vai trò Verifier Agent giám sát tri thức y khoa

M-LEAF Framework

8 Trụ cột An toàn Y tế

Thang điểm $0 - 5$

N/A

Đánh giá toàn diện độ an toàn, ảo giác và minh bạch y khoa

5. Kết luận và Khuyến nghị Triển khai Đề án

Phân tích toàn diện cho thấy việc xây dựng Hệ thống AI Agent Dinh dưỡng Lâm sàng tại Việt Nam là một giải pháp công nghệ mang tính khả thi và cấp thiết nhằm giải quyết rào cản quản lý bệnh mãn tính. Tuy nhiên, do các mô hình LLM nguyên bản luôn tồn tại lỗi lệch định lượng và rủi ro ảo giác y khoa, kiến trúc hệ thống bắt buộc phải tuân thủ mô hình kết hợp giữa AI linh hoạt và Deterministic Clinical Engine được kiểm soát bởi kỹ thuật RAG bám sát Guidelines. Đồng thời, hệ thống phải được bản địa hóa sâu sắc để giải bài toán văn hóa "ăn chung mâm", ước tính lượng Natri trong ẩm thực truyền thống và phân rã chính xác công thức món ăn Việt Nam.

Để đưa Đề án vào triển khai thực tế, ba khuyến nghị chiến lược được đề xuất:

Phát triển mô hình Hybrid Architecture: Llama-3 70B hoặc GPT-4o đảm nhiệm vai trò phân tích hình ảnh và phân rã món ăn, còn các tính toán định lượng, tra cứu tương tác thuốc DDID và kiểm soát ngưỡng chuyển hóa được thực hiện bởi Rule-Based Engine nhằm triệt tiêu hoàn toàn rủi ro sai số.

Thiết kế tính năng "Tư vấn Kép" cho bối cảnh "ăn chung mâm": Cho phép AI Agent phân bổ khẩu phần cá thể từ mâm cơm gia đình và cung cấp hướng dẫn chế biến giảm muối/đường riêng cho người nội trợ.

Triển khai thử nghiệm mô hình Sandbox: Thử nghiệm tại các Khoa Dinh dưỡng bệnh viện theo Thông tư 08/2024/TT-BYT, tiến hành đối chiếu kết quả giữa AI Agent và Bác sĩ Dinh dưỡng lâm sàng để đảm bảo độ đồng thuận đạt trên $95\%$ trước khi phát hành rộng rãi.

6. Danh mục Tài liệu Tham khảo (References)

Viện Khoa học Quản lý Y tế (2024). Tài liệu đào tạo liên tục: Dinh dưỡng lâm sàng và điều trị một số bệnh mạn tính.

Bộ Y tế Việt Nam (2024). Chiến lược Quốc gia phòng, chống bệnh không lây nhiễm và Khuyến nghị giảm muối trong khẩu phần ăn.

Trung tâm Y tế / Sở Y tế (2023). Chế độ ăn giảm muối và vai trò đối với sức khỏe tim mạch và huyết áp.

PubMed / Clinical Nutrition Research (2024). Large Language Models as Clinical Nutrition Decision Tools: Quantitative Bias and Guideline Deviation in Type 2 Diabetes Meal Planning.

Bệnh viện Bình Dân (2018). Tập 4: Dinh dưỡng lâm sàng và phác đồ can thiệp bệnh viện.

Bộ Y tế (2024). Thông tư 08/2024/TT-BYT & Văn bản hợp nhất quy định về hoạt động dinh dưỡng trong bệnh viện.

arXiv Research (2026). A Closed-Loop Multi-Agent System Driven by LLMs for Meal-Level Personalized Nutrition Management. arXiv:2601.04491.

arXiv Research (2025). NutriGen: Personalized Meal Plan Generator Leveraging Large Language Models to Enhance Dietary and Nutritional Adherence. arXiv:2502.20601.

arXiv Research (2024). ChatDiet: Empowering Personalized Nutrition-Oriented Food Recommender Chatbots through an LLM-Augmented Framework. arXiv:2403.00781.

PubMed / Medical Informatics (2025). Improving Personalized Meal Planning with Large Language Models: Identifying and Decomposing Compound Ingredients.

BioData & Drug Database (DDID). Diet-Drug Interaction Database. Hangzhou Normal University.

Google Research / Med-PaLM Team. Med-PaLM 2: Large Language Models Encode Clinical Knowledge.

Stanford HAI (2025). MedArena: Comparing LLMs for Medicine in the Wild.

EACL Anthology (2026). MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for Evaluating LLM Clinical Skills.