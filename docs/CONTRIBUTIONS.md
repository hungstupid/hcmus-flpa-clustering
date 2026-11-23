# Phân công đồ án FLPA

Vai trò được xác nhận trong yêu cầu “tôi là track B”. Theo đề bài đính kèm, Track B tương ứng TV1, còn Track A tương ứng TV2. Họ tên và MSSV đã được thành viên xác nhận. [Danh sách thành viên](../README.md#phân-công)

| Vai trò | Phần chịu trách nhiệm | Bằng chứng bàn giao |
|---|---|---|
| TV1 · Track B | Cài đặt và kiểm thử LPA, Retention-LPA, FLPA. Đo E1 về tốc độ và E3 về hàng đợi. Viết phương pháp, độ phức tạp và thảo luận hiệu năng. | `src/flpa/algorithms.py`, `tests/`, `configs/e1_runtime.json`, `configs/e3_ablation.json`, hai notebook TV1, nhánh `feat/tv1-algorithms-benchmarks` |
| TV2 · Track A | E2 về chất lượng trên SBM và E4 về email-Eu-core. Nạp và kiểm tra dữ liệu thực. Chuẩn bị notebook, bảng và diễn giải tương ứng. | Các kết quả và văn bản do TV2 bàn giao |
| TV1 và TV2 | Tích hợp báo cáo IEEE, chỉ mục GitHub, công bố notebook và tracking, rà soát clean clone và vấn đáp | `docs/RUBRIC_MATRIX.md`, `docs/RUBRIC_AUDIT.md`, `docs/VIVA_PREPARATION.md` |

Track B cung cấp `Graph`, sinh đồ thị synthetic, Leiden, metrics và runner dùng chung để chạy E1/E3 và để TV2 tái sử dụng. TV2 có thể chuẩn hoá đồ thị mới qua `Graph.from_edges` và truyền nhãn theo `graph.node_ids` cho `evaluate_partition`. Các hàm phát hiện cộng đồng chỉ nhận topology. Với Leiden, gọi `detect_communities(graph, "leiden", seed)` nếu không cần giới hạn hoặc `run_trial` khi cần timeout cứng. Cách chuẩn hoá đồ thị và các trường CSV được mô tả trong [giao thức](EXPERIMENT_PROTOCOL.md).
