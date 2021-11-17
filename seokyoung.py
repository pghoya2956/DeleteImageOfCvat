import sys
import os
import zipfile
import shutil
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


url = 'http://192.168.0.73:8080/'
folder_name = 'data' + datetime.today().strftime("%Y%m%d")
del_file = os.path.expanduser('~') + '\\Desktop\\' + folder_name + '\\del.txt'
desktop_dir = os.path.expanduser('~') + '\\Desktop\\'
dir = desktop_dir
downdir = os.path.expanduser('~') + '\\Downloads\\'


def _enable_download_in_headless_chrome(driver: webdriver, download_dir: str):
    """
    :param driver: 크롬 드라이버 인스턴스
    :param download_dir: 파일 다운로드 경로
    """
    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

    params = {
        'cmd': 'Page.setDownloadBehavior',
        'params': {
            'behavior': 'allow',
            'downloadPath': download_dir
        }
    }
    driver.execute("send_command", params)


def _close_chrome(chrome: webdriver):
    """
    크롬 종료

    :param chrome: 크롬 드라이버 인스턴스
    """
    def close():
        chrome.close()
    return close


def get_tasklist(hi, driver, username):
    task_list = []
    breakcount = False
    driver.get(url + 'tasks?page=1&search=' + username)
    while True:
        for i in range(1, 11):
            div = '//*[@id="root"]/section/main/div/div[2]/div/div[' + str(i) + ']'
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.XPATH, div + '/div[2]/span[2]')))
            nm = driver.find_element(By.XPATH, div + '/div[2]/span[2]').text
            if hi in nm:
                task_list.append(driver.find_element(By.XPATH, div + '/div[2]/span[1]').text[1:-1])
                if nm.split('_')[-1] == '1':
                    breakcount = True
                    break
        if breakcount:
            breakcount = False
            break
        driver.find_element(By.CLASS_NAME, 'ant-pagination-next').click()
    print("task load 완료.")
    return task_list


def zip_download(tsk, driver, case):
    breakcount = False
    # task url 접속
    driver.get(url + 'tasks/' + tsk)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/section/main/div/div/div[2]/div[1]')))

    # date_case_id_name_taskid 받아오기
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    hname = soup.find('div', 'ant-col cvat-task-details-task-name')
    zip_name = hname.find('h4', 'ant-typography cvat-text-color').text

    # Action 버튼 누르기
    action = ActionChains(driver)
    driver.find_element(By.CLASS_NAME, 'ant-btn.ant-btn-lg.ant-dropdown-trigger').click()
    WebDriverWait(driver, 20).until(EC.presence_of_element_located(
        (By.CLASS_NAME, 'ant-menu-submenu-title')))
    time.sleep(0.5)

    # Case1 : datumaro 받기
    if case == '1':
        # dump annotation 버튼 클릭
        eleme = driver.find_element(By.CLASS_NAME, 'ant-menu-submenu-title')
        action.move_to_element(eleme).perform()
        action.move_to_element(eleme).click().perform()

        # datumaro 1.0 버튼 클릭
        eleme2 = driver.find_element(By.XPATH, '//*[@id="dump_task_anno$Menu"]/li[5]')
        action.move_to_element(eleme2).perform()
        action.move_to_element(eleme2).click().perform()
        cnt = 0
    while True:
        cur_dwn = os.listdir(downdir)
        for c in cur_dwn:
            if zip_name.lower() in c.lower() and 'crdown' not in c and 'datumaro' in c:
                time.sleep(0.5)
                shutil.move(os.path.join(downdir, c), dir + folder_name + '\\zip\\' + c)
                breakcount = True
                break

        if breakcount:
            print(zip_name)
            breakcount = False
            time.sleep(0.5)
            break
        else:
            cnt += 1
            print(cnt)
            if cnt == 8:
                print('Network Delay... Retry...\n')
                zip_download(tsk, driver, case)
                break
            time.sleep(1)


def json_extract(z, case):
    nm = z[:-4]
    print(nm)
    n = nm.split('_')
    rename = n[1] + '_' + n[3].upper() + '_' + n[5].split('-')[0] + '.json'
    with zipfile.ZipFile(os.path.join(dir + folder_name + '\\zip', z), 'r') as zip:
        if case == '1':
            json_name = 'dataset/annotations/default.json'
        if case == '2':
            json_name = 'annotations/instances_default.json'
        zip.extract(json_name, dir)
        shutil.move(dir + json_name, dir + folder_name + '\\json\\' + rename)

    # rename_z = n[1] + '_' + n[3].upper() + '_' + n[5].split('-')[0] + '.zip'
    # os.rename(os.path.join(dir + folder_name + '\\zip', z), os.path.join(dir + folder_name, 'zip', rename_z))


