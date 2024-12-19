import subprocess
import sys
import os
# 현재 디렉토리 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# main.py 경로
main_dir = os.path.abspath(os.path.join(current_dir, ".."))
if main_dir not in sys.path:
    sys.path.append(main_dir)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config



class Musical_Process:
    def execute_script(self, script_name):
        # 현재 파일 기준으로 스크립트 경로 설정
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
        # 가상환경의 Python 실행 경로 가져오기
        venv_python = sys.executable
        try:
            subprocess.run([venv_python, script_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while executing {script_name}: {e}")
            raise

if __name__ == "__main__":
    processed_data_file_path = f'{config.file_path}/{config.processed_data}'
    add_genre_file_path = f'{config.file_path}/{config.add_genre_file_name}'

    process = Musical_Process() 

    """처음 전처리 코드 per+raw.json -> processed_data.json"""
    if not os.path.exists(processed_data_file_path):
        process.execute_script("first_preprocessing.py")
    else:
        print('pass first_preprocessing')
     
    """장르 추가 실행 조건 processed_data.json -> add_genre_story.json"""
    if not os.path.exists(add_genre_file_path):
        process.execute_script("prompt.py")
    else:
        print('pass prompt')
        pass

    """전처리 코드 실행 조건 add_genre_story.json -> df_with_negatives.json"""
    if not os.path.exists(config.df_with_negatives_path):
        process.execute_script("preprocessing.py")
    else:
        print('pass Preprocessing')
            
    """모델 생성 실행 조건"""
    if not os.path.exists(config.save_model_path):
        # print("DeepFM 실행")
        process.execute_script("DeepFM.py")
    else:
        print('pass model')
        pass
