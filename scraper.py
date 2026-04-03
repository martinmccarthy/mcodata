from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

driver = webdriver.Firefox()
driver.get("https://flymco.com/flights/?scope=arrivals")
assert "Orlando International Airport" in driver.title

wait = WebDriverWait(driver, 10)

try:
    cookie_button = driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonDecline")
    cookie_button.click()
    wait.until(EC.invisibility_of_element_located((By.ID, "CybotCookiebotDialog")))
except TimeoutException:
    pass

more_button = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "css-1sg5vc0-Base-Base-Button-StyledButton-Button-ButtonStyled"))
)

more_button = more_button[1]

second_flight_list = driver.find_elements(By.CLASS_NAME, "css-1vqyji3-FlightList-FlightListDate")

while len(second_flight_list) == 0:
    second_flight_list = driver.find_elements(By.CLASS_NAME, "css-1vqyji3-FlightList-FlightListDate")
    more_button.click()

flight_data = driver.find_elements(By.CLASS_NAME, "css-1t0gxgj-FlightListRow-StyledRow")
print(flight_data)

assert "No results found." not in driver.page_source
driver.close()
