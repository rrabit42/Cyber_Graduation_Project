import os
# info, warning 제거
os.environ['TF_CPP_MIN_LOG_LEVEL'] ='2'
import tensorflow as tf
import pandas as pd
import numpy as np
import datetime
from distutils.dir_util import copy_tree
import shutil
import json
import requests
import math
import joblib
import sys

model_dir = './model/'
m_pred_dir = './pred/mouse' 
r_pred_dir = './pred/resource'
m_feature_file = './m_feature_extract.csv'
r_feature_file = './r_feature_extract.csv'


def set_yesterday_str():
    yesterday = datetime.datetime.today() + datetime.timedelta(days=-1) 
    yesterday_str = yesterday.strftime("%Y%m%d")
    return yesterday_str

# predict을 대기하고 있는 중복된 user 찾기
def find_user():
    user = None
    while True:
        m_user_list = os.listdir(m_pred_dir)            # mouse predict 대기 user list
        r_user_list = os.listdir(r_pred_dir)            # resource predict 대기 user list
        for user in m_user_list:
            if user in r_user_list:
                break
            else:
                user = None
        if user is not None:
            if len(os.listdir(m_pred_dir+'\\'+user)) > 0:       # 폴더 하위 파일 생긴 경우만 break(폴더만 생겨서 break 되는 가능성 제거)
                if len(os.listdir(r_pred_dir+'\\'+user)) > 0:
                    break
    return user

# ~/target_dir/user/file(s) 정보 수집
def find_files(target_dir_path, user):
    dir_path = target_dir_path+'\\'+user
    file_dict_list = []
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)                # 전체 path
        user_index = file_path.find('\\')
        filename_index = file_path.rfind('\\')
        extension_index = file_path.rfind('.')          # 확장자 시작 직전 인덱스
        upper_dir = file_path[:filename_index]          # 상위 디렉토리
        filename = file_path[filename_index+1:extension_index]     # 파일명
        user = file_path[user_index+1:filename_index]   # file의 owner
        file_dict_list.append({"path":file_path, "user":user, "upper_dir":upper_dir, "filename":filename})
    return file_dict_list

# ~/target_dir/user/file 정보 수집
def find_file(target_dir_path, user):
    dir_path = target_dir_path+'\\'+user
    file_dict_list = []
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)                # 전체 path
        user_index = file_path.find('\\')
        filename_index = file_path.rfind('\\')
        extension_index = file_path.rfind('.')          # 확장자 시작 직전 인덱스
        upper_dir = file_path[:filename_index]          # 상위 디렉토리
        filename = file_path[filename_index+1:extension_index]     # 파일명
        user = file_path[user_index+1:filename_index]   # file의 owner
        file_dict_list.append({"path":file_path, "user":user, "upper_dir":upper_dir, "filename":filename})
        break
    return file_dict_list

# mouse file에 'action interval'을 추가하고 button-state의 7가지 경우의 수를 'button state' 열로 나타냄
# 그 외에 이동방향, 이동거리 등을 계산하여 열로 나타냄, 불필요한 열 제거
# file(file dictionary)
def mouse_parse_save(file):
    df = pd.read_csv(file['path'], engine='python')
    
    # action interval 은 action 간의 시간 차이
    # button state의 경우의 수는 7가지
    # (NoButton-Move, NoButton-Drag, Nobutton-Scrool, Left-Pressed, Left-Released, Right-Pressed, Right-Released)
    df.insert(len(df.columns),'action interval',np.nan)
    df.insert(len(df.columns),'button state',np.nan)
    df.insert(len(df.columns), 'move distance', np.nan)
    df.insert(len(df.columns), 'move way', np.nan)
    for i in range(0, df.shape[0]):
        # action interval
        if i == 0:
            df['action interval'].iloc[i] = 0.0
        else:
            df['action interval'].iloc[i] = df['client timestamp'].iloc[i] - df['client timestamp'].iloc[i-1]
        # button state
        state = df['state'].iloc[i]
        ButtonState = ""
        if(state == 'Move'):
            ButtonState = 'Move'
        elif(state == 'Drag'):
            ButtonState = 'Drag'
        elif(state == 'Scrool'):
            ButtonState = 'Scroll'
        elif(state == 'Pressed'):
            if(df['button'].iloc[i]=='Left'):
                ButtonState = 'Left_Pressed'
            else:
                ButtonState = 'Right_Pressed'
        elif(state == 'Released'):
            if(df['button'].iloc[i]=='Left'):
                ButtonState = 'Left_Released'
            else:
                ButtonState = 'Right_Released'
        df['button state'].iloc[i] = ButtonState
        # 기존 Scrool의 Y좌표는 X좌표와 동일 -> Y좌표를 앞선 action의 Y좌표로 변경
        # Scrool Y 좌표 변경은 move distance, move way 구하기 전 처리해야함
        if (state == 'Scrool'):
            if i != 0 :
                df['y'].iloc[i] = df['y'].iloc[i-1]
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
    
    df = df.drop(['client timestamp', 'state', 'button'], axis=1)
    
    yesterday_str = set_yesterday_str()
    new_filename = yesterday_str+'_'+file['user']+'_'+file['filename']
    write_file_path = file['upper_dir']+'/'+new_filename
    
    df.to_csv(write_file_path+'.csv', header=True, index=False)
    os.remove(file['path'])         # 기존 파일 삭제

