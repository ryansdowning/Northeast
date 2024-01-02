import os
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()
SMTP_SERVER = os.environ.get("NORTHEAST_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = os.environ.get("NORTHEAST_SMTP_PORT", 587)
SMTP_USERNAME = os.environ.get("NORTHEAST_SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("NORTHEAST_SMTP_PASSWORD")
HEADLESS = os.environ.get("NORTHEAST_HEADLESS", "false") == "true"


def send_email(recipient: str, subject: str, body: str):
    message = MIMEMultipart()
    message["From"] = SMTP_USERNAME
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, recipient, message.as_string())


class NorthEast:
    def __init__(self, email: str, confirmation_code: str, first_name: str, last_name: str, threshold: int = 0):
        self.email = email
        self.confirmation_code = confirmation_code
        self.first_name = first_name
        self.last_name = last_name
        self.threshold = threshold

        options = Options()
        if HEADLESS:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.waiter = WebDriverWait(self.driver, 10)

    def send_price_alert_email(self, flight_number: str, price_change: int):
        logger.debug(f"Sending price alert email to {self.email}.")
        subject = f"The price for flight {flight_number} has changed!"
        body = f'The price for flight {flight_number} has {"dropped" if price_change <= 0 else "raised"} ${abs(price_change)}.'
        send_email(self.email, subject, body)

    def search(self):
        logger.debug("Entering confirmation code.")
        confirmation_input = self.waiter.until(EC.element_to_be_clickable((By.ID, "confirmationNumber")))
        confirmation_input.send_keys(self.confirmation_code)
        logger.debug("Entering first name.")
        first_name_input = self.waiter.until(EC.element_to_be_clickable((By.ID, "passengerFirstName")))
        first_name_input.send_keys(self.first_name)
        logger.debug("Entering last name.")
        last_name_input = self.waiter.until(EC.element_to_be_clickable((By.ID, "passengerLastName")))
        last_name_input.send_keys(self.last_name)

        logger.debug("Clicking submit button.")
        search_button = self.waiter.until(EC.element_to_be_clickable((By.ID, "form-mixin--submit-button")))
        search_button.click()

    def get_flight_numbers(self):
        logger.debug("Navigating to reservation page.")
        self.driver.get("https://www.southwest.com/air/manage-reservation/index.html")
        self.search()

        logger.debug("Waiting for page navigation...")
        self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, "air-flight-title")))

        logger.debug("Getting flight numbers")
        flight_number_elements = self.driver.find_elements(By.CLASS_NAME, "flight-segments--flight-number")
        flight_numbers = {el.text for el in flight_number_elements}
        logger.info(f"Found flight numbers: {', '.join(flight_numbers)}")
        return flight_numbers

    def change_reservation(self):
        logger.debug("Navigating to change reservation page.")
        self.driver.get("https://www.southwest.com/air/change/index.html")
        self.search()

        logger.debug("Waiting for page navigation...")
        self.waiter.until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, "air-change-landing-page--subheading"), "Select flights to change"
            )
        )

        logger.debug("Clicking checkboxes.")
        flight_checkboxes = self.driver.find_elements(By.CLASS_NAME, "landing-checkbox-selector")
        for checkbox in flight_checkboxes:
            checkbox.click()

        explore_button = self.waiter.until(EC.element_to_be_clickable((By.ID, "form-mixin--submit-button")))
        explore_button.click()

    def _get_flight_prices(self, flight_element, flight_number):
        flight_list_element = flight_element.find_element(By.XPATH, "ancestor::li[1]")
        price_elements = flight_list_element.find_elements(By.CLASS_NAME, "fare-button")
        if len(price_elements) < 4:
            logger.warning(f"Found less than 4 price elements for flight number: {flight_number}")

        prices = [re.search(r"\d+", el.text) for el in price_elements]
        prices = [
            int(price.group(0)) * ((("-" not in el.text) * 2) - 1) for price, el in zip(prices, price_elements) if price
        ]
        if len(prices) < 4:
            logger.warning(f"Found less than 4 prices for flight number: {flight_number}")

        logger.info(f"Found the following (flight number - prices): {flight_number} - {prices}")
        return prices

    def get_flights_prices(self, flight_numbers: list[str]):
        self.change_reservation()
        logger.debug("Waiting for page navigation...")
        self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, "air-booking-select-price-matrix")))

        logger.debug("Getting flight elements.")
        flight_elements = self.driver.find_elements(By.CLASS_NAME, "flight-numbers--flight-number")
        flight_prices = {}
        for flight_element in flight_elements:
            flight_element_numbers = re.findall(r"\d+", flight_element.text)
            for flight_number in flight_numbers:
                if flight_number not in flight_element_numbers:
                    continue

                logger.debug(f"Getting prices for flight number: {flight_number}")
                flight_prices[flight_number] = self._get_flight_prices(flight_element, flight_number)

        for flight_number in flight_numbers:
            if flight_number not in flight_prices:
                logger.warning(f"Failed to find prices for flight number: {flight_number}")

        return flight_prices

    def check_for_price_changes(self):
        flight_numbers = self.get_flight_numbers()
        flight_prices = self.get_flights_prices(flight_numbers)
        for flight_number, prices in flight_prices.items():
            if len(prices) != 4 and prices[3] <= self.threshold:
                logger.warning(f"Could not find price for flight number: {flight_number}.")
            if prices[3] <= self.threshold:
                logger.info(f"Flight number {flight_number} price changed by {prices[3]} which is below the threshold.")
                self.send_price_alert_email(flight_number, prices[3])
            else:
                logger.info(f"Price change for flight number {flight_number} did not exceed the threshold.")


if __name__ == "__main__":
    # Replace these!
    # Threshold is number of whole dollars to trigger email alert if price changes at least the threshold
    # amount. For example, -1 will send an alert if the price lowers at all, where a threshold of -10 will only send an
    # alert if the prices decreases at least 10 dollars.
    northeast = NorthEast("your.email@example.com", "CONFIRMATION_CODE", "FIRST_NAME", "LAST_NAME", threshold=0)

    northeast.check_for_price_changes()
    northeast.driver.quit()
