import requests
from googletrans import Translator
from datetime import datetime, timedelta
import random
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# 환경변수로부터 키 가져오기
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

# SMTP (메일 발송용)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

recipients = ['jonah.whang@sktelecom.com', 'yona997@naver.com']

# 키워드 리스트
keywords_en = ['mobile device', 'mobile modem chipset', 'on-device AI', 'on-device security']
keywords_kr = ['이동통신 단말기', '단말 모뎀 칩셋', '온디바이스 AI', '온디바이스 보안']

translator = Translator()
today = datetime.utcnow().date() + timedelta(hours=9)  # UTC +9 서울시간으로 변환
yesterday = today - timedelta(days=1)

NEWSAPI_URL = 'https://newsapi.org/v2/everything'
NAVER_URL = 'https://openapi.naver.com/v1/search/news.json'

def fetch_newsapi_news(keyword):
    from_date = yesterday.strftime('%Y-%m-%d')
    to_date = yesterday.strftime('%Y-%m-%d')
    params = {
        'q': keyword,
        'pageSize': 10,
        'sortBy': 'relevancy',
        'language': 'en',
        'from': from_date,
        'to': to_date,
        'apiKey': NEWSAPI_KEY,
    }
    response = requests.get(NEWSAPI_URL, params=params)
    if response.status_code == 200:
        return response.json().get('articles', [])
    else:
        print(f'NewsAPI error ({keyword}):', response.status_code, response.text)
        return []

def fetch_naver_news(keyword):
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
    }
    params = {
        'query': keyword,
        'display': 20,
        'sort': 'date'
    }
    response = requests.get(NAVER_URL, headers=headers, params=params)
    if response.status_code == 200:
        items = response.json().get('items', [])
        filtered_items = []
        for item in items:
            pub_date = item.get('pubDate', '')
            try:
                dt = datetime.strptime(pub_date[:-6], '%a, %d %b %Y %H:%M:%S')
                if dt.date() == today:
                    filtered_items.append(item)
            except:
                pass
        return filtered_items[:10]
    else:
        print(f'Naver API error ({keyword}):', response.status_code, response.text)
        return []

def translate_text(text):
    try:
        return translator.translate(text, src='en', dest='ko').text
    except Exception:
        return text

def escape_html(text):
    return html.escape(text)

def build_html_dashboard():
    html_output = """
    <html>
    <head>
      <meta charset="UTF-8">
      <title>뉴스 대시보드</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color:#f7f7f7; margin:0; padding:20px;">
      <h2 style="color:#2c3e50; border-bottom:2px solid #2980b9; padding-bottom:10px;">뉴스 대시보드</h2>
    """

    for i in range(len(keywords_en)):
        kw_en = keywords_en[i]
        kw_kr = keywords_kr[i]

        section_style = (
            "background-color:#ffffff; padding:15px; margin-bottom:30px; "
            "border-radius:8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);"
        )

        html_output += f'<div style="{section_style}">'
        html_output += f'<h3 style="color:#2980b9;">{escape_html(kw_kr)} (영어: {escape_html(kw_en)})</h3>'

        english_news = fetch_newsapi_news(kw_en)
        english_items = []
        for article in english_news:
            title = translate_text(article.get('title', ''))
            description = translate_text(article.get('description', ''))
            url = article.get('url', '')
            published_at = article.get('publishedAt', '')
            try:
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                published_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                published_str = published_at
            english_items.append({
                'title': title,
                'description': description,
                'url': url,
                'publishedAt': published_str
            })

        korean_news = fetch_naver_news(kw_kr)
        korean_items = []
        for item in korean_news:
            title = item.get('title', '').replace('&quot;', '"').replace('<b>', '').replace('</b>', '')
            description = item.get('description', '').replace('&quot;', '"').replace('<b>', '').replace('</b>', '')
            url = item.get('originallink', '')
            pub_date = item.get('pubDate', '')
            try:
                dt = datetime.strptime(pub_date[:-6], '%a, %d %b %Y %H:%M:%S')
                published_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                published_str = pub_date
            korean_items.append({
                'title': title,
                'description': description,
                'url': url,
                'publishedAt': published_str
            })

        combined = english_items[:5] + korean_items[:5]
        random.shuffle(combined)

        table_style = "width:100%; border-collapse: collapse;"
        th_style = (
            "background-color:#2980b9; color:#fff; padding:10px; text-align:left; font-size:16px;"
            "border-bottom: 2px solid #1c5980;"
        )
        td_style = "border-bottom:1px solid #ddd; padding:10px; vertical-align:top;"

        html_output += f'<table style="{table_style}">'
        html_output += (
            f"<tr>"
            f"<th style='{th_style}'>번호</th>"
            f"<th style='{th_style}'>제목</th>"
            f"<th style='{th_style}'>요약</th>"
            f"<th style='{th_style}'>배포일</th>"
            f"<th style='{th_style}'>링크</th>"
            f"</tr>"
        )

        for idx, item in enumerate(combined, 1):
            title = escape_html(item['title'])
            description = escape_html(item['description'])
            publishedAt = escape_html(item['publishedAt'])
            url = escape_html(item['url'])

            html_output += (
                f"<tr>"
                f"<td style='{td_style}'>{idx}</td>"
                f"<td style='{td_style}'>{title}</td>"
                f"<td style='{td_style}'>{description}</td>"
                f"<td style='{td_style}'>{publishedAt}</td>"
                f"<td style='{td_style}'><a href='{url}' target='_blank' "
                f"style='color:#2980b9; text-decoration:none;'>링크</a></td>"
                f"</tr>"
            )
        html_output += "</table></div>"

    html_output += """
    </body>
    </html>
    """
    return html_output

def send_email(subject, html_content, sender, recipients):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(sender, recipients, msg.as_string())
        print("메일 발송 성공")

def main():
    html_dashboard = build_html_dashboard()
    send_email("SKT 뉴스 대시보드", html_dashboard, SMTP_USER, recipients)

if __name__ == "__main__":
    main()
