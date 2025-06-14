from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os


def authenticate_and_get_drive():
    # PyDrive2 인증 객체 생성
    gauth = GoogleAuth()

    # 인증: 처음 실행 시 브라우저 팝업으로 로그인 필요
    gauth.LocalWebserverAuth()

    # 인증 완료 후 Drive 객체 생성
    drive = GoogleDrive(gauth)

    return drive  # GoogleDrive 객체 반환