# mouse file feature extract and save
def mouse_feature_extract(path, filename, label):
    df = pd.read_csv(path)

    # feature extract dict
    extract = {}
    # 파일명 저장
    extract['filename'] = filename
    # label 저장
    extract['label'] = label
    # 생성 시간
    time = datetime.datetime.today()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    extract['time'] = time

    # mouse action이 하나도 없는 경우(idle)
    if df.shape[0] == 0:
        extract_df = pd.DataFrame([extract])
        # extract_df.to_csv(m_feature_file, mode='a', index=False, header=None)     # idle 데이터 저장x 
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
    
    # extract to dataframe and save
    extract_df = pd.DataFrame([extract])
    if(os.path.isfile(m_feature_file)):
        extract_df.to_csv(m_feature_file, mode='a', index=False, header=None)
    else:
        extract_df.to_csv(m_feature_file, mode='w', index=False)
    
    return extract_df

# file_dict_list에 있는 파일에서 feature 추출하고 파일 저장
# 각 file의 feature들을 합쳐서 하나의 dataframe으로 반환 
def mouse_preprocess(file_dict_list):
    # empty dataframe
    mouse_data = pd.DataFrame()
    for i in range(len(file_dict_list)):
        data = mouse_feature_extract(file_dict_list[i]['path'], file_dict_list[i]['filename'], file_dict_list[i]['user'])
        mouse_data = mouse_data.append(data)
    return mouse_data

# resource file을 유용한 형태로 변환하여 저장
def resource_parse_save(file):
    df = pd.read_csv(file['path'])
    
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
    
    # datatime parsing
    featureVector=[None] * 5
    for i in range(df.shape[0]):
        date = df.iloc[i,0] # 날짜 column 가져옴
        arr = date.split(' ')

        ymd = arr[0].split('/')
        month = int(ymd[0])
        day = int(ymd[1])
        year = int(ymd[2])

        time = arr[1].split(':')
        hour = int(time[0])
        minute = int(time[1])

        yoli = datetime.date(year, month, day).weekday()

        features = np.array([month, day, yoli, hour, minute])
        featureVector = np.column_stack((featureVector,features))
    df = df.drop(['DateTime'], axis=1)

    # 빈칸은 mean값으로 채우기
    df_columns = df.columns
    for i in range(len(df_columns)):
        col = df_columns[i]
        if(df[col].dtypes == 'object'):
            df[col] = df[col].replace(r'[\s]',np.nan,regex=True)
        mean = df[col].astype('float64').mean()
        df[col] = df[col].fillna(mean)

    featureVector = featureVector[:,1:] # 첫번째 행이 None이라
    date_df = pd.DataFrame(data=featureVector,
                        index=["Month", "Day", "Yoli", "Hour", "Minute"])
    date_df = date_df.transpose()
    df = pd.concat([df, date_df],axis=1)

    yesterday_str = set_yesterday_str()
    new_filename = yesterday_str+'_'+file['user']+'_'+file['filename']
    write_file_path = file['upper_dir']+'/'+new_filename
    df.to_csv(write_file_path+'.csv', index=False)

    os.remove(file['path'])         # 기존 파일 삭제

