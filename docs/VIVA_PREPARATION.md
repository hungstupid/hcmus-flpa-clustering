# Chuẩn bị vấn đáp FLPA

## Dữ liệu và thiết kế thí nghiệm

**1. Vì sao dùng ba họ đồ thị cho E1?** ER cung cấp đối chứng thưa với các cặp đỉnh có xác suất ngang nhau. BA có hub giúp thảo luận chi phí xử lý đỉnh bậc cao. SBM cung cấp nhóm trồng sẵn để kiểm tra việc một thuật toán chạy nhanh có đi cùng gộp hoặc tách cụm hay không. Dùng cùng bậc đích cho phép so sánh cấu trúc khi số cạnh tăng theo quy mô gần giống nhau.

**2. Đặt bậc trung bình ER và BA bằng cách nào?** Trong ER, mỗi đỉnh có n−1 cạnh ứng viên, mỗi cạnh xác suất d/(n−1). Trong BA, mỗi đỉnh mới thêm 5 cạnh theo đính kèm ưu tiên, nên m = 5(n−5) với cách khởi tạo sao đang dùng và bậc tiến về 10. Số cạnh ER là biến ngẫu nhiên còn BA có số cạnh xác định ở cùng n.

**3. μ trong SBM đo điều gì?** Đây là phần bậc kỳ vọng nối khác nhóm. Mỗi đỉnh có s−1 hàng xóm ứng viên nội khối và n−s ứng viên ngoại khối. Lấy xác suất tương ứng bằng (1−μ)d/(s−1) và μd/(n−s). `mixing_mu_realized` mới là tỷ lệ cạnh ngoại khối đếm trên đồ thị đã sinh.

**4. Vì sao cách sinh SBM không cần ma trận kề?** Từng cặp khối có M cặp đỉnh ứng viên. Chọn K theo Binomial(M,p), rồi lấy đều K chỉ mục khác nhau. Xác suất cho một tập K cạnh cụ thể là p^K(1−p)^(M−K). Biểu diễn lưu các cạnh trúng và index hàng tam giác, do đó vẫn là SBM Bernoulli và tránh dùng bộ nhớ n².

**5. Vì sao phải giữ isolate, node mapping và seed riêng?** Loại đỉnh cô lập sẽ đổi số đỉnh được chấm và có thể làm lệch hàng so với nhãn thật. `graph.node_ids` định nghĩa thứ tự minh bạch, còn các adjacency dùng index liên tục. Graph seed tái sinh cạnh. Algorithm seed tái sinh hoán vị và cách phá hoà. Mỗi thuật toán trong một lần so sánh lấy chung cả hai seed và SHA-256 topology.

**6. Công bằng trong benchmark được kiểm như thế nào?** Dùng cùng graph, chỉ đổi thuật toán, xoay thứ tự chạy theo lượt lặp, đo riêng giai đoạn thuật toán rồi tính metric sau. Báo cáo backend từng dòng. Python và Leiden chạy qua các backend khác nhau nên chênh lệch wall time phản ánh cả ngôn ngữ và mục tiêu tối ưu.

## Cơ chế LPA, Retention-LPA và FLPA

**7. Bất đồng bộ nghĩa là gì?** Mỗi đỉnh đọc nhãn hiện hành của láng giềng tại lúc xử lý. Nếu láng giềng vừa đổi nhãn trước đó trong cùng sweep, đỉnh sau dùng luôn nhãn mới. Do vậy thứ tự xử lý là một phần của thuật toán.

**8. Bản chuẩn và retention khác ở đâu khi hoà?** Lấy ví dụ đỉnh `v` có láng giềng nhãn A và B, đang giữ A. LPA có thể chọn B vì bốc đều trong tập nhãn cực đại. Retention giữ A. Với retention, một sweep không đổi xác nhận maximality cho cả đồ thị vì vector nhãn không đổi trong suốt sweep. LPA chạy kiểm tra điều kiện riêng sau sweep.

