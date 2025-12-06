import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QHBoxLayout, QLineEdit, QHeaderView, QComboBox, QLabel, 
    QFileDialog, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import QTimer
from datetime import datetime, timedelta
from database import init_db, add_event, get_all_events, delete_event, search_events_by_name, update_event 
from nlp import tao_json

# -----------------------------
# Dialog thêm/sửa sự kiện
# -----------------------------
class AddEditEventDialog(QDialog):
    def __init__(self, event_data=None):
        super().__init__()
        
        # Nếu là thêm mới, khởi tạo dữ liệu mặc định
        if event_data is None:
            self.data = {
                'id': None,
                'name': '',
                'start_time': datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), # Gợi ý thời gian hiện tại
                'end_time': '',
                'location': '',
                'reminder_minutes': 15 # Mặc định 15p
            }
            self.setWindowTitle("Thêm sự kiện thủ công")
        else:
            self.data = event_data
            self.setWindowTitle("Sửa sự kiện")

        self.setGeometry(200, 200, 400, 300)

        layout = QFormLayout()

        # 1. Tên sự kiện
        self.name_input = QLineEdit(self.data.get('name', ''))
        layout.addRow("Tên sự kiện:", self.name_input)

        # 2. Bắt đầu (Ở dạng ISO format để dễ sửa)
        self.start_input = QLineEdit(self.data.get('start_time', ''))
        layout.addRow("Bắt đầu (ISO format, VD: 2025-12-05T10:00:00):", self.start_input)

        # 3. Kết thúc
        self.end_input = QLineEdit(self.data.get('end_time', ''))
        layout.addRow("Kết thúc (ISO format, để trống nếu không có):", self.end_input)

        # 4. Địa điểm
        self.location_input = QLineEdit(self.data.get('location', ''))
        layout.addRow("Địa điểm:", self.location_input)

        # 5. Nhắc trước (phút)
        # Chuyển về chuỗi và kiểm tra None/0
        reminder_str = str(self.data.get('reminder_minutes', 0)) if self.data.get('reminder_minutes') is not None else '0'
        self.reminder_input = QLineEdit(reminder_str)
        layout.addRow("Nhắc trước (phút):", self.reminder_input)

        # 6. Nút OK và Cancel
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        self.setLayout(layout)

    def get_updated_data(self):
        """Trả về dữ liệu đã được cập nhật, bao gồm ID (nếu là sửa)."""
        name_text = self.name_input.text().strip()
        start_time_str = self.start_input.text().strip()
        end_time_str = self.end_input.text().strip()
        location_text = self.location_input.text().strip() or None

        if not name_text or not start_time_str:
             QMessageBox.critical(self, "Lỗi nhập liệu", "Tên sự kiện và Thời gian bắt đầu không được để trống.")
             return None
        
        try:
            reminder = int(self.reminder_input.text() or 0)
            if reminder < 0:
                 raise ValueError("Nhắc trước phải là số dương.")
        except ValueError as e:
            QMessageBox.critical(self, "Lỗi nhập liệu", f"Nhắc trước không hợp lệ: {e}")
            return None

        # Kiểm tra định dạng thời gian ISO
        try:
            if start_time_str: datetime.fromisoformat(start_time_str)
            if end_time_str: datetime.fromisoformat(end_time_str)
        except ValueError as e:
            QMessageBox.critical(self, "Lỗi định dạng", f"Thời gian phải ở định dạng ISO 8601 hợp lệ (YYYY-MM-DDTHH:MM:SS). Chi tiết: {e}")
            return None

        return {
            'id': self.data['id'], 
            'name': name_text,
            'start_time': start_time_str,
            'end_time': end_time_str or None, 
            'location': location_text, 
            'reminder_minutes': reminder
        }

