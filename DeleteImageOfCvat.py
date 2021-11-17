import os
import sys
import chromedriver_autoinstaller
from time import sleep

# pyqt5
from PyQt5.QtCore import QThread, pyqtSignal

# webCrawling
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


class WorkerPrint(QThread):
    # signal
    thread_signal_textBrowser = pyqtSignal(str)
    thread_signal_textBrowser_wait = pyqtSignal(str)
    thread_signal_textBrowser_clear = pyqtSignal()
    thread_signal_label_tot_count = pyqtSignal(str)
    thread_signal_progressbar = pyqtSignal(int)
    thread_signal_stop = pyqtSignal()
    thread_signal_toast = pyqtSignal(str)

    def __init__(self, data: dict, parent=None):
        super(WorkerPrint, self).__init__(parent)
        self.parent = parent
        self.thread_signal_textBrowser.emit("try access...")
        # receive data
        self.data = data

        # CVAT URL
        self.cvat_url = self.data['input_url']

        self.options = webdriver.ChromeOptions()
        # execute Chrome
        if self.parent.checkBox.isChecked():
            self.options.add_argument("headless")

        # chrome drive import when using pyinstaller
        # 크롬드라이버 버전 확인
        chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
        try:
            self.thread_signal_textBrowser.emit("Chrome Driver Exist")
            if getattr(sys, 'frozen', False):
                chromedriver_path = os.path.join(sys._MEIPASS, f'./{chrome_ver}/chromedriver.exe')
                self.driver = webdriver.Chrome(chromedriver_path, options=self.options)
            else:
                self.driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options=self.options)
        except:
            self.thread_signal_textBrowser.emit("Chrome Driver Install")
            chromedriver_autoinstaller.install(True)
            self.driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe')

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
            self.driver.find_element(By.CLASS_NAME,
                                     value="ant-btn.ant-btn-primary.login-form-button").click()

            while self.driver.current_url == f"{self.cvat_url}/auth/login":
                sleep(0.5)

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

