# Agent Lab — Bản đồ Spooksville

Ứng dụng chạy cục bộ trong trình duyệt. Bản đồ có bộ lọc, zoom, ghim thử và mô phỏng di chuyển.

## Chạy ứng dụng

Yêu cầu Python 3.10 trở lên; không cần cài thư viện ngoài. Từ thư mục dự án, chạy:

```powershell
python run_app.py
```

Mở `http://127.0.0.1:8765/`.

## Bản đồ

Tọa độ marker được ước lượng từ ảnh bản đồ đã cung cấp. Hai shop là **Witch of Halloween** và **Nyx**; marker hồi sinh là **Spawn Point**. Rê chuột lên biểu tượng để xem tên. Đây là lớp tham khảo tĩnh, không đọc vị trí nhân vật trong game.

Ảnh marker hồi sinh đã cắt lề trong suốt để dễ nhìn. Bản đồ giữ nguyên tỉ lệ gốc; kích thước marker ổn định khi zoom.