**9. Vì sao FLPA chỉ đưa lại láng giềng khác nhãn mới?** Nếu `v` đổi sang B và láng giềng `u` đang B, điểm B tại `u` tăng một, còn đối thủ giữ nguyên hoặc giảm. Nếu `u` đã maximal thì vẫn maximal. Láng giềng khác B có thể mất ưu thế và cần xếp hàng. Đỉnh đang chờ sẽ được xét sau với nhãn cập nhật nên chỉ cần một bản ghi trong hàng đợi.

**10. Tại sao queue rỗng đủ để xác nhận maximality?** Bắt đầu mọi đỉnh đều chờ. Mỗi đỉnh rời hàng khi đã chọn nhãn cực đại. Mọi thay đổi sau đó hoặc bảo toàn cực đại của đỉnh ở ngoài, hoặc đưa đỉnh này trở lại. Việc hết đỉnh chờ biến bất biến cục bộ thành bảo đảm cho mọi đỉnh có láng giềng. Với isolate, giữ nhãn ban đầu.

**11. Có thể chứng minh FLPA luôn chạy O(m) không?** Chi phí một lượt xét đỉnh tỷ lệ với bậc. Queue push/pop hằng số, nhưng chính một đỉnh có thể trở lại nhiều lần. Tổng cần cộng bậc của từng đỉnh được lấy ra, cộng bậc ở những lần quét để enqueue. LPA cũng phụ thuộc số sweep. Gần tuyến tính quan sát trên một tập đồ thị là phát hiện thực nghiệm.

**12. Vì sao retention có bảo đảm hữu hạn đơn giản hơn?** Xét số cạnh đồng nhãn. Mỗi lần retention đổi nhãn, số này tăng ít nhất 1 và tối đa bằng m. Trong LPA và FLPA, đổi trong thế hoà có thể giữ nguyên số cạnh đồng nhãn. Bảo đảm maximality của FLPA là phát biểu về trạng thái khi queue cạn.

**13. `node_visits`, `label_updates` và `requeues` khác gì?** `node_visits` đếm xử lý đỉnh và kiểm tra dừng nội bộ. `label_updates` đếm đổi ID nhãn thực tế. `requeues` đếm đỉnh thêm lại sau khởi tạo. Một đỉnh có thể được xét mà giữ nhãn. Với FLPA hoàn thành, số lượt lấy đỉnh bằng số đỉnh ban đầu cộng số requeue.

**14. Đồ thị nào kiểm thử được bằng lý luận?** Lá của star phải mang nhãn tâm khi maximal. Trên clique, một đỉnh thuộc nhóm nhỏ thấy ít nhất bằng số phiếu từ nhóm lớn khác, thậm chí thiếu phiếu của chính nó, nên chỉ một cụm có thể ổn định. Các thành phần liên thông rời không chia sẻ nhãn vì nhãn bắt nguồn từ từng đỉnh và chỉ truyền qua cạnh.

## Độ đo và kết quả

**15. NMI, ARI và ACC cung cấp thông tin gì?** NMI lấy lượng thông tin chung chia theo entropy trung bình. ARI đo quyết định cùng cụm của cặp đỉnh và hiệu chỉnh theo ngẫu nhiên, nên có thể âm. ACC tối đa hoá số đỉnh ghép đúng bằng Hungarian. Nếu nhóm thật hoặc dự đoán bị tách hay gộp, ghép một-một sẽ tính các phần dư vào lỗi. Các độ đo bất biến với đổi ID nhãn.

**16. Vì sao Q cao có thể đi cùng NMI hoặc ACC thấp?** Q so sánh tỷ lệ cạnh nội cụm với kỳ vọng từ bậc. NMI và ACC so với nhãn gốc. Một cách gộp nhiều phòng ban hợp tác thường xuyên có thể thoả tiêu chí topology và vẫn lệch khỏi nhãn tổ chức. Leiden được chọn vì bài báo gốc dùng Leiden tối ưu modularity, và backend hiện tại ghi rõ độ phân giải 1.

