import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from config import SCREENSHOTS_DIR

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_driver = None


def _get_driver():
    global _driver
    if _driver is not None:
        return _driver

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=service, options=options)
    _driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return _driver


def _extract_result_from_card(card):
    title = ""
    url = ""
    snippet = ""

    try:
        link = card.find_element(By.CSS_SELECTOR, "h2 a")
        title = link.text.strip()
        url = link.get_attribute("href") or ""
    except NoSuchElementException:
        pass

    if not title:
        try:
            link = card.find_element(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
            title = link.text.strip()
            url = link.get_attribute("href") or ""
        except NoSuchElementException:
            pass

    try:
        snippet = card.find_element(By.CSS_SELECTOR, "[data-result='snippet']").text.strip()
    except NoSuchElementException:
        try:
            snippet = card.find_element(By.CSS_SELECTOR, ".result__snippet").text.strip()
        except NoSuchElementException:
            snippet = ""

    return title, url, snippet


def search_web(query: str) -> str:
    try:
        if not query:
            return "Search query de bhai."

        driver = _get_driver()
        driver.get(f"https://duckduckgo.com/?q={quote_plus(query)}")
        time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='result']")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div.result")

        rows = []
        for card in cards:
            title, url, snippet = _extract_result_from_card(card)
            if title and url:
                rows.append((title, url, snippet))
            if len(rows) == 3:
                break

        if not rows:
            return "Bhai koi solid search result nahi mila."

        lines = []
        for i, (title, url, snippet) in enumerate(rows, start=1):
            lines.append(f"{i}. {title}\n{url}\n{snippet}")

        return "Top results mil gaye bhai:\n\n" + "\n\n".join(lines)
    except Exception as err:
        return f"Arre bhai browser search mein gadbad: {err}"


def open_url(url: str) -> str:
    try:
        if not url:
            return "URL de bhai."
        final_url = url.strip()
        if not final_url.startswith(("http://", "https://")):
            final_url = f"https://{final_url}"

        driver = _get_driver()
        driver.get(final_url)
        time.sleep(1)
        title = driver.title or "Untitled"
        return f"Site khul gayi bhai. Title: {title}"
    except Exception as err:
        return f"Arre bhai URL kholne mein gadbad: {err}"


def take_screenshot(url: str) -> str:
    try:
        if not url:
            return "Screenshot ke liye URL de bhai."

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = SCREENSHOTS_DIR / f"web-shot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"

        driver = _get_driver()
        open_url(url)
        time.sleep(1)
        driver.save_screenshot(str(file_path))
        return f"Web screenshot save kar diya bhai: {file_path}"
    except Exception as err:
        return f"Arre bhai web screenshot mein gadbad: {err}"


def search(query: str) -> str:
    return search_web(query)
