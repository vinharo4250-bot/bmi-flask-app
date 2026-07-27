import os
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from supabase import create_client

ST = 1.5

COMPANY_LIST = [
    "삼천리",
    "서울도시가스",
    "예스코",
    "귀뚜라미에너지",
    "경동도시가스",
    "대성에너지",
]

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

GMAIL_SENDER = os.environ.get("GMAIL_SENDER", "vinharo4250@gmail.com")
GMAIL_RECEIVER = os.environ.get("GMAIL_RECEIVER", "vinharo4250@gmail.com")
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

EXCEL_RAW = "naver_cafe_반응.xlsx"
EXCEL_SUMMARY = "DE.xlsx"


def crawl_company(company):
    result = []

    options = EdgeOptions()
    if os.environ.get("HEADLESS", "1") != "0":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Edge(options=options)

    try:
        driver.get("https://www.naver.com")
        time.sleep(ST)

        search = driver.find_element(By.ID, "query")
        search.send_keys(company)

        driver.find_element(By.ID, "search-ai-tab-button-inner").click()
        time.sleep(ST)

        tabs = driver.find_elements(By.CLASS_NAME, "dV1n4PiA4lcDslot")

        for tab in tabs:
            if tab.text.strip() == "카페":
                tab.click()
                break

        time.sleep(ST)

        posts = driver.find_elements(By.CLASS_NAME, "title_area")

        for post in posts:
            try:
                a = post.find_element(By.TAG_NAME, "a")
                result.append([company, a.text, a.get_attribute("href")])
            except Exception:
                pass
    finally:
        driver.quit()

    return result


def run_crawl():
    all_result = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        for r in executor.map(crawl_company, COMPANY_LIST):
            all_result.extend(r)

    return all_result


def save_to_supabase(rows, run_at):
    if not rows:
        return

    records = [
        {"company": company, "title": title, "url": url, "run_at": run_at}
        for company, title, url in rows
    ]
    supabase.table("cafe_posts").insert(records).execute()


def build_excel(rows):
    df = pd.DataFrame(rows, columns=["기업명", "게시글제목", "게시글URL"])
    df.to_excel(EXCEL_RAW, index=False)

    summary_df = df.groupby("기업명").size().reset_index(name="게시글갯수")
    summary_df.to_excel(EXCEL_SUMMARY, index=False)

    return summary_df


def send_email():
    subject = "가스회사별 카페반응 정보 전달드립니다."
    body = "네이버에서 카페게시글 중 가스회사별 게시글갯수를 요약했습니다."

    msg = MIMEMultipart()
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(EXCEL_SUMMARY, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={EXCEL_SUMMARY}")
    msg.attach(part)

    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.starttls()
    smtp.login(GMAIL_SENDER, GMAIL_APP_PASSWORD.replace(" ", ""))
    smtp.sendmail(GMAIL_SENDER, GMAIL_RECEIVER, msg.as_string())
    smtp.quit()


def main():
    run_at = datetime.now(timezone.utc).isoformat()

    rows = run_crawl()
    print(f"크롤링 완료: {len(rows)}건")

    save_to_supabase(rows, run_at)
    print("Supabase 저장 완료")

    build_excel(rows)
    print(f"{EXCEL_RAW}, {EXCEL_SUMMARY} 저장 완료")

    send_email()
    print("메일 전송 완료!")


if __name__ == "__main__":
    main()
