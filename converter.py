import pandas as pd
import numpy as np
import os

def parse_time_to_seconds(time_str: str) -> float:
    if pd.isna(time_str): return np.nan
    time_str = str(time_str).strip()
    if 's' in time_str:
        try: return float(time_str.replace('s', ''))
        except ValueError: return np.nan
    elif ':' in time_str:
        parts = time_str.split(':')
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError: return np.nan
    return np.nan

def to_srt_time(total_seconds: float) -> str:
    if pd.isna(total_seconds): return "00:00:00,000"
    total_seconds = max(0, float(total_seconds))
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds * 1000) % 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def create_srt_content(df: pd.DataFrame, platform: str, subtitle_type: str) -> str:
    time_col = next((c for c in df.columns if 'Time' in str(c) or 'Start' in str(c)), "Time")
    orig_col = next((c for c in df.columns if 'Subtitle' in str(c) or 'Original' in str(c)), "")
    trans_col = next((c for c in df.columns if 'Translation' in str(c) or '한국어' in str(c)), "")

    if time_col not in df.columns:
        raise ValueError(f"시간 컬럼('{time_col}')을 찾을 수 없습니다.")

    def clean_text(text):
        if pd.isna(text): return ""
        return str(text).replace('\n', ' ').strip()

    df['Start_Sec'] = df[time_col].apply(parse_time_to_seconds)
    df['End_Sec'] = df['Start_Sec'].shift(-1).fillna(df['Start_Sec'] + 3.0)

    srt_content = []
    counter = 1
    for index, row in df.iterrows():
        if pd.isna(row['Start_Sec']): continue

        orig_text = clean_text(row.get(orig_col, ""))
        trans_text = clean_text(row.get(trans_col, ""))
        
        # 3가지 유형 처리
        if subtitle_type == "dual":
            display_text = f"{orig_text}\n{trans_text}" if orig_text and trans_text else (orig_text or trans_text)
        elif subtitle_type == "translation":
            display_text = trans_text if trans_text else orig_text
        else: # original
            display_text = orig_text if orig_text else trans_text

        srt_content.append(str(counter))
        srt_content.append(f"{to_srt_time(row['Start_Sec'])} --> {to_srt_time(row['End_Sec'])}")
        srt_content.append(display_text)
        srt_content.append("")
        counter += 1
        
    return '\n'.join(srt_content).strip()