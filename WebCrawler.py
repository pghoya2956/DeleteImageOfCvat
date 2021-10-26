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

# webCrawling
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# Qt Designer load
form_class = uic.loadUiType(resource_path("webcrawler.ui"))[0]
options = webdriver.ChromeOptions()


class KSTWebCrawler(QWidget, form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # set icon
        icon = resource_path("KST.png")
        self.setWindowIcon(QIcon(icon))

        # thread
        self.th = None

        # button listener
        self.btn_search.clicked.connect(self.execute)
        self.btn_go_sheet.clicked.connect(lambda: webbrowser.open(
            'https://docs.google.com/spreadsheets/d/1i9zy90_Qbr03lKZC-CYBfDKxnhWE0aPHbyQFZYqK_dE/edit#gid=0'))

        # default date is today date
        self.dateEdit.setDate(QDate.currentDate())

        # comboBox
        self.comboBox_url.addItem("http://222.97.145.216")
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

    def execute(self):
        # init UI
        self.init_ui()

        # read input value
        input_url = self.comboBox_url.currentText()
        input_id = self.lineEdit_id.text()
        input_pw = self.lineEdit_pw.text()
        input_taskid = self.lineEdit_taskid.text()

        # input check
        if self.input_fail(input_id, input_pw, input_taskid):
            QMessageBox.about(self, "KST", "입력을 완료하세요.")
            return

        # set button enable
        self.btn_search.setEnabled(False)

        data = {'input_url': input_url,
                'input_id': input_id,
                'input_pw': input_pw,
                'input_taskid': input_taskid}

        # send data for thread(Worker)
        self.th = Worker(data, parent=self)
        self.th.thread_signal_textBrowser.connect(self.show_textBrowser)
        self.th.thread_signal_textBrowser_wait.connect(self.show_textBrowser_wait)
        self.th.thread_signal_textBrowser_clear.connect(self.show_textBrowser_clear)
        self.th.thread_signal_progressbar.connect(self.show_progressbar)
        self.th.thread_signal_label_tot_count.connect(self.show_count)
        self.th.thread_signal_toast.connect(self.show_toast)
        self.th.thread_signal_stop.connect(self.thread_stop)

        # thread start
        self.th.start()

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
        self.th.terminate()


class Worker(QThread):
    # signal
    thread_signal_textBrowser = pyqtSignal(str)
    thread_signal_textBrowser_wait = pyqtSignal(str)
    thread_signal_textBrowser_clear = pyqtSignal()
    thread_signal_label_tot_count = pyqtSignal(str)
    thread_signal_progressbar = pyqtSignal(int)
    thread_signal_stop = pyqtSignal()
    thread_signal_toast = pyqtSignal(str)

    def __init__(self, data: dict, parent=None):
        super(Worker, self).__init__(parent)
        self.parent = parent
        self.thread_signal_textBrowser.emit("try access...")
        # receive data
        self.data = data

        # CVAT URL
        self.cvat_url = self.data['input_url']

        # execute Chrome
        if self.parent.checkBox.isChecked():
            options.add_argument("headless")

        # chrome drive import when using pyinstaller
        if getattr(sys, 'frozen', False):
            chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
            self.driver = webdriver.Chrome(chromedriver_path, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        # chrome start
        self.driver.get(self.cvat_url)
        self.driver.implicitly_wait(10)

        # img text
        self.txt_username = ''
        self.seg_img = 1

        self.isLogin = False

    def run(self):
        self.thread_signal_textBrowser.emit("Connect Cvat")
        # login
        if self.isLogin is not True:
            # send input value to chrome
            self.driver.find_element(By.ID, value='username').send_keys(self.data['input_id'])
            self.driver.find_element(By.ID, value='password').send_keys(self.data['input_pw'])

            # login
            if self.cvat_url == "http://222.97.145.216":
                self.driver.find_element(By.XPATH,
                                         value='//*[@id="root"]/div/div/form/div[3]/div/div/div/button').click()
            elif self.cvat_url == "http://192.168.0.33:8080":
                self.driver.find_element(By.XPATH,
                                         value='//*[@id="root"]/section/main/div/div/form/div[3]/div/div/div/button').click()

            sleep(1)

            if self.driver.current_url != f"{self.cvat_url}/tasks":
                self.thread_signal_toast.emit("로그인 실패")
                self.parent.btn_search.setEnabled(True)
                return

        self.thread_signal_textBrowser.emit("Login Success")
        self.isLogin = True

        try:
            # get username, num of image
            search_url = f"{self.cvat_url}/tasks/{self.data['input_taskid']}"
            self.driver.get(search_url)
            sleep(1)

            self.txt_username = self.driver.find_element(By.CSS_SELECTOR,
                                                         value='#root > section > main > div > div > div.cvat-task-details > div.ant-row.ant-row-start.ant-row-middle > div > h4').text
            self.seg_img = int(self.driver.find_elements(By.CLASS_NAME,
                                                         value='ant-descriptions-item-content')[1].text)

            # textBrowser
            self.thread_signal_textBrowser.emit("Get Data...")

            # set progressbar max by segment img
            self.parent.progressBar.setMaximum(self.seg_img - 1)

            self.driver.find_element(By.XPATH,
                                     value='//*[@id="root"]/section/main/div/div/div[3]/div[2]/div/div/div/div/div/table/tbody/tr/td[1]/div/a').click()

            # explicitly wait
            wait = "Please Wait.."
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            while soup.find('span', 'ant-typography ant-typography-secondary') == None:
                wait = wait + "."
                self.thread_signal_textBrowser_wait.emit(wait)
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                sleep(1)

            # for body
            element = self.driver.find_element(By.XPATH, value='//body')

            # check delete image
            total_count = 0
            txt_date = str(self.parent.dateEdit.date().toString("yyyy.MM.dd"))
            self.thread_signal_textBrowser_clear.emit()
            for i in range(self.seg_img):
                # BeautifulSoup를 사용해 웹페이지 정보 얻어오기
                self.thread_signal_progressbar.emit(i)
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'lxml')

                # 파싱시작
                class_list = soup.find('div', 'cvat-objects-sidebar-states-list')

                if class_list.text == '':
                    total_count = total_count + 1
                    img_name = soup.find('span', 'ant-typography ant-typography-secondary')
                    txt_send = txt_date + '\t' + str(i) + '\t' + str(img_name) + '\t' + self.txt_username
                    self.thread_signal_textBrowser.emit(txt_send)

                element.send_keys('f')
                sleep(0.1)

            self.thread_signal_label_tot_count.emit("총 개수: " + str(total_count))

        except Exception as e:
            self.thread_signal_toast.emit("Task 입력 오류")
        finally:
            self.parent.btn_search.setEnabled(True)
            self.driver.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = KSTWebCrawler()
    form.show()
    app.exec_()
