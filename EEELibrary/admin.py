import json

import psutil
import getmac
import socket
import platform
import requests
import schedule
import datetime
import time
import jwt

# 관리자 기능 제공
class AdminFunction:
    cache_bypass_key = None
    cache_bypass_token = None

    def __init__(self):
        cache_bypass_key = {}
        cache_bypass_token = {}
        self.initCache()

    def initCache(self):
        # 자정마다 key와 token 초기화
        schedule.every().day.at("00:00").do(self.__init__)
        while True:
            schedule.run_pending()
            time.sleep(1)
        
    # AI 공격 탐지 알림(탐지된 계정 정보, 탐지 정확도 등) 확인
    def alertAttack(self, from_url, to_url, attack_json):
        # # API: API로 AI 에게서 공격 알림 받기
        # from_url = ""
        # response = requests.post(from_url)
        #
        # if response.status_code == 200:
        #     attack_json = response.json()
        # else:
        #     pass

        # 데이터가 맞는지 검증
        attack_data = json.loads(attack_json)
        attr_keys = ("user", "detected_time", "alarm_created_time", "resource_prediction",
                     "recommend_manage", "mouse_file_list", "resource_file_list")
        if all(attr in attack_data for attr in attr_keys):
            # 관리자에게 AI 공격 알림 정보 전달
            # done: False - 관리자 확인 전 / True - 관리자 확인 후
            alert_data = json.dumps(dict({"done": False}, **attack_data))
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            response = requests.post(to_url, data=alert_data, verify=False, headers=headers)
            return response
        else:
            raise AttributeError("Wrong json data")

    # 계정 차단 및 벌점 기능 -> 회사의 user 모델에 따른 별도 구현 필요
    def accountManage(self):
        raise NotImplementedError()

    # by-pass 기능(AI 탐지를 일정 기간 동안 by-pass 할 수 있는 key, token 발급 및 refresh 기능)
    def genBypassKey(self, key_name, user):
        if self.cache_bypass_key.get(key_name):
            return ValueError("Same key name exists")

        self.cache_bypass_key[key_name] = user

    def genBypassToken(self, key_name, user):
        target_user = self.cache_bypass_key.get(key_name)
        if target_user:
            # user 계정이 valid한지 검사(차단된 계정인지)

            # 계정이 일치하는지 확인
            if target_user == user:
                # 맞다면 token 발급
                return jwt.encode({"user": user, "time": datetime.datetime.now()}, algorithm="HS256")

        return PermissionError("유효하지 않은 요청입니다.")
