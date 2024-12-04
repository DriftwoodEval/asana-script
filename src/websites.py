from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)


def check_q_done(q_link: str, name: str):
    driver.implicitly_wait(5)
    print(f"Checking {q_link} from {name}...")
    url = q_link.split(" ")[0]
    driver.get(url)

    complete = False

    if "mhs.com" in url:
        try:
            driver.find_element(
                By.XPATH, "//*[contains(text(), 'Thank you for completing')]"
            )
            complete = True
        except NoSuchElementException:
            complete = False
    elif "pearsonassessments.com" in url:
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'Test Completed!')]")
            complete = True
        except NoSuchElementException:
            complete = False

    return complete
