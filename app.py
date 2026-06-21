#!/usr/bin/env python3
"""
Voter List Extractor - Desktop App
Beautiful Python GUI for converting Telugu Voter PDF to Excel.
"""

import os
import sys
import threading
import subprocess
import platform

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFileDialog, QFrame, QSpacerItem, QSizePolicy,
    QDialog, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert_full import convert_pdf_to_excel


# ============================================================
# Signal bridge for thread-safe UI updates
# ============================================================
class ProgressSignals(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str, int, list)
    error = pyqtSignal(str)


# ============================================================
# Stylesheet
# ============================================================
STYLESHEET = """
QMainWindow {
    background-color: #0f0d1a;
}

QWidget#central {
    background-color: #0f0d1a;
}

QLabel#title {
    color: #7c3aed;
    font-size: 34px;
    font-weight: bold;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial;
}

QLabel#subtitle {
    color: #9895a8;
    font-size: 15px;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial;
}

QFrame#card {
    background-color: #1a1730;
    border: 1px solid #2d2a45;
    border-radius: 20px;
}

QLabel#fileIcon {
    font-size: 48px;
}

QLabel#fileLabel {
    color: #9895a8;
    font-size: 14px;
}

QLabel#fileLabelSelected {
    color: #f1f0f5;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#browseBtn {
    background-color: #7c3aed;
    color: white;
    font-size: 15px;
    font-weight: bold;
    padding: 12px 24px;
    border-radius: 12px;
    border: none;
}
QPushButton#browseBtn:hover {
    background-color: #6d28d9;
}
QPushButton#browseBtn:disabled {
    background-color: #3b3654;
    color: #6b6880;
}

QPushButton#convertBtn {
    background-color: #ec4899;
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 14px 24px;
    border-radius: 12px;
    border: none;
}
QPushButton#convertBtn:hover {
    background-color: #db2777;
}
QPushButton#convertBtn:disabled {
    background-color: #3b3654;
    color: #6b6880;
}

QProgressBar {
    background-color: #2d2a45;
    border-radius: 7px;
    height: 14px;
    text-align: center;
    font-size: 0px;
    border: none;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #ec4899);
    border-radius: 7px;
}

QLabel#progressLabel {
    color: #9895a8;
    font-size: 13px;
}

QLabel#statusSuccess {
    color: #22c55e;
    font-size: 14px;
    font-weight: bold;
}

QLabel#statusError {
    color: #ef4444;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#openBtn {
    background-color: #22c55e;
    color: white;
    font-size: 15px;
    font-weight: bold;
    padding: 12px 24px;
    border-radius: 12px;
    border: none;
}
QPushButton#openBtn:hover {
    background-color: #16a34a;
}

QPushButton#verifyBtn {
    background-color: #3b82f6;
    color: white;
    font-size: 15px;
    font-weight: bold;
    padding: 12px 24px;
    border-radius: 12px;
    border: none;
}
QPushButton#verifyBtn:hover {
    background-color: #2563eb;
}

QPushButton#resetBtn {
    background: none;
    border: none;
    color: #7c3aed;
    font-size: 13px;
    text-decoration: underline;
}
QPushButton#resetBtn:hover {
    color: #a78bfa;
}

QLabel#footerLabel {
    color: #6b6880;
    font-size: 12px;
}
"""


class VerifyDialog(QDialog):
    def __init__(self, samples, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verify Extracted Data")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(STYLESHEET)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("Random Verification Samples")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0f0d1a; }")
        
        content = QWidget()
        content.setStyleSheet("background-color: #0f0d1a;")
        content_layout = QVBoxLayout(content)
        
        for sample in samples:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            
            header = QLabel(f"Page {sample['page']}")
            header.setStyleSheet("color: #7c3aed; font-weight: bold;")
            card_layout.addWidget(header)
            
            img_label = QLabel()
            pixmap = QPixmap(sample['image'])
            if not pixmap.isNull():
                img_label.setPixmap(pixmap.scaledToWidth(700, Qt.TransformationMode.SmoothTransformation))
            card_layout.addWidget(img_label)
            
            text_str = "  |  ".join(filter(None, sample['text']))
            text_label = QLabel(text_str)
            text_label.setStyleSheet("color: #f1f0f5; font-size: 15px; margin-top: 10px;")
            text_label.setWordWrap(True)
            card_layout.addWidget(text_label)
            
            content_layout.addWidget(card)
            
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("convertBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

class VoterListApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voter List Extractor")
        self.setMinimumSize(700, 580)
        self.resize(700, 580)
        self.setStyleSheet(STYLESHEET)

        # State
        self.selected_pdf = None
        self.output_path = None
        self.is_processing = False

        # Signals
        self.signals = ProgressSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.finished.connect(self._on_success)
        self.signals.error.connect(self._on_error)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(0)

        # ── Title ──
        title = QLabel("Voter List Extractor")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Telugu Voter PDF  →  Formatted Excel")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(25)

        # ── Card ──
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 25)
        card_layout.setSpacing(12)

        # File icon
        file_icon = QLabel("📄")
        file_icon.setObjectName("fileIcon")
        file_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(file_icon)

        # File label
        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("fileLabel")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.file_label)

        card_layout.addSpacing(8)

        # Browse button
        self.browse_btn = QPushButton("📂   Browse PDF File")
        self.browse_btn.setObjectName("browseBtn")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.clicked.connect(self._browse_file)

        browse_layout = QHBoxLayout()
        browse_layout.addSpacing(80)
        browse_layout.addWidget(self.browse_btn)
        browse_layout.addSpacing(80)
        card_layout.addLayout(browse_layout)

        card_layout.addSpacing(8)

        # Convert button
        self.convert_btn = QPushButton("⚡   Convert to Excel")
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self._start_conversion)

        convert_layout = QHBoxLayout()
        convert_layout.addSpacing(60)
        convert_layout.addWidget(self.convert_btn)
        convert_layout.addSpacing(60)
        card_layout.addLayout(convert_layout)

        card_layout.addSpacing(12)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        pb_layout = QHBoxLayout()
        pb_layout.addSpacing(30)
        pb_layout.addWidget(self.progress_bar)
        pb_layout.addSpacing(30)
        card_layout.addLayout(pb_layout)

        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.progress_label)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusSuccess")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        card_layout.addWidget(self.status_label)

        # Open button (hidden initially)
        self.open_btn = QPushButton("📊   Open Excel File")
        self.open_btn.setObjectName("openBtn")
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.clicked.connect(self._open_output)
        
        self.verify_btn = QPushButton("👁️   Verify Data")
        self.verify_btn.setObjectName("verifyBtn")
        self.verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.verify_btn.clicked.connect(self._verify_data)

        open_layout = QHBoxLayout()
        open_layout.addSpacing(30)
        open_layout.addWidget(self.open_btn)
        open_layout.addWidget(self.verify_btn)
        open_layout.addSpacing(30)
        
        self.open_layout_widget = QWidget()
        self.open_layout_widget.setLayout(open_layout)
        self.open_layout_widget.setVisible(False)
        card_layout.addWidget(self.open_layout_widget)

        # Convert another button (hidden initially)
        self.reset_btn = QPushButton("Convert Another File")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self._reset)
        self.reset_btn.setVisible(False)
        card_layout.addWidget(self.reset_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)

        layout.addSpacing(10)

        # ── Footer ──
        footer = QLabel("✨ Direct text extraction  •  Zero OCR  •  Perfect quality  •  Lightning fast")
        footer.setObjectName("footerLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    # ── Actions ──

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Telugu Voter List PDF",
            "",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if path:
            self.selected_pdf = path
            name = os.path.basename(path)
            self.file_label.setText(f"📎  {name}")
            self.file_label.setObjectName("fileLabelSelected")
            self.file_label.setStyleSheet(self.file_label.styleSheet())  # Force refresh
            self.file_label.style().unpolish(self.file_label)
            self.file_label.style().polish(self.file_label)
            self.convert_btn.setEnabled(True)
            self.status_label.setText("")
            self.open_layout_widget.setVisible(False)
            self.open_btn.setVisible(False)
            self.reset_btn.setVisible(False)
            self.progress_bar.setValue(0)
            self.progress_label.setText("")

    def _start_conversion(self):
        if self.is_processing or not self.selected_pdf:
            return

        self.is_processing = True
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("⏳   Converting...")
        self.browse_btn.setEnabled(False)
        self.status_label.setText("")
        self.open_layout_widget.setVisible(False)
        self.open_btn.setVisible(False)
        self.reset_btn.setVisible(False)
        self.progress_bar.setValue(0)

        # Prompt for save location
        default_name = f"{os.path.splitext(os.path.basename(self.selected_pdf))[0]}_VoterList.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File As",
            os.path.join(os.path.dirname(self.selected_pdf), default_name),
            "Excel Files (*.xlsx)"
        )
        if not save_path:
            self.convert_btn.setEnabled(True)
            self.convert_btn.setText("⚡   Convert to Excel")
            self.browse_btn.setEnabled(True)
            self.is_processing = False
            return
            
        self.output_path = save_path

        thread = threading.Thread(target=self._run_conversion, daemon=True)
        thread.start()

    def _run_conversion(self):
        try:
            def progress_callback(percent, message):
                self.signals.progress.emit(percent, message)

            out_path, num_rows, samples = convert_pdf_to_excel(
                self.selected_pdf,
                self.output_path,
                progress_callback=progress_callback,
            )
            self.signals.finished.emit(out_path, num_rows, samples)

        except Exception as e:
            self.signals.error.emit(str(e))

    def _on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"{percent}%  •  {message}")

    def _on_success(self, path, num_rows, samples):
        self.is_processing = False
        self.current_samples = samples
        self.progress_bar.setValue(100)
        self.progress_label.setText("100%  •  Done!")

        self.status_label.setObjectName("statusSuccess")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.status_label.setText(f"✅  Success! Extracted {num_rows} voters.\nSaved to: {os.path.basename(path)}")

        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("⚡   Convert to Excel")
        self.browse_btn.setEnabled(True)

        self.open_btn.setVisible(True)
        self.open_layout_widget.setVisible(True)
        self.reset_btn.setVisible(True)

    def _on_error(self, error_msg):
        self.is_processing = False
        self.progress_bar.setValue(0)
        self.progress_label.setText("")

        self.status_label.setObjectName("statusError")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.status_label.setText(f"❌  Error: {error_msg}")

        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("⚡   Convert to Excel")
        self.browse_btn.setEnabled(True)

    def _verify_data(self):
        if not hasattr(self, "current_samples") or not self.current_samples:
            return
        dlg = VerifyDialog(self.current_samples, self)
        dlg.exec()

    def _open_output(self):
        if self.output_path and os.path.exists(self.output_path):
            system = platform.system()
            if system == "Linux":
                subprocess.Popen(["xdg-open", self.output_path])
            elif system == "Darwin":
                subprocess.Popen(["open", self.output_path])
            elif system == "Windows":
                os.startfile(self.output_path)

    def _reset(self):
        self.selected_pdf = None
        self.output_path = None
        self.file_label.setText("No file selected")
        self.file_label.setObjectName("fileLabel")
        self.file_label.style().unpolish(self.file_label)
        self.file_label.style().polish(self.file_label)
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("⚡   Convert to Excel")
        self.progress_bar.setValue(0)
        self.progress_label.setText("")
        self.status_label.setText("")
        self.open_layout_widget.setVisible(False)
        self.open_btn.setVisible(False)
        self.reset_btn.setVisible(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0f0d1a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f1f0f5"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1a1730"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f1f0f5"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1a1730"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f1f0f5"))
    app.setPalette(palette)

    window = VoterListApp()
    window.show()
    sys.exit(app.exec())
