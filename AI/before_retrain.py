# 재학습 전에 실행해야함
# cert에서 내린 판정을 바탕으로 
# m_feature_extract.csv, r_feature_extract.csv에서 filename을 찾아 label 수정
import pandas as pd
import pymysql
from sqlalchemy import create_engine
# MySQL Connector using pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
import os

DB_HOST = os.environ.get('DB_HOST','')
DB_NAME = os.environ.get('DB_NAME', '')
DB_USERNAME = os.environ.get('DB_USERNAME','')
DB_PASSWORD = os.environ.get('DB_PASSWORD','')
table_name = 'graduate_certpage'

# mysql DB 연결
def connect_db():
    engine = create_engine("mysql+mysqldb://"+DB_USERNAME+":"+DB_PASSWORD+"@"+DB_HOST+"/"+DB_NAME, encoding='utf-8')
    conn = engine.connect()       #mysql에 생성된 db로 연결
    return conn
# mysql table 읽어 dataframe으로 반환
def read_table(table):
    conn = connect_db()
    sql = 'SELECT * FROM '+table
    df = pd.read_sql(sql, conn)
    conn.close()
    return df
# dataframe을 mysql table로 만듦
def write_table(df, table):
    conn = connect_db()
    df.to_sql(name=table,con=conn,if_exists='append', index=False)
    conn.close()


if __name__ == "__main__":
    m_feature_file = './m_feature_extract.csv'
    r_feature_file = './r_feature_extract.csv'
    m_df = pd.read_csv(m_feature_file)
    r_df = pd.read_csv(r_feature_file)
    cert_df = read_table(table_name)['label', 'mouse_file_list', 'resource_file_list']
    
    for i in range(cert_df):
        # 실제 패턴의 주인
        label = cert_df.iloc[i]['label']    
        # 수정해야할 mouse filename list
        m_files = cert_df.iloc[i]['mouse_file_list'] 
        m_files = m_files.split(",")    
        # 수정해야할 mouse filename list                
        r_files = cert_df.iloc[i]['resource_file_list'] 
        r_files = r_files.split(",")
        # modify file label
        for i in range(len(m_files)):
            m_df.loc[m_df['filename']==m_files[i], 'label'] = label
        for i in range(len(r_files)):
            r_df.loc[r_df['filename']==r_files[i], 'label'] = label
    m_df.to_csv(m_feature_file, index=False)
    r_df.to_csv(r_feature_file, index=False)