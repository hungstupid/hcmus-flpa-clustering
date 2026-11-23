# Giao thức E1 và E3

## Mục tiêu và phân vai

E1 hỏi FLPA FIFO thay đổi chi phí xử lý và thời gian thế nào khi kích thước ER, BA và SBM tăng. Đây là tái hiện ba panel tăng kích thước của Figure 1, gồm panel SBM tại μ = 0,6. Bài báo khảo sát thêm forest fire, geometric 2D, các panel SBM μ = 0,1/0,3 và một sweep μ tại 100.000 đỉnh. E2 của TV2 phụ trách tái hiện Figure 4 trái. Bài báo báo cáo trung bình và độ lệch chuẩn từ 2.000 lượt khi không có ngoại lệ và dùng igraph C trên Intel Xeon E5-2697. [Traag và Šubelj, 2023, tr. 5–8](https://lovro.fri.uni-lj.si/papers/flpa.pdf)

E3 hỏi chế độ lấy đỉnh LIFO và điều kiện chọn láng giềng khi đưa lại vào hàng đợi ảnh hưởng thế nào đến chi phí và chất lượng. Kiểm chứng trên SBM 5.000 đỉnh, 100 nhóm, bậc kỳ vọng 10, μ ∈ {0,30, 0,45, 0,60}. Hai phép so sánh dùng cùng đối chứng FLPA FIFO, graph, cách đếm nhãn, RNG, seed, điều kiện kết thúc và kiểu lưu trữ.

| Biến thể | Lấy đỉnh | Điều kiện đưa lại sau khi `v` đổi nhãn |
|---|---|---|
| `flpa` | Đầu `deque` | Láng giềng chưa trong hàng đợi và có nhãn khác nhãn mới của `v` |
| `flpa_lifo` | Cuối `deque` | Như đối chứng |
| `flpa_all` | Đầu `deque` | Mọi láng giềng chưa trong hàng đợi |

Hai đầu của cùng một hoán vị ban đầu trở thành vị trí ưu tiên của FIFO và LIFO. Xử lý bất đồng bộ làm thứ tự gọi RNG và thứ tự thay đổi nhãn phân kỳ sau đó. `flpa_all` có thể đưa lại cả đỉnh vẫn maximal, giúp kiểm tra tác động của lọc có chọn lọc. Khi chạm 30 giây, E3 giữ hàng `timeout` và đếm vào mẫu số hoàn thành.

## Tạo cùng một đồ thị cho mỗi cặp seed

- E1 dùng *n* ∈ {1.000, 5.000, 10.000, 50.000, 100.000} cho mỗi họ, bậc đích 10, 100 khối đều và μ = 0,6 cho SBM. ER dùng từng cạnh Bernoulli với p = 10/(*n*−1) qua `fast_gnp_random_graph`. BA thêm 5 liên kết đính kèm ưu tiên cho mỗi đỉnh, bắt đầu từ đồ thị sao mặc định của NetworkX. Bậc trung bình BA hữu hạn là 10(1−5/*n*).
- SBM có *s = n/k* đỉnh mỗi khối với *k* nhóm. Đặt p_in = (1−μ)d/(s−1) và p_out = μd/(n−s), với *d* là bậc kỳ vọng. Từng cặp khối lấy *K* theo Binomial(*M*, *p*) trên *M* cạnh ứng viên, sau đó chọn đều *K* cạnh khác nhau. Mỗi tập cạnh cụ thể có xác suất p^K(1−p)^(M−K), đúng với lấy mẫu Bernoulli độc lập. Chỉ mục tam giác trong khối được đổi thành cặp đầu mút bằng `searchsorted`. Cách lấy mẫu có cùng phân phối với SBM Bernoulli và không cần ma trận kề dày. Bài báo mô tả nhóm, bậc và μ, vì vậy việc trùng phân phối phụ thuộc vào giả định về generator của tác giả.
- Đồ thị vô hướng, không trọng số, không self-loop. Dùng tuple danh sách láng giềng đối xứng và sắp xếp nội bộ. ID bên ngoài nằm trong `Graph.node_ids`, kể cả đỉnh cô lập. Cạnh lặp hoặc đảo chiều được gộp. Nhãn thật là tuple riêng trong `Dataset.truth`, cùng thứ tự nội bộ và chỉ dùng để chấm.
- Cùng mỗi case, mọi thuật toán nhận đúng topology được tạo một lần cho mỗi cặp seed, được kiểm qua SHA-256. `mixing_mu_realized` lưu số cạnh nối khác khối chia tổng số cạnh. `n_isolates`, `n_edges` và `average_degree` kiểm tra điều kiện hữu hạn.
- E1 bắt đầu graph seed từ 31001 và algorithm seed từ 21001. E3 lần lượt từ 41001 và 51001. Tăng riêng mỗi dãy một đơn vị mỗi lần lặp. Pilot có ba cặp đầu. Main có mười cặp. Pilot kiểm tra giao thức, kết quả của nó lưu riêng. Thiết kế một lần chạy mỗi cặp không tách được phương sai theo hai nguồn ngẫu nhiên. Runner xoay thứ tự thuật toán theo chỉ số lặp để giãn ảnh hưởng vị trí.

## Đo thời gian và điều kiện dừng

Chạy tuần tự trên một máy. `perf_counter` đo wall time của Python từ khởi tạo nhãn đến khi thuật toán dừng, tính cả shuffle, kiểm tra điều kiện dừng và bộ đếm. Chuyển graph, tạo fingerprint, tính metrics và phép kiểm tra maximality độc lập của runner nằm ngoài timer. Leiden dùng `leidenalg.ModularityVertexPartition`, độ phân giải modularity chuẩn γ = 1, hai vòng tối ưu với seed riêng. Tiến trình con chuyển cùng tập đỉnh/cạnh sang igraph trước khi báo sẵn sàng. Tiến trình cha giám sát thời hạn và chấm điểm theo membership trả về.

`update_visits` đếm lượt đỉnh đi qua vòng xử lý, kể cả isolate. `check_visits` là lượt kiểm tra maximality nội bộ của LPA, có dừng sớm khi gặp đỉnh vi phạm. `node_visits` là tổng hai loại. `label_updates` đếm thay đổi nhãn ID. `neighbor_examinations` là tổng số láng giềng đọc trong chấm nhãn và quét để đưa lại vào hàng đợi. `requeues` loại lượt enqueue ban đầu. Với FLPA hoàn thành, `update_visits = n_nodes + requeues`. Các bộ đếm vắng mặt ở Leiden và backend C được lưu NA.

E1 đặt timeout 90 giây. Timeout Python kiểm tra lúc bắt đầu và sau mỗi 256 lượt đỉnh, rồi xác nhận thời gian cuối. Ngưỡng an toàn API `max_visits` trả `visit_limit`. Runner chỉ tính chất lượng khi `status = ok`. Completion rate dùng tất cả lần thử. Các thống kê mô tả dùng những lần `ok` và SD mẫu với mẫu số n−1. SD vắng khi chỉ có một mẫu. Tỷ lệ ghép cặp là `runtime(comp)/runtime(FIFO)` cho mỗi graph và algorithm seed, sau đó lấy trung bình và SD. Tỷ số trung bình trên các cặp hoàn thành được xuất riêng.

## Metrics và đối chiếu

NMI sử dụng chuẩn hoá trung bình số học theo lối Danon và cs. ARI hiệu chỉnh đồng thuận theo ngẫu nhiên. ACC chọn ghép một-một giữa các cụm và nhãn thật bằng Hungarian, kể cả ma trận chữ nhật. Modularity Q bổ sung đánh giá cấu trúc với null model bảo toàn bậc. ER/BA thiếu nhãn, vì vậy các cột NMI/ARI/ACC để trống. `final_maximality` được áp dụng cho nhóm LPA, kể cả mã tham chiếu, và để trống ở Leiden.

So sánh E1 theo ba mức. Figure 1 là chuẩn đã công bố. Đọc xấp xỉ các điểm trung bình có thể nhận ra trên panel trùng kích thước, ghi độ chính xác hữu hạn và không suy ra SD từ điểm bị cắt. Chạy thêm nhánh igraph `flpa` do tác giả cung cấp, commit `b89649877e15a2a4d3ca199c9190fe3dc181c643`, trên ba cặp seed đầu ở n = 10.000 và 100.000. Đo bên trong trình gọi C, dùng các biến thể `IGRAPH_LPA_DOMINANCE`, `IGRAPH_LPA_RETENTION`, `IGRAPH_LPA_FAST`. Giữ riêng CSV tham chiếu và kết quả Python. RNG, thứ tự cạnh, compiler, nền phần cứng và cách kiểm tra hội tụ có thể khác. Độ lệch tương đối tính trên trung bình có sẵn theo (Python−tham chiếu)/tham chiếu.

## Đầu ra

Mỗi bundle chứa `raw.csv`, `summary.csv`, `paired.csv`, hình từ summary và `manifest.json`. Manifest có cấu hình đã mở rộng, commit, trạng thái source, phiên bản phần mềm, nền phần cứng, thời gian UTC và SHA-256 từng kết quả. Raw CSV giữ cả run không hoàn thành. `verify_results.py` kiểm schema, cặp đồ thị, công thức tổng hợp và tính nhất quán. W&B lấy dữ liệu sau khi đo, log theo bundle với `run_id` cho từng lượt và artifact CSV/hình/manifest.
