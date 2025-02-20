# main.py
import sys, os, json
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPlainTextEdit, QPushButton, QLabel,
    QSpinBox, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import QUrl

import llm
import llm_to_wiki
import wiki

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("설정 불러오기 실패:", e)
    return {"api_key": "", "max_tokens": 2048, "api_type": "Gemini"}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("설정 저장 실패:", e)

# Worker 클래스: 긴 프로세스를 별도 스레드에서 실행하며 진행 상태를 알림
class WikiWorker(QObject):
    finished = Signal(str)  # event_title 전달
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, event_title, event_text, parent=None):
        super().__init__(parent)
        self.event_title = event_title
        self.event_text = event_text
    
    @Slot()
    def run(self):
        try:
            self.progress.emit("main.py = 요청 전송중 (0%)")
            settings = load_settings()
            api_key = settings.get("api_key", "")
            max_tokens = settings.get("max_tokens", 2048)
            api_type = settings.get("api_type", "Gemini")
            
            self.progress.emit("내용 생성중 (25%)")
            keywords_dict = llm.summarize_event(self.event_text, api_type=api_type, api_key=api_key, max_tokens=max_tokens)
            
            self.progress.emit("위키 작성중 (50%)")
            detailed_articles = llm_to_wiki.expand_event_to_wiki(self.event_text, keywords_dict, api_key, max_tokens=8192)
            
            self.progress.emit("위키 생성중 (75%)")
            wiki.generate_wiki_html(self.event_title, self.event_text, detailed_articles, output_file="wiki.html")
            
            self.progress.emit("100% 완료")
            self.finished.emit(self.event_title)
        except Exception as e:
            self.error.emit(str(e))

# 중앙 영역 위젯: 이벤트 제목, 입력 이력, 텍스트 입력창, 진행 상태 표시
class MainCentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # 이벤트 제목 입력란
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("이벤트 제목 입력 (예: 가상의 전쟁 사건)")
        layout.addWidget(QLabel("Event Title"))
        layout.addWidget(self.title_edit)
        
        # 상단: 입력 이력 (read-only)
        self.history_view = QPlainTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setStyleSheet("background-color: #ffffff;")
        layout.addWidget(QLabel("입력 이력"))
        layout.addWidget(self.history_view, stretch=1)
        
        # 하단: 텍스트 입력창과 전송 버튼
        bottom_layout = QHBoxLayout()
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("텍스트 입력...")
        self.input_edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)  # 가로 길이 다 차면 줄바꿈
        self.input_edit.setFixedHeight(100)  # 필요에 따라 높이 조정 가능
        self.submit_btn = QPushButton("전송")
        bottom_layout.addWidget(self.input_edit)
        bottom_layout.addWidget(self.submit_btn)
        layout.addLayout(bottom_layout)
        
        # 진행 상태 표시 (로딩/진행 텍스트)
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        self.submit_btn.clicked.connect(self.start_process)
    
    def start_process(self):
        event_title = self.title_edit.text().strip()
        event_text = self.input_edit.toPlainText().strip()  # QPlainTextEdit는 toPlainText()로 텍스트 읽기
        if not event_title or not event_text:
            QMessageBox.warning(self, "입력 오류", "이벤트 제목과 텍스트를 모두 입력하세요.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history_view.appendPlainText(f"[{now}] 입력: {event_text}")
        self.progress_label.setText("진행 중...")
        self.submit_btn.setEnabled(False)
        
        # 워커 스레드 생성 및 실행
        self.thread = QThread()
        self.worker = WikiWorker(event_title, event_text)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.process_finished)
        self.worker.error.connect(self.process_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    
    @Slot(str)
    def update_progress(self, progress_text):
        self.progress_label.setText(progress_text)
    
    @Slot(str)
    def process_finished(self, event_title):
        self.progress_label.setText("[출력이 완료되었습니다.]")
        self.submit_btn.setEnabled(True)
        self.parent().add_wiki_button(event_title)
    
    @Slot(str)
    def process_error(self, error_msg):
        self.progress_label.setText("")
        self.history_view.appendPlainText(f"오류 발생: {error_msg}")
        self.submit_btn.setEnabled(True)

# 설정 패널 위젯 (좌측 DockWidget 내)
class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # LLM API 선택
        self.layout.addWidget(QLabel("LLM 선택"))
        self.api_combo = QComboBox()
        self.api_combo.addItems(["OpenAI(미구현)", "Gemini"])
        self.layout.addWidget(self.api_combo)
        
        # API Key 입력
        self.layout.addWidget(QLabel("API Key"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("API Key 입력")
        self.layout.addWidget(self.api_key_edit)
        
        # Max Tokens 설정
        self.layout.addWidget(QLabel("Max Tokens"))
        self.max_token_spin = QSpinBox()
        self.max_token_spin.setRange(1, 32000)
        self.max_token_spin.setValue(2048)
        self.layout.addWidget(self.max_token_spin)
        
        # 저장 버튼
        self.save_btn = QPushButton("설정 저장")
        self.layout.addWidget(self.save_btn)
        
        # 버튼 추가 영역 (Wiki 버튼들이 추가될 영역)
        self.button_area = QVBoxLayout()
        self.layout.addLayout(self.button_area)
        
        self.layout.addStretch()
        self.save_btn.clicked.connect(self.save_settings)
    
    def load_settings(self):
        settings = load_settings()
        self.api_key_edit.setText(settings.get("api_key", ""))
        self.max_token_spin.setValue(settings.get("max_tokens", 2048))
        api_type = settings.get("api_type", "Gemini")
        index = self.api_combo.findText(api_type)
        if index != -1:
            self.api_combo.setCurrentIndex(index)
    
    def save_settings(self):
        settings = {
            "api_key": self.api_key_edit.text().strip(),
            "max_tokens": self.max_token_spin.value(),
            "api_type": self.api_combo.currentText()
        }
        save_settings(settings)
        QMessageBox.information(self, "저장", "설정이 저장되었습니다.")

# 메인 윈도우
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("생성형 위키 프로그램")
        self.setGeometry(100, 100, 800, 600)
        
        self.central_widget = MainCentralWidget()
        self.setCentralWidget(self.central_widget)
        
        self.settings_dock = QDockWidget("", self)
        self.settings_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        gear_icon = QIcon.fromTheme("preferences-system")
        if gear_icon.isNull():
            gear_icon = QIcon("gear.png")
        self.settings_dock.setWindowIcon(gear_icon)
        self.settings_widget = SettingsWidget()
        self.settings_dock.setWidget(self.settings_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.settings_dock)
        self.settings_dock.setMinimumWidth(50)
        self.settings_dock.setMaximumWidth(250)
        
        self.settings_widget.load_settings()
        self.apply_styles()
    
    def add_wiki_button(self, event_title):
        btn = QPushButton(event_title)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath("wiki.html"))))
        self.settings_widget.button_area.addWidget(btn)
    
    def apply_styles(self):
        style_sheet = """
        QMainWindow {
            background-color: #f2f2f2;
        }
        QWidget {
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        QLineEdit, QPlainTextEdit, QSpinBox {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 6px;
            background-color: #ffffff;
        }
        QPushButton {
            background-color: #007acc;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 12px;
        }
        QPushButton:hover {
            background-color: #005a9c;
        }
        QLabel {
            margin-bottom: 4px;
        }
        QDockWidget {
            border: 1px solid #ccc;
            background-color: #ffffff;
        }
        QDockWidget::title {
            background: #007acc;
            color: white;
            text-align: center;
        }
        """
        self.setStyleSheet(style_sheet)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
