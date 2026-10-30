from pathlib import Path
import os

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QFileDialog, QFrame, QMessageBox
)

from core.database import SearchDatabase
from core.indexer import index_pdf_folder


class IndexWorker(QThread):
    finished_indexing = Signal(int, int, list)
    progress = Signal(str)

    def __init__(self, folders):
        super().__init__()
        self.folders = folders

    def run(self):
        total_pdfs = 0
        total_pages = 0
        errors = []
        for folder in self.folders:
            self.progress.emit(f"Indeksowanie: {folder}")
            pdfs, pages, folder_errors = index_pdf_folder(
                folder, lambda name, page, count: self.progress.emit(
                    f"{name}: strona {page}/{count}"
                )
            )
            total_pdfs += pdfs
            total_pages += pages
            errors.extend(folder_errors)
        self.finished_indexing.emit(total_pdfs, total_pages, errors)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileLens")
        self.resize(1120, 720)
        self.setMinimumSize(820, 560)
        self.selected_folders = []
        self.worker = None
        self._build_ui()
        self._refresh_index_count()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 18)
        side.setSpacing(12)
        brand = QLabel("FileLens")
        brand.setObjectName("brand")
        side.addWidget(brand)
        tagline = QLabel("Twoje dokumenty.\nWyszukiwane lokalnie.")
        tagline.setObjectName("muted")
        side.addWidget(tagline)
        side.addSpacing(22)
        for label, active in (
            ("⌕  Wyszukiwarka", True),
            ("▣  Indeksowane foldery", False),
            ("⚙  Ustawienia", False),
            ("ⓘ  O aplikacji", False),
        ):
            button = QPushButton(label)
            button.setObjectName("navActive" if active else "navButton")
            side.addWidget(button)
        side.addStretch()
        privacy = QLabel("●  Pliki pozostają na tym komputerze")
        privacy.setObjectName("privacy")
        privacy.setWordWrap(True)
        side.addWidget(privacy)
        root.addWidget(side)

        content = QWidget()
        content.setObjectName("content")
        body = QVBoxLayout(content)
        body.setContentsMargins(34, 28, 34, 28)
        body.setSpacing(16)

        top = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Wyszukiwarka dokumentów")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Przeszukuj tekst w plikach PDF zapisanych na komputerze.")
        subtitle.setObjectName("muted")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        top.addLayout(heading)
        top.addStretch()
        self.folder_button = QPushButton("＋  Dodaj folder")
        self.folder_button.setObjectName("primaryButton")
        self.folder_button.clicked.connect(self.add_folder)
        top.addWidget(self.folder_button)
        self.index_button = QPushButton("Indeksuj PDF")
        self.index_button.clicked.connect(self.start_indexing)
        top.addWidget(self.index_button)
        body.addLayout(top)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Wpisz słowa lub frazę, np. gwarancja na pralkę…")
        self.search_input.setMinimumHeight(46)
        self.search_input.returnPressed.connect(self.search_documents)
        search_row.addWidget(self.search_input)
        self.search_button = QPushButton("Szukaj")
        self.search_button.setMinimumHeight(46)
        self.search_button.setObjectName("primaryButton")
        self.search_button.clicked.connect(self.search_documents)
        search_row.addWidget(self.search_button)
        body.addLayout(search_row)

        filters = QHBoxLayout()
        for label in ("PDF",):
            chip = QLabel(label)
            chip.setObjectName("chip")
            filters.addWidget(chip)
        filters.addStretch()
        self.folder_count = QLabel("Nie dodano folderów")
        self.folder_count.setObjectName("muted")
        filters.addWidget(self.folder_count)
        self.index_count = QLabel("")
        self.index_count.setObjectName("muted")
        filters.addWidget(self.index_count)
        body.addLayout(filters)

        results_title = QLabel("Wyniki wyszukiwania")
        results_title.setObjectName("sectionTitle")
        body.addWidget(results_title)
        self.results = QListWidget()
        self.results.setObjectName("results")
        self.results.itemDoubleClicked.connect(self.open_result)
        body.addWidget(self.results, 1)
        self.status = QLabel("Dodaj folder zawierający pliki PDF, a następnie wybierz „Indeksuj PDF”.")
        self.status.setObjectName("status")
        body.addWidget(self.status)
        root.addWidget(content, 1)

        self.setStyleSheet("""
            QMainWindow { background: #f5f7fb; }
            #sidebar { background: #17243a; }
            #brand { color: white; font-size: 25px; font-weight: 700; }
            #muted { color: #718096; font-size: 13px; }
            #sidebar #muted { color: #aebbd0; }
            #privacy { color: #9ed8bb; font-size: 12px; }
            #content { background: #f5f7fb; }
            #pageTitle { color: #17243a; font-size: 25px; font-weight: 700; }
            #sectionTitle { color: #24344d; font-size: 16px; font-weight: 600; }
            QPushButton { border: 0; border-radius: 8px; padding: 10px 14px; color: #26364d; background: #e8edf5; }
            QPushButton:hover { background: #dce5f1; }
            #primaryButton { background: #2864d7; color: white; font-weight: 600; }
            #primaryButton:hover { background: #1f55bd; }
            #navButton { text-align: left; color: #dce5f1; background: transparent; padding: 12px; }
            #navActive { text-align: left; color: white; background: #293b57; padding: 12px; }
            QLineEdit { background: white; border: 1px solid #d8e0eb; border-radius: 9px; padding: 0 14px; font-size: 14px; color: #24344d; }
            QLineEdit:focus { border: 1px solid #2864d7; }
            #chip { background: #e7edf7; color: #40536e; border-radius: 12px; padding: 5px 11px; font-size: 11px; font-weight: 700; }
            #results { background: white; border: 1px solid #e0e6ef; border-radius: 10px; padding: 12px; color: #52627a; }
            #status { color: #718096; font-size: 12px; }
        """)

    def _refresh_index_count(self):
        try:
            self.index_count.setText(f"Zaindeksowane strony: {SearchDatabase().count_pages()}")
        except Exception:
            self.index_count.setText("")

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder zawierający pliki PDF")
        if not folder:
            return
        path = str(Path(folder).resolve())
        if path not in self.selected_folders:
            self.selected_folders.append(path)
        self.folder_count.setText(f"Foldery: {len(self.selected_folders)}")
        self.status.setText(f"Dodano folder: {path}")
        self.results.clear()
        for item in self.selected_folders:
            self.results.addItem(QListWidgetItem(f"📁  {item}"))

    def start_indexing(self):
        if not self.selected_folders:
            QMessageBox.information(self, "FileLens", "Najpierw dodaj folder.")
            return
        if self.worker and self.worker.isRunning():
            return
        self.index_button.setEnabled(False)
        self.folder_button.setEnabled(False)
        self.status.setText("Rozpoczynam indeksowanie plików PDF…")
        self.worker = IndexWorker(self.selected_folders)
        self.worker.progress.connect(self.status.setText)
        self.worker.finished_indexing.connect(self.indexing_finished)
        self.worker.start()

    def indexing_finished(self, pdfs, pages, errors):
        self.index_button.setEnabled(True)
        self.folder_button.setEnabled(True)
        self._refresh_index_count()
        message = f"Zindeksowano {pdfs} plików PDF i {pages} stron."
        if errors:
            message += f" Błędy: {len(errors)}. Pierwszy: {errors[0]}"
        self.status.setText(message)

    def search_documents(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.information(self, "FileLens", "Wpisz słowa, których chcesz szukać.")
            return
        try:
            matches = SearchDatabase().search(query)
        except Exception as exc:
            QMessageBox.critical(self, "Błąd wyszukiwania", str(exc))
            return
        self.results.clear()
        if not matches:
            self.results.addItem(QListWidgetItem("Nie znaleziono pasujących fragmentów."))
            self.status.setText("Brak wyników. Sprawdź pisownię lub najpierw zaindeksuj PDF-y.")
            return
        for match in matches:
            item = QListWidgetItem(
                f"{Path(match['path']).name}  •  strona {match['page']}\n"
                f"{match['excerpt']}\n{match['path']}"
            )
            item.setData(Qt.UserRole, match["path"])
            self.results.addItem(item)
        self.status.setText(f"Znaleziono wyników: {len(matches)}. Dwuklik otwiera plik PDF.")

    def open_result(self, item):
        path = item.data(Qt.UserRole)
        if path and Path(path).exists():
            try:
                os.startfile(path)
            except Exception as exc:
                QMessageBox.warning(self, "Nie można otworzyć pliku", str(exc))
