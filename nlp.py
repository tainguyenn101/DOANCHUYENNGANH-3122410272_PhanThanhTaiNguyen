import re
import json
from typing import Tuple
from datetime import datetime, timedelta

# -----------------------------
# Hàm parse ngày từ từ khóa
def parse_relative_date(text, base_date=None):
    """
    Phân tích các ngày tương đối (hôm nay, ngày mai, cuối tuần, thứ X tới, thứ X tuần sau).

    Args:
        text (str): Chuỗi chứa ngày tương đối.
        base_date (datetime, optional): Ngày cơ sở để tính toán. Mặc định là datetime.today().

    Returns:
        datetime: Đối tượng datetime tương ứng.
    """
    # 1. Khởi tạo ngày cơ sở và làm sạch văn bản
    base_date = base_date or datetime.today()
    # Loại bỏ thông tin về giờ, phút, giây để chỉ làm việc với ngày
    base_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0) 
    text = text.lower().strip()

    # 2. Kiểm tra từ khóa tuần
    is_next_week = "tuần sau" in text or "tuần tới" in text

    # 3. Ngày tương đối: nay, hôm nay, mai, ngày mai, mốt, ngày mốt, kia, ngày kia
    if "nay" in text or "hôm nay" in text:
        return base_date
    elif "mai" in text or "ngày mai" in text:
        return base_date + timedelta(days=1)
    elif "mốt" in text or "ngày mốt" in text:
        return base_date + timedelta(days=2)
    elif "kia" in text or "ngày kia" in text:
        return base_date + timedelta(days=3)

    # 4. Cuối tuần: cuối tuần, cuối tuần này, cuối tuần sau (Chủ Nhật gần nhất)
    if "cuối tuần" in text:
        target_weekday = 6 
        current_weekday = base_date.weekday()
        days_to_target = target_weekday - current_weekday
        # Tính Chủ Nhật GẦN NHẤT (bao gồm hôm nay nếu hôm nay là Chủ Nhật)
        if days_to_target < 0:
            # Nếu Chủ Nhật đã qua, phải nhảy sang Chủ Nhật tuần sau
            days_to_target += 7
        # Số ngày đến Chủ Nhật gần nhất (0-6 ngày)
        delta_days = days_to_target
        
        if is_next_week:
            # Nếu là "cuối tuần sau", thêm 7 ngày nữa vào Chủ Nhật gần nhất
            delta_days += 7
            
        return base_date + timedelta(days=delta_days)

    # 5. Thứ trong tuần: thứ 2, thứ ba, thứ sáu tới, ...
    weekdays = {
        "thứ hai": 0, "thứ 2": 0, "thứ2": 0, 
        "thứ ba": 1, "thứ 3": 1, "thứ3": 1, 
        "thứ tư": 2, "thứ 4": 2, "thứ4": 2,
        "thứ năm": 3, "thứ 5": 3, "thứ5": 3,
        "thứ sáu": 4, "thứ 6": 4, "thứ6": 4,
        "thứ bảy": 5, "thứ 7": 5, "thứ7": 5,
        "chủ nhật": 6, "cn": 6,
        # Dạng viết tắt
        "t2": 0, "t3": 1, "t4": 2, "t5": 3, "t6": 4, "t7": 5
    }
    
    for k, v in weekdays.items():
        # Kiểm tra nếu từ khóa ngày trong tuần
        # Phải dùng regex để bắt các dạng như "thứ 7"
        day_pattern = r"\b" + re.escape(k) + r"\b"
        if re.search(day_pattern, text):
            target_weekday = v
            current_weekday = base_date.weekday()

            # Tính số ngày chênh lệch
            days_ahead = target_weekday - current_weekday

            if is_next_week:
                # Nếu có "tuần sau/tới"
                if days_ahead <= 0:
                    # Nếu đã qua hoặc là hôm nay, nhảy sang tuần sau
                    days_ahead += 7
                else:
                    # Nếu ngày đó còn trong tuần này, thêm 7 ngày (2+7=9)
                    days_ahead += 7 
            else:
                # Nếu ngày đó là hôm nay
                if days_ahead <= 0:
                    days_ahead += 7
            
            return base_date + timedelta(days=days_ahead)

    # 6. Ngày cụ thể dd/mm hoặc dd/mm/yyyy
    m_date = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", text)
    if m_date:
        try:
            day = int(m_date.group(1))
            month = int(m_date.group(2))
            # Xử lý năm: nếu không có thì lấy năm hiện tại
            year_str = m_date.group(3)
            if year_str:
                year = int(year_str)
                if len(year_str) == 2:
                    year += 2000
            else:
                year = base_date.year
                
            # Kiểm tra nếu ngày/tháng đã qua trong năm hiện tại, chuyển sang năm sau
            try:
                result_date = datetime(year, month, day)
                # Chỉ kiểm tra nếu không có năm cụ thể trong chuỗi
                if not m_date.group(3) and result_date < base_date:
                    result_date = datetime(year + 1, month, day)
                return result_date
            except ValueError:
                return None
        except Exception:
            return None

    # 7. Mặc định
    return base_date

