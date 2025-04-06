import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import logging # エラーログ用に追加

# --- 定数 ---
PRIMARY_AREA_URL = "https://weather.tsukumijima.net/primary_area.xml"
WEATHER_API_URL_BASE = "https://weather.tsukumijima.net/api/forecast/city/"
DEFAULT_PREF = "東京都"
DEFAULT_CITY = "東京"
CACHE_TTL = 3600 # キャッシュ有効期間（秒）

# --- ロギング設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- データ取得関数 (キャッシュ付き) ---
@st.cache_data(ttl=CACHE_TTL)
def get_location_data_from_xml():
    """地点定義XMLを取得してパースし、JSONライクな構造に変換する"""
    try:
        response = requests.get(PRIMARY_AREA_URL, timeout=10) # タイムアウト追加
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        root = ET.fromstring(response.text)

        location_list = []
        for pref_elem in root.findall('.//pref'):
            pref_name = pref_elem.get('title')
            if not pref_name: continue

            cities_list = []
            for city_elem in pref_elem.findall('./city'):
                city_id = city_elem.get('id')
                city_name = city_elem.get('title')
                if city_id and city_name:
                    cities_list.append({'id': city_id, 'name': city_name})

            if cities_list:
                location_list.append({'name': pref_name, 'cities': cities_list})

        logging.info("地点情報を正常に取得・パースしました。")
        return location_list

    except requests.exceptions.Timeout:
        logging.error(f"地点情報の取得がタイムアウトしました: {PRIMARY_AREA_URL}")
        st.error("地点情報の取得がタイムアウトしました。しばらくしてから再試行してください。")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"地点情報の取得に失敗しました: {e}")
        st.error(f"地点情報の取得に失敗しました: {e}")
        return None
    except ET.ParseError as e:
        logging.error(f"地点情報のXMLパースに失敗しました: {e}")
        st.error(f"地点情報のXMLパースに失敗しました。")
        return None
    except Exception as e:
        logging.error(f"地点情報の処理中に予期せぬエラーが発生しました: {e}", exc_info=True)
        st.error(f"地点情報の処理中に予期せぬエラーが発生しました。")
        return None

def get_weather_forecast(city_code):
    """指定されたcity_codeの天気予報を取得する"""
    url = f"{WEATHER_API_URL_BASE}{city_code}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logging.info(f"天気予報を正常に取得しました: city_code={city_code}")
        return response.json()
    except requests.exceptions.Timeout:
        logging.error(f"天気予報の取得がタイムアウトしました: {url}")
        st.error("天気予報の取得がタイムアウトしました。しばらくしてから再試行してください。")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"天気予報の取得に失敗しました: {e}")
        st.error(f"天気予報の取得に失敗しました: {e}")
        return None
    except Exception as e: # JSONDecodeErrorなども拾う
        logging.error(f"天気予報の処理中に予期せぬエラーが発生しました: {e}", exc_info=True)
        st.error(f"天気予報の処理中に予期せぬエラーが発生しました。")
        return None

