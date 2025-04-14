import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeView, QListView,
                             QSplitter, QMenu, QAction, QInputDialog, QMessageBox,
                             QLabel, QVBoxLayout, QWidget, QTextEdit, QTabWidget,
                             QToolBar, QDialog, QLineEdit, QPushButton, QHBoxLayout,
                             QFileSystemModel, QAbstractItemView)
from PyQt5.QtCore import Qt, QDir, QModelIndex, QAbstractItemModel, QVariant
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence


class FileSystemModel(QAbstractItemModel):
    def __init__(self, root_path=""):
        super().__init__()
        self.root_path = root_path
        self.contents = []
        self.refresh_contents()

    def refresh_contents(self):
        self.beginResetModel()
        try:
            self.contents = sorted(os.listdir(self.root_path))
        except Exception:
            self.contents = []
        self.endResetModel()

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            return self.createIndex(row, column, None)
        return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.contents)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return self.contents[index.row()]
        return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return "Name"
        return QVariant()

    def filePath(self, index):
        if index.isValid():
            return os.path.join(self.root_path, self.contents[index.row()])
        return self.root_path

    def isDir(self, index):
        if index.isValid():
            path = os.path.join(self.root_path, self.contents[index.row()])
            return os.path.isdir(path)
        return True


class TextEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_edit = QTextEdit()
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as file:
                self.text_edit.setPlainText(file.read())
        except Exception as e:
            self.text_edit.setPlainText(f"Error loading file: {str(e)}")

    def save_file(self, path):
        try:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(self.text_edit.toPlainText())
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
            return False


class ImageViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def load_image(self, path):
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.image_label.setText("Unsupported image format")
        except Exception as e:
            self.image_label.setText(f"Error loading image: {str(e)}")


class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python File Manager")
        self.setGeometry(100, 100, 1024, 768)

        # Clipboard
        self.clipboard = {'files': [], 'operation': None}

        # Create UI
        self.create_models()
        self.create_views()
        self.create_toolbar()
        self.create_statusbar()
        self.create_tabs()

        # Connect signals
        self.connect_signals()

        # Navigate to home
        self.navigate_to_home()

    def create_models(self):
        self.model = FileSystemModel()

    def create_views(self):
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)

        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.tree_view)
        self.splitter.addWidget(self.list_view)
        self.splitter.setSizes([200, 600])

    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Navigation
        home_action = QAction(QIcon.fromTheme('go-home'), 'Home', self)
        home_action.triggered.connect(self.navigate_to_home)
        toolbar.addAction(home_action)

        back_action = QAction(QIcon.fromTheme('go-previous'), 'Back', self)
        back_action.triggered.connect(self.navigate_back)
        toolbar.addAction(back_action)

        # File operations
        copy_action = QAction(QIcon.fromTheme('edit-copy'), 'Copy', self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_files)
        toolbar.addAction(copy_action)

        paste_action = QAction(QIcon.fromTheme('edit-paste'), 'Paste', self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_files)
        toolbar.addAction(paste_action)

        delete_action = QAction(QIcon.fromTheme('edit-delete'), 'Delete', self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self.delete_selected)
        toolbar.addAction(delete_action)

    def create_statusbar(self):
        self.status_bar = self.statusBar()
        self.path_label = QLabel()
        self.status_bar.addPermanentWidget(self.path_label)

    def create_tabs(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        layout.addWidget(self.tab_widget)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def connect_signals(self):
        self.tree_view.clicked.connect(self.navigate_to)
        self.list_view.doubleClicked.connect(self.open_item)
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)

    def navigate_to_home(self):
        self.model.root_path = QDir.homePath()
        self.model.refresh_contents()
        self.update_statusbar(self.model.root_path)

    def navigate_to(self, index):
        path = self.model.filePath(index)
        if self.model.isDir(index):
            self.model.root_path = path
            self.model.refresh_contents()
            self.update_statusbar(path)

    def navigate_back(self):
        parent = os.path.dirname(self.model.root_path)
        if parent != self.model.root_path:
            self.model.root_path = parent
            self.model.refresh_contents()
            self.update_statusbar(parent)

    def update_statusbar(self, path):
        self.path_label.setText(path)

    def open_item(self, index):
        path = self.model.filePath(index)
        if self.model.isDir(index):
            self.navigate_to(index)
        else:
            self.open_file(path)

    def open_file(self, path):
        try:
            if path.lower().endswith(('.txt', '.py', '.html', '.css', '.js', '.json', '.md')):
                self.open_text_editor(path)
            elif path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
                self.open_image_viewer(path)
            else:
                if sys.platform == 'linux':
                    os.system(f'xdg-open "{path}"')
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")

    def open_text_editor(self, path):
        editor = TextEditor()
        editor.load_file(path)
        self.tab_widget.addTab(editor, os.path.basename(path))

    def open_image_viewer(self, path):
        viewer = ImageViewer()
        viewer.load_image(path)
        self.tab_widget.addTab(viewer, os.path.basename(path))

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def show_context_menu(self, pos):
        menu = QMenu()
        index = self.list_view.indexAt(pos)

        if index.isValid():
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.open_item(index))
            menu.addAction(open_action)

            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_file(index))
            menu.addAction(rename_action)

            menu.addSeparator()

            copy_action = QAction("Copy", self)
            copy_action.triggered.connect(self.copy_files)
            menu.addAction(copy_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_selected)
            menu.addAction(delete_action)

            menu.exec_(self.list_view.mapToGlobal(pos))

    def get_selected_paths(self):
        paths = []
        for index in self.list_view.selectedIndexes():
            if index.isValid():
                paths.append(self.model.filePath(index))
        return paths

    def copy_files(self):
        paths = self.get_selected_paths()
        if paths:
            self.clipboard = {'files': paths, 'operation': 'copy'}
            self.status_bar.showMessage(f"Copied {len(paths)} items", 3000)

    def paste_files(self):
        if not self.clipboard['files']:
            return

        dest_dir = self.model.root_path
        for src_path in self.clipboard['files']:
            try:
                dest_path = os.path.join(dest_dir, os.path.basename(src_path))
                if self.clipboard['operation'] == 'copy':
                    if os.path.isdir(src_path):
                        self.copy_dir(src_path, dest_path)
                    else:
                        self.copy_file(src_path, dest_path)
                elif self.clipboard['operation'] == 'cut':
                    os.rename(src_path, dest_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to paste: {str(e)}")

        self.clipboard = {'files': [], 'operation': None}
        self.model.refresh_contents()

    def copy_file(self, src, dest):
        with open(src, 'rb') as fsrc, open(dest, 'wb') as fdest:
            fdest.write(fsrc.read())

    def copy_dir(self, src, dest):
        os.makedirs(dest, exist_ok=True)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dest, item)
            if os.path.isdir(s):
                self.copy_dir(s, d)
            else:
                self.copy_file(s, d)

    def delete_selected(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        reply = QMessageBox.question(
            self, 'Confirm Delete',
            f"Delete {len(paths)} selected items?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for path in paths:
                try:
                    if os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete: {str(e)}")

            self.model.refresh_contents()

    def rename_file(self, index):
        old_path = self.model.filePath(index)
        new_name, ok = QInputDialog.getText(
            self, 'Rename',
            'New name:',
            text=os.path.basename(old_path)
        )

        if ok and new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.model.refresh_contents()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to rename: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Установите эти пакеты вручную:
    # sudo dnf install libcanberra-gtk3 PackageKit-gtk3-module

    window = FileManager()
    window.show()
    sys.exit(app.exec_())  # <-- Только одна эта строка должна быть здесь
