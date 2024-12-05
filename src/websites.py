import time
from datetime import datetime
from os import getenv

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

load_dotenv()

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(30)


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


def log_in_ta():
    driver.get("https://portal.therapyappointment.com")

    username = getenv("TA_USERNAME")
    if username is None:
        raise ValueError("TA_USERNAME environment variable must be set")
    username_field = driver.find_element(By.NAME, "user_username")
    username_field.send_keys(username)

    password = getenv("TA_PASSWORD")
    if password is None:
        raise ValueError("TA_PASSWORD environment variable must be set")
    password_field = driver.find_element(By.NAME, "user_password")
    password_field.send_keys(password)

    submit_button = driver.find_element(
        by=By.CSS_SELECTOR, value="button[type='submit']"
    )
    submit_button.click()


def go_to_client(firstname, lastname):
    clients_button = driver.find_element(
        by=By.XPATH, value="//*[contains(text(), 'Clients')]"
    )
    clients_button.click()

    firstname_label = driver.find_element(By.XPATH, "//label[text()='First Name']")
    firstname_field = firstname_label.find_element(
        By.XPATH, "./following-sibling::input"
    )
    firstname_field.send_keys(firstname)

    lastname_label = driver.find_element(By.XPATH, "//label[text()='Last Name']")
    lastname_field = lastname_label.find_element(By.XPATH, "./following-sibling::input")
    lastname_field.send_keys(lastname)

    search_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Search'")
    time.sleep(1)
    search_button.click()

    driver.find_element(
        By.CSS_SELECTOR,
        f"a[aria-description='Press Enter to view the profile of {firstname} {lastname}",
    ).click()

    return driver.current_url


def check_if_opened_portal():
    try:
        driver.find_element(By.CSS_SELECTOR, "input[aria-checked='true']")
        return True
    except NoSuchElementException:
        return False


def check_if_docs_signed():
    try:
        driver.implicitly_wait(5)
        driver.find_element(
            By.XPATH,
            "//div[contains(normalize-space(text()), 'has completed registration')]",
        )
        return True
    except NoSuchElementException:
        try:
            driver.find_element(
                By.XPATH,
                "//div[contains(normalize-space(text()), 'has not completed registration')]",
            )
            return False
        except NoSuchElementException:
            return "not found"


def extract_client_data(client_url: str):
    driver.get(client_url)
    name = driver.find_element(By.CLASS_NAME, "text-h4").text
    firstname = name.split(" ")[0]
    lastname = name.split(" ")[-1]
    account_number_element = driver.find_element(
        By.XPATH, "//div[contains(normalize-space(text()), 'Account #')]"
    ).text
    account_number = account_number_element.split(" ")[-1]
    birthdate_element = driver.find_element(
        By.XPATH, "//div[contains(normalize-space(text()), 'DOB ')]"
    ).text
    birthdate_str = birthdate_element.split(" ")[-1]
    birthdate = time.strftime("%Y/%m/%d", time.strptime(birthdate_str, "%m/%d/%Y"))
    gender_title_element = driver.find_element(
        By.XPATH,
        "//div[contains(normalize-space(text()), 'Gender') and contains(@class, 'v-list-item__title')]",
    )
    # print(gender_title_element.get_attribute("class"))
    gender_element = gender_title_element.find_element(
        By.XPATH, "following-sibling::div"
    )
    # IDK why but we have to wait before getting the gender text specifically
    time.sleep(0.5)
    gender = gender_element.text.split(" ")[0]

    age = datetime.now().year - datetime.strptime(birthdate, "%Y/%m/%d").year
    return {
        "firstname": firstname,
        "lastname": lastname,
        "account_number": account_number,
        "birthdate": birthdate,
        "gender": gender,
        "age": age,
    }


def log_in_mhs():
    driver.get("https://assess.mhs.com/Account/Login.aspx")

    username = getenv("MHS_USERNAME")
    if username is None:
        raise ValueError("MHS_USERNAME environment variable must be set")
    username_field = driver.find_element(By.NAME, "txtUsername")
    username_field.send_keys(username)

    password = getenv("MHS_PASSWORD")
    if password is None:
        raise ValueError("MHS_PASSWORD environment variable must be set")
    password_field = driver.find_element(By.NAME, "txtPassword")
    password_field.send_keys(password)

    sign_in_button = driver.find_element(By.NAME, "cmdLogin")
    sign_in_button.click()


