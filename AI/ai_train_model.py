# ./m_feature_extract.csv, ./r_feature_extract.csv를 읽어서 
# user 별로 model 생성
import ai_pred_pattern as ap
import tensorflow as tf
import pandas as pd
from keras.layers import Input, Dense, Dropout, concatenate
from keras.models import Model
from keras.metrics import Precision, Recall
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import joblib

model_dir = './model/'
m_feature_file = './m_feature_extract.csv'
r_feature_file = './r_feature_extract.csv'

# dataframe에서 label만 one-hot encoding
def label_one_hot_encoding(df):
    label = df['label']
    label = pd.get_dummies(label)
    return label

# path에서 data와 label 추출하여 반환
def load_data_label(path):
    df = pd.read_csv(path)
    data = df.drop(['filename', 'label', 'time'],axis=1)
    label = label_one_hot_encoding(df)    
    return data, label

# model 구조
def make_model(input_size, output_size, unit=15, rate=0.3):
    inputs =Input(shape=(input_size,))

    X = Dense(units = unit, kernel_initializer = 'glorot_uniform', activation = 'relu')(inputs)
    H = Dense(units = unit, kernel_initializer = 'glorot_uniform', activation = 'relu')(X)
    H = Dropout(rate)(H)
    H = Dense(units = unit, kernel_initializer = 'glorot_uniform', activation = 'relu')(H)
    H = Dropout(rate)(H)
    H = Dense(units = unit, kernel_initializer = 'glorot_uniform', activation = 'relu')(H)
    H = Dropout(rate)(H)
    Y = Dense(units = output_size, kernel_initializer = 'glorot_uniform', activation = 'sigmoid')(H)
    
    return inputs, Y

# model 생성
def compile_model(inputs, Y, lr=0.01):
    model = Model(inputs=inputs, outputs=Y)
    model.compile(optimizer = Adam(lr=lr), loss = 'binary_crossentropy', metrics = ['accuracy', Precision(), Recall()])
    model.summary()
    return model

# model 정확도 시각화
def acc_graph(history):
    from pylab import rcParams
    from matplotlib import pyplot as plt
    rcParams['figure.figsize'] = 10, 4
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()
    # summarize history for loss
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()

# 모델 정확도, 예측값, 실제값 출력
def evaluate(model, test_X, test_Y, batch_size=100):
    evaluation = model.evaluate(test_X,test_Y, batch_size=batch_size)
    print("acc : ", evaluation[1])
    pred = pd.DataFrame(model.predict(test_X))
    pred = pred.round(decimals=2)
    print(pred)
    print(test_Y)


# df(scaler 학습 대상), filename(scaler 이름)
def save_MinMaxScaler(df,filename):
    df = df.fillna(0)
    scaler = MinMaxScaler()
    scaler.fit(df)
    joblib.dump(scaler, model_dir+filename)
    return scaler


if __name__ == "__main__":
    
    yesterday_str = ap.set_yesterday_str()

    model_dir = './model/'
    m_feature_file = './m_feature_extract.csv'
    r_feature_file = './r_feature_extract.csv'

    # data(X), labeling & one-hot encoding(Y)
    m_data, m_labels = load_data_label(m_feature_file)
    r_data, r_labels = load_data_label(r_feature_file)
    
    # 데이터 셋 분할 전 전처리
    m_data = m_data.fillna(0)
    r_data = r_data.fillna(0)
    
    user_list = m_labels.columns
    m_scores = []
    r_scores = []
    for user in user_list:
        m_label = m_labels[[user]]
        r_label = r_labels[[user]]
        # 데이터 셋 분할
        m_train_X,m_test_X,m_train_Y,m_test_Y = train_test_split(m_data, m_label, test_size=0.3, stratify=m_labels)
        r_train_X,r_test_X,r_train_Y,r_test_Y = train_test_split(r_data, r_label, test_size=0.3, stratify=r_labels)

        # data scaler 생성 및 저장
        m_scaler_name = yesterday_str+'_'+user+'_scaler_m.gz'
        m_scaler = save_MinMaxScaler(m_train_X, m_scaler_name)
        r_scaler_name = yesterday_str+'_'+user+'_scaler_r.gz'
        r_scaler = save_MinMaxScaler(r_train_X, r_scaler_name)   

        # data 전처리
        m_train_X = m_scaler.transform(m_train_X)
        m_test_X = m_scaler.transform(m_test_X)
        r_train_X = r_scaler.transform(r_train_X)
        r_test_X = r_scaler.transform(r_test_X)

        # shape 정의
        m_input_size = m_test_X.shape[-1]
        m_output_size = 1
        r_input_size = r_test_X.shape[-1]
        r_output_size = 1

        # AI
        # mouse model
        m_inputs, m_Y = make_model(m_input_size, m_output_size)
        m_model = compile_model(m_inputs, m_Y, 0.0005)
        es = tf.keras.callbacks.EarlyStopping(monitor='val_loss',mode='min', patience=100)        # epoch 과적합 방지
        m_history = m_model.fit(m_train_X, m_train_Y, batch_size=256, epochs=1000, validation_data=(m_test_X, m_test_Y),callbacks=[es])
        print("<Mouse>\n")
        acc_graph(m_history)
        evaluate(m_model, m_test_X, m_test_Y)
        m_scores.append(m_model.evaluate(m_test_X, m_test_Y))

        # resource model
        r_inputs, r_Y = make_model(r_input_size, r_output_size)
        r_model = compile_model(r_inputs,  r_Y, 0.001)
        r_history =  r_model.fit(r_train_X, r_train_Y, batch_size=256, epochs=1000, validation_data=(r_test_X, r_test_Y),callbacks=[es])
        print("<Resource>\n")
        acc_graph(r_history)
        evaluate(r_model, r_test_X, r_test_Y)
        r_inputs, r_Y = make_model(r_input_size, r_output_size)
        r_scores.append(r_model.evaluate(r_test_X, r_test_Y))
        
        # model 저장
        m_model_name = yesterday_str+'_'+user+'_model_m.h5'
        m_model.save(model_dir+m_model_name)
        r_model_name = yesterday_str+'_'+user+'_model_r.h5'
        r_model.save(model_dir+r_model_name)
    print("Done!!")