# --- Streamlit アプリケーション ---
def main():
    st.set_page_config(page_title="天気アプリ", layout="wide") # ページ設定
    st.title("天気アプリ")
    st.write("調べたい地域を選んでください。")

    location_data = get_location_data_from_xml()

    if not location_data:
        st.error("アプリケーションを初期化できません。地点情報を取得できませんでした。")
        return # 地点情報がなければ処理中断

    prefecture_list = [pref['name'] for pref in location_data]

    try:
        default_pref_index = prefecture_list.index(DEFAULT_PREF)
    except ValueError:
        logging.warning(f"デフォルト都道府県 '{DEFAULT_PREF}' が見つかりません。リストの先頭を使用します。")
        default_pref_index = 0

    selected_prefecture_name = st.selectbox(
        "都道府県を選んでください。",
        prefecture_list,
        index=default_pref_index
    )

    selected_cities = []
    city_list = []
    default_city_index = 0

    if selected_prefecture_name:
        for pref_data in location_data:
            if pref_data['name'] == selected_prefecture_name:
                selected_cities = pref_data['cities']
                city_list = [city['name'] for city in selected_cities]
                if selected_prefecture_name == DEFAULT_PREF:
                    try:
                        default_city_index = city_list.index(DEFAULT_CITY)
                    except ValueError:
                        logging.warning(f"'{selected_prefecture_name}' 内のデフォルト地域 '{DEFAULT_CITY}' が見つかりません。リストの先頭を使用します。")
                        default_city_index = 0
                else:
                    default_city_index = 0
                break

    selected_city_name = st.selectbox(
        "地域を選んでください。",
        city_list,
        index=default_city_index,
        key=f"city_selectbox_{selected_prefecture_name}" # 都道府県変更時のリセット用キー
    )

    city_code = None
    if selected_city_name and selected_cities:
        for city_data in selected_cities:
            if city_data['name'] == selected_city_name:
                city_code = city_data['id']
                break

    if not city_code:
        st.warning("地域を選択してください、または選択した地域のコードが見つかりません。")
        return # City Codeがなければ処理中断

    st.write(f"**選択中の地域:** {selected_prefecture_name} - {selected_city_name} (コード: {city_code})")
    st.divider() # 区切り線

    weather_json = get_weather_forecast(city_code)

    if not weather_json:
        # get_weather_forecast内でエラー表示済みなのでここでは何もしないか、追加メッセージ
        # st.error("天気予報データを取得できませんでした。")
        return # 天気情報がなければ処理中断

    # --- 現在の降水確率表示 ---
    st.subheader("現在の降水確率")
    now_hour = datetime.now().hour
    weather_now = '--'
    forecast_today = weather_json.get('forecasts', [{}])[0] # 今日の予報を安全に取得
    chance_of_rain_today = forecast_today.get('chanceOfRain')

    if chance_of_rain_today: # Noneでないことを確認
        time_slots = {'T00_06': (0, 6), 'T06_12': (6, 12), 'T12_18': (12, 18), 'T18_24': (18, 24)}
        found_slot = False
        for key, (start, end) in time_slots.items():
            # now_hourが24時以降になることは通常ないが、ロジックとして18-24に含める
            current_hour_in_slot = (start <= now_hour < end) or (key == 'T18_24' and now_hour >= end)
            if current_hour_in_slot:
                weather_now = chance_of_rain_today.get(key, '--')
                found_slot = True
                break
        # どのスロットにも当てはまらない場合（通常ありえないが念のため）
        if not found_slot and now_hour >= 0:
             weather_now = chance_of_rain_today.get('T18_24', '--') # フォールバックとして最後の時間帯

    st.metric(label="現在時刻の含まれる時間帯", value=f"{weather_now}")
    st.divider() # 区切り線

    # --- 3日間の降水確率DataFrame表示 ---
    st.subheader("時間帯別 降水確率")
    data = []
    index_labels = ["今日", "明日", "明後日"]
    forecasts = weather_json.get('forecasts', [])
    days_to_show = min(len(forecasts), 3)

    for i in range(days_to_show):
        forecast = forecasts[i]
        chance_of_rain = forecast.get('chanceOfRain')
        if chance_of_rain:
            rain_probabilities = [
                chance_of_rain.get('T00_06', '--'),
                chance_of_rain.get('T06_12', '--'),
                chance_of_rain.get('T12_18', '--'),
                chance_of_rain.get('T18_24', '--')
            ]
            data.append(rain_probabilities)
        else:
            logging.warning(f"{index_labels[i]} の降水確率データ(chanceOfRain)が見つかりません。city_code={city_code}")
            data.append(['--'] * 4)

    if data:
        df = pd.DataFrame(
            data,
            index=index_labels[:days_to_show],
            columns=['0-6時', '6-12時', '12-18時', '18-24時']
        )
        st.dataframe(df, use_container_width=True) # コンテナ幅に合わせる
    else:
        st.warning("降水確率データを表示できませんでした。")


if __name__ == "__main__":
    main()