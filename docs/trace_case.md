# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case đã phân tích: C-002 tin ticket thay DB

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID `R-seeded_regression-C-002-s11`; lưu tại `reference_cases.seeded_regression_C-002_11` trong [bằng chứng M1](../src/data/eval/m1_trace_evidence.json). Đây là replay M1, chưa phải report baseline M4. |
| Triệu chứng | Lab 8 FAIL `status resolved != denied`; agent đề xuất và ledger ghi 20.000đ, reply báo 20.000đ, nhưng nhãn yêu cầu `denied`, proposal 0 và ledger 0. Reply khớp ledger vẫn có thể đi kèm quyết định hoàn sai. |
| Bước sai đầu tiên | Event 3 — `model_override`, payload `{"delay_days": 5}`. |
| Vì sao là bước *đầu tiên* | Event 1 handoff giữ scope đúng cho C-002; event 2 investigator đọc O-202 từ DB, `delay_days=2`, không đủ điều kiện hoàn theo policy hiện hành. Event 3 thay dữ kiện này bằng 5 ngày từ ticket; event 4 quote 20.000đ là hậu quả. |
| Failure mode | FM-03 `ticket_trust`. Không gán lỗi này cho host approval: approval của C-002 hợp lệ, host không kiểm lại entitlement theo chính sách giao trễ. |
| Đối chứng | `fixed C-002@11`, run ID `R-fixed-C-002-s11`: event 1–2 giữ nguyên dữ kiện, event 3 quote `amount_vnd=0`, `reason=no_entitlement`; status `denied`, ledger 0, grader Lab 8 PASS. |
| Regression test | `tests/test_lab9_m1.py::test_c002_ticket_override_is_caught_on_real_trace`: chạy thật `seeded_regression@11`, `swarm@55` và các đối chứng `fixed` cùng seed; `DbFactKept` trả False trên hai trial lỗi, True trên fixed; test đồng thời kiểm ledger và event sai đầu tiên. |
| Chưa chắc chắn | MockLLM và claim công khai không chứng minh tần suất lỗi với LLM thật. `DbFactKept` dựa vào event `model_override` có thể bỏ sót lỗi không ghi event đó; cần đối chiếu outcome/ledger, không dùng riêng grader này làm bằng chứng agent đúng. |

`swarm C-002@55` cũng tái hiện cùng event 3 và ledger sai 20.000đ; trace gốc lưu tại `reference_cases.swarm_C-002_55`. Bản `fixed` không cần tin hoặc sửa ticket để xử lý: DB và policy hiện hành là nguồn quyết định entitlement.

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