# resource file feature extract, save, and return datframe
def resource_feature_extract(path, filename, label):
    df = pd.read_csv(path)
    
    df = df.astype('float64')
    df = df.drop(['Month', 'Day', 'Yoli', 'Hour', 'Minute'], axis=1)

    # feature extract dict
    extract = {}

    # 파일명 저장
    extract['filename'] = filename
    # label 저장
    extract['label'] = label
    # 생성 시간
    time = datetime.datetime.today()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    extract['time'] = time

    extract_df = pd.DataFrame([extract])
    
    columns = df.columns
    for i in range(df.shape[0]):
        new_columns = str(i+1)+'_'+columns
        row_df = pd.DataFrame([df.iloc[i].values], columns=new_columns)
        extract_df = pd.concat([extract_df, row_df], axis=1)     
    
    if(os.path.isfile(r_feature_file)):
        extract_df.to_csv(r_feature_file, mode='a', index=False, header=None)
    else:
        extract_df.to_csv(r_feature_file, mode='w', index=False)
    return extract_df

# file_dict_list에 있는 파일 feature를 추출하여 저장
# 각 file의 feature들을 합쳐서 하나의 dataframe으로 반환 
def resource_preprocess(file_dict_list):
    resource_data = pd.DataFrame()
    for i in range(len(file_dict_list)):
        data = resource_feature_extract(file_dict_list[i]['path'], file_dict_list[i]['filename'], file_dict_list[i]['user'])
        resource_data = resource_data.append(data)
    return resource_data

# model 사용을 위한 dataframe 전처리
# df(scaling 대상), filename(저장된 scaler 이름)
def scaling(df, filename):
    df = df.fillna(0)
    scaler = joblib.load(model_dir+filename)
    sc_data = scaler.transform(df)
    return sc_data

# AI를 통해 패턴 owner 예측 확률 반환
def predict_pattern(user, data, kind):
    yesterday_str = set_yesterday_str()
    model_name = model_dir+yesterday_str+'_'+user+'_model'
    if(kind == 'mouse'):
        model_name += '_m.h5'
    else:
        model_name += '_r.h5'
    # model load
    model = tf.keras.models.load_model(model_name)
    # model pred
    pred = model.predict(data)
    return pred

# directory 이동
# user(login한 user), preDir(이전 directory path)
def preDir_move_patternDir(user, preDir):
    m_pred_user_dir = preDir+'/mouse/'+ user
    r_pred_user_dir = preDir+'/resource/'+ user
    m_data_user_dir = './pattern/mouse/'
    r_data_user_dir = './pattern/resource/'

    copy_tree(m_pred_user_dir, m_data_user_dir)
    shutil.rmtree(m_pred_user_dir)
    copy_tree(r_pred_user_dir, r_data_user_dir)
    shutil.rmtree(r_pred_user_dir)

# pattern 파일에 labeling
def modify_pattern_label(file_dict_list, kind, label):
    path = m_feature_file       # path의 default는 mouse path
    if kind == 'resource':
        path = r_feature_file
    df = pd.read_csv(path)
    
    for file in file_dict_list:
        df.loc[df['filename']==file['filename'], 'label'] = label
    
    df.to_csv(path, index=False)

# request로 보낼 데이터 만들기
def make_sendData(issue, user, label, m_pred, r_pred, m_files, r_files):
    time = datetime.datetime.today()
    time = time.strftime("%Y-%m-%d %H:%M:%S.%f")

    m_file_list =[]
    for file in m_files:
        m_file_list.append(file['filename'])
    m_file_string = ','.join(m_file_list)
    r_file_list =[]
    for file in r_files:
        r_file_list.append(file['filename'])
    r_file_string = ','.join(r_file_list)
    m_pred = m_pred[0][0]
    r_pred = r_pred[0][0]

    sendData = {'user':user, 
    'time':time, 
    'mouse_prediction': str(round(m_pred,5)),
    'resource_prediction': str(round(r_pred,5)), 
    'type':issue, 
    'label':label, 
    'mouse_file_list': m_file_string, 
    'resource_file_list': r_file_string
    }
    return sendData

# CERT 팀에게 경고 알리는 함수
def alert_to_CERT(data, url):
    data = json.dumps(data)
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    res = requests.post(url, data=data, verify=False , headers=headers)    # verify는 SSL인증서 체크 관련 내용
    return res


