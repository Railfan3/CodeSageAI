import sys
import os
import json
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, Table
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from analysis.language_detector import detect_language

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))






from PyQt6.QtCore import (
    Qt,
    QSize,
    QThread,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QFont,
    QTextOption,
    QIcon,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
    QStatusBar,
)

# Optional: modern dark theme (pip install qdarktheme)
try:
    import qdarktheme
    HAS_QDARKTHEME = True
except Exception:
    HAS_QDARKTHEME = False


# -------------------------
# Config
# -------------------------
API_BASE = os.environ.get("AI_REVIEWER_API", "http://127.0.0.1:8000")
ANALYZE_URL = "http://127.0.0.1:8000/analyze"


# Try several possible backend routes (supports your Day-4 variants)
ANALYZE_ENDPOINTS = [
    f"{API_BASE}/analyze/",        # POST {"code": "..."}
    f"{API_BASE}/analyze/code",    # POST {"code": "..."}
    f"{API_BASE}/analyze/code/",   # POST {"code": "..."}
]


CORPORATE_FONT = "Segoe UI"
MONO_FONT = "Cascadia Code"  # Fallback to Consolas if not available


# -------------------------
# Helpers
# -------------------------
def hline():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


def vspacer(h=1):
    return QSpacerItem(20, 20 * h, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)


@dataclass
class AnalysisResult:
    score: Optional[float]
    maintainability: Optional[float]
    issues: List[Dict[str, Any]]
    complexity: List[Dict[str, Any]]
    suggestions: List[str]
    file: Optional[str] = None


