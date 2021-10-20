from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

if __name__ == "__main__":
    search_url = "http://222.97.145.216/"

    s = Service('./chromedriver.exe')
    driver = webdriver.Chrome(service=s)
    driver.maximize_window()

    # 접속
    driver.get(search_url)

    # 아디디와 비밀번호 입력(2초 기다림)
    driver.implicitly_wait(2)
    driver.find_element(By.ID, value='username').send_keys('L050')
    driver.implicitly_wait(2)
    driver.find_element(By.ID, value='password').send_keys('!kst7412')

    # XPath를 이용해 로그인 시도
    driver.find_element(By.XPATH, value='//*[@id="root"]/div/div/form/div[3]/div/div/div/button').click()
    driver.implicitly_wait(2)

    sleep(1)

    # Task에 접속
    search_url = "http://222.97.145.216/tasks/3722/"
    driver.get(search_url)
    sleep(2)

    username = driver.find_element(By.CSS_SELECTOR,
                                   value='#root > section > main > div > div > div.cvat-task-details > div.ant-row.ant-row-start.ant-row-middle > div > h4')
    print(username.text)
    s1 = driver.find_elements(By.CLASS_NAME,
                              value='ant-descriptions-item-content')[1].text
    print(s1)

    driver.find_element(By.XPATH,
                        value='//*[@id="root"]/section/main/div/div/div[3]/div[2]/div/div/div/div/div/table/tbody/tr/td[1]/div/a').click()

    sleep(4)

    # for body
    element = driver.find_element(By.XPATH, value='//body')

    for i in range(50):
        # BeautifulSoup를 사용해 웹페이지 정보 얻어오기기
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        # 파싱시작
        class_list = soup.find('div', 'cvat-objects-sidebar-states-list')

        if class_list.text == '':
            img_name = soup.find('span', 'ant-typography ant-typography-secondary')
            print(img_name.text)

        element.send_keys('f')
