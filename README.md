# Radar ý tưởng Dr Lizzi

Mỗi sáng 5:30 (giờ VN), GitHub Actions tự quét YouTube (trong nước và nước ngoài) và Google Trends VN. Riêng TikTok chỉ quét thứ Hai, qua TikNeuron. Sau đó Gemini miễn phí lọc theo hồ sơ kênh và viết 8–12 ý tưởng tiếng Việt vào **[y-tuong/moi-nhat.md](y-tuong/moi-nhat.md)**.

Toàn bộ chạy trên cloud, máy tính tắt vẫn chạy, và không tốn token Claude. Khi muốn đưa ý tưởng vào Kho ý tưởng của Thư viện, nói với Claude: **"Nhập ý tưởng radar"**.

## Cài đặt (làm một lần)

### 1. Tạo key YouTube Data API (miễn phí)
1. Vào https://console.cloud.google.com/ rồi tạo project mới, ví dụ "drlizzi-radar".
2. Vào **APIs & Services → Library**, tìm **YouTube Data API v3**, bấm **Enable**.
3. Vào **APIs & Services → Credentials → Create credentials → API key**, rồi chép key.
4. Nên bấm **Restrict key** và chỉ cho dùng YouTube Data API v3.

### 2. Tạo repo trên GitHub
1. Vào https://github.com/new, đặt tên `drlizzi-radar`, chọn **Public**, không tick thêm gì, rồi bấm **Create repository**.
2. Đưa code lên. Cách dễ nhất: báo Claude địa chỉ repo, Claude sẽ đẩy code từ máy này lên. Nếu Git hiện cửa sổ đăng nhập GitHub thì bác sĩ tự đăng nhập.

### 3. Thêm 3 key bí mật
Vào repo → **Settings → Secrets and variables → Actions → New repository secret**, thêm lần lượt:

| Name | Giá trị |
|---|---|
| `YOUTUBE_API_KEY` | key vừa tạo ở bước 1 |
| `GEMINI_API_KEY` | key Gemini, có sẵn trong file `youtube project\radar\ai.env` (dòng `GEMINI_API_KEY=`) |
| `TIKNEURON_API_KEY` | key TikNeuron. Nên tạo key mới vì key cũ đã dán vào chat |

Key nằm trong Secrets thì không ai xem được, kể cả khi repo để công khai.

### 4. Chạy thử
Vào tab **Actions → Radar y tuong → Run workflow**.
- Để trống ô TikTok nếu không muốn tốn credit.
- Chạy xong (khoảng 2–5 phút) thì mở `y-tuong/moi-nhat.md`.

## Tùy chỉnh
- **Từ khóa và giới hạn:** sửa `radar/tu-khoa.json`. Sửa ngay trên web GitHub được, bằng nút cây bút.
- **Hồ sơ kênh mà Gemini dựa vào:** sửa `radar/ho-so-ngan.md`.
- **Đổi model Gemini:** vào Settings → Secrets and variables → Actions → Variables, thêm `GEMINI_MODEL`.

## Giới hạn miễn phí
- **YouTube:** khoảng 10.000 đơn vị mỗi ngày. Radar dùng khoảng 3.100 (30 lượt tìm).
- **Gemini:** dùng hạn mức miễn phí. Hết hạn mức thì hôm đó ghi danh sách thô, đánh dấu "chưa lọc".
- **TikNeuron:** gói miễn phí 20 credit. Radar dùng tối đa 18, mỗi thứ Hai 1 credit, và tự dừng khi hết hoặc bị từ chối.
- **GitHub Actions:** repo công khai chạy miễn phí.
