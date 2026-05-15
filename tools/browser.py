import time
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

_driver = None


def _get_driver():
    global _driver
    if _driver is not None:
        return _driver

    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=service, options=options)
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


def search(query):
    try:
        if not query:
            return "Search query de bhai."

        driver = _get_driver()
        driver.get(f"https://duckduckgo.com/?q={quote_plus(query)}")
        time.sleep(3)

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

        return "Le bhai top results:\n\n" + "\n\n".join(lines)
    except Exception as err:
        return f"Arre bhai browser search mein gadbad: {err}"


def open_url(url):
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
        return f"Site khul gayi bhai. Page title: {title}"
    except Exception as err:
        return f"Arre bhai URL kholne mein gadbad: {err}"
