import sys
from PySide6.QtWidgets import QApplication
from ui_main import TimeTrackerUI
from database import init_db

def main():
    init_db()
    app = QApplication(sys.argv)
    window = TimeTrackerUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()