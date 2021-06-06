# 수집한 resoucre file을 시간(T)을 단위로 split
# base_data_save 이전에 수행
import ai_pred_pattern as ap
import os 
import pandas as pd

# resource file에 num(T를 통해 계산)개의 block으로 file을 나눠 저장함
# file(file dictionary)
def resource_time_split_save(file):
    t = 15 #데이터 수집 간격(단위: 1sec)
    T = 300 #데이터 블럭 크기(단위: 1sec)
    num = (int)(T/t) #한 데이터 블럭 안의 데이터 개수
    
    df = pd.read_csv(file['path'], engine='python')
    
    new_filename = file['filename']+"_"
    write_file_path = file['upper_dir']+'/'+new_filename
    
    if df.shape[0]%num == 0:
        for i in range(0,df.shape[0]//num):
            total = pd.DataFrame()
            total = pd.concat([total,df[i*num:(i+1)*num]])
            total.to_csv(write_file_path +str(int(i))+'.csv', header=True, index=False)               
    else:
        for i in range(0,df.shape[0]//num+1):
            total = pd.DataFrame()
            # 마지막에 num개 안되는 block은 버림
            if i!=(df.shape[0]//num):
                total = pd.concat([total,df[i*num:(i+1)*num]])
                total.to_csv(write_file_path +str(int(i))+'.csv', header=True, index=False)
    
    os.remove(file['path'])         # 기존 파일 삭제

if __name__ == "__main__":
    r_data_dir = './data/resource' 
    user_list = os.listdir(r_data_dir)      

    r_files = []
    for user in user_list:
        r_files.extend(ap.find_files(r_data_dir, user))
    
    for file in r_files:
        resource_time_split_save(file)
    
    print("Done!")