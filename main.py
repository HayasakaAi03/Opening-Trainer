from openings import MainWindow  
from PyQt5.QtWidgets import QApplication
import sys

def main():  
    App = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(App.exec())

if __name__ == '__main__':
    main()