def main():
    # task_date = datetime.today().strftime("%Y.%m.%d")
    print('copyright 2021. KST & HeoSeokYong All Rights Reserved.\n')

    # 폴더 생성
    if not os.path.exists(desktop_dir + folder_name):
        os.makedirs(desktop_dir + folder_name)
    if not os.path.exists(desktop_dir + folder_name + '\\zip'):
        os.makedirs(desktop_dir + folder_name + '\\zip')
    if not os.path.exists(desktop_dir + folder_name + '\\json'):
        os.makedirs(desktop_dir + folder_name + '\\json')
    with open(del_file, 'at', encoding='utf-8') as d:
        d.write('')

    case = ''
    ver = ''

    while ver != '1' and ver != '2' and ver != '3':
        ver = input('1.알집만 다운로드  2. json 압축만 풀기  3.알집 다운로드 & json 압축 풀기\n')

    while case != '1' and case != '2':
        case = input('Case: ')

    # 알집 받아오기
    if ver == '1' or ver == '3':
        print('현재 작업중인 CVAT에 있는 task만 가능합니다. | 현재 CVAT 주소: ', url)
        task_date = input('다운로드 받기를 원하는 날짜를 입력하세요.(YYYY.MM.DD 형태로 입력하세요. ex: 2021.11.01)\n')
        # url = input('해당 날짜 task가 있는 CVAT의 주소를 입력하세요.(ex와 같은 부분까지 끊어주세요. ex: http://192.168.0.73:8080/)')
        # 로그인 하기
        username = input('ID: ')
        password = input('PW: ')
        login_data = {
            'username': username,
            'password': password
        }
        options = Options()
        prefs = {'profile.default_content_setting_values': {'plugins': 2, 'popups': 2, 'plugins': 2,
                                                            'geolocation': 2, 'notifications': 2,
                                                            'auto_select_certificate': 2, 'fullscreen': 2,
                                                            'mouselock': 2,
                                                            'media_stream_mic': 2,
                                                            'media_stream_camera': 2, 'protocol_handlers': 2,
                                                            'ppapi_broker': 2, 'automatic_downloads': 2,
                                                            'midi_sysex': 2,
                                                            'push_messaging': 2, 'ssl_cert_decisions': 2,
                                                            'metro_switch_to_desktop': 2,
                                                            'app_banner': 2, 'site_engagement': 2,
                                                            'durable_storage': 2}}
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument('--headless')  # 크롬 안 키고

        if getattr(sys, 'frozen', False):
            chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
            driver = webdriver.Chrome(chromedriver_path, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        _enable_download_in_headless_chrome(driver, os.path.expanduser('~') + '\\Downloads\\')
        os.system('cls')

        driver.get(url + 'auth/login')
        driver.implicitly_wait(15)

        driver.find_element(By.XPATH, "//*[@id='username']").send_keys(login_data['username'])
        driver.find_element(By.XPATH, "//*[@id='password']").send_keys(login_data['password'])
        driver.find_element(By.CLASS_NAME, 'ant-btn.ant-btn-primary.login-form-button').click()

        hi = '_'.join([task_date, 'CASE' + str(case), login_data['username']])

        time.sleep(1)
        print('글자가 안 표시될 경우, 아무 키나 눌러주세요. 10초 이상 반응이 없다면 프로그램을 다시 한번 껐다가 켜주세요.')

        task_list = get_tasklist(hi, driver, username)
        for tsk in task_list:
            zip_download(tsk, driver, case)
        print('알집이 바탕화면의 ' + folder_name + ' 폴더 안의 zip 폴더에 저장되었습니다.')
        _close_chrome(driver)
        time.sleep(1)

    # json 받기
    if ver == '2' or ver == '3':
        len_cnt = 0
        zip_list = os.listdir(dir + folder_name + '\\zip')

        # 압축풀기
        for z in zip_list:
            if 'zip' in z and 'task' in z:
                json_extract(z, case)
                len_cnt += 1

        if os.path.exists(dir + 'datasets'):
            shutil.rmtree(dir + 'dataset')
        print('총 ' + str(len_cnt) + '개 완료')
        print('json 파일이 바탕화면의 ' + folder_name + ' 폴더 안의 json 폴더에 저장되었습니다.')
        time.sleep(2)


if __name__ == "__main__":
    main()
