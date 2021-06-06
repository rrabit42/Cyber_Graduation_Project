# 수집한 mouse file을 시간(T)을 단위로 split
# base_data_save 이전에 수행
import ai_pred_pattern as ap
import os 
import pandas as pd

# mouse filed에 client timestamp를 기준으로 T size로 file을 나눠 저장함
# file(file dictionary)
def mouse_time_split_save(file):
    T =  300000 # window size
    
    df = pd.read_csv(file['path'], engine='python')
    
    new_filename = file['filename']+"_"
    write_file_path = file['upper_dir']+'/'+new_filename
    c = 0     # window 번호
    start_i = 0   # winodw size로 자를 때 첫번째 인덱스
    
    for i in range(df.shape[0]):
        q = df.iloc[i]['client timestamp']//T
        if(q != c or i == df.shape[0]-1):
            data = df.iloc[start_i:i,:]
            if(i == df.shape[0]-1):
                data = df.iloc[start_i:,:]
            if (i-start_i == 1):
                data = pd.DataFrame(columns=['client timestamp', 'button','state','x','y'])
            data.to_csv(write_file_path +str(int(c))+'.csv', header=True, index=False)
            start_i = i
            c = q           # idle 포함할 경우, c=c+1로 설정
            
    os.remove(file['path'])         # 기존 파일 삭제

if __name__ == "__main__":
    m_data_dir = './data/mouse' 
    user_list = os.listdir(m_data_dir)      

    m_files = []
    for user in user_list:
        m_files.extend(ap.find_files(m_data_dir, user))
    
    for file in m_files:
        mouse_time_split_save(file)
    
    print("Done!")