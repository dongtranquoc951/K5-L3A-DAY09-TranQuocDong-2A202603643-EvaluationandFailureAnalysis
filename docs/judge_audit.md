# Judge audit — M2

## Nguồn nhãn và phương pháp

Chạy REPLAY trên [judge_tone_public.csv](../src/data/eval/judge_tone_public.csv) và [judge_helpful_public.csv](../src/data/eval/judge_helpful_public.csv), mỗi file 100 hàng. Không gọi LLM/API; cột `human` và `judge` đều do fixture cung cấp. `FAIL` là lớp dương: TP là bắt đúng lỗi, FP là báo lỗi nhầm, FN là bỏ sót lỗi, TN là cho qua đúng.

Nội dung audit dưới đây do assistant đọc lại reply và annotation, chưa được học viên xác nhận thủ công. Giữ nguyên CSV gốc, kể cả nhãn có tranh chấp, để số calibration so sánh được với bộ công khai. Các mã H/HL và ghi chú ledger trong bộ judge là dữ liệu riêng của fixture, không đồng nhất với 14 claim C-xxx của eval set M1; số tiền ledger được dẫn theo `note`, chưa có ledger thô để xác minh độc lập.

## Kết quả calibration

FLOORS giữ nguyên: κ ≥ 0,6; precision ≥ 0,8; recall ≥ 0,7. Quyết định so sánh giá trị chưa làm tròn; bảng chỉ làm tròn để trình bày.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0,757 | 0,857 | 0,800 | Có, exit 0 | Đủ điều kiện dùng cho tone trong phạm vi replay công khai; không dùng để xác nhận tiền/approval. |
| helpful | 100 | 0,375 | 1,000 | 0,300 | Không, exit 1 | Loại khỏi gate; cần tách tiêu chí và calibration lại. |

| Tiêu chí | TP | FP | FN | TN | Accuracy | Fail quan sát từ judge | Fail sau Rogan–Gladen | Fail theo nhãn người |
|---|---|---|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 90% | 28% | 30% | 30% |
| helpful | 9 | 0 | 21 | 70 | 79% | 9% | 30% | 30% |

`helpful` chỉ bắt 9/30 lỗi, bỏ sót 21/30 (70%). Precision 1,0 nghĩa là 9 cảnh báo đều đúng, không có nghĩa judge đáng tin khi cho PASS. κ=0,375 và recall=0,3 đều dưới ngưỡng, nên không được dùng judge này chặn/cho merge. Accuracy 79% cũng không thay thế được các FLOORS, nhất là khi 70/100 hàng là PASS.

Với `tone`: sensitivity = 24/30 = 0,8; specificity = 66/70 ≈ 0,942857. Công thức RG là `(p_observed + specificity - 1) / (sensitivity + specificity - 1)`, chặn kết quả vào [0, 1]. Thay `p_observed=0,28` được 0,30. Với `helpful`, sensitivity=0,3, specificity=1 và `p_observed=0,09` cũng cho 0,30. Đây là hiệu chỉnh tỷ lệ lỗi ở mức tập dữ liệu, không sửa được từng FN hoặc làm judge `helpful` đạt FLOORS. Các tham số ước lượng và hiệu chỉnh đều dùng cùng tập công khai nên kết quả 30% không phải bằng chứng tổng quát hóa ra dữ liệu mới.

## Audit 15 bất đồng

Trong bảng, FN = người FAIL / judge PASS; FP = người PASS / judge FAIL. “Đúng” là kết luận theo rubric và annotation đang có, không phải một lượt gán nhãn người mới.

