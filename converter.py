import pandas as pd
import numpy as np
import os
import re

# ==============================================================================
# 1. 시간 및 SRT 변환 함수
# ==============================================================================

def parse_time_to_seconds(time_str: str) -> float:
    """LR 커스텀 시간 문자열 ('2:02' 또는 '18s')을 전체 초(second)로 변환합니다."""
    if pd.isna(time_str):
        return np.nan
        
    time_str = str(time_str).strip()
    
    # 's' 형식 (초) 처리
    if 's' in time_str:
        try:
            return float(time_str.replace('s', ''))
        except ValueError:
            return np.nan
            
    # M:SS 형식 (분:초) 처리
    elif ':' in time_str:
        parts = time_str.split(':')
        try:
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            # HH:MM:SS 형식도 지원
            elif len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return np.nan
            
    return np.nan

def to_srt_time(total_seconds: float) -> str:
    """전체 초(float)를 SRT 형식 (HH:MM:SS,mmm)으로 변환합니다."""
    if pd.isna(total_seconds):
        return "00:00:00,000"

    total_seconds = max(0, float(total_seconds))
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    # 밀리초는 소수점 이하 셋째 자리까지 사용
    milliseconds = int((total_seconds * 1000) % 1000)

    # 00:00:00,000 형식으로 포맷팅
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def create_srt_content(df: pd.DataFrame, subtitle_column: str) -> str:
    """DataFrame을 받아 SRT 파일 내용을 문자열로 생성합니다."""
    
    # 필수 컬럼 검사
    if 'Time' not in df.columns or subtitle_column not in df.columns:
        raise ValueError(f"필수 컬럼 ('Time', '{subtitle_column}')이 파일에 없습니다. 파일이 Language Reactor 형식인지 확인해주세요.")

    # 1. 시간 변환 및 종료 시간 계산
    df['Start_Sec'] = df['Time'].apply(parse_time_to_seconds)
    # 다음 자막의 시작 시간을 현재 자막의 종료 시간으로 설정 (마지막은 3초 길이)
    df['End_Sec'] = df['Start_Sec'].shift(-1).fillna(df['Start_Sec'] + 3.0)

    # 2. SRT 시간 형식으로 포맷팅
    df['Start_SRT'] = df['Start_Sec'].apply(to_srt_time)
    df['End_SRT'] = df['End_Sec'].apply(to_srt_time)
    
    # 3. SRT 구조 생성
    # 자막 텍스트 내의 줄 바꿈을 공백으로 대체하고 공백 제거
    df[subtitle_column] = df[subtitle_column].astype(str).str.replace(r'\n', ' ', regex=True).str.strip()
    
    srt_content = []
    for index, row in df.iterrows():
        # Nan 값이 포함된 행은 건너뜀 (시간이 파싱되지 않은 경우)
        if pd.isna(row['Start_Sec']):
            continue

        # 순서 번호
        srt_content.append(str(len(srt_content) // 4 + 1))
        # 시간 코드
        timecode = f"{row['Start_SRT']} --> {row['End_SRT']}"
        srt_content.append(timecode)
        # 자막 텍스트
        srt_content.append(row[subtitle_column])
        # 빈 줄
        srt_content.append("")
        
    return '\n'.join(srt_content).strip()

# ==============================================================================
# 2. 메인 파일 처리 함수 (app.py에서 호출됨)
# ==============================================================================

def process_xlsx_file(input_file_path: str, output_dir: str, subtitle_column: str, final_srt_filename: str) -> tuple[bool, str, str]:
    """
    XLSX 파일을 읽어 SRT로 변환하고 지정된 출력 디렉토리에 저장합니다.
    :param final_srt_filename: 공백이 유지된 SRT 파일 이름
    :return: (성공 여부, 메시지, 자막 컬럼 이름)
    """
    try:
        # 1. 파일 읽기
        # openpyxl 엔진을 사용하여 XLSX 파일을 읽습니다.
        df = pd.read_excel(input_file_path, engine='openpyxl')
        
        # 2. SRT 내용 생성
        srt_content = create_srt_content(df, subtitle_column)
        
        # 3. SRT 파일 저장 경로 결정 (app.py에서 받은 이름을 사용)
        output_file_path = os.path.join(output_dir, final_srt_filename)
        
        # 4. SRT 파일 저장
        # UTF-8 인코딩을 사용하여 자막 깨짐 방지
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        return True, f"'{os.path.basename(input_file_path)}' 파일이 '{final_srt_filename}'로 변환되어 저장되었습니다.", subtitle_column
        
    except ValueError as e:
        # 컬럼 이름 오류 등
        return False, str(e), subtitle_column
        
    except Exception as e:
        # 기타 파일 입출력 오류 등
        return False, f"변환 중 알 수 없는 오류가 발생했습니다: {e}", subtitle_column