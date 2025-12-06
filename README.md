# Ứng Dụng Quản Lý Lịch Trình Cá Nhân

Ứng dụng **Quản Lý Lịch Trình Cá Nhân** viết bằng **Python 3**, sử dụng **PyQt6** cho giao diện người dùng, **SQLite** để lưu trữ dữ liệu và **NLP** để phân tích câu tiếng Việt mô tả sự kiện thành thông tin chi tiết.

---

## 📂 Cấu trúc dự án

- **`main.py`**:  
  Giao diện PyQt6 chính, cho phép:
  - Thêm, sửa, xóa sự kiện
  - Tìm kiếm và lọc sự kiện
  - Nhắc nhở tự động
  - Nhập/Xuất dữ liệu JSON

- **`nlp.py`**:  
  Xử lý ngôn ngữ tự nhiên (NLP):
  - Nhận diện ngày tương đối (hôm nay, mai, mốt, thứ 2, cuối tuần,…)
  - Nhận diện giờ bắt đầu/kết thúc
  - Nhận diện địa điểm
  - Nhận diện nhắc trước (reminder)
  - Chuyển dữ liệu thành JSON chuẩn

- **`database.py`**:  
  Quản lý SQLite:
  - Khởi tạo bảng `events`
  - Thêm, sửa, xóa, tìm kiếm sự kiện
  - Lấy danh sách sự kiện theo thời gian

---

## 💻 Yêu cầu

- Python >= 3.10
- Thư viện:
  ```bash
  pip install PyQt6

🚀 Hướng dẫn chạy

Clone repository:

git clone https://github.com/tainguyenn101/DOANCHUYENNGANH-3122410272_PhanThanhTaiNguyen.git
cd DoAnChuyenNganh-PhanThanhTaiNguyen-3122410272


Cài đặt thư viện:

pip install PyQt6


Chạy ứng dụng:

python main.py

📝 Ví dụ sử dụng

Nhập câu nhắc việc tiếng Việt:

Nhắc tôi họp nhóm lúc 10h sáng mai ở phòng 302 nhắc trước 15 phút


Kết quả phân tích và lưu vào cơ sở dữ liệu:

{
    "event": "họp nhóm",
    "start_time": "2025-12-07T10:00:00",
    "end_time": null,
    "location": "phòng 302",
    "reminder_minutes": 15
}

🔧 Tính năng nổi bật

Nhận dạng ngôn ngữ tự nhiên bằng tiếng Việt

Hỗ trợ ngày tương đối và ngày cụ thể

Nhắc nhở tự động với thời gian tùy chỉnh

Nhập/Xuất dữ liệu JSON

Lọc sự kiện theo ngày, tuần, tháng

📌 License

MIT License

🧑‍💻 Tác giả

Phan Thanh Tài Nguyên
GitHub: tainguyenn101
