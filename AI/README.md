# 폴더 구조 생성
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

# 수집한 데이터를 학습에 사용하기 위해 필요한 작업
1) 수집한 데이터를 /data/mouse/userID/~.csv, /data/resource/userID/~.csv에 저장
2-1) mouse_time_split    <- 수집한 mouse file을 시간(T)을 단위로 split
2-2) resource_time_split <- 수집한 resource file을 시간(T)을 단위로 split
3) base_data_save	<- 학습에 사용할 데이터로 변환
4) ai_train_model

