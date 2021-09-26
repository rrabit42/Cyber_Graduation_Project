# user 별로 model 생성
import tensorflow as tf
import pandas as pd
from keras.layers import Input, Dense, Dropout
from keras.models import Model
from keras.metrics import Precision, Recall
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import datetime


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
def make_model(input_size, output_size, unit, rate):
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
def evaluate(model, test_X, test_Y, batch_size=256):
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
    model_dir = os.environ.get('MODEL_DIR', '')
    joblib.dump(scaler, model_dir+filename)
    return scaler

# type(mouse or resource)
def train(user, type, unit=15, dropout=0.3, lr=0.0005, batch_size=256, epochs=1000):
    scaler_name = user+'_scaler_'
    model_name = user+'_model_'
    if(type == 'mouse'):
        scaler_name += '_m.gz'
        model_name += '_m.h5'
        feature_file = os.environ.get('M_FEATURE_FILE', '')
    else:
        scaler_name += '_r.gz'
        model_name += '_r.h5'
        feature_file = os.environ.get('R_FEATURE_FILE', '')
    
    # data(X), labeling & one-hot encoding(Y)
    data, labels = load_data_label(feature_file)
    label = labels[[user]]
    # 데이터 셋 분할 전 전처리
    data = data.fillna(0)
    # 데이터 셋 분할
    train_X, test_X, train_Y, test_Y = train_test_split(data, label, test_size=0.3, stratify=labels)

    # data scaler 생성 및 저장
    scaler = save_MinMaxScaler(train_X, scaler_name)
    # data 전처리
    train_X = scaler.transform(train_X)
    test_X = scaler.transform(test_X)

    # shape 정의
    input_size = test_X.shape[-1]
    output_size = 1

    # AI
    inputs, Y = make_model(input_size, output_size, unit, dropout)
    model = compile_model(inputs, Y, lr)
    es = tf.keras.callbacks.EarlyStopping(monitor='val_loss',mode='min', patience=100)        # epoch 과적합 방지
    history = model.fit(train_X, train_Y, batch_size=batch_size, epochs=epochs, validation_data=(test_X, test_Y),callbacks=[es])
    acc_graph(history)
    evaluate(model, test_X, test_Y)
    print(model.evaluate(test_X, test_Y))

    # model 저장
    model_dir = os.environ.get('MODEL_DIR', '')
    model.save(model_dir+model_name)

# 근래 생긴 데이터만을 가지고 기존 모델 재학습(like fine-tuning)
# @@ freeze 조정 필요
def retrain(user, type, base_model, days=2, lr=0.00005, batch_size=256, epochs=1000):
    scaler_name = user+'_scaler_'
    model_name = user+'_model_'
    if(type == 'mouse'):
        scaler_name += '_m.gz'
        model_name += '_m.h5'
        feature_file = os.environ.get('M_FEATURE_FILE', '')
    else:
        scaler_name += '_r.gz'
        model_name += '_r.h5'
        feature_file = os.environ.get('R_FEATURE_FILE', '')
    retain_allowed_days = (datetime.datetime.today() + datetime.timedelta(days=-days)).strftime("%Y-%m-%d")  # default: 3일간 데이터 재학습에 사용
    
    # data(X), labeling & one-hot encoding(Y)
    df = pd.read_csv(feature_file)
    df = df[df['time']>=retain_allowed_days]
    data = df.drop(['filename', 'label', 'time'],axis=1)
    labels = label_one_hot_encoding(df) 
    label = labels[[user]]

    # 데이터 셋 분할 전 전처리
    data = data.fillna(0)
    # 데이터 셋 분할
    train_X, test_X, train_Y, test_Y = train_test_split(data, label, test_size=0.3, stratify=labels)
    # Load scaler & data 전처리
    scaler = joblib.load(scaler_name)
    train_X = scaler.transform(train_X)
    test_X = scaler.transform(test_X)

    # shape 정의
    input_size = test_X.shape[-1]
    # AI
    inputs = Input(shape=(input_size,))
    # freeze some layers
    for layer in base_model.layers[:-3]:   
        layer.trainable = False
    Y = base_model.output
    model = compile_model(inputs, Y, lr)
    es = tf.keras.callbacks.EarlyStopping(monitor='val_loss',mode='min', patience=100)        # epoch 과적합 방지
    history = model.fit(train_X, train_Y, batch_size=batch_size, epochs=epochs, validation_data=(test_X, test_Y),callbacks=[es])
    acc_graph(history)
    evaluate(model, test_X, test_Y)
    print(model.evaluate(test_X, test_Y))

    # model 저장
    model_dir = os.environ.get('MODEL_DIR', '')
    model.save(model_dir+model_name)