def add_client_to_mhs(client: dict, Q: str):
    firstname = client["firstname"]
    lastname = client["lastname"]
    id = client["account_number"]
    dob = client["birthdate"]
    gender = client["gender"]
    driver.find_element(
        By.XPATH, "//div[@class='pull-right']//input[@type='submit']"
    ).click()

    firstname_label = driver.find_element(By.XPATH, "//label[text()='FIRST NAME']")
    firstname_field = firstname_label.find_element(
        By.XPATH, "./following-sibling::input"
    )
    firstname_field.send_keys(firstname)

    lastname_label = driver.find_element(By.XPATH, "//label[text()='LAST NAME']")
    lastname_field = lastname_label.find_element(By.XPATH, "./following-sibling::input")
    lastname_field.send_keys(lastname)

    id_label = driver.find_element(By.XPATH, "//label[text()='ID']")
    id_field = id_label.find_element(By.XPATH, "./following-sibling::input")
    id_field.send_keys(id)

    date_of_birth_field = driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='YYYY/Mmm/DD']"
    )
    date_of_birth_field.send_keys(dob)

    if Q != "Conners 4":
        male_label = driver.find_element(By.XPATH, "//label[text()='Male']")
        female_label = driver.find_element(By.XPATH, "//label[text()='Female']")
        if gender == "Male":
            male_label.click()
        else:
            female_label.click()
    else:
        gender_element = driver.find_element(
            By.CSS_SELECTOR,
            "select[aria-label*='Gender selection dropdown']",
        )
        gender_select = Select(gender_element)
        if gender == "Male":
            gender_select.select_by_visible_text("Male")
        elif gender == "Female":
            gender_select.select_by_visible_text("Female")
        else:
            gender_select.select_by_visible_text("Other")

    purpose_element = driver.find_element(
        By.CSS_SELECTOR,
        "select[placeholder='Select an option']",
    )
    purpose = Select(purpose_element)
    purpose.select_by_visible_text("Psychoeducational Evaluation")

    driver.find_element(By.CSS_SELECTOR, ".pull-right > input[type='submit']").click()

    try:
        driver.implicitly_wait(5)
        error = driver.find_element(
            By.XPATH,
            "//span[contains(text(), 'A client with the same ID already exists')]",
        )
        if error:
            print("A client with the same ID already exists")
            if Q == "Conners 4":
                print(
                    f"Manual intervention required for Conners 4: {client["firstname"]} {client["lastname"]}"
                )
                return False
            driver.find_element(
                By.XPATH, "//span[contains(normalize-space(text()), 'My Assessments')]"
            ).click()

            driver.find_element(
                By.XPATH, f"//span[contains(normalize-space(text()), '{Q}')]"
            ).click()

            driver.find_element(
                By.XPATH, "//div[contains(normalize-space(text()), 'Email Invitation')]"
            ).click()
            driver.find_element(
                By.CSS_SELECTOR, "input[value='Search Client']"
            ).send_keys(id)
            time.sleep(1)
            driver.find_element(
                By.XPATH,
                f"//li[contains(@class,'rsbListItem') and contains(text(), '{id}')]",
            ).click()
            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
            purpose_element = driver.find_element(By.CSS_SELECTOR, "select")
            purpose = Select(purpose_element)
            purpose.select_by_visible_text("Psychoeducational Evaluation")

            driver.find_element(
                By.CSS_SELECTOR, ".pull-right > input[type='submit']"
            ).click()

    except NoSuchElementException:
        print("New client created")
        return True


def gen_asrs(client: dict):
    driver.implicitly_wait(20)
    driver.find_element(
        By.XPATH, "//span[contains(normalize-space(text()), 'My Assessments')]"
    ).click()
    driver.find_element(
        By.XPATH, "//span[contains(normalize-space(text()), 'ASRS')]"
    ).click()
    driver.find_element(
        By.XPATH, "//div[contains(normalize-space(text()), 'Email Invitation')]"
    ).click()

    add_client_to_mhs(client, "ASRS")

    description_element = driver.find_element(By.ID, "ddl_Description")
    description = Select(description_element)

    if client["age"] < 18 and client["age"] >= 6:
        description.select_by_visible_text("ASRS (6-18 Years)")
    elif client["age"] < 6:
        description.select_by_visible_text("ASRS (2-5 Years)")

    time.sleep(1.5)  # Rater field is very fussy

    rater_element = driver.find_element(By.ID, "ddl_RaterType")
    rater = Select(rater_element)
    rater.select_by_visible_text("Parent")

    time.sleep(1.5)

    language_element = driver.find_element(By.ID, "ddl_Language")
    language = Select(language_element)
    language.select_by_visible_text("English")

    rater_name = driver.find_element(By.ID, "txtRaterName")
    rater_name.send_keys("Parent/Guardian")

    driver.find_element(By.CSS_SELECTOR, ".pull-right > input[type='submit']").click()

    time.sleep(1)

    driver.find_element(By.CSS_SELECTOR, ".pull-right > input[type='submit']").click()

    time.sleep(1)

    q_link = driver.find_element(By.CLASS_NAME, "txtLinkBox").get_attribute("value")

    return q_link


