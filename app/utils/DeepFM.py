# 필요한 라이브러리 임포트
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten, Add, Lambda, Dropout
import tensorflow as tf
from tensorflow.keras import backend as K
from keras.layers import Layer
import matplotlib.pyplot as plt
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.saving import register_keras_serializable
from tensorflow.keras.regularizers import l2
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config

# MusicalRecommender 클래스 정의
class MusicalRecommender:
    def __init__(self):
        self.data = None
        self.original_data = None
        self.model = None
        self.label_encoders = {}
        self.vocab_sizes = {}
    
    def load_and_preprocess_data(self):
        # 데이터 로드 및 전처리
        # Load data (Ensure the file is in the same directory or provide correct relative path)
        self.data = pd.read_json(config.df_with_negatives_path, lines=True)  # Update the path to a relative one if necessary
        self.original_data = self.data.copy()
        
        categorical_features = ['title', 'cast', 'genre']
        
        # 범주형 변수 레이블 인코딩
        for feature in categorical_features:
            self.label_encoders[feature] = LabelEncoder()
            self.data[feature] = self.label_encoders[feature].fit_transform(self.data[feature].astype(str))
            self.vocab_sizes[feature] = len(self.label_encoders[feature].classes_)

    def prepare_training_data(self):
        # 범주형 데이터와 수치형 데이터를 처리
        categorical_features = ['title', 'cast', 'genre']
        categorical_data = {}
        
        for feature in categorical_features:
            categorical_data[feature] = self.data[feature].values  # 각 범주형 데이터를 딕셔너리에 저장
        
        
        # X 구성: 카테고리형 데이터와 수치형 데이터를 모두 합친 DataFrame 생성
        X = pd.DataFrame({
            'title': categorical_data['title'],
            'cast': categorical_data['cast'],
            'genre': categorical_data['genre']  # 첫 번째 수치형 변수
        })
        
        # 타겟 데이터
        y = self.data['target']
        
        # X와 y의 길이가 일치하는지 확인
        print(f"Length of X: {len(X)}")
        print(f"Length of y: {len(y)}")
        
        # 길이가 일치하면 훈련/테스트 데이터로 분리
        if len(X) == len(y):
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        else:
            print("Error: Lengths of X and y do not match!")
        
        return X_train, X_test, y_train, y_test


    def create_deepfm_model(self):
        # 모델 구조 정의
        inputs = {
            'title': Input(shape=(1,), dtype=tf.int32, name='title'),
            'cast': Input(shape=(1,), dtype=tf.int32, name='cast'),
            'genre': Input(shape=(1,), dtype=tf.int32, name='genre')
        }
        # 임베딩 정의 (L2 정규화 추가)
        embeddings = {
            'title': Embedding(self.vocab_sizes['title'], 16, embeddings_regularizer=l2(1e-4))(inputs['title']),
            'cast': Embedding(self.vocab_sizes['cast'], 16, embeddings_regularizer=l2(1e-4))(inputs['cast']),
            'genre': Embedding(self.vocab_sizes['genre'], 16, embeddings_regularizer=l2(1e-4))(inputs['genre']),
        }
    
        fm_output = FMInteraction()([embeddings['title'], embeddings['cast'], embeddings['genre']])

        # Flatten embeddings and concatenate with numerical data
        concatenated = Concatenate()(
            [Flatten()(embeddings['title']), 
             Flatten()(embeddings['cast']),
             Flatten()(embeddings['genre']),
             Flatten()(fm_output)
        ])
        
        # 완전 연결 계층 (Dense 레이어 L2 정규화 추가)
        x = Dense(128, activation='relu', kernel_regularizer=l2(1e-4))(concatenated)
        x = Dropout(0.3)(x)
        x = Dense(64, activation='relu', kernel_regularizer=l2(1e-4))(x)
        x = Dropout(0.3)(x)
        x = Dense(32, activation='relu', kernel_regularizer=l2(1e-4))(x)
        output = Dense(1, activation='sigmoid', kernel_regularizer=l2(1e-4))(x)

        self.model = Model(inputs=[inputs['title'], inputs['cast'], inputs['genre']], outputs=output)
        self.model.compile(optimizer='adam', loss=weighted_loss, metrics=['accuracy', 'Precision', 'Recall'])
        self.model.summary()

    def train_model(self):
        X_train, X_test, y_train, y_test = self.prepare_training_data()
        self.create_deepfm_model()

        # EarlyStopping 콜백 정의
        early_stopping = EarlyStopping(
            monitor='val_loss',  # 검증 손실을 모니터링
            patience=3,          # 손실이 개선되지 않으면 3 에포크 후 중지
            restore_best_weights=True  # 가장 좋은 모델 가중치를 복원
        )
        
        # Train the model and display progress
        history = self.model.fit(
            [X_train['title'], X_train['cast'], X_train['genre']],
            y_train,
            batch_size=64,
            epochs=20,
            verbose=1,
            validation_data=([X_test['title'], X_test['cast'], X_test['genre']], y_test),
            callbacks=[early_stopping]  
        )
        # Plot training history
        plt.plot(history.history['accuracy'], label='accuracy')
        plt.plot(history.history['val_accuracy'], label = 'val_accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.ylim([0, 1])
        plt.legend(loc='lower right')
        plt.savefig(config.picture_file_path)
        self.retrain()

    def retrain(self):
        X_full = pd.DataFrame({
        'title': self.data['title'],
        'cast': self.data['cast'],
        'genre': self.data['genre']
        })
        y_full = self.data['target']

        self.model.fit(
            [X_full['title'], X_full['cast'], X_full['genre']],
            y_full,
            batch_size=64,
            epochs=5,  # 전체 데이터로 재학습할 에포크 수
            verbose=1
        )
        print("Retraining completed.")
        evaluation_results = self.model.evaluate(
            [X_full['title'],X_full[    'cast'], X_full['genre']],
            y_full, verbose=2
        )
        # 레이블 인코더 저장
        self.save_model(config.save_model_path)
        
        test_loss = evaluation_results[0]  # 손실 (loss)
        test_accuracy = evaluation_results[1]  # 정확도 (accuracy)
        test_precision = evaluation_results[2]  # 정밀도 (Precision)
        test_recall = evaluation_results[3]  # 재현율 (Recall)

        print(f"Test Loss: {test_loss}")
        print(f"Test Accuracy: {test_accuracy}")
        print(f"Test Precision: {test_precision}")
        print(f"Test Recall: {test_recall}")


    def save_model(self, path):
        self.model.save(path)

    def run(self):
        self.load_and_preprocess_data()
        self.train_model()

# Keras 직렬화 시스템에 FMInteraction 클래스를 등록
# package 파라미터는 사용자 지정 이름(Custom)을 설정하여 직렬화 중 충돌을 방지
# 저장된 모델을 로드할 때 FMInteraction 클래스를 올바르게 인식
@register_keras_serializable(package="Custom")
class FMInteraction(Layer):
    def __init__(self, **kwargs):
        super(FMInteraction, self).__init__(**kwargs)

    def call(self, inputs):
        pairwise_interactions = []
        for i in range(len(inputs)):
            for j in range(i + 1, len(inputs)):
                interaction = K.sum(inputs[i] * inputs[j], axis=-1, keepdims=True)
                pairwise_interactions.append(interaction)
        return K.sum(pairwise_interactions, axis=0)

@register_keras_serializable(package="Custom")
def weighted_loss(y_true, y_pred):
    weight = K.cast(y_true == 1, 'float32') * 0.7 + 0.3  # 긍정 샘플에 더 높은 가중치
    return K.mean(weight * K.binary_crossentropy(y_true, y_pred))


if __name__ == "__main__":
    recommender = MusicalRecommender()
    recommender.run()