# -----------------------------
# Hàm parse giờ sang datetime.time
# -----------------------------

def parse_time_string(time_str: str) -> Tuple[int, int]:
    """
    Chuyển chuỗi giờ Tiếng Việt sang giờ và phút (hệ 24 giờ).

    Hỗ trợ các dạng: 4 giờ 30, 4 giờ 30 phút, 4h30, 4g30p, 4:30, 4.30, 4 giờ, 4h, 4g.
    Nhận biết các từ khóa: sáng, trưa, chiều, tối.
    
    Trả về (hour, minute) (0-23, 0-59) hoặc (-1, -1) nếu không phân tích được.
    """
    time_str_lower = time_str.lower().strip()

    # 1. Kiểm tra sáng/trưa/chiều/tối
    is_am = "sáng" in time_str_lower
    is_noon = "trưa" in time_str_lower
    is_afternoon = "chiều" in time_str_lower
    is_pm_night = "tối" in time_str_lower 
    
    time_str_for_parsing = re.sub(r"(sáng|trưa|chiều|tối)", " ", time_str_lower).strip()

    # 2. Regex linh hoạt cho các dạng giờ/phút
    m = re.search(r"(\d{1,2})\s*(?:[:h|g|giờ|\.|\s]*)\s*(\d{1,2})?\s*(?:p|phút)?", time_str_for_parsing)

    hour = -1
    minute = -1
    
    if m:
        try:
            hour = int(m.group(1))
            # Lấy phút (Group 2). Nếu không có (None), mặc định là 0.
            minute = int(m.group(2)) if m.group(2) else 0

            # Kiểm tra giá trị hợp lệ
            if hour < 0 or hour > 23 or minute < 0 or minute >= 60:
                return -1, -1

        except (ValueError, TypeError):
            # Xử lý nếu việc chuyển đổi int thất bại
            return -1, -1
        
        # 3. Xử lý sáng/trưa/chiều/tối (Chuyển sang hệ 24 giờ)
        
        is_pm_keyword = is_noon or is_afternoon or is_pm_night

        if is_am and hour == 12:
            # 12h sáng (nửa đêm) -> 0h
            hour = 0
        elif is_pm_keyword and hour < 12:
            # 1h trưa, 4h chiều/tối -> cộng thêm 12h
            hour += 12
        # Trường hợp 12h trưa/chiều/tối (hour=12) giữ nguyên
            
        return hour, minute

    return -1, -1



# -----------------------------
# Hàm parse reminder thành số
# -----------------------------
def parse_reminder(reminder_str):
    reminder_str = reminder_str.lower()
    hours = 0
    minutes = 0

    # Tìm giờ
    m_hour = re.search(r"(\d+)\s*(?:giờ|h)", reminder_str)
    if m_hour:
        hours = int(m_hour.group(1))

    # Tìm phút
    m_minute = re.search(r"(\d+)\s*(?:phút|p)", reminder_str)
    if m_minute:
        minutes = int(m_minute.group(1))

    total_minutes = hours * 60 + minutes
    #if total_minutes == 0:
        #total_minutes = 0
    return total_minutes