if __name__ == "__main__":
    user = sys.argv[1]
    by_pass = sys.argv[2]
    print(user +', '+ by_pass + " in python")
    
    # 0 ~ < threshold : user 차단
    # threshold <= ~ < tolerance : 허용&벌점부여
    # tolerance <= ~ 1 : 허용 
    m_threshold = 0.9           # 마우스 임계값
    m_tolerance = 0.95          # 마우스 벌점범위
    r_threshold = 0.9           # 리소스 임계값
    r_tolerance = 0.95          # 리소스 벌점범위
    idle_r_threshold = 0.95     # 마우스 idle인 경우, 임계값
    idle_r_tolerance = 0.98   # 마우스 idle인 경우, 벌점 범위

    yesterday_str = set_yesterday_str()
    url = 'http://localhost:8222/cert'          # proxy 주소
    
    model_dir = './model/'
    m_pred_dir = './pred/mouse' 
    r_pred_dir = './pred/resource'
    m_feature_file = './m_feature_extract.csv'
    r_feature_file = './r_feature_extract.csv'


    # Resource
    # R file에서 필요한 column 구성하여 저장
    r_files = find_file(r_pred_dir, user)
    for file in r_files:
        resource_parse_save(file)
    # 수정된 R 파일 정보 저장  
    r_files = find_file(r_pred_dir, user)
    # R file에서 feature 추출 및 csv로 저장, 반환
    r_data = resource_preprocess(r_files)
    print(r_data.shape)
    # preprocess
    r_scaler_name = yesterday_str+'_'+user+'_scaler_r.gz'
    r_data = r_data.drop(['filename', 'label', 'time'], axis=1)
    r_data = scaling(r_data, r_scaler_name)
    # AI
    # 사용자 패턴 owner 예측
    r_pred = predict_pattern(user, r_data, 'resource')  # resource AI가 예측한 해당 user일 확률

    # Mouse
    # M file에서 필요한 column 구성하여 저장
    m_files = find_file(m_pred_dir, user)
    for file in m_files:
        mouse_parse_save(file)
    # 수정한 M 파일 정보 저장
    m_files = find_file(m_pred_dir, user)
    # M file에서 feature 추출 및 csv로 저장, 반환
    m_data = mouse_preprocess(m_files)
    print(m_data.shape)
    if(m_data.shape != (1,3)):          # 마우스가 idle이 아닌 경우
        # preprocess
        m_scaler_name = yesterday_str+'_'+user+'_scaler_m.gz'
        m_data = m_data.drop(['filename', 'label', 'time'], axis=1)
        m_data = scaling(m_data, m_scaler_name)
        # AI
        # 사용자 패턴 owner 예측
        m_pred = predict_pattern(user, m_data, 'mouse')     # mouse AI가 예측한 해당 user일 확률
    else:
        m_pred = np.array([[-1.0]])     # AI 예측값이 -1이면 idle로 마우스 예측은 하지 않은 것으로 가정
    
    print(str(m_pred[0][0])+', '+ str(r_pred[0][0]))
    
    # ./pred/mouse/user/M, ./pred/resource/user/R file을 
    # ./pattern/mouse/~, ./pattenr/resource/~ 로 이동
    preDir_move_patternDir(user, './pred')

    # bypass 권한 있으면, AI 판단 후 처리 과정 거치지 않음
    if by_pass != "PASS":
        if m_pred == -1:        # idle인 경우
            if r_pred < idle_r_threshold:
                label = 'unknown'
                modify_pattern_label(r_files, 'resource', label)
                sendData = make_sendData(4, user, label, m_pred, r_pred, m_files, r_files)
                res = alert_to_CERT(sendData, url)        # 관리자에게 idle 차단 알림(block : 4)
            elif r_pred < idle_r_tolerance:
                sendData = make_sendData(5, user, user, m_pred, r_pred, m_files, r_files)
                res = alert_to_CERT(sendData, url)    # 관리자에게 idle 벌점 알림(demerit : 5)
        else:      # idle이 아닌 경우
            # true) file들 unknown으로 labeling, CERT(proxy 거쳐서 서버로)
            # elif true) CERT(proxy 거쳐서 서버로)
            if m_pred < m_threshold or r_pred < r_threshold :
                label = 'unknown'
                modify_pattern_label(m_files, 'mouse', label)
                modify_pattern_label(r_files, 'resource', label)
                sendData = make_sendData(2, user, label, m_pred, r_pred, m_files, r_files)
                res = alert_to_CERT(sendData, url)        # 관리자에게 차단 알림(block : 2)
            elif m_pred < m_tolerance or r_pred < r_tolerance:
                sendData = make_sendData(3, user, user, m_pred, r_pred, m_files, r_files)
                res = alert_to_CERT(sendData, url)    # 관리자에게 벌점 알림(demerit : 3)