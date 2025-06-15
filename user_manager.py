# user_manager.py

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
def get_user_row(df, user_id):
    return df[df["ID"].astype(str) == user_id].iloc[0]

# 신규 사용자 정보 시트에 추가
def register_user(worksheet, user_id, name, grade, major, style):
    try:
        row = [user_id, name, grade, major, style]
        worksheet.append_row(row)
        print(f"[register_user] 등록 완료: {row}")
        return True
    except Exception as e:
        print(f"[register_user] 등록 실패: {e}")
        return False