**17. Figure 1 và Figure 4 khác câu hỏi nào?** Figure 1 hỏi thời gian theo cỡ hoặc mức trộn. Figure 4 trái hỏi phục hồi khối theo μ trên 100.000 đỉnh, dùng NMI. E1 lấy ba panel tăng kích thước và E2 dành cho Figure 4 trái. E3 thay hàng đợi trên 5.000 đỉnh, cung cấp bằng chứng theo mục tiêu ablation và ở quy mô riêng.

**18. Diễn giải E3 như thế nào để tránh kết luận quá mức?** Ở μ = 0,30 và 0,45, LIFO tốn thêm thời gian và tăng nhẹ chất lượng so với FIFO. Ở μ = 0,60, LIFO quy về một cụm cả 10 lượt và vẫn maximal. Lịch ưu tiên đỉnh vừa được đưa lại là cơ chế có thể làm nhãn lan nhanh trong một vùng. Để xác nhận cơ chế cần lưu trace hoặc thiết kế thêm đối chứng, vì hiện tại chỉ có phép đo kết quả và tổng công việc.

**19. Enqueue-all trả lời được câu hỏi gì?** Thay riêng quy tắc đưa lại nhưng giữ FIFO, để kiểm tra tác động của chọn lọc láng giềng. Trên ba mức μ đã chạy, mọi láng giềng làm tăng số lượt, nhất là ở μ = 0,60. Nhiều lượt đánh giá lại còn đổi quỹ đạo phá hoà, nên cùng bất biến cuối có thể dẫn đến chất lượng khác.

**20. Speedup của nhóm tính ra sao?** Chia thời gian phương pháp so sánh cho thời gian FIFO trên đúng cặp graph và seed. Sau đó lấy mean và SD của các tỷ lệ thành công. Tỷ số trung bình runtime được xuất riêng, vì một tỷ lệ của hai giá trị trung bình dùng trọng số hiệu dụng khác với trung bình tỷ lệ.

**21. Lý do chính cho sai lệch với Figure 1 là gì?** Số graph, đồ thị thực tế, phiên bản code, thứ tự kề, RNG, phần cứng và chi phí bộ đếm có thể khác. Figure 1 có 2.000 lần lặp theo mô tả và các giá trị đọc từ hình có sai số đọc. Đối chiếu cùng đồ thị với nhánh C giữ topology chung để thu hẹp một nguồn sai khác. Cùng giá trị seed ở hai backend vẫn có thể cho hai chuỗi RNG khác nhau.

**22. Tại sao 10 lượt và SD?** Mười cặp đủ ghi nhận mức biến thiên ban đầu và phù hợp ngân sách thời gian máy này. SD mẫu mô tả mức phân tán giữa lượt, không phải khoảng tin cậy. Cần nhiều cặp hoặc thiết kế nhiều seed thuật toán lồng trong graph seed để phân tích nguồn biến động.

**23. Bằng chứng tái lập gồm những gì?** Cấu hình JSON mở rộng trong manifest, phiên bản phần mềm và commit, SHA-256 đồ thị, raw có mọi trạng thái dừng, bảng tính lại được, notebook smoke thực thi thật và danh sách kiểm tra từ clean clone. Gọi `verify_results.py` để kiểm schema, thông tin ghép cặp và hash file. Khi chạy lại trên máy khác, số liệu xác định như cấu trúc và các bộ đếm có thể đối chiếu trước thời gian đo.

**24. Đề xuất bước tiếp theo dựa trên các hạn chế nào?** Dùng thiết kế nhiều algorithm seed trên cùng topology để phân rã phương sai. Đánh giá FLPA làm khởi tạo cho Leiden bằng cả chất lượng và tổng runtime. Với email-Eu-core, kiểm ảnh hưởng của việc giữ hay bỏ chiều và đọc nhãn phòng ban như một chuẩn tổ chức có thể khác cộng đồng liên lạc.

Đọc thêm [giao thức experiment](EXPERIMENT_PROTOCOL.md), [mã thuật toán](../src/flpa/algorithms.py) và [bản nháp báo cáo](../report/Report-draft.pdf).
