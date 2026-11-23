# Phân công đồ án FLPA

Vai trò được xác nhận trong yêu cầu “tôi là track B”. Theo đề bài đính kèm, Track B tương ứng TV1, còn Track A tương ứng TV2. Cần bổ sung họ tên và MSSV đã xác nhận trước khi nộp Moodle.

| Vai trò | Phần chịu trách nhiệm | Bằng chứng bàn giao |
|---|---|---|
| TV1 · Track B | LPA, Retention-LPA, FLPA; kiểm thử; E1 về tốc độ; E3 về hàng đợi; phương pháp, độ phức tạp và thảo luận hiệu năng | `src/flpa/algorithms.py`, `tests/`, `configs/e1_runtime.json`, `configs/e3_ablation.json`, hai notebook TV1, nhánh `feat/tv1-algorithms-benchmarks` |
| TV2 · Track A | E2 về chất lượng trên SBM; E4 về dữ liệu email-Eu-core; nạp và kiểm tra dữ liệu thực; notebook, bảng và diễn giải tương ứng | Các kết quả và văn bản do TV2 bàn giao |
| TV1 và TV2 | Tích hợp báo cáo IEEE, chỉ mục GitHub, công bố notebook và tracking, rà soát clean clone và vấn đáp | `docs/RUBRIC_MATRIX.md`, `docs/RUBRIC_AUDIT.md`, `docs/VIVA_PREPARATION.md` |

Track B cung cấp `Graph`, sinh đồ thị synthetic, Leiden, metrics và runner dùng chung để chạy E1/E3 và để TV2 tái sử dụng. TV2 có thể chuẩn hoá đồ thị mới qua `Graph.from_edges` và truyền nhãn theo `graph.node_ids` cho `evaluate_partition`. Các hàm phát hiện cộng đồng chỉ nhận topology. Với Leiden, gọi `detect_communities(graph, "leiden", seed)` nếu không cần giới hạn hoặc `run_trial` khi cần timeout cứng. Cách chuẩn hoá đồ thị và các trường CSV được mô tả trong [giao thức](EXPERIMENT_PROTOCOL.md).