# -----------------------------
# Hàm tách câu
# -----------------------------
def tach_cau(text):
    text = text.lower().strip()
    text = text.replace(",", "")
    text = re.sub(r"\bhãy\b\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bgiúp\b\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r'\bgiúp tôi\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r"\bvà\b\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    event_keywords = r"(nhắc tôi|lên lịch cho tôi|lên lịch|lịch|hẹn tôi|hẹn|đặt lịch cho tôi|đặt lịch)"
    start_keywords = r"(lúc|bắt đầu lúc|từ)"
    end_keywords = r"(đến|tới)"
    location_keywords = r"(ở|tại)"
    reminder_keywords = r"(nhắc trước|nhắn trước|trước|thông báo trước cho tôi|thông báo trước|báo trước)"
    
    # Định nghĩa các mẫu ngày trong tuần, bao gồm viết tắt (t2, t7) và viết số (thứ 7, thứ 2)
    # \s* cho phép khoảng trắng giữa "thứ" và số (ví dụ: "thứ 7")
    weekday_base = r"(thứ\s*[2-7]|thứ hai|thứ ba|thứ tư|thứ năm|thứ sáu|thứ bảy|chủ nhật|cn|t[2-7])"
    
    # Date_keywords
    date_keywords = r"((?:" + weekday_base + r")\s+(?:tuần sau|tuần tới)|nay|hôm nay|mai|ngày mai|sáng mai|tối mai|mốt|ngày mốt|sáng mốt|kia|ngày kia|cuối tuần sau|cuối tuần này|cuối tuần|" + weekday_base + r"|tuần sau|tuần tới|tuần này|\d{1,2}/\d{1,2}(?:/\d{2,4})?)"


    date_text = ""
    event = ""
    start_time = ""
    end_time = ""
    location = ""
    reminder = ""

    # 1. Tìm từ khóa ngày
    m_date = re.search(date_keywords, text)
    if m_date:
        date_text = m_date.group(0).strip()
        text = text.replace(date_text, "").strip()

    # 2. Tìm start time
    m_start = re.search(rf"({start_keywords}.*?)(?={end_keywords}|{location_keywords}|{reminder_keywords}|$)", text)
    if m_start:
        start_time = m_start.group(1)
        start_time = re.sub(start_keywords, "", start_time).strip()
        text = text.replace(m_start.group(1), "").strip() 
    else:
        start_time =None

    # 3. Tìm end time
    m_end = re.search(rf"({end_keywords}.*?)(?={start_keywords}|{location_keywords}|{reminder_keywords}|$)", text)
    if m_end:
        end_time = m_end.group(1)
        end_time = re.sub(end_keywords, "", end_time).strip()
        text = text.replace(m_end.group(1), "").strip()

    # 4. Tìm location
    m_location = re.search(rf"({location_keywords}.*?)(?={start_keywords}|{end_keywords}|{reminder_keywords}|$)", text)
    if m_location:
        location = m_location.group(1)
        location = re.sub(location_keywords, "", location).strip()
        text = text.replace(m_location.group(1), "").strip()

    # 5. Tìm reminder
    m_reminder = re.search(rf"({reminder_keywords}.*?)(?={start_keywords}|{end_keywords}|{location_keywords}|$)", text)
    if m_reminder:
        reminder = parse_reminder(m_reminder.group(1))
        text = text.replace(m_reminder.group(1), "").strip()
    
    # 2. Event
    m_event = re.search(rf"({event_keywords}.*?)(?={start_keywords}|{location_keywords}|{reminder_keywords}|{end_keywords}|$)", text)
    if m_event:
        event = m_event.group(1)
        event = re.sub(event_keywords, "", event).strip()
    else:
        event = text.strip()

    # 7. Kết hợp date + start_time
    dt_start = None
    if start_time:
        # Nếu có giờ,tìm ngày
        date_base = parse_relative_date(date_text)
        h, m = parse_time_string(start_time)
        dt_start = datetime(date_base.year, date_base.month, date_base.day, h, m)
        start_time = dt_start.isoformat()
    else:
        #tìm ngày + giờ hiện tại 
        date_base = parse_relative_date(date_text)
        dt_start = datetime.now()
        dt_start = datetime(date_base.year, date_base.month, date_base.day, dt_start.hour, dt_start.minute)
        start_time = dt_start.isoformat()
    
    # 8. End time
    if end_time:
        # Nếu có end_time, phải có date_base từ start_time hoặc date_text
        date_base = parse_relative_date(date_text)
        h, m = parse_time_string(end_time)
        dt_end = datetime(date_base.year, date_base.month, date_base.day, h, m)
        end_time = dt_end.isoformat()
    else:
        end_time =None

    return event, start_time, end_time, location, reminder


# -----------------------------
# Chuyển sang JSON
# -----------------------------
def tao_json(text):
    event, start_time, end_time, location, reminder = tach_cau(text)
    data = {
        "event": event,
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "reminder_minutes": reminder if reminder else 0
    }
    return data
def parse_event(text):
    return tao_json(text)

# -----------------------------
# Chạy thử
# -----------------------------
if __name__ == "__main__":
    print("Nhập câu nhắc việc:")
    text = input("> ")
    result = tao_json(text)
    print("\nKết quả JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=4))
    