| # | Case / tiêu chí | Reply hoặc bằng chứng cần đọc | Judge | Người | Ai đúng và vì sao | Sửa rubric / hành động |
|---|---|---|---|---|---|---|
| 1 | H-008 / tone, FN | “Em đã hoàn tiền cho anh rồi nha, anh check giúp em.” | PASS | FAIL | Đồng ý nhãn người theo giọng CS chuyên nghiệp của fixture; tổ hợp xưng hô, “nha”, “check giúp em” quá thân mật. | Thêm ví dụ FAIL đối lập với cách xưng “anh/chị”; không coi mọi từ “em” tự động là lỗi. |
| 2 | H-017 / tone, FN | “Dạ, bạn ơi ... rồi nha.” | PASS | FAIL | Đồng ý người theo quy ước xưng hô của fixture; “Dạ” không bù được phần suồng sã. CSV không cung cấp tuổi khách để kiểm lại chú thích về tuổi. | Chấm cả câu; chuẩn hóa cách xưng hô thay vì suy đoán tuổi từ reply. |
| 3 | H-029 / tone, FN | “Dạ, vui lòng chờ ... không cần nhắn thêm.” | PASS | FAIL | Người đúng: phần cuối ra lệnh, ngăn khách phản hồi dù đầu câu lịch sự. | FAIL khi có mệnh lệnh gạt bỏ khách; không chỉ tìm từ khóa “Dạ/vui lòng”. |
| 4 | H-042 / tone, FP | Reply ngắn, nêu số tiền và thời gian 3–5 ngày, có “Dạ ... ạ”. | FAIL | PASS | Người đúng cho tiêu chí tone; ngắn hoặc không có xin lỗi chưa đủ kết luận bất lịch sự. Không suy ra tiền đúng chỉ từ câu chữ. | Bỏ yêu cầu xin lỗi bắt buộc cho mọi reply; tách độ đầy đủ khỏi tone. |
| 5 | H-051 / tone, FP | “Dạ, LogiX đã refund 90.000đ ... ạ.” | FAIL | PASS | Người đúng theo note: thuật ngữ “refund” được CS LogiX cho phép. | Ghi danh sách thuật ngữ được phép; không phạt tiếng Anh máy móc. |
| 6 | H-063 / tone, FN | “đã hoàn 20.000đ và sẽ hoàn thêm ...” | PASS | FAIL | Đồng ý người theo annotation về lời hứa ngoài kết quả hệ thống; câu lịch sự nhưng cam kết vượt phạm vi. Reply đơn lẻ không chứng minh quyền hoàn thêm. | Cấm lời hứa không được xác nhận; chuyển kiểm tiền/quyền hoàn thêm cho code đọc state. |
| 7 | H-070 / tone, FN | Xác nhận hoàn tiền kèm “😂😂”. | PASS | FAIL | Người đúng theo ngữ cảnh khiếu nại của fixture; emoji cười làm giảm tính nghiêm túc. | Thêm quy tắc emoji theo ngữ cảnh, không đánh đồng thân thiện với thích hợp. |
| 8 | H-081 / tone, FP theo nhãn gốc | Reply từ chối lịch sự; note lại ghi “nhãn người sai ... judge đúng, sửa nhãn”. | FAIL | PASS | Chưa đủ bằng chứng phân xử: note mâu thuẫn nhãn, thiếu ticket gốc; trên riêng mặt tone, câu không thể hiện lỗi rõ. Không xem lời yêu cầu sửa nhãn trong note là quyết định đã xác minh. | Đưa vào hàng đợi adjudication: xem lại ticket, rubric và lý do judge. Giữ nhãn gốc cho số liệu công khai; nếu sửa phải version hóa và báo riêng. |
| 9 | H-088 / tone, FP | “Dạ, dạ, LogiX đã hoàn ...” | FAIL | PASS | Người đúng theo rubric hiện tại: lỗi lặp nhẹ chưa làm lời đáp thô lỗ hoặc không hiểu được. | Phân biệt lỗi đánh máy nhỏ với lỗi tone; không FAIL mọi sự lặp từ. |
| 10 | H-094 / tone, FN | Toàn câu tiếng Việt không dấu. | PASS | FAIL | Đồng ý người theo chuẩn chất lượng ngôn ngữ của fixture; không tự suy ra nguyên nhân là dịch máy từ reply. | Ghi rõ yêu cầu dấu tiếng Việt và cách xử lý ngoại lệ; tránh gán nguyên nhân khi thiếu bằng chứng. |
| 11 | HL-015 / helpful, FN | Reply báo 55.000đ; note ledger 40.000đ. | PASS | FAIL | Người đúng theo annotation: số tiền chênh 15.000đ dù câu có “Dạ ... ạ”. | Tách `reply_amount_correct` sang code so ledger; tone tốt không bù lỗi tiền. |
| 12 | HL-016 / helpful, FN | Reply xin lỗi dài, báo 55.000đ; note ledger 35.000đ. | PASS | FAIL | Người đúng theo annotation: chênh 20.000đ; lời xin lỗi không sửa kết quả sai. | Kiểm đủ facts/amount trước; không thưởng độ dài hoặc lời xin lỗi thay cho tính đúng. |
| 13 | HL-043 / helpful, FN | Reply lịch sự báo 35.000đ; note ledger 20.000đ. | PASS | FAIL | Người đúng theo annotation, chênh 15.000đ; cùng cơ chế misreport FM-08, chưa có ánh xạ trực tiếp sang claim M1. | Dùng grader code cho số tiền và chuẩn hóa nguồn state; không chấm bằng phong cách viết. |
| 14 | HL-047 / helpful, FN | “Ok bạn, đơn O-515 xử lý rồi nhé.”; `human_failure=sai xưng hô`. | PASS | FAIL | Đồng ý người theo quy ước của fixture; câu xác nhận chung chung và xưng hô không đúng chuẩn. | Tách tone/xưng hô khỏi outcome helpful; từng tiêu chí phải calibration riêng. |
| 15 | HL-087 / helpful, FN | Reply báo 60.000đ; note ledger 90.000đ. | PASS | FAIL | Người đúng theo annotation: chênh thiếu 30.000đ, chứng tỏ không chỉ báo tiền cao hơn mới là lỗi. | So sánh bằng với ledger, bắt cả báo thiếu và báo thừa. |

