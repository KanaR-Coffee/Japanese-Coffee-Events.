import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime


def clean_title(title):
  # タイトル末尾の媒体名（例: " - 週末、金沢。", " - Yahoo!ニュース" など）を自動カット
  title = re.sub(r'\s*[-|–]\s*[^—–\-]+$', '', title)
  return title.strip()


def fetch_live_coffee_events():
  events = []
  url = 'https://news.google.com/rss/search?q=%E3%82%B3%E3%83%BC%E3%83%92%E3%83%BC%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88&hl=ja&gl=JP&ceid=JP:ja'

  try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
      xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = root.findall('.//item')

    # 47都道府県のリスト
    prefectures = [
        '北海道',
        '青森',
        '岩手',
        '宮城',
        '秋田',
        '山形',
        '福島',
        '茨城',
        '栃木',
        '群馬',
        '埼玉',
        '千葉',
        '東京',
        '神奈川',
        '新潟',
        '富山',
        '石川',
        '福井',
        '山梨',
        '長野',
        '岐阜',
        '静岡',
        '愛知',
        '三重',
        '滋賀',
        '京都',
        '大阪',
        '兵庫',
        '奈良',
        '和歌山',
        '鳥取',
        '島根',
        '岡山',
        '広島',
        '山口',
        '徳島',
        '香川',
        '愛媛',
        '高知',
        '福岡',
        '佐賀',
        '長崎',
        '熊本',
        '大分',
        '宮崎',
        '鹿児島',
        '沖縄',
    ]

    # 主要都市から都道府県への逆引き辞書
    city_to_pref = {
        '札幌': '北海道',
        '仙台': '宮城',
        '金沢': '石川',
        '横浜': '神奈川',
        '名古屋': '愛知',
        '京都': '京都',
        '大阪': '大阪',
        '神戸': '兵庫',
        '広島': '広島',
        '福岡': '福岡',
        '博多': '福岡',
        '那覇': '沖縄',
        '軽井沢': '長野',
    }

    # コーヒーイベントに関連するキーワード（これが含まれない関係のない記事は弾く）
    keywords = [
        'コーヒー',
        '珈琲',
        'フェス',
        'マルシェ',
        'イベント',
        '試飲',
        '出店',
        'ロースター',
        'カフェ',
    ]

    valid_count = 0
    for item in items:
      raw_title = (
          item.find('title').text if item.find('title') is not None else ''
      )
      link = item.find('link').text if item.find('link') is not None else ''
      pub_date = (
          item.find('pubDate').text
          if item.find('pubDate') is not None
          else ''
      )
      description = (
          item.find('description').text
          if item.find('description') is not None
          else ''
      )

      # 関連性の薄いニュース記事を除外するフィルター
      if not any(kw in raw_title or kw in description for kw in keywords):
        continue

      title = clean_title(raw_title)

    # 地域判定（都道府県名または主要都市名から特定）
      region = '全国'
      # まず都市名からチェック
      for city, pref in city_to_pref.items():
        if city in title or city in description:
          region = pref
          break
      # 次に都道府県名からチェック
      if region == '全国':
        for pref in prefectures:
          if pref in title or pref in description:
            region = pref
            break

      # イベントの種別を判定
      ev_type = 'フェスティバル'
      if 'マーケット' in title or 'マルシェ' in title:
        ev_type = 'マーケット'
      elif 'ポップアップ' in title or '出店' in title:
        ev_type = 'ポップアップ'
      elif '試飲' in title or 'カッピング' in title:
        ev_type = '試飲会'

      # 画像（プレースホルダーとして美しいコーヒー画像を動的に割り当て）
      images = [
          'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=600&q=80',
          'https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=600&q=80',
          'https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=600&q=80',
          'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=600&q=80',
      ]
      img_url = images[valid_count % len(images)]

      valid_count += 1
      events.append({
          'id': valid_count,
          'title': title,
          'region': region,
          'type': ev_type,
          'date': pub_date[:16] if pub_date else '近日開催',
          'location': (
              f'{region} 特設会場 / 周辺エリア'
              if region != '全国'
              else '全国各地'
          ),
          'organizer': '自動巡回クローラー',
          'desc': (
              description[:90] + '...'
              if description
              else '詳細情報は公式サイトをご確認ください。'
          ),
          'url': link,
          'image': img_url,
      })

      # 最大40件まで取得
      if valid_count >= 40:
        break

  except Exception as e:
    print(f'エラー: {e}')

  if not events:
    events.append({
        'id': 1,
        'title': '最新のコーヒーイベント情報を収集中です',
        'region': '全国',
        'type': 'フェスティバル',
        'date': datetime.now().strftime('%Y/%m/%d'),
        'location': '日本全国',
        'organizer': 'BrewSync System',
        'desc': '自動巡回システムが最新のトピックをスキャンしています。',
        'url': 'https://www.google.com/search?q=コーヒーイベント',
        'image': (
            'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=600&q=80'
        ),
    })

  return events


def main():
  print(f'[{datetime.now()}] 高精度・自動巡回エンジン稼働中...')
  live_events = fetch_live_coffee_events()

  with open('events.json', 'w', encoding='utf-8') as f:
    json.dump(live_events, f, ensure_ascii=False, indent=4)

  print(f'[{datetime.now()}] 成功: {len(live_events)} 件のイベントを同期しました。')


if __name__ == '__main__':
  main()
