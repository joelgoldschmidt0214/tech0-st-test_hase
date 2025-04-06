import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

# --- 地点定義データの取得と処理 (XML対応) ---
PRIMARY_AREA_URL = "https://weather.tsukumijima.net/primary_area.xml"

@st.cache_data(ttl=3600)
def get_location_data_from_xml():
    """地点定義XMLを取得してパースし、JSONライクな構造に変換する"""
    try:
        response = requests.get(PRIMARY_AREA_URL)
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
        return location_list
    except requests.exceptions.RequestException as e:
        st.error(f"地点情報の取得に失敗しました: {e}")
        return None
    except ET.ParseError as e:
        st.error(f"地点情報のXMLパースに失敗しました: {e}")
        return None
    except Exception as e:
        st.error(f"地点情報の処理中に予期せぬエラーが発生しました: {e}")
        return None

# --- ここからメイン処理 ---
location_data = get_location_data_from_xml()

if location_data:
    # 都道府県リストを作成
    prefecture_list = [pref['name'] for pref in location_data]

    # --- デフォルト値の設定 ---
    DEFAULT_PREF = "東京都"
    DEFAULT_CITY = "東京"

    # デフォルト都道府県のインデックスを探す
    try:
        default_pref_index = prefecture_list.index(DEFAULT_PREF)
    except ValueError:
        st.warning(f"デフォルトの都道府県 '{DEFAULT_PREF}' が見つかりません。リストの先頭を使用します。")
        default_pref_index = 0 # 見つからなければ先頭(0)をデフォルトにする

    # --- Streamlit UI ---
    st.title("天気アプリ")
    st.write("調べたい地域を選んでください。")

    # 1. 都道府県選択 (indexを指定してデフォルト値を設定)
    selected_prefecture_name = st.selectbox(
        "都道府県を選んでください。",
        prefecture_list,
        index=default_pref_index # ここでデフォルトインデックスを指定
    )

    # 2. 地域選択
    selected_cities = []
    city_list = []
    default_city_index = 0 # 地域のデフォルトインデックス初期値

    if selected_prefecture_name:
        # 選択された都道府県のcitiesリストを検索
        for pref_data in location_data:
            if pref_data['name'] == selected_prefecture_name:
                selected_cities = pref_data['cities']
                city_list = [city['name'] for city in selected_cities]

                # --- 選択された都道府県がデフォルト都道府県の場合のみ、デフォルト地域を探す ---
                if selected_prefecture_name == DEFAULT_PREF:
                    try:
                        default_city_index = city_list.index(DEFAULT_CITY)
                    except ValueError:
                        st.warning(f"'{selected_prefecture_name}' 内にデフォルトの地域 '{DEFAULT_CITY}' が見つかりません。リストの先頭を使用します。")
                        default_city_index = 0 # 見つからなければ先頭(0)
                else:
                    # デフォルト都道府県以外が選択された場合は、地域のデフォルトは先頭(0)にする
                    default_city_index = 0
                break # 都道府県が見つかったらループを抜ける

    # 地域selectbox (indexを指定してデフォルト値を設定)
    # keyを設定して、都道府県が変わったときに地域selectboxの状態をリセットさせる
    selected_city_name = st.selectbox(
        "地域を選んでください。",
        city_list,
        index=default_city_index, # デフォルトインデックスを指定
        key=f"city_selectbox_{selected_prefecture_name}" # 都道府県名に基づいてキーを動的に変更
    )

    # 3. City Code取得 (ここからは変更なし)
    city_code = None
    if selected_city_name and selected_cities:
        for city_data in selected_cities:
            if city_data['name'] == selected_city_name:
                city_code = city_data['id']
                break

    if city_code:
        st.write(f"選択中の地域: {selected_prefecture_name} - {selected_city_name} (コード: {city_code})")

        # --- 天気予報の取得と表示 (変更なし) ---
        # ... (前のコードと同じ天気予報表示処理) ...
        url = f"https://weather.tsukumijima.net/api/forecast/city/{city_code}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            weather_json = response.json()

            # 現在の降水確率
            now_hour = datetime.now().hour
            weather_now = '--'
            if 'forecasts' in weather_json and len(weather_json['forecasts']) > 0 and 'chanceOfRain' in weather_json['forecasts'][0] and weather_json['forecasts'][0]['chanceOfRain']:
                cor = weather_json['forecasts'][0]['chanceOfRain']
                if cor:
                    time_slots = {'T00_06': (0, 6), 'T06_12': (6, 12), 'T12_18': (12, 18), 'T18_24': (18, 24)}
                    for key, (start, end) in time_slots.items():
                        if start <= now_hour < end:
                           weather_now = cor.get(key, '--')
                           break
                    # 24時以降（日付が変わる直前）の場合
                    if now_hour >= 24 or now_hour < 0 : # 通常ありえないが念のため
                         weather_now = cor.get('T18_24', '--') # 深夜は18-24の区分とするか、要件次第

            st.write(f"現在の降水確率: {weather_now if weather_now is not None else '--'}")

            # DataFrame表示
            data = []
            index_labels = ["今日", "明日", "明後日"]
            if 'forecasts' in weather_json:
                num_forecasts = len(weather_json['forecasts'])
                days_to_show = min(num_forecasts, 3)

                for i in range(days_to_show):
                    forecast = weather_json['forecasts'][i]
                    if 'chanceOfRain' in forecast and forecast['chanceOfRain'] is not None:
                        chance_of_rain = forecast['chanceOfRain']
                        rain_probabilities = [
                            chance_of_rain.get('T00_06', '--'),
                            chance_of_rain.get('T06_12', '--'),
                            chance_of_rain.get('T12_18', '--'),
                            chance_of_rain.get('T18_24', '--')
                        ]
                        data.append(rain_probabilities)
                    else:
                        data.append(['--'] * 4)

                if data:
                    df = pd.DataFrame(
                        data,
                        index=index_labels[:days_to_show],
                        columns=['0-6時', '6-12時', '12-18時', '18-24時']
                    )
                    st.dataframe(df)
                else:
                     st.warning("降水確率データを表示できませんでした。")
            else:
                st.warning("天気予報データが見つかりません。")

        except requests.exceptions.RequestException as e:
            st.error(f"天気予報の取得に失敗しました: {e}")
        except Exception as e:
            st.error(f"天気予報の処理中にエラーが発生しました: {e}")

    else:
        if selected_prefecture_name and selected_city_name:
             st.warning(f"選択された地域 ({selected_city_name}) のコードが見つかりませんでした。")
        # else: # 初期表示時などはメッセージ不要な場合もある
        #      st.info("都道府県と地域を選択してください。")

else:
    st.error("アプリケーションの初期化に失敗しました。地点情報を取得できません。")