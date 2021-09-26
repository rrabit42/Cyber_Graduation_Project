~~추후 문서 정리 예정. 아직은 rough합니다.~~  

# ☀️전체적인 흐름☀️  
- User(Client) : collector를 통한 패턴 수집 -> 패턴 parse -> 패턴 extract -> 패턴 send 
- Server : 패턴 recv -> 사용자 이름으로 패턴 라벨링하여 저장 -> user by-pass 확인 -> 
    - if by-pass(권한 있음) -> 끝  
    - if not by-pass -> AI predict -> 허용범위 확인 -> 결과에 따라 패턴의 label 수정 -> json 형태의 경고 데이터 반환 -> 끝  

# ⚡EEE-MPC
- 마우스 사용 패턴 수집기
- collect pattern only if cursor position has changed  
- feature : action interval, button state, x, y  
> action interval - interval time with above value  
> button state - Move, Drag, Scroll, Left-Pressed, Left-Released, Right-Pressed, Right-Released

# ⚡EEE-RPC
- 리소스 사용 패턴 수집기
> memory | committed bytes in use  
> memory | available MBytes  
> process total | processor time  
> process total | private bytes  
> process total | working set  
> processor information total | processor time  
> processor information total | processor utility  
  
# ⚡agent.py
## mouse
- collector가 file로 수집된 패턴 데이터를 떨구면, filename과 label(사용자 이름)을 전달받음
- 이동거리, 이동방향을 parsing 한 후 action에 대한 통계값을 extract한 값을 서버로 전송함 (send() 내부에서 parse, extract 수행함)

## resource
- collector가 file로 수집된 패턴 데이터를 떨구면, filename과 label(사용자 이름)을 전달받음
- column명을 통일하고 빈칸은 mean값으로 채운 후 M x N 배열을 1 x NM 배열로 변환한 값을 서버로 전송함 (send() 내부에서 parse, extract 수행함)


# ⚡train_ai.py
- 사용자의 사용 패턴을 학습한 모델을 생성함
- 사용자별 마우스, 리소스 사용 패턴에 대한 scaler(.gz)와 model(.h5)를 만들어냄


# ⚡ZeroTrustAPI.py
## AI
- 사용자 행위 인증(분석) 모델 생성
- 생성된 모델을 사용자 인증에 판단(예측)에 사용
- 모델 전체/부분 재학습

## User
- 사용자 정보 정의
    - name : 사용자 이름
    - bypass : AI 인증 우회 여부(Y/N)
    - threshold, tolerance : m_(마우스), r_(리소스), idle_r_(마우스 idle상태일 경우 리소스만 보고 판단)
        - 0 ~ < threshold : user 차단
        - threshold <= ~ < tolerance : 허용&벌점부여
        - tolerance <= ~ 1 : 허용

## ZTControlServer
- 전체적인 제로트러스트 기능 흐름 제어  

# ⚡admin.py  
## AdminFunction  
- AI 공격 탐지 알림 확인 및 대응  
- by-pass 기능(키 발급, 토큰 발급)  
- by-pass 키, 토큰 자정마다 초기화  
- 계정 차단 및 벌점 기능(더미데이터로 구체적으로 구현할 예정)  