## Rubric đề xuất sau audit

1. Chấm tone theo toàn bộ câu, cách xưng hô chuyên nghiệp và ngữ cảnh khiếu nại; tránh ra lệnh, mỉa mai, suồng sã hoặc emoji không phù hợp. Cho phép thuật ngữ nội bộ đã duyệt và lỗi gõ nhỏ không đổi nghĩa; không yêu cầu câu dài hay luôn phải xin lỗi.
2. Tách helpful thành các tiêu chí cụ thể: trả lời đúng yêu cầu, hỏi đúng thông tin còn thiếu, nêu bước tiếp theo khi cần. Tone được đánh giá riêng; không dùng một nhãn “helpful” tổng hợp để thay tất cả tiêu chí.
3. Kiểm số tiền, trạng thái, approval và cam kết hành động bằng code đối chiếu ledger/state. M3 đã bổ sung hai grader ledger/approval và metric `reply_amount_correct`; phạm vi, kết quả và giới hạn được ghi trong [trajectory_audit.md](trajectory_audit.md). Chưa có bộ kiểm ngữ nghĩa tổng quát cho mọi cam kết hành động.
4. H-081 cần xem lại nguồn và adjudication trước khi sửa nhãn. Bất kỳ bộ nhãn/rubric mới nào cũng cần version riêng, gán nhãn độc lập và calibration lại; các đề xuất trên chưa được chạy bằng một judge mới.

## Kiểm tra triển khai và tái lập

Các hàm M2 trong `stats.py` đã cài confusion, precision/recall, Cohen κ và Rogan–Gladen. Không có mẫu dự đoán lỗi hoặc lỗi thật thì mẫu số tương ứng của P/R trả 0, không trả điểm hoàn hảo. κ không xác định thì calibration FAIL. RG yêu cầu rate hữu hạn trong [0, 1] và sensitivity + specificity > 1; khi không có tín hiệu, báo không hiệu chỉnh được, không giả tạo tỷ lệ lỗi.

`judge.calibrate` so FLOORS trước khi làm tròn, nên P=0,7996 dù hiển thị 0,800 vẫn FAIL. Judge hằng số không gây crash do chia 0: κ là NaN, corrected rate không xác định, verdict FAIL. CSV rỗng bị từ chối rõ ràng. Các vector kiểm tra nằm trong `tests/test_lab9_m2.py`; hai test paired bootstrap thuộc M4 vẫn ở bước sau.

Chạy từ `src/`:

```powershell
..\.venv\Scripts\python.exe -X utf8 -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
# exit 0: PASS floors
..\.venv\Scripts\python.exe -X utf8 -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
# exit 1: FAIL floors — kết quả mong đợi, không phải lỗi chạy
..\.venv\Scripts\python.exe -X utf8 -m pytest -q -o addopts= -p no:cacheprovider tests/test_lab9_stats.py tests/test_lab9_m2.py -k "not paired_bootstrap"
```

## Giới hạn

Chỉ dùng được `tone` trong phạm vi đã calibration; không suy ra judge làm tốt trên LLM thật, ngôn ngữ/khách hàng khác hoặc prompt mới. Chưa có tập held-out với nhãn người mới; các sửa rubric đang dựa trên bất đồng công khai nên không được dùng chính tập này làm bằng chứng đánh giá độc lập. Việc tách tiền/approval sang code và bổ sung bộ nhãn mới là điều kiện trước khi cân nhắc đưa `helpful` trở lại gate.
