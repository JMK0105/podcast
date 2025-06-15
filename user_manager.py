# user_manager.py
import streamlit as st
import pandas as pd

# 사용자 목록을 DataFrame으로 불러오기
def get_user_df(worksheet):
    try:
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        print(f"[get_user_df] 오류: {e}")
        return pd.DataFrame()

# 해당 학번(ID)이 이미 등록된 사용자 여부 확인
def is_existing_user(df, user_id):
    return "ID" in df.columns and user_id in df["ID"].astype(str).values

# 사용자 row 반환
def register_user(ws, user_id, name, grade, major, style):
    try:
        st.info(f"✅ 저장 시도: {[user_id, name, grade, major, style]}")
        ws.append_row([user_id, name, grade, major, style])
        st.success("✅ Google 시트에 저장 성공")
        return True
    except Exception as e:
        st.error(f"❌ Google 시트 저장 실패: {e}")
        return False
