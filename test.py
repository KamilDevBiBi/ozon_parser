from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located

import time

opts = Options()

# скрываем от веб-сайта, что браузер управляется драйвером
opts.add_argument("--start-maximized")
opts.add_experimental_option("useAutomationExtension", False)
opts.add_experimental_option("excludeSwitches", ["enable-automation"])

service = Service(executable_path="chromedriver.exe")

driver = webdriver.Chrome(service=service)

# включаем скрытый режим, чтобы обойти защиту от скраппинга от озона
stealth(driver=driver,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        platform="Win32",
        languages=["ru-RU", "ru"],
        vendor="Google Inc."
        )

driver.get("https://www.ozon.ru")

def scroll_page(deep: int, distance: float = 200) -> None:
    for _ in range(deep):
        # 833px - расстояние скролла, которое нужно пагинотору озона,
        # чтобы загрузить следующий div с товарами
        driver.execute_script(f"window.scrollBy(0, {distance})")
        time.sleep(0.4)

# Ждём пока загрузит сайт
WebDriverWait(driver, 5).until(
    presence_of_element_located((By.ID, "__ozon"))
)

scroll_page(6)
scroll_page(1, 192)

top_distance = driver.execute_script(f"return document.querySelector(\".container\").lastChild.firstChild.children[8].getBoundingClientRect().top + window.pageYOffset")

window_height = driver.execute_script("return window.innerHeight")
first_orders_scroll = top_distance - window_height


orders_count = int(input("Напишите сколько товаров вы хотите получить: "))

catalog_wrapper = driver.find_element(By.CLASS_NAME, "container")
orders_wrapper_children = catalog_wrapper.find_elements(By.XPATH, "./*")

paginator = orders_wrapper_children[-1]
prev = 1
#проверка работоспособности поиска товаров в пагинаторе
#нахождение оптимального расстояния для успешного поиска

# !! - иногда поиск "перескакивает" на следующий блок с товарами, что приводит
# к увелечению желаемого числа товаров на 10
while True:
    scroll = driver.execute_script("return window.pageYOffset")
    scroll_page(5, 200)
    scroll_page(1, 41)
    time.sleep(1)

    inf_paginator = (paginator.find_element(By.TAG_NAME, "div")
    .find_elements(By.XPATH, "./*")[-2]
    )

    main_content = (inf_paginator.find_element(By.TAG_NAME, "div")
                    .find_element(By.TAG_NAME, "div")
                    .find_element(By.TAG_NAME, "div")
                    )

    all_orders_wrapper = main_content.find_elements(By.XPATH, "./*")[1]
    orders_wrapper = all_orders_wrapper.find_elements(By.XPATH, "./*")
    last_index = int(all_orders_wrapper.find_elements(By.XPATH, "./*")[-1].find_element(By.TAG_NAME, "div").get_dom_attribute("data-index"))

    print(last_index)
    print(driver.execute_script(f"return window.pageYOffset - {scroll}"))

#поиск перескакивает после четвертого блока на шестой

count = 0
prev = driver.execute_script("return window.pageYOffset")
while True:
    driver.execute_script("window.scrollBy(0, 1)")
    count += 1
    time.sleep(0.1)

    inf_paginator = (paginator.find_element(By.TAG_NAME, "div")
    .find_elements(By.XPATH, "./*")[-2]
    )

    main_content = (inf_paginator.find_element(By.TAG_NAME, "div")
                    .find_element(By.TAG_NAME, "div")
                    .find_element(By.TAG_NAME, "div")
                    )

    all_orders_wrapper = main_content.find_elements(By.XPATH, "./*")[1]
    orders_wrapper = all_orders_wrapper.find_elements(By.XPATH, "./*")
    last_index = int(all_orders_wrapper.find_elements(By.XPATH, "./*")[-1].find_element(By.TAG_NAME, "div").get_dom_attribute("data-index"))
    if last_index == 4 or last_index == 5:
        print(driver.execute_script(f"return window.pageYOffset - {prev}"))
        print(count)
        break

#по какой то причине между третьим и четвертым блоком остается 243 пикселя,
# а не 1042, как у всех