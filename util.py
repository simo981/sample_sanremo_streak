import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def parse_head_to_head(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    rows = soup.find_all('div', class_='template_mg-market-attribute__Y16SU')
    for row in rows:
        desc_div = row.find('div', class_='mg-market-attribute-desc')
        if not desc_div: continue
        full_title = desc_div.get_text(strip=True).replace("T/T ", "")
        if " - " in full_title:
            sfidante_1, sfidante_2 = full_title.split(" - ", 1)
        else:
            sfidante_1 = full_title
            sfidante_2 = "Avversario"
        buttons = row.find_all('button', class_='chips-commons')
        if len(buttons) >= 2:
            try:
                quota_1 = buttons[0].find('span').get_text(strip=True)
                quota_2 = buttons[1].find('span').get_text(strip=True)
                results.append({
                    'sfidante_1': sfidante_1,
                    'quota_1': float(quota_1),
                    'sfidante_2': sfidante_2,
                    'quota_2': float(quota_2)
                })
            except ValueError:
                continue
    return results

def save_to_json(data, filename="quote_sanremo_TT.json"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[OK] Saved file: {filename}")
    except Exception as e:
        print(f"[ERRORE] I/O Error: {e}")

def get_matches():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--window-size=1920,1080")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        url = "https://www.sisal.it/scommesse-matchpoint/quote/spettacolo/festival-sanremo"
        print(f"Connecting to: {url}")
        driver.get(url)
        btn_xpath = '//*[@id="fr-competition-detail-97-3906"]/div/div[2]/div[1]/section/div/div/button[2]/span'
        table_xpath = '//*[@id="fr-competition-detail-97-3906"]/div/div[2]/div[2]'
        print("Button clicker T/T'...")
        try:
            btn_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, btn_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_element)
            time.sleep(1)            
            driver.execute_script("arguments[0].click();", btn_element)
            print(">>> Going on")
            time.sleep(5) 
        except Exception as e:
            print(f"Click error")
            driver.save_screenshot("debug_error_click.png")
            print("Dump as 'debug_error_click.png'")
            raise e
        table_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, table_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table_element)
        time.sleep(1)
        html_content = table_element.get_attribute('outerHTML')
        matches = parse_head_to_head(html_content)
        if matches:
            print(f"Extracted {len(matches)} match.")
            save_to_json(matches)
        else:
            print("Dump as 'debug_empty_table.png'")
            driver.save_screenshot("debug_empty_table.png")
    except Exception as e:
        print(f"Errore generale: {e}")
    finally:
        driver.quit()
    return matches

if __name__ == "__main__":
    get_matches()