def gen_conners(client: dict):
    driver.implicitly_wait(20)
    driver.find_element(
        By.XPATH, "//span[contains(normalize-space(text()), 'My Assessments')]"
    ).click()
    time.sleep(1)
    if client["age"] < 6:
        conners_ver = "Conners EC"
        driver.find_element(
            By.XPATH, "//span[contains(normalize-space(text()), 'Conners EC')]"
        ).click()
    else:
        conners_ver = "Conners 4"
        driver.find_element(
            By.XPATH, "//span[contains(normalize-space(text()), 'Conners 4')]"
        ).click()
    driver.find_element(
        By.XPATH, "//div[contains(normalize-space(text()), 'Email Invitation')]"
    ).click()

    client_added = add_client_to_mhs(client, conners_ver)

    if not client_added:
        print(client)

    description_element = driver.find_element(By.ID, "ddl_Description")
    description = Select(description_element)

    if client["age"] < 6:
        description.select_by_visible_text("Conners EC")
    else:
        description.select_by_visible_text("Conners 4")

    time.sleep(1.5)  # Rater field is very fussy

    rater_element = driver.find_element(By.ID, "ddl_RaterType")
    rater = Select(rater_element)
    rater.select_by_visible_text("Parent")

    time.sleep(1.5)

    language_element = driver.find_element(By.ID, "ddl_Language")
    language = Select(language_element)
    language.select_by_visible_text("English")

    rater_name = driver.find_element(By.ID, "txtRaterName")
    rater_name.send_keys("Parent/Guardian")

    if client["age"] > 9:
        driver.find_element(By.ID, "btn_addRow").click()
        time.sleep(1.5)
        description_element = driver.find_elements(By.ID, "ddl_Description")[1]
        description = Select(description_element)
        description.select_by_visible_text("Conners 4")

        time.sleep(1.5)  # Rater field is very fussy

        rater_element = driver.find_elements(By.ID, "ddl_RaterType")[1]
        rater = Select(rater_element)
        rater.select_by_visible_text("Self-Report")

        time.sleep(1.5)

        language_element = driver.find_elements(By.ID, "ddl_Language")[1]
        language = Select(language_element)
        language.select_by_visible_text("English")

        driver.find_element(By.ID, "_btnnext").click()

        time.sleep(1)

        driver.find_element(By.ID, "btnGenerateLinks").click()

        time.sleep(1)

        q_link_els = driver.find_elements(By.CLASS_NAME, "txtLinkBox")
        q_links = []
        for link_el in q_link_els:
            q_links.append(link_el.get_attribute("value"))
        return q_links

    driver.find_element(By.ID, "_btnnext").click()

    time.sleep(1)

    driver.find_element(By.ID, "btnGenerateLinks").click()

    time.sleep(1)

    q_link = driver.find_element(By.CLASS_NAME, "txtLinkBox").get_attribute("value")

    return q_link


def send_message_ta(client_url: str, message: str):
    driver.get(client_url)
    driver.find_element(
        By.XPATH, "//a[contains(normalize-space(text()), 'Messages')]"
    ).click()
    driver.find_element(
        By.XPATH,
        "//div[2]/section/div/a/span/span",
    ).click()
    driver.find_element(By.ID, "message_thread_subject").send_keys(
        "Please complete the link(s) below"
    )
    time.sleep(1)
    text_field = driver.find_element(By.XPATH, "//section/div/div[3]")
    text_field.click()
    time.sleep(1)
    text_field.send_keys(message)
    time.sleep(1)
    text_field.click()
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()


def send_asrs(firstname, lastname):
    log_in_ta()
    client_url = go_to_client(firstname, lastname)
    client = extract_client_data(client_url)

    log_in_mhs()
    asrs_link = gen_asrs(client)
    if asrs_link:
        send_message_ta(client_url, asrs_link)


def send_conners(firstname, lastname):
    log_in_ta()
    client_url = go_to_client(firstname, lastname)
    client = extract_client_data(client_url)

    log_in_mhs()
    conners_link = gen_conners(client)
    if conners_link:
        if isinstance(conners_link, list):
            conners_link = "\n".join(conners_link)
        send_message_ta(client_url, conners_link)


# TODO:
# - Pull names from Asana
