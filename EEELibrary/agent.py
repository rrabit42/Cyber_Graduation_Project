import pandas as pd
import numpy as np
import datetime
import math
import os
import requests

class mouse:
    def __init__(self, filename, label):
        self.filename = filename
        self.label = label
        mouse_dir = os.environ.get('COLLECT_DIR', '')
        self.path = mouse_dir+filename
        self.time = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    
    # 이동방향, 이동거리 등을 계산하여 열로 나타냄
    def parse(self):
        df = pd.read_csv(self.path, engine='python')
        
        # action interval 은 action 간의 시간 차이
        # button state의 경우의 수는 7가지
        # (Move, Drag, Scroll, Left-Pressed, Left-Released, Right-Pressed, Right-Released)
        df.insert(len(df.columns), 'move distance', np.nan)
        df.insert(len(df.columns), 'move way', np.nan)
        
        for i in range(0, df.shape[0]): 
            # move distance
            if i == 0:
                df['move distance'].iloc[i] = 0.0
            else:
                x1 = df['x'].iloc[i-1]
                y1 = df['y'].iloc[i-1]
                x2 = df['x'].iloc[i]
                y2 = df['y'].iloc[i]
                distance = math.sqrt(math.pow((x2 - x1), 2) + math.pow((y2 - y1),2))
                df['move distance'].iloc[i] = distance
            # move way
            move_way = np.nan
            if i != 0:
                xl = df['x'].iloc[i] - df['x'].iloc[i-1]
                yl = df['y'].iloc[i] - df['y'].iloc[i-1]
                if xl >= 0 and yl >= 0:
                    if xl > yl: move_way = 1
                    else: move_way = 2
                elif xl <= 0 and yl >= 0:
                    if -xl > yl: move_way = 4
                    else: move_way = 3
                elif xl <= 0 and yl <= 0:
                    if -xl > -yl: move_way = 5
                    else: move_way = 6
                elif xl >= 0 and yl <= 0:
                    if xl > -yl: move_way = 8
                    else: move_way = 7
            df['move way'].iloc[i] = move_way
        os.remove(self.path)
        return df
    
    # action에 대한 통계값 추출 
    def extract(self):
        df = self.parse()

        # feature extract dict
        extract = {}
        # 파일명 저장
        extract['filename'] = self.filename
        # label 저장
        extract['label'] = self.label
        # 생성 시간
        extract['time'] = self.time

        # mouse action이 하나도 없는 경우(idle)
        if df.shape[0] == 0:
            extract_df = pd.DataFrame([extract])
            return extract_df
        # 전체 액션 count
        total_action_count = df['button state'].count()
        # 각 action별 통계
        ButtonState_values = ['Move','Drag','Scroll','Left_Pressed','Left_Released','Right_Pressed','Right_Released']
        for i in range(len(ButtonState_values)):
            action = ButtonState_values[i]
            action_desc = df[df['button state']==action]['action interval'].describe()
            # 각 action별 count 비율
            action_count = action_desc['count']
            action_count_ratio = action_count/total_action_count
            key = action+'_ratio'
            extract[key] = action_count_ratio
            # 각 action 별 소요시간 (std, mean, 25%, 50%, 75%)
            statistics_list = ['mean', 'std', '25%', '50%', '75%']
            for j in range(len(statistics_list)):
                statistics = statistics_list[j]
                key = action+'_'+statistics
                extract[key] = action_desc[statistics]
            # 각 action, move way 별 통계(시간-50%, 거리-50%)
            for j in range(1,9):
                action_way = df[(df['button state']==action)& (df['move way']==j)]
                key = action+'_way_timeMedian_'+str(j)
                extract[key] = action_way['action interval'].describe()['50%']
                key = action+'_way_distanceMedian_'+str(j)
                extract[key] = action_way['move distance'].describe()['50%']
        
        # extract to dataframe
        extract_df = pd.DataFrame([extract])
        return extract_df
    
    # extracted pattern 서버로 전송
    def send(self, url):
        extract_df = self.extract()
        json_df = extract_df.to_json(orient = 'records')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        url = os.environ.get('M_PATTERN_URL', '')
        res = requests.post(url, data=json_df, verify=False , headers=headers)    # verify는 SSL인증서 체크 관련 내용
        return res


class resource:
    def __init__(self, filename, label):
        self.filename = filename
        self.label = label
        resource_dir = os.environ.get('COLLECT_DIR', '')
        self.path = resource_dir+filename
        self.time = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    # 칼럼명 통일
    def parse(self):
        df = pd.read_csv(self.path, engine='python')
        
         # resource file column명 통일
        df.columns = [
            "DateTime",
            "Memory\% Committed Bytes In Use",
            "Memory\Available MBytes",
            "Process(_Total)\% Processor Time",
            "Process(_Total)\Private Bytes",
            "Process(_Total)\Working Set",
            "Processor Information(_Total)\% Processor Time",
            "Processor Information(_Total)\% Processor Utility"
            ]
        
        # 빈칸은 mean값으로 채우기
        df_columns = df.columns
        for i in range(len(df_columns)):
            col = df_columns[i]
            if(df[col].dtypes == 'object'):
                df[col] = df[col].replace(r'[\s]',np.nan,regex=True)
            mean = df[col].astype('float64').mean()
            df[col] = df[col].fillna(mean)

        os.remove(self.path)
        return df
    
    # 배열 형태 변환
    def extract(self):
        df = self.parse()
        
        df = df.astype('float64')

        # feature extract dict
        extract = {}
        # 파일명 저장
        extract['filename'] = self.filename
        # label 저장
        extract['label'] = self.label
        # 생성 시간
        extract['time'] = self.time

        # extract to dataframe
        extract_df = pd.DataFrame([extract])
        # M x N 배열 -> 1 x NM 배열로 변환
        columns = df.columns
        for i in range(df.shape[0]):
            new_columns = str(i+1)+'_'+columns
            row_df = pd.DataFrame([df.iloc[i].values], columns=new_columns)
            extract_df = pd.concat([extract_df, row_df], axis=1) 
        return extract_df
    
    # extracted pattern 서버로 전송
    def send(self, url):
        extract_df = self.extract()
        json_df = extract_df.to_json(orient = 'records')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        url = os.environ.get('R_PATTERN_URL', '')
        res = requests.post(url, data=json_df, verify=False , headers=headers)    # verify는 SSL인증서 체크 관련 내용
        return res