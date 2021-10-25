import os
import sys
import webbrowser
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

        self.txt_date = ""

        # by Thread
        self.th = None
        self.btn_search.clicked.connect(self.execute)
        self.btn_go_sheet.clicked.connect(lambda: webbrowser.open(
            'https://docs.google.com/spreadsheets/d/1i9zy90_Qbr03lKZC-CYBfDKxnhWE0aPHbyQFZYqK_dE/edit#gid=0'))

        # default date is today date
        self.dateEdit.setDate(QDate.currentDate())
        # set icon
        icon = resource_path("KST.png")
        self.setWindowIcon(QIcon(icon))

    def execute(self):
        # set date
        self.txt_date = str(self.dateEdit.date().toString("yyyy.MM.dd"))
        # init progress bar
        self.progressBar.setValue(0)
        # init
        self.textBrowser.clear()
        self.label_tot_count.setText("총 개수: ")

        # read input value
        input_id = self.lineEdit_id.text()
        input_pw = self.lineEdit_pw.text()
        input_taskid = self.lineEdit_taskid.text()

        # wrong value
        if input_id == '' or input_pw == '' or input_taskid == '':
            QMessageBox.about(self, "KST", "입력을 완료하세요.")
            return

        data = {'txt_date': self.txt_date,
                'input_id': input_id,
                'input_pw': input_pw,
                'input_taskid': input_taskid}

        # button disable
        self.btn_search.setEnabled(False)

        # send data for thread(Worker)
        self.th = Worker(data, parent=self)
        self.th.thread_signal_data.connect(self.show_result)
        self.th.thread_signal_progressbar.connect(self.show_progressbar)
        self.th.start()

    def show_result(self, img_name):
        self.textBrowser.append(img_name)

    def show_progressbar(self, value):
        self.progressBar.setValue(value)


class Worker(QThread):
    thread_signal_data = pyqtSignal(str)
    thread_signal_progressbar = pyqtSignal(int)

    def __init__(self, data: dict, parent=None):
        super(Worker, self).__init__(parent)
        self.parent = parent

        self.data = data
        self.working = True

        # CVAT URL
        self.cvat_url = "http://222.97.145.216"
        # execute Chrome
        if self.parent.checkBox.isChecked():
            options.add_argument("headless")

        if getattr(sys, 'frozen', False):
            chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
            self.driver = webdriver.Chrome(chromedriver_path, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        # chrome start
        self.driver.get(self.cvat_url)
        self.driver.implicitly_wait(10)

        # img text
        self.txt_send = ''
        self.txt_date = ''
        self.txt_username = ''
        self.seg_img = 1

        self.isLogin = False

    def run(self):
        if self.working is not True:
            self.terminate()
            self.quit()

        if self.isLogin is not True:
            # send input value to chrome
            self.driver.find_element(By.ID, value='username').send_keys(self.data['input_id'])
            self.driver.find_element(By.ID, value='password').send_keys(self.data['input_pw'])

            # login
            self.driver.find_element(By.XPATH,
                                     value='//*[@id="root"]/div/div/form/div[3]/div/div/div/button').click()
            sleep(1)
            if self.driver.current_url != f"{self.cvat_url}/tasks":
                QMessageBox.about(self.parent, "KST", "로그인 실패")
                return

        self.txt_date = self.data['txt_date']

        # get username, num of image
        search_url = f"{self.cvat_url}/tasks/{self.data['input_taskid']}"
        self.driver.get(search_url)
        sleep(1)

        try:
            self.txt_username = self.driver.find_element(By.CSS_SELECTOR,
                                                         value='#root > section > main > div > div > div.cvat-task-details > div.ant-row.ant-row-start.ant-row-middle > div > h4').text
            self.seg_img = int(self.driver.find_elements(By.CLASS_NAME,
                                                         value='ant-descriptions-item-content')[1].text)
        except Exception as e:
            QMessageBox.about(self, "KST", "로그인 실패")


        # set progressbar max by segment img
        self.parent.progressBar.setMaximum(self.seg_img - 1)

        self.driver.find_element(By.XPATH,
                                 value='//*[@id="root"]/section/main/div/div/div[3]/div[2]/div/div/div/div/div/table/tbody/tr/td[1]/div/a').click()

        sleep(8)

        # for body
        element = self.driver.find_element(By.XPATH, value='//body')

        total_count = 0
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
                self.txt_send = self.txt_date + '\t' + str(i) + '\t' + str(img_name) + '\t' + self.txt_username
                self.thread_signal_data.emit(self.txt_send)

            element.send_keys('f')
            sleep(0.15)

        self.parent.btn_search.setEnabled(True)
        self.parent.label_tot_count.setText("총 개수: " + str(total_count))
        self.isLogin = True
        self.driver.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = KSTWebCrawler()
    form.show()
    app.exec_()