# -----------------------------
# Cửa sổ chính
# -----------------------------
class Scheduler(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quản lý lịch trình cá nhân")
        self.setGeometry(100, 100, 1100, 700)
        self.center_window()

        self.layout = QVBoxLayout()

        # 1. Ô nhập văn bản
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Nhập câu tiếng Việt mô tả sự kiện ví dụ: 'Nhắc tôi họp nhóm lúc 10h sáng mai ở phòng 302 nhắc trước 15 phút'"
        )
        self.text_input.setFixedHeight(80)
        self.layout.addWidget(self.text_input)

        # 2. Nút thêm/xóa/sửa/tìm kiếm/nhập/xuất
        action_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Thêm sự kiện")
        self.add_btn.clicked.connect(self.add_event)
        action_layout.addWidget(self.add_btn)
        
        # NÚT THÊM THỦ CÔNG MỚI
        self.add_manual_btn = QPushButton("Thêm sự kiện thủ công")
        self.add_manual_btn.clicked.connect(self.add_manual_event) # KẾT NỐI VỚI HÀM MỚI
        action_layout.addWidget(self.add_manual_btn) 

        # NÚT SỬA
        self.edit_btn = QPushButton("Sửa sự kiện đã chọn")
        self.edit_btn.clicked.connect(self.edit_selected)
        action_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Xóa sự kiện đã chọn")
        self.delete_btn.clicked.connect(self.delete_selected)
        action_layout.addWidget(self.delete_btn)

        self.export_btn = QPushButton("Xuất JSON")
        self.export_btn.clicked.connect(self.export_json)
        action_layout.addWidget(self.export_btn)

        self.import_btn = QPushButton("Nhập JSON")
        self.import_btn.clicked.connect(self.import_json)
        action_layout.addWidget(self.import_btn)

        action_layout.addStretch(1)

        # 3. Bộ lọc & Tìm kiếm
        filter_search_layout = QHBoxLayout()
        filter_search_layout.addWidget(QLabel("Xem theo:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Tất cả", "Hôm nay", "Tuần này", "Tháng này"])
        self.view_combo.currentIndexChanged.connect(self.filter_view)
        filter_search_layout.addWidget(self.view_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm theo tên")
        filter_search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Tìm kiếm")
        self.search_btn.clicked.connect(self.search_by_name)
        filter_search_layout.addWidget(self.search_btn)

        action_layout.addLayout(filter_search_layout)
        self.layout.addLayout(action_layout)

        # 4. Bảng hiển thị
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["STT", "Tên sự kiện", "Bắt đầu", "Kết thúc", "Địa điểm", "Nhắc trước (phút)"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

        # Load dữ liệu ban đầu
        self.refresh_table()

        # Timer nhắc nhở (1p kiểm tra 1 lần,chậm thông báo tối đa 1p)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(60000) 

    # -----------------------------
    # Thêm sự kiện thủ công
    def add_manual_event(self):
        # Tạo dialog với dữ liệu mặc định (None)
        dialog = AddEditEventDialog(event_data=None)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_updated_data()
            if new_data is None:
                return 

            try:
                # Dùng add_event để thêm sự kiện mới
                add_event(
                    new_data['name'],
                    new_data['start_time'],
                    new_data['end_time'],
                    new_data['location'],
                    new_data['reminder_minutes']
                )
                self.refresh_table()
                QMessageBox.information(self, "Thành công", "Đã thêm sự kiện thủ công.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi thêm sự kiện", f"Không thể thêm sự kiện. Chi tiết: {e}")

    # -----------------------------
    # Sửa sự kiện
    def edit_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chọn hàng", "Vui lòng chọn sự kiện cần sửa.")
            return

        row_index = selected_rows[0].row()
        event_id = self.table.item(row_index, 0).data(1)
        
        if event_id is None:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy ID sự kiện.")
            return

        # 1. Lấy dữ liệu gốc ISO format từ DB
        all_events = get_all_events()
        original_event = next((e for e in all_events if e[0] == event_id), None)
        
        if not original_event:
            QMessageBox.critical(self, "Lỗi", "Không thể lấy dữ liệu gốc của sự kiện.")
            return

        # Tạo dictionary dữ liệu ISO format để truyền vào dialog
        event_data_iso = {
            'id': original_event[0],
            'name': original_event[1],
            'start_time': original_event[2] or '',
            'end_time': original_event[3] or '',
            'location': original_event[4] or '',
            'reminder_minutes': original_event[5]
        }
        
        # 2. Hiển thị Dialog Sửa
        dialog = AddEditEventDialog(event_data_iso) # Truyền dữ liệu gốc vào
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_updated_data()
            if updated_data is None:
                return 

            # 3. Cập nhật vào Database
            try:
                update_event(
                    updated_data['id'],
                    updated_data['name'],
                    updated_data['start_time'],
                    updated_data['end_time'],
                    updated_data['location'],
                    updated_data['reminder_minutes']
                )
                self.refresh_table()
                QMessageBox.information(self, "Thành công", "Đã cập nhật sự kiện.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi cập nhật", f"Không thể cập nhật sự kiện. Chi tiết: {e}")

    
    # -----------------------------
    # Căn giữa cửa sổ chính
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # -----------------------------
    # Thêm sự kiện 
    def add_event(self):
        text = self.text_input.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Lỗi nhập liệu", "Vui lòng nhập mô tả sự kiện")
            return
        try:
            info = tao_json(text)
            add_event(info["event"], info["start_time"], info["end_time"], info["location"], info["reminder_minutes"])
            self.text_input.clear()
            self.view_combo.setCurrentIndex(0) 
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi phân tích", f"Không thể phân tích sự kiện. Chi tiết: {e}")

    # -----------------------------
    # Làm mới bảng 
    def refresh_table(self, events=None):
        if events is None:
            events = get_all_events()
        self.table.setRowCount(len(events))
        for idx, row in enumerate(events):
            event_id = row[0]
            # STT
            self.table.setItem(idx, 0, QTableWidgetItem(str(idx+1)))
            # Tên sự kiện
            self.table.setItem(idx, 1, QTableWidgetItem(row[1].capitalize() if row[1] else ""))
            # Bắt đầu (Định dạng hiển thị)
            self.table.setItem(idx, 2, QTableWidgetItem(self.format_dt(row[2])))
            # Kết thúc (Định dạng hiển thị)
            self.table.setItem(idx, 3, QTableWidgetItem(self.format_dt(row[3]) if row[3] else ""))
            # Địa điểm
            self.table.setItem(idx, 4, QTableWidgetItem(row[4].capitalize() if row[4] else ""))
            # Nhắc trước
            self.table.setItem(idx, 5, QTableWidgetItem(str(row[5])))
            # Lưu Event ID vào item STT để sử dụng cho chức năng sửa/xóa
            self.table.item(idx, 0).setData(1, event_id)

    def format_dt(self, iso_time_str):
        if not iso_time_str:
            return ""
        try:
            dt = datetime.fromisoformat(iso_time_str)
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return iso_time_str

    # -----------------------------
    # Xóa sự kiện 
    def delete_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chọn hàng", "Vui lòng chọn sự kiện cần xóa")
            return
        row_index = selected_rows[0].row()
        event_id_item = self.table.item(row_index, 0)
        event_id = event_id_item.data(1)
        if event_id is not None:
            delete_event(event_id)
            self.refresh_table()
            QMessageBox.information(self, "Thành công", "Đã xóa sự kiện")

    # -----------------------------
    # Tìm kiếm theo tên 
    def search_by_name(self):
        name_text = self.search_input.text().strip()
        if name_text:
            events = search_events_by_name(name_text)
            self.refresh_table(events)
        else:
            self.filter_view(self.view_combo.currentIndex())
        self.search_input.clear()

    # -----------------------------
    # Lọc theo ngày / tuần / tháng 
    def filter_view(self, index):
        all_events = get_all_events()
        now = datetime.now()
        filtered = []

        if index == 0: 
            self.refresh_table(all_events)
            return

        for e in all_events:
            start_dt_str = e[2]
            if not start_dt_str:
                continue
            try:
                start_dt = datetime.fromisoformat(start_dt_str)
            except ValueError:
                continue

            match = False
            if index == 1: # Hôm nay
                if start_dt.date() == now.date():
                    match = True
            elif index == 2: # Tuần này
                week_start = now.date() - timedelta(days=now.weekday())
                week_end = week_start + timedelta(days=6)
                if week_start <= start_dt.date() <= week_end:
                    match = True
            elif index == 3: # Tháng này
                if start_dt.year == now.year and start_dt.month == now.month:
                    match = True

            if match:
                filtered.append(e)

        self.refresh_table(filtered)

    # -----------------------------
    # Nhắc nhở tự động 
    def check_reminders(self):
        now = datetime.now()
        events = get_all_events()
        for e in events:
            start_time_str = e[2]
            reminder_minutes = e[5]
            if not start_time_str or reminder_minutes < 0:
                continue
            try:
                start_time = datetime.fromisoformat(start_time_str)
            except ValueError:
                continue

            reminder_time = start_time - timedelta(minutes=reminder_minutes)
            if reminder_time <= now < reminder_time + timedelta(seconds=60):
                QApplication.beep()
                msg = QMessageBox(self)
                msg.setWindowTitle("Nhắc nhở sự kiện")
                msg.setText(
                    f"Sự kiện: {e[1]}\n"
                    f"Bắt đầu: {self.format_dt(e[2])}\n"
                    f"Địa điểm: {e[4] or 'Không xác định'}\n\n"
                    f"Sự kiện sẽ diễn ra sau {reminder_minutes} phút"
                )
                msg.setIcon(QMessageBox.Icon.Information)
                
                screen = QApplication.primaryScreen().availableGeometry()
                x = (screen.width() - msg.width()) // 2
                y = (screen.height() - msg.height()) // 2
                msg.move(x, y)

                msg.exec()

    # -----------------------------
    # Xuất JSON
    def export_json(self):
        events = get_all_events()
        data_list = []
        for e in events:
            data_list.append({
                "name": e[1],
                "start_time": e[2],
                "end_time": e[3],
                "location": e[4],
                "reminder_minutes": e[5]
            })
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file JSON", "", "JSON Files (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Xuất JSON", "Đã xuất dữ liệu thành công!")

    # -----------------------------
    # Nhập JSON
    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data_list = json.load(f)
                for item in data_list:
                    add_event(item.get("name", ""),
                              item.get("start_time", ""),
                              item.get("end_time", ""),
                              item.get("location", ""),
                              item.get("reminder_minutes", 0))
                self.refresh_table()
                QMessageBox.information(self, "Nhập JSON", "Đã nhập dữ liệu thành công!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi JSON", f"Không thể đọc file JSON. Chi tiết: {e}")
                
# -----------------------------
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = Scheduler()
    window.show()
    sys.exit(app.exec())