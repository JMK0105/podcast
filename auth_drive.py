from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os


def authenticate_and_get_service():
    # 인증 설정 파일 경로
    gauth = GoogleAuth()

    # 사용자 인증 방식 설정
    gauth.LocalWebserverAuth()  # 처음 실행 시 브라우저 팝업됨

    drive = GoogleDrive(gauth)
    service = gauth.service  # Google Drive API 서비스 객체
    return service


# 📌 사용 시 주의:
# - 프로젝트 폴더에 client_secrets.json 필요
# - Google Drive API & OAuth2 API 활성화 필요 (GCP 콘솔)
# - 최초 실행 시 구글 로그인창 뜸 → 이후 refresh_token으로 자동 유지됨
