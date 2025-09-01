from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.remote.webelement import WebElement # для аннотации

import time
import json
from bs4 import BeautifulSoup, Tag

# import threading
# import queue

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

def scroll_page(deep: int, distance: int = 1041) -> None:
    for _ in range(deep):
        # 833px - расстояние скролла, которое нужно пагинотору озона,
        # чтобы загрузить следующий div с товарами
        driver.execute_script(f"window.scrollBy(0, {distance})")
        time.sleep(0.2)

# Ждём пока загрузит сайт
WebDriverWait(driver, 5).until(
    presence_of_element_located((By.ID, "__ozon"))
)



scroll_page(6, 200)


distance_to_top = driver.execute_script(f"return document.querySelector(\".container\").lastChild.firstChild.children[8].getBoundingClientRect().top + window.pageYOffset")

window_height = driver.execute_script("return window.innerHeight")
first_orders_distance = distance_to_top - window_height
# first_orders_distance - расстояние, которое нужно проскроллить,
# чтобы пагинатор озона загрузил первый блок товаров

scroll_page(6, 200)
scroll_page(1, 34)

orders_count = int(input("Напишите сколько товаров вы хотите получить: "))


def get_next_paginator_orders(all_orders_wrapper: WebElement, last_index: int) -> list[WebElement]:
    for _ in range(orders_count // 10 - 2):
        scroll_page(3, 347)
        time.sleep(0.5)

        orders_wrapper = all_orders_wrapper.find_elements(By.XPATH, "./*")
        cur_index = int(orders_wrapper[-1].find_element(By.TAG_NAME, "div").get_dom_attribute("data-index"))

        if cur_index >= 5:
            order_html = orders_wrapper[0].get_attribute("outerHTML")
            order_soup = BeautifulSoup(order_html, "lxml")
            order = order_soup.find("div").find("div").find("div").find("div").find("div")

            parse_orders(order.find_all(recursive=False))

        orders_wrapper = all_orders_wrapper.find_elements(By.XPATH, "./*")
        cur_index = int(orders_wrapper[-1].find_element(By.TAG_NAME, "div").get_dom_attribute("data-index"))
        if cur_index == last_index:
            count = 0
            while True:
                driver.execute_script("window.scrollBy(0, 1)")
                count += 1
                time.sleep(0.1)
                orders_wrapper = all_orders_wrapper.find_elements(By.XPATH, "./*")
                cur_index = int(orders_wrapper[-1].find_element(By.TAG_NAME, "div").get_dom_attribute("data-index"))
                if cur_index > last_index:
                    break

    return orders_wrapper

def parse_infinite_paginator(paginator_wrapper: WebElement) -> None:

    inf_paginator = (paginator_wrapper.find_element(By.TAG_NAME, "div")
                    .find_elements(By.XPATH, "./*")[-2]
                    )

    main_content = (inf_paginator.find_element(By.TAG_NAME, "div")
                    .find_element(By.TAG_NAME, "div")
                    .find_element(By.TAG_NAME, "div")
                    )

    all_orders_wrapper = main_content.find_elements(By.XPATH, "./*")[1]
    last_index = int(all_orders_wrapper.find_elements(By.XPATH, "./*")[-1].find_element(By.TAG_NAME, "div").get_dom_attribute("data-index"))

    orders_wrapper = get_next_paginator_orders(all_orders_wrapper, last_index)

    for order_wrapper in orders_wrapper:
        orders_row = (order_wrapper.find_element(By.TAG_NAME, "div")
                      .find_element(By.TAG_NAME, "div")
                      .find_element(By.TAG_NAME, "div")
                      .find_element(By.TAG_NAME, "div")
                      )
        orders_row_html = orders_row.get_attribute("outerHTML")
        orders_row_soup = BeautifulSoup(orders_row_html, "lxml")
        orders_row = orders_row_soup.find("div").find_all(recursive=False)

        parse_orders(orders_row)


def get_short_name(name: str) -> str:
    if len(name) > 24:
        splited_text = name.split()
        length = 0
        short_name = ""
        for i in range(len(splited_text)):
            length += len(splited_text[i])
            if length >= 24:
                short_name = " ".join(splited_text[:i + 1])
                break

        if not short_name:
            return name

        return short_name + "..."
    return name

def get_pretty_price(price: str) -> str:
    # меняем символ THSP на пробел, чтобы корректно показать его в json
    if not price:
        time.sleep(1000)
    price = price.replace("\u2009", " ")
    price = price[:-2] + price[-1]
    return price

order_data = dict()
def parse_orders(orders_row: list[Tag]) -> None:
    for order in orders_row:
        special_offer = "Отсутствует"

        card_order = order.find("a")
        try:
            special_offer = card_order.find("section").text
        except Exception as E:
            pass

        data_wrapper = order.find_all(recursive=False)[-1].find_all(recursive=False)

        price_data = data_wrapper[0].find("div").find_all(recursive=False)

        cur_price = get_pretty_price(price_data[0].text)
        last_price = cur_price
        discount = "Цена фиксирована"

        if len(price_data) > 2:
            last_price = get_pretty_price(price_data[1].text)
            discount = price_data[2].text

        name = get_short_name(data_wrapper[1].text)

        score = "оценка отсутствует"
        responses = "отзывы отсутствуют"

        if len(data_wrapper) > 2:
            rating_field = data_wrapper[2].find_all(recursive=False)
            score = rating_field[0].text
            responses = rating_field[1].text.replace("\u00A0", " ").replace("\u2009", " ")

        if name in order_data:
            name += "2"
        order_data[name] = {
            "Специальные предложения": special_offer,
            "Цена": cur_price,
            "Прошлая цена": last_price,
            "Скидка": discount,
            "Оценка товара": score,
            "Отзывы": responses
        }




def get_next_fifty_orders() -> None:
    # paginator_soup = BeautifulSoup(paginator.get_attribute("innerHTML"), "lxml")
    # paginator_children = paginator_soup.find("div").find_all("div", recursive=False)
    # paginator_orders = list()
    # for i in range(0, 13, 4):
    #     paginator_orders.append(paginator_children[i])
    #
    # for order in paginator_orders[:3]:
    #     parse_orders(order.find("div").find("div").find("div").children)
    #     print(len(order_data))

    parse_infinite_paginator(paginator)


catalog_wrapper = driver.find_element(By.CLASS_NAME, "container")
orders_wrapper_children = catalog_wrapper.find_elements(By.XPATH, "./*")

paginator = orders_wrapper_children[-1]


get_next_fifty_orders()
print(f"Товаров получено - {len(order_data)} шт.")
with open("orders.json", "w", encoding="utf-8") as f:
    json.dump(order_data, f, indent=4, ensure_ascii=False)


time.sleep(1000)

driver.quit()