# -------------------------
# Background worker (no UI freeze)
# -------------------------
class AnalyzeWorker(QThread):
    finished_ok = pyqtSignal(AnalysisResult)
    failed = pyqtSignal(str)

    def __init__(self, code: str):
        super().__init__()
        self.code = code

    def run(self):
        last_err = None
        try_endpoints = ANALYZE_ENDPOINTS  # from global config
        for url in try_endpoints:
            try:
                resp = requests.post(url, json={"code": self.code}, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    analysis = data.get("analysis", data)

                    score = analysis.get("score")
                    mi = analysis.get("maintainability") or analysis.get("maintainability_index")
                    issues = analysis.get("issues", [])
                    complexity = analysis.get("complexity", [])
                    suggestions = analysis.get("suggestions", [])
                    file_name = analysis.get("file")

                    result = AnalysisResult(
                        score=score if isinstance(score, (int, float)) else None,
                        maintainability=mi if isinstance(mi, (int, float)) else None,
                        issues=issues if isinstance(issues, list) else [],
                        complexity=complexity if isinstance(complexity, list) else [],
                        suggestions=suggestions if isinstance(suggestions, list) else [],
                        file=file_name
                    )
                    self.finished_ok.emit(result)
                    return
                else:
                    last_err = f"{resp.status_code} {resp.text}"
            except Exception as e:
                  last_err = f"{type(e).__name__}: {e}"

        self.failed.emit(f"All analyze endpoints failed.\nLast error: {last_err}")



# -------------------------
# Main Window
# -------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeSage AI - A wise AI for reviewing code")
        self.setMinimumSize(1200, 760)
        self.setWindowIcon(QIcon())  # you can set a corporate icon here

        # Top-level layout
        container = QWidget()
        root = QHBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar, 0)

        # Main stack (pages)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        # Pages
        self.page_dashboard = self._build_dashboard_page()
        self.page_analyze = self._build_analyze_page()
        self.page_reports = self._build_reports_page()

        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_analyze)
        self.stack.addWidget(self.page_reports)

        self.setCentralWidget(container)

        # Menu & actions
        self._build_menu()
        self.setStatusBar(QStatusBar(self))

        # Default page
        self._goto_page(1)  # Analyze by default

    # ---- UI Builders ----
    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setFixedWidth(260)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("CodeSage AI")
        title.setObjectName("SidebarTitle")
        title.setWordWrap(True)

        font = title.font()
        font.setPointSize(25)
        font.setBold(True)
        title.setFont(font)


        subtitle = QLabel("Code Rivewer Dashboard")
        subtitle.setObjectName("SidebarSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(hline())

        self.nav = QListWidget()
        self.nav.setSpacing(6)
        self.nav.setFrameShape(QFrame.Shape.NoFrame)
        self.nav.setAlternatingRowColors(False)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.addItem(QListWidgetItem("Dashboard"))
        
        self.nav.addItem(QListWidgetItem("Analyze Code"))
        self.nav.addItem(QListWidgetItem("Reports"))
        self.nav.setCurrentRow(1)
        self.nav.currentRowChanged.connect(self._goto_page)
        layout.addWidget(self.nav)

        layout.addStretch(1)

        # Theme toggle
        theme_bar = QHBoxLayout()
        theme_label = QLabel("Theme")
        theme_toggle = QToolButton()
        theme_toggle.setText("Toggle Dark/Light")
        theme_toggle.clicked.connect(self._toggle_theme)
        theme_bar.addWidget(theme_label)
        theme_bar.addStretch(1)
        theme_bar.addWidget(theme_toggle)
        layout.addLayout(theme_bar)

        return side

    def _build_header(self, title: str, subtitle: str) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 8)
        h1 = QLabel(title)
        h1.setObjectName("H1")
        h2 = QLabel(subtitle)
        h2.setObjectName("H2")
        l.addWidget(h1)
        l.addWidget(h2)
        l.addWidget(hline())
        return w

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.addWidget(self._build_header("Dashboard", "Overview & quick stats"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        self.card_score = self._metric_card("Last Score", "--/100")
        self.card_mi = self._metric_card("Maintainability", "--")
        self.card_issues = self._metric_card("Issues Found", "--")
        self.card_complex = self._metric_card("Complex Functions", "--")

        grid.addWidget(self.card_score, 0, 0)
        grid.addWidget(self.card_mi, 0, 1)
        grid.addWidget(self.card_issues, 1, 0)
        grid.addWidget(self.card_complex, 1, 1)

        outer.addLayout(grid)
        outer.addStretch(1)
        return page

    def _metric_card(self, title: str, value: str) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(6)
        t = QLabel(title)
        t.setObjectName("CardTitle")
        val = QLabel(value)
        val.setObjectName("CardValue")
        v.addWidget(t)
        v.addWidget(val)
        v.addStretch(1)
        # store reference for later updates
        card.title_label = t
        card.value_label = val
        return card

    def _build_analyze_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.addWidget(self._build_header("Analyze Code", "Paste code, load from file, and run analysis"))

        # Top controls
        top = QHBoxLayout()
        self.btn_load = QPushButton("Load .py file")
        self.btn_clear = QPushButton("Clear")
        self.btn_analyze = QPushButton("Run Analysis")
        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_export_html = QPushButton("Export HTML")
        self.btn_export_json = QPushButton("Export JSON")
        

        self.btn_load.setStyleSheet("color: white; background-color: #0078D7; font-weight: bold;")
        self.btn_clear.setStyleSheet("color: red; font-weight: bold;")
        self.btn_analyze.setStyleSheet("color: white; background-color: green; font-weight: bold;")
        self.btn_export_pdf.setStyleSheet("color: blue; font-weight: bold;")
        self.btn_export_html.setStyleSheet("color: #ff6600; font-weight: bold;")
        self.btn_export_json.setStyleSheet("color: #009688; font-weight: bold;")

        self.btn_load.clicked.connect(self._load_file)
        self.btn_clear.clicked.connect(self._clear_editor)
        self.btn_analyze.clicked.connect(self._run_analysis)
        self.btn_export_pdf.clicked.connect(lambda: self._export_report("pdf"))
        self.btn_export_html.clicked.connect(lambda: self._export_report("html"))
        self.btn_export_json.clicked.connect(lambda: self._export_report("json"))

        top.addWidget(self.btn_load)
        top.addWidget(self.btn_clear)
        top.addStretch(1)
        top.addWidget(self.btn_export_pdf)
        top.addWidget(self.btn_export_html)
        top.addWidget(self.btn_export_json)
        top.addWidget(self.btn_analyze)


        outer.addLayout(top)

        # Split: editor (left) | results (right)
        body = QHBoxLayout()
        body.setSpacing(18)

        # Editor panel
        editor_panel = QVBoxLayout()
        lbl = QLabel("Source Code")
        editor_panel.addWidget(lbl)
        self.editor = QPlainTextEdit()
        self.editor.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(' '))
        mono = QFont(MONO_FONT, 11)
        if not mono.exactMatch():
            mono = QFont("Consolas", 11)
        self.editor.setFont(mono)
        self.editor.setPlaceholderText("# Paste your Python code here or click 'Load .py file' ...")
        editor_panel.addWidget(self.editor, 1)
        left = QWidget()
        left.setLayout(editor_panel)
        left.setMinimumWidth(500)

        # Results panel (scrollable)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right = QWidget()
        right_scroll.setWidget(right)
        r = QVBoxLayout(right)
        r.setContentsMargins(0, 0, 0, 0)
        r.setSpacing(12)

        # KPI Row
        kpi = QHBoxLayout()
        self.kpi_score = self._kpi_box("Score", "--/100")
        self.kpi_mi = self._kpi_box("Maintainability", "--")
        self.kpi_issues = self._kpi_box("Issues", "--")
        kpi.addWidget(self.kpi_score)
        kpi.addWidget(self.kpi_mi)
        kpi.addWidget(self.kpi_issues)
        r.addLayout(kpi)
        r.addWidget(hline())

        # Issues table
        r.addWidget(QLabel("Issues"))
        self.tbl_issues = QTableWidget(0, 5)
        self.tbl_issues.setHorizontalHeaderLabels(["Type", "Message", "Path", "Line", "Column"])
        self.tbl_issues.setMinimumHeight(100)
        self.tbl_issues.horizontalHeader().setStretchLastSection(True)
        self.tbl_issues.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        r.addWidget(self.tbl_issues)
        
        # Complexity table
        r.addWidget(QLabel("Complexity"))
        self.tbl_complex = QTableWidget(0, 3)
        self.tbl_complex.setHorizontalHeaderLabels(["Function", "Line", "Rank/Score"])
        self.tbl_complex.setMinimumHeight(100)
        self.tbl_complex.horizontalHeader().setStretchLastSection(True)
        self.tbl_complex.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        r.addWidget(self.tbl_complex)
        

        # Suggestions list
        r.addWidget(QLabel("Suggestions"))
        self.suggest_list = QTableWidget(0, 1)
        self.suggest_list.setMinimumHeight(100)
        self.suggest_list.setHorizontalHeaderLabels(["Suggestion"])
        self.suggest_list.horizontalHeader().setStretchLastSection(True)
        self.suggest_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        r.addWidget(self.suggest_list)
        

        r.addItem(vspacer(2))

        body.addWidget(left, 1)
        body.addWidget(right_scroll, 1)

        outer.addLayout(body)
        return page

    def _kpi_box(self, title: str, value: str) -> QWidget:
        box = QFrame()
        box.setObjectName("KPI")
        v = QVBoxLayout(box)
        v.setContentsMargins(12, 12, 12, 12)
        t = QLabel(title)
        t.setObjectName("KPI_Title")
        val = QLabel(value)
        val.setObjectName("KPI_Value")
        v.addWidget(t)
        v.addWidget(val)
        return box

    def _build_reports_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.addWidget(self._build_header("Reports", "Open generated PDF/HTML/JSON reports"))
        info = QLabel(
            "Reports are generated when you click **Export PDF** or **Export HTML** or **Export JSON** on the Analyze page.\n"
            "You can find them under the backend's configured reports directory, or choose a location when exporting."
        )
        info.setWordWrap(True)
        outer.addWidget(info)
        outer.addStretch(1)
        return page

    def _build_menu(self):
        mbar = self.menuBar()
        file_menu = mbar.addMenu("&File")
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = mbar.addMenu("&View")
        act_theme = QAction("Toggle Dark/Light", self)
        act_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(act_theme)

        help_menu = mbar.addMenu("&Help")
        act_about = QAction("About", self)
        act_about.triggered.connect(self._about)
        help_menu.addAction(act_about)

    # ---- Actions ----
    def _about(self):
        QMessageBox.information(
            self,
            "About",
            "CodeSage AI — Professional PyQt6 Frontend\n"
            "Modern dashboard UI that connects to FastAPI backend."
        )

    def _toggle_theme(self):
        if HAS_QDARKTHEME:
            # Toggle between "dark" and "light"
            current = QApplication.instance().property("app_theme") or "dark"
            new_theme = "light" if current == "dark" else "dark"
            QApplication.instance().setProperty("app_theme", new_theme)
            self.setStyleSheet(qdarktheme.load_stylesheet(new_theme))
        else:
            # Minimal fallback: invert palette by switching Fusion style role
            # (kept simple; recommend installing qdarktheme for best experience)
            QMessageBox.information(self, "Theme", "Install 'qdarktheme' for theme toggling:\n\npip install qdarktheme")

    def _goto_page(self, idx: int):
        self.stack.setCurrentIndex(idx)

    def _clear_editor(self):
        self.editor.clear()

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Python file",
            os.path.expanduser("~"),
            "Python Files (*.py)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.statusBar().showMessage(f"Loaded {path}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    def _run_analysis(self):
         code = self.editor.toPlainText().strip()
         if not code:
             QMessageBox.warning(self, "Empty", "Please paste code or load a .py file first.")
             return

    # Disable just the Run button and show busy cursor
         self.btn_analyze.setEnabled(False)
         QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
         self.statusBar().showMessage("Analyzing...")

         self.worker = AnalyzeWorker(code)
         self.worker.finished_ok.connect(self._on_analysis_ok)
         self.worker.failed.connect(self._on_analysis_failed)
         self.worker.start()


    def _on_analysis_ok(self, result: AnalysisResult):
        self.btn_analyze.setEnabled(True)
        QApplication.restoreOverrideCursor()
        self.statusBar().clearMessage()

        # Update dashboard cards
        self.card_score.value_label.setText(
            f"{result.score:.2f}/100" if result.score is not None else "--/100"
        )
        self.card_mi.value_label.setText(
            f"{result.maintainability:.2f}" if result.maintainability is not None else "--"
        )
        self.card_issues.value_label.setText(str(len(result.issues)))
        self.card_complex.value_label.setText(str(len(result.complexity)))

        # Update Analyze KPIs
        self.kpi_score.findChild(QLabel, "KPI_Value").setText(
            f"{result.score:.2f}/100" if result.score is not None else "--/100"
        )
        self.kpi_mi.findChild(QLabel, "KPI_Value").setText(
            f"{result.maintainability:.2f}" if result.maintainability is not None else "--"
        )
        self.kpi_issues.findChild(QLabel, "KPI_Value").setText(str(len(result.issues)))

        # Fill issues table
        self.tbl_issues.setRowCount(0)
        for issue in result.issues:
            row = self.tbl_issues.rowCount()
            self.tbl_issues.insertRow(row)
            self.tbl_issues.setItem(row, 0, QTableWidgetItem(str(issue.get("type", ""))))
            self.tbl_issues.setItem(row, 1, QTableWidgetItem(str(issue.get("message", ""))))
            self.tbl_issues.setItem(row, 2, QTableWidgetItem(str(issue.get("path", ""))))
            self.tbl_issues.setItem(row, 3, QTableWidgetItem(str(issue.get("line", ""))))
            self.tbl_issues.setItem(row, 4, QTableWidgetItem(str(issue.get("column", ""))))

        # Fill complexity table (supports both dicts and objects)
        self.tbl_complex.setRowCount(0)
        for comp in result.complexity:
            name = getattr(comp, "name", comp.get("name") if isinstance(comp, dict) else "")
            lineno = getattr(comp, "lineno", comp.get("lineno") if isinstance(comp, dict) else "")
            rank = getattr(comp, "rank", comp.get("rank") if isinstance(comp, dict) else comp)
            row = self.tbl_complex.rowCount()
            self.tbl_complex.insertRow(row)
            self.tbl_complex.setItem(row, 0, QTableWidgetItem(str(name)))
            self.tbl_complex.setItem(row, 1, QTableWidgetItem(str(lineno)))
            self.tbl_complex.setItem(row, 2, QTableWidgetItem(str(rank)))

        # Fill suggestions
        self.suggest_list.setRowCount(0)
        for s in result.suggestions:
            row = self.suggest_list.rowCount()
            self.suggest_list.insertRow(row)
            self.suggest_list.setItem(row, 0, QTableWidgetItem(str(s)))

        msg = QMessageBox(self)
        msg.setWindowTitle("Done")
        msg.setText("Analysis completed successfully.")

# Style the message box text and button
        msg.setStyleSheet("""
    QMessageBox {
        color: #00ffcc;            /* Text color */
        font-weight: bold;         /* Bold text */
        font-size: 12pt;           /* Bigger text */
    }
    QPushButton {
        color: white;              /* Button text color */
        background-color: #0078d7; /* Button background */
        padding: 6px 12px;         /* Button padding */
        border-radius: 6px;        /* Rounded corners */
    }
    QPushButton:hover {
        background-color: #005a9e; /* Hover effect */
    }
""")

        msg.exec()

        

    def _on_analysis_failed(self, error: str):
        self.btn_analyze.setEnabled(True)
        QApplication.restoreOverrideCursor()
        self.statusBar().clearMessage()
        QMessageBox.critical(self, "Analysis Failed", error)

        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch

    def _export_report(self, fmt: str):
       """Export analysis as PDF, HTML, or JSON with professional formatting."""
       code = self.editor.toPlainText().strip()
       if not code:
        QMessageBox.warning(self, "Empty", "Please paste code or load a .py file first.")
        return

    # Fetch analysis from backend
       try:
        resp = requests.post(ANALYZE_URL, json={"code": code}, timeout=60)
        resp.raise_for_status()
        analysis = resp.json().get("analysis", {})
       except Exception as e:
        QMessageBox.critical(self, "Export Failed", f"Could not get analysis from API:\n{e}")
        return

    # Get current file name (if loaded)
       current_file = getattr(self, "current_file", None)
       file_title = f"AI Code Review Report - {os.path.basename(current_file)}" if current_file else "AI Code Review Report"

    # ---------- PDF ----------
       if fmt == "pdf":
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", "analysis_report.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            doc = SimpleDocTemplate(path, pagesize=A4,
                                    rightMargin=30, leftMargin=30,
                                    topMargin=30, bottomMargin=30)
            styles = getSampleStyleSheet()
            story = []

            # Title
            story.append(Paragraph(f"<b>{file_title}</b>", styles["Title"]))
            story.append(Spacer(1, 20))

            # Professional Summary
            score = analysis.get("score", "N/A")
            maintainability = analysis.get("maintainability", "N/A")
            story.append(Paragraph(f"<b>Score:</b> {score}", styles["Normal"]))
            story.append(Paragraph(f"<b>Maintainability:</b> {maintainability}", styles["Normal"]))
            story.append(Spacer(1, 12))

            # Issues Table
            issues = analysis.get("issues", [])
            if issues:
                data = [["Type", "Message", "Line", "Column"]]   #"Path"
                for i in issues:
                    data.append([
                        i.get("type", ""),
                        Paragraph(i.get("message", ""), styles["Normal"]),
                        # i.get("path", ""),
                        str(i.get("line", "")),
                        str(i.get("column", "")),
                    ])
                table = Table(data, colWidths=[60, 220, 50, 50])   #80
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(Paragraph("<b>Issues</b>", styles["Heading2"]))
                story.append(table)
                story.append(Spacer(1, 20))

            # Suggestions
            suggestions = analysis.get("suggestions", [])
            if suggestions:
                story.append(Paragraph("<b>Suggestions</b>", styles["Heading2"]))
                for s in suggestions:
                    story.append(Paragraph(f"- {s}", styles["Normal"]))
                story.append(Spacer(1, 20))

            # Build PDF safely
            try:
                doc.build(story)
                QMessageBox.information(self, "Saved", f"PDF report saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{e}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{e}")



    def _render_html(self, result: Dict[str, Any]) -> str:
        """Simple corporate-styled HTML render."""
        issues = result.get("issues", [])
        complexity = result.get("complexity", [])
        suggestions = result.get("suggestions", [])
        score = result.get("score", "N/A")
        mi = result.get("maintainability") or result.get("maintainability_index")

        def esc(s):
            return (s or "").__str__().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html = []
        html.append("<!DOCTYPE html><html><head><meta charset='utf-8'>")
        html.append("<title>AI Code Review Report</title>")
        html.append("""
<style>
body { font-family: Segoe UI, system-ui, -apple-system, Arial; margin: 24px; color: #222; }
h1 { color: #1b365d; margin-bottom: 4px; }
h2 { color: #274472; margin-top: 24px; }
.card { border: 1px solid #eee; border-radius: 12px; padding: 16px; margin: 12px 0; }
.kpi { display: inline-block; padding: 12px 16px; border-radius: 10px; background:#f7f9fc; margin-right:8px; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; border-bottom: 1px solid #eee; padding: 8px; }
th { background: #f5f7fb; }
.badge { display:inline-block; padding:4px 8px; border-radius:8px; background:#eef2ff; color:#334155; font-size:12px; }
</style>
        """)
        html.append("</head><body>")
        html.append("<h1>AI Code Review Report</h1>")
        html.append("<div class='card'>")
        html.append(f"<span class='kpi'><b>Score:</b> {esc(score)} / 10</span>")
        if mi is not None:
            html.append(f"<span class='kpi'><b>Maintainability:</b> {esc(f'{mi:.2f}')}</span>")
        html.append(f"<span class='kpi'><b>Issues:</b> {len(issues)}</span>")
        html.append(f"<span class='kpi'><b>Complexity:</b> {len(complexity)}</span>")
        html.append("</div>")

        html.append("<h2>Issues</h2><div class='card'>")
        if issues:
            html.append("<table><thead><tr><th>Type</th><th>Message</th><th>Path</th><th>Line</th><th>Column</th></tr></thead><tbody>")
            for i in issues:
                html.append("<tr>")
                html.append(f"<td><span class='badge'>{esc(i.get('type',''))}</span></td>")
                html.append(f"<td>{esc(i.get('message',''))}</td>")
                html.append(f"<td>{esc(i.get('path',''))}</td>")
                html.append(f"<td>{esc(i.get('line',''))}</td>")
                html.append(f"<td>{esc(i.get('column',''))}</td>")
                html.append("</tr>")
            html.append("</tbody></table>")
        else:
            html.append("<p>No major issues found.</p>")
        html.append("</div>")

        html.append("<h2>Complexity</h2><div class='card'>")
        if complexity:
            html.append("<table><thead><tr><th>Function</th><th>Line</th><th>Rank/Score</th></tr></thead><tbody>")
            for c in complexity:
                name = getattr(c, "name", c.get("name") if isinstance(c, dict) else "")
                lineno = getattr(c, "lineno", c.get("lineno") if isinstance(c, dict) else "")
                rank = getattr(c, "rank", c.get("rank") if isinstance(c, dict) else c)
                html.append("<tr>")
                html.append(f"<td>{esc(name)}</td>")
                html.append(f"<td>{esc(lineno)}</td>")
                html.append(f"<td>{esc(rank)}</td>")
                html.append("</tr>")
            html.append("</tbody></table>")
        else:
            html.append("<p>No complexity findings.</p>")
        html.append("</div>")

        html.append("<h2>Suggestions</h2><div class='card'>")
        if suggestions:
            html.append("<ul>")
            for s in suggestions:
                html.append(f"<li>{esc(s)}</li>")
            html.append("</ul>")
        else:
            html.append("<p>Code looks clean! 🎉</p>")
        html.append("</div>")

        html.append("</body></html>")
        return "\n".join(html)


# -------------------------
# Minimal corporate QSS
# -------------------------
QSS = """
QMainWindow, QWidget {
    font-family: 'Segoe UI';
    font-size: 11pt;
}
#SidebarTitle {
    font-size: 18pt;
    font-weight: 700;
}
#SidebarSubtitle {
    color: #64748b;
    font-size: 10pt;
}
#H1 { font-size: 20pt; font-weight: 700; }
#H2 { color: #6b7280; margin-bottom: 12px; }
#Card, QFrame#Card {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    background: #ffffff;
}
#CardTitle {
    color: #6b7280;
    font-size: 10pt;
}
#CardValue {
    font-size: 22pt;
    font-weight: 800;
    color: #0f172a;
}
#KPI, QFrame#KPI {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    background: #fff;
}
#KPI_Title {
    color: #6b7280;
    font-size: 10pt;
}
#KPI_Value {
    font-size: 18pt;
    font-weight: 700;
    color: #111827;
}
QListWidget {
    background: transparent;
    border: none;
}
QListWidget::item {
    padding: 10px 12px;
    border-radius: 8px;
}
QListWidget::item:selected {
    background: #e5f0ff;
    color: #1d4ed8;
}
QPushButton {
    padding: 8px 14px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fafafa;
}
QPushButton:hover { background: #f3f4f6; }
QTableWidget {
    gridline-color: #e5e7eb;
    selection-background-color: #e5f0ff;
}
"""


# -------------------------
# App bootstrap
# -------------------------
def main():
    app = QApplication(sys.argv)

    # Theme
    if HAS_QDARKTHEME:
        # default dark (corporate feel), toggle in UI
        QApplication.instance().setProperty("app_theme", "dark")
        app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
    else:
        app.setStyleSheet(QSS)  # fallback to your custom QSS if theme not available

    win = MainWindow()
    win.show()

    sys.exit(app.exec())

from flask import Flask, render_template, request
import os
from analysis.analyzer import CodeAnalyzer
from analysis.report_generator import ReportGenerator

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    output = None
    if request.method == "POST":
        if "file" not in request.files:
            output = "[Error] No file uploaded"
        else:
            file = request.files["file"]
            if file.filename == "":
                output = "[Error] No file selected"
            else:
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(filepath)

                analyzer = CodeAnalyzer(filepath)
                raw_output = analyzer.analyze()

                report = ReportGenerator(filepath)
                output = report.format_output(raw_output)

    return render_template("index.html", output=output)





if __name__ == "__main__":
    main()
