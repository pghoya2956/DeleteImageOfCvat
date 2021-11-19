import os
import sys
import webbrowser
from telnetlib import EC
from time import sleep

# pyqt5
from PyQt5.QtCore import QDate, pyqtSignal, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5 import uic

from DeleteImageOfCvat import WorkerPrint


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# Qt Designer load
form_class = uic.loadUiType(resource_path("webcrawler.ui"))[0]


class KSTWebCrawler(QWidget, form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # set icon
        icon = resource_path("KST.png")
        self.setWindowIcon(QIcon(icon))

        # thread
        self.th1 = None

        # button listener
        self.btn_search.clicked.connect(self.deleteImageOfCvat)
        self.btn_go_sheet.clicked.connect(lambda: webbrowser.open(
            'https://docs.google.com/spreadsheets/d/1i9zy90_Qbr03lKZC-CYBfDKxnhWE0aPHbyQFZYqK_dE/edit#gid=0'))

        # default date is today date
        self.dateEdit.setDate(QDate.currentDate())

        # comboBox
        self.comboBox_url.addItem("http://222.97.145.216:8001")
        self.comboBox_url.addItem("http://192.168.0.73:8080")
        self.comboBox_url.addItem("http://192.168.0.33:8080")

    def init_ui(self):
        # init
        self.textBrowser.clear()
        self.progressBar.setValue(0)
        self.label_tot_count.setText("총 개수: ")

    def input_fail(self, input_id, input_pw, input_taskid) -> bool:
        # wrong value
        if input_id == '' or input_pw == '' or input_taskid == '':
            QMessageBox.about(self, "KST", "입력을 완료하세요.")
            return True

        return False

    def deleteImageOfCvat(self):
        # init UI
        self.init_ui()

        # set button enable
        self.btn_search.setEnabled(False)

        # read input value
        input_url = self.comboBox_url.currentText()
        input_id = self.lineEdit_id.text()
        input_pw = self.lineEdit_pw.text()
        input_taskid = self.lineEdit_taskid.text()

        # input check
        if self.input_fail(input_id, input_pw, input_taskid):
            QMessageBox.about(self, "KST", "입력을 완료하세요.")
            self.btn_search.setEnabled(True)
            return

        data = {'input_url': input_url,
                'input_id': input_id,
                'input_pw': input_pw,
                'input_taskid': input_taskid}

        # send data for thread(Worker)
        self.th1 = WorkerPrint(data, parent=self)
        self.th1.thread_signal_textBrowser.connect(self.show_textBrowser)
        self.th1.thread_signal_textBrowser_wait.connect(self.show_textBrowser_wait)
        self.th1.thread_signal_textBrowser_clear.connect(self.show_textBrowser_clear)
        self.th1.thread_signal_progressbar.connect(self.show_progressbar)
        self.th1.thread_signal_label_tot_count.connect(self.show_count)
        self.th1.thread_signal_toast.connect(self.show_toast)
        self.th1.thread_signal_stop.connect(self.thread_stop)

        # thread start
        self.th1.start()

    def show_textBrowser(self, img_name):
        self.textBrowser.append(img_name)

    def show_textBrowser_wait(self, img_name):
        self.textBrowser.setPlainText(img_name)

    def show_textBrowser_clear(self):
        self.textBrowser.clear()

    def show_progressbar(self, value):
        self.progressBar.setValue(value)

    def show_count(self, string):
        self.label_tot_count.setText(string)

    def show_toast(self, string):
        QMessageBox.about(self, "KST", string)

    def thread_stop(self):
        self.th1.terminate()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = KSTWebCrawler()
    form.show()
    app.exec_()
