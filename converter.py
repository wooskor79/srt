import pandas as pd
import numpy as np
import os

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
            # HH:MM:SS 형식 지원
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
    milliseconds = int((total_seconds * 1000) % 1000)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def create_srt_content(df: pd.DataFrame, platform: str, subtitle_type: str) -> str:
    """플랫폼별 특성에 맞춰 SRT 내용을 생성합니다."""
    
    # 1. 컬럼 매핑 로직
    actual_col = ""
    # 시간 컬럼 찾기 (유튜브/넷플릭스 공통)
    time_col = next((c for c in df.columns if 'Time' in str(c) or 'Start' in str(c)), "Time")
    
    if platform == "youtube":
        # 유튜브는 보통 'Translation' 혹은 'Subtitle' 키워드 사용
        if subtitle_type == "Human Translation":
            actual_col = next((c for c in df.columns if 'Translation' in str(c) or '한국어' in str(c)), "")
        else:
            actual_col = next((c for c in df.columns if 'Subtitle' in str(c) or 'Original' in str(c)), "")
    else:
        # 넷플릭스는 기존처럼 전달받은 컬럼명 그대로 사용
        actual_col = subtitle_type

    # 매핑 실패 시 예외 처리
    if not actual_col or actual_col not in df.columns:
        if subtitle_type in df.columns:
            actual_col = subtitle_type
        else:
            raise ValueError(f"자막 컬럼을 찾을 수 없습니다. (플랫폼: {platform}, 선택: {subtitle_type})")

    if time_col not in df.columns:
        raise ValueError(f"시간 컬럼('{time_col}')을 찾을 수 없습니다.")

    # 2. 시간 변환 및 종료 시간 계산
    df['Start_Sec'] = df[time_col].apply(parse_time_to_seconds)
    df['End_Sec'] = df['Start_Sec'].shift(-1).fillna(df['Start_Sec'] + 3.0)

    # 3. SRT 구조 생성
    df[actual_col] = df[actual_col].astype(str).str.replace(r'\n', ' ', regex=True).str.strip()
    
    srt_content = []
    for index, row in df.iterrows():
        if pd.isna(row['Start_Sec']):
            continue

        srt_content.append(str(len(srt_content) // 4 + 1))
        timecode = f"{to_srt_time(row['Start_Sec'])} --> {to_srt_time(row['End_Sec'])}"
        srt_content.append(timecode)
        srt_content.append(row[actual_col])
        srt_content.append("")
        
    return '\n'.join(srt_content).strip()

# ==============================================================================
# 2. 메인 파일 처리 함수
# ==============================================================================

def process_xlsx_file(input_file_path: str, output_dir: str, platform: str, subtitle_column: str, final_srt_filename: str) -> tuple[bool, str]:
    try:
        df = pd.read_excel(input_file_path, engine='openpyxl')
        srt_content = create_srt_content(df, platform, subtitle_column)
        
        output_file_path = os.path.join(output_dir, final_srt_filename)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        return True, f"'{final_srt_filename}' 변환 완료."
        
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"변환 중 오류 발생: {e}"