# AI & proxy README
---
## 폴더 구조 생성(사전 작업 필요)

```
AI
+-- model 
+-- pred
|    +-- mouse
|    +-- resource 
+-- pattern
+--- mouse
+--- resource 
```

## 수집한 데이터를 학습에 사용하기 위해 필요한 작업
```
  1. 수집한 데이터를 ./data/mouse/userID/*.csv, ./data/resource/userID/*.csv에 저장
  2. mouse_time_split 실행 (수집한 mouse file을 시간(T)을 단위로 split)
  3. resource_time_split 실행 (수집한 resource file을 시간(T)을 단위로 split)
  4. base_data_save 실행 (학습에 사용할 데이터로 변환)
  5. ai_train_model 실행 (모델 학습)
