import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.font_manager as fm

# 日本語フォント設定（macOS用）
font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
font_prop = fm.FontProperties(fname=font_path)

# CSVファイルの読み込み（感性語辞書）
df_dict = pd.read_csv("kansei_dict_.csv")

# データ構造を辞書形式に変換
kansei_dict_by_context = {}
for _, row in df_dict.iterrows():
    word = row["感性語"]
    age = row["世代"]
    region = row["地域"]
    category = row["印象カテゴリ"]
    score = row["スコア"]
    
    if word not in kansei_dict_by_context:
        kansei_dict_by_context[word] = {}
    kansei_dict_by_context[word][(age, region)] = (category, score)

# カテゴリマップをCSVから自動生成
category_map = {}
for _, row in df_dict.iterrows():
    word = row["感性語"]
    category = row["印象カテゴリ"]
    if category not in category_map:
        category_map[category] = []
    if word not in category_map[category]:
        category_map[category].append(word)

# Streamlit UI
st.title("ブランド印象の感性評価ツール")

age_group = st.selectbox("世代を選択してください", sorted(df_dict["世代"].unique()))
region = st.selectbox("地域を選択してください", sorted(df_dict["地域"].unique()))

brand_inputs = {}
cols = st.columns(3)
brand_list = ["ブランドA", "ブランドB", "ブランドC"]

for idx, brand in enumerate(brand_list):
    with cols[idx]:
        st.subheader(f"{brand}（最大5語）")
        selected_words = set()
        for category, words in category_map.items():
            st.markdown(f"**{category}**")
            for word in words:
                if st.checkbox(f"{word}", key=f"{brand}_{category}_{word}"):
                    selected_words.add(word)
        if len(selected_words) > 5:
            st.error(f"{brand} は最大5語までです。現在 {len(selected_words)} 語選択されています。")
        brand_inputs[brand] = " ".join(list(selected_words)[:5])

if st.button("評価する"):
    all_results = []
    total_scores = {}
    for brand, text in brand_inputs.items():
        category_scores = defaultdict(float)
        total_score = 0
        for word in text.split():
            if word in kansei_dict_by_context:
                context_data = kansei_dict_by_context[word]
                if (age_group, region) in context_data:
                    category, score = context_data[(age_group, region)]
                elif "default" in context_data:
                    category, score = context_data["default"]
                else:
                    continue
                category_scores[category] += score
                total_score += score
        total_scores[brand] = total_score
        for category, score in category_scores.items():
            all_results.append({"ブランド": brand, "印象カテゴリ": category, "スコア": score})

    df_result = pd.DataFrame(all_results)
    pivot_df = df_result.pivot(index="印象カテゴリ", columns="ブランド", values="スコア").fillna(0)

    fig, ax = plt.subplots(figsize=(10, 6))
    pivot_df.plot(kind="bar", ax=ax)
    ax.set_title(f"{age_group}（{region}）におけるブランド印象カテゴリ比較", fontproperties=font_prop)
    ax.set_xlabel("印象カテゴリ", fontproperties=font_prop)
    ax.set_ylabel("スコア", fontproperties=font_prop)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontproperties=font_prop)
    ax.legend(prop=font_prop)
    st.pyplot(fig)

    st.subheader("スコア詳細")
    st.dataframe(df_result)

    st.subheader("ブランド別 総合スコア")
    for brand, score in total_scores.items():
        st.metric(label=brand, value=round(score, 2))