# 기존 데이터 셋 학습에 사용할 수 있도록 file을 parse, 저장, 이동 & feature 추출 및 labeling 수행
# ./data/mouse/user/~, ./data/resource/user/~에서 
# ./pattern/mouse/~, ./pattern/resource/~으로 이동
# ./m_feature_extract.csv, ./r_feature_extract.csv에 filename, label, 추출한 features 저장
import ai_pred_pattern as ap
import os 

if __name__ == "__main__":

    m_data_dir = './data/mouse' 
    r_data_dir = './data/resource'
    user_list = os.listdir(m_data_dir)     

    m_files = []
    r_files = []
    for user in user_list:
        m_files.extend(ap.find_files(m_data_dir, user))
        r_files.extend(ap.find_files(r_data_dir, user))

    for file in m_files:
        ap.mouse_parse_save(file)
    for file in r_files:
        ap.resource_parse_save(file)

    # 수정된 M, R 파일 features 정보 저장
    for user in user_list:
        m_files = ap.find_files(m_data_dir, user)
        m_data = ap.mouse_preprocess(m_files)
        print(m_data.shape)
        r_files = ap.find_files(r_data_dir, user)
        r_data = ap.resource_preprocess(r_files)
        print(r_data.shape)
        ap.preDir_move_patternDir(user, './data')


    print("Done!!")