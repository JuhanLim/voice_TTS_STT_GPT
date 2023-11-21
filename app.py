# 함수 지향적 프로그래밍 
# 실행 : streamlit run app.py
import streamlit as stl

from openai import OpenAI 

from audiorecorder import audiorecorder

import numpy as np

import os 

from datetime import datetime

from gtts import gTTS
import base64 # mp3 -> base64 변환 

#  global variable ============================ ( 전역 변수 )

client = None # OpenAI(api_key='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') # open api 를 저수준에서 직접 수행하는 객체 
model_name = None # GPT 질의시 사용(처리) 할 모델 이름  

# UI start ==============================================
def make_layout_main_top() : 
    # 1. 페이지 기본 정보 삽입 , 타이틀바 (탭) , 화면 스타일 ( wide : 세팅화면 넓게사용 , 미세팅 : 중앙정렬 ) 
    stl.set_page_config(
        page_title='Voice AI 비서입니다!', ## 탭이름 
        layout    ='wide') # 기본값은 센터 정렬 ( 특정 크기를 넘어가면 같이 넓어 지지 않음  )
    
    # 2 . 메인페이지 제목 설정
    stl.header('Voice AI S/W') 
    # 3. 구분선 -> markdown 문법
    stl.markdown('---') 
    # 4. 기본 설명
    # 접기 기능 
    with stl.expander('with this s/w', expanded= True) : 
        stl.write(
            '''
                - 프로그램 설명
                - streamlit , STT(gpt의 Whisper AI 사용) , 답변 ( GPT ) , TTS  (구글의 Translate TTS ) 
            '''
        )
        stl.markdown(' ') # 설명 밑에 너무 긴격이 없어서 br 태그 넣듯이 공백 추가
    pass 

def make_layout_main_side_bar() : 
    global client  # client 를 글로벌 변수라고 선언 
    
    # 사이드바 생성
    with stl.sidebar :
        # openai key 입력 
        
        api_key = stl.text_input(placeholder='API 키를 입력하세요',label='OPEN API KEY',type='password') # text_input 는 한줄입력받기, area 는 여러줄 , placeholder은 입력 힌트
        # text_input 에서 입력 받은 키를 api_key 에 저장하기
        #print(api_key)
        if api_key.strip() : # 값이 0 , 0.0 , [] , () , {} , None 는 무조건 조건식이 false 인 경우이고 현재는 값이 있다면
        #정상입력
            try : 
                # api 키가 틀려도 오류 상황 발생하지 X 실제 사용 때 문제 될 듯 
                client = OpenAI(api_key=api_key)
                print('client =>', client )
            except Exception : 
                # 웹에서 팝업 처리 할것 
                print(' API 키가 부적절 합니다 다시 시도하세요 ')
            pass 
        # 비정상 입력 -> 팝업 ( 현재는 생략 )
        else :   
            print('정확하게 입력하세요') # -> 웹에서 뜨게 수정하긴해야함 , 이벤트 발생시 마다 작동 
        stl.markdown('---')
        
 
        
        # GPT 모델 선택 ( 여러 목록 중 한개 선택 ->  radio or select )
        global model_name
        model_name = stl.radio(label='GPT 모델', options=['gpt-4','gpt-3.5-turbo'])   
        stl.markdown('---')
        
        # 전역 상태 변수 필요시 강제 초기화 -> 클릭하면 작동 
        if stl.button(label = '상태 초기화') : # 상태 초기화 버튼을 누른다면 
            print('상태 초기화 실행')
            init_state()
            pass 
         
        pass 
def make_layout_main_bottom() : 
    # 보이스 -> 질의 , 채팅 데이터 구성 완료됬음을 아는 변수 필요 ( flag ) 
    is_stt_complete_flag = False
    # 공통 
    left , right = stl.columns(2)
    # 왼쪽 : 오디오 입력 및 재생 
    with left : 
        # 부제목 
        stl.subheader('음성 질문')
        # 음성 녹음 버튼 추가 # requests 에서 따로 설치했던 audio recoder 사용 
        audio_arr = audiorecorder(record_prompt='클릭하여 녹음 시작', recording_prompt='레코딩 중...')  # 리턴값은 ndarray 인것 확인 
        print( len(audio_arr), audio_arr.shape )
        if len(audio_arr) and not np.array_equal( audio_arr , stl.session_state['audio_check']) :  # 새로운 음성 데이터가 존재하고 , 기존에 저장한 음성 데이터와 다르다면 
            # 음성 재생 -> <audio> -> 음원 삽입( 배열 -> 바이트s 로 변환 )
            stl.audio( audio_arr.tobytes() )
            # 음원 파일에서 텍스트 추출 ( STT ) 
            question = stt(audio_arr)
            print( 'question -> ' , question)
            #채팅창에 내용을 넣기 위한 준비
            now_str = datetime.now().strftime('%H:%M')
            # 채팅창에 보일 내용 세팅 ( 전역 세션 상태 변수에 저장  )
            stl.session_state['chat'] = stl.session_state['chat'] + [('user', now_str , question)]
            # GPT 모델에 질의한 프럼프트 
            stl.session_state['msg'] = stl.session_state['msg'] + [
                {
                    'role' : 'user' , 
                    'content' : question
                }
            ]
            # 오디오 저장 
            stl.session_state['audio_check'] = audio_arr
            # STT 완료 
            is_stt_complete_flag = True 
            
        pass 
    # 오른쪽:채팅창
    with right:
        # 부제목
        stl.subheader('채팅창')
        # STT가 완료된 상황에서만 진행
        if is_stt_complete_flag:
            # GPT에게 질의
            response = gpt_proc( stl.session_state['msg'] )
            print( 'GPT 응답', response)
            # GPT 모델 응답결과 저장
            stl.session_state['msg']  = stl.session_state['msg'] + [
                {
                    'role':'system',
                    'content':response
                }
            ]
            # 채팅창 화면 처리
            now_str = datetime.now().strftime('%H:%M')
            stl.session_state['chat'] = stl.session_state['chat'] + [('ai', now_str, response)]

            # 채팅창 시각화
            for sender, send_time, msg in stl.session_state['chat']:
                if sender == 'user':
                    stl.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{msg}</div><div style="font-size:0.8rem;color:gray;">{send_time}</div></div>', unsafe_allow_html=True)
                    stl.write('')
                    pass
                else:
                    stl.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{msg}</div><div style="font-size:0.8rem;color:gray;">{send_time}</div></div>', unsafe_allow_html=True)
                    stl.write('')
                    pass

            # TTS처리
            tts( response )

            pass
        pass
    pass

def make_layout() : 
    # 메인 페이지 상부 ( 본문 ) # UI 기본 연습 ( 타이틀 , 등등 )
    make_layout_main_top()
    # 왼쪽 사이드바( opnai API key 입력 , 모델 셀렙 ( 3.5-turbo / 4 ))
    make_layout_main_side_bar()
    # 메인 페이지 하부 ( 본문 ) # UI 음성 녹음 , 채팅 목록 
    make_layout_main_bottom()
    pass 

# UI end ==============================================


# state start ==============================================

def init_state() : 
    # 스트림릿의 상태를 저장 , 이벤트 발생 => 코드가 처음부터 재실행 => 입력 받은 값들 ( 키 , 모델명 ) 모두 초기화 된다. 전역변수는 저장됨 .
    # session_state 라는 전역 관리 공간을 제공 , 여기에 필요한 내용 저장해 두면 됨 . 
    if 'chat' not in stl.session_state : # 저장소 안에 chat 이라는 키가 없다면 -> 저장한적 없다 
        stl.session_state['chat'] = []   # 세션 상태 저장 공간에 chat 이라는 키를 생성한다.  
    if 'msg' not in stl.session_state :
        stl.session_state['msg'] = [
            {   
                # 페르소나 부여
                'role' : 'system',
                # 영어로 부여
                'content' : 'You ara a thoughtful assistant. Respond to all input in 25 words and answer in Korean'   
            }
        ]
    # audio 버퍼 체크 
    if 'audio_check' not in stl.session_state :
        stl.session_state['audio_check'] = []
    pass 
# state end ==============================================


# special func start ===========================================

def stt( audio_arr ) -> str :
    global client 
    try : 
        # 데이터 전처리 
        filename = 'input_voice.mp3'
        # 파일 기록
        with open(filename , 'wb') as f:
            f.write(audio_arr.tobytes() ) # ndarray 는 바로 못쓰므로 tobytes 로. 
            
        with open(filename,'rb') as audio_file : 
        # GPT 를 이용한 STT 처리 
            transcript = client.audio.transcriptions.create(
                
                model = 'whisper-1',
                file = audio_file,
                response_format= 'text'
        )
        
        # 삭제 처리 
        os.remove(filename)
            
            
        # 텍스트 응답 
        return transcript
    except Exception as e : 
        print ( 'STT 변환 오류 ', e ) 

     
    pass 

def tts(answer):
    # 응답 데이터 -> TTS 변환 -> 파일 저장 
    filename = 'answer.mp3'
    tts = gTTS(text = answer , lang = 'ko') 
    tts.save(filename)
    
    # 자동 재생 ( 답변 재생 )
    # <audio src = 'data:audio/mp3;base64,{데이터}'
    with open(filename, 'rb') as f : 
        data = f.read() 
        voice_src = base64.b64encode(data).decode()
        html = f'''
            <audio autoplay ='true'>
                <source src = 'data:audio/mp3;base64,{voice_src}' type ='audio/mp3' />
            </audio>
        '''
        stl.markdown( html, unsafe_allow_html= True )
    # 파일 삭제 
    os.remove(filename)
    pass 

def gpt_proc(prompt) : 
    global client
    global model_name
    response = client.chat.completions.create(
      model = model_name , # gpt-4 제외한 가장 최신 모델
      messages = prompt ,  # 프럼프트가 접목된 채팅 메시지
      #temperature = 0, 
  )

    return response.choices[0].message.content.strip()
    pass 

# special func end ===========================================

def main() :
    make_layout() # 레이아웃 구성 ( UI ) 
    init_state()  # 전역 관리 상태변수 초기화 
    pass 



if __name__ == '__main__' :
    main()