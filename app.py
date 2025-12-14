import os
from flask import Flask, request, render_template
# secure_filename 함수는 이제 사용하지 않습니다.
from converter import process_xlsx_file

# --- 설정 ---
app = Flask(__name__)
# 컨테이너 내 임시 업로드 경로
UPLOAD_FOLDER = 'uploads'
# 컨테이너 내 최종 출력 경로 (NAS /volume1/torrent와 매핑)
OUTPUT_FOLDER = '/output'
ALLOWED_EXTENSIONS = {'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """허용된 파일 확장자인지 확인합니다."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # 1. 파일 목록 및 자막 유형 선택
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return render_template('index.html', messages=[("Error", "파일을 선택하지 않았습니다.")])

        # 자막 선택 (Subtitle: 원문, Human Translation: 한국어 번역)
        subtitle_choice = request.form.get('subtitle_type', 'Human Translation') # ★ 디폴트: Human Translation으로 변경 ★
        results = []
        
        # 2. 파일 처리 및 변환
        for file in files:
            if file and allowed_file(file.filename):
                # 공백을 포함한 원본 파일 이름
                original_filename = file.filename
                # 임시 저장 경로에는 공백 포함 이름을 그대로 사용
                temp_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                
                # 임시 파일 저장
                file.save(temp_upload_path) 

                # 최종 SRT 파일 이름 결정 (공백 유지, 확장자만 .srt로 변경)
                if original_filename.lower().endswith('.xlsx'):
                    final_srt_filename = original_filename[:-5] + '.srt'
                else:
                    final_srt_filename = original_filename + '.srt'
                
                # 변환 실행: 최종 SRT 파일 이름도 함께 전달
                success, message, sub_col = process_xlsx_file(
                    temp_upload_path, 
                    OUTPUT_FOLDER, 
                    subtitle_column=subtitle_choice,
                    final_srt_filename=final_srt_filename 
                )
                
                if success:
                    # ★ 성공 시: 성공 메시지만 단순하게 표시 ★
                    results.append(("Success", f"'{final_srt_filename}' 변환 완료."))
                else:
                    # ★ 실패 시: 오류 메시지 표시 ★
                    results.append(("Error", f"'{original_filename}' 처리 실패: {message}"))
                    
                # 임시 파일 정리
                os.remove(temp_upload_path)
            else:
                 results.append(("Error", f"'{file.filename}'은 지원하지 않는 파일 형식입니다. (지원: .xlsx)"))

        # 3. 결과 표시
        return render_template('index.html', messages=results)
        
    return render_template('index.html')

if __name__ == '__main__':
    # 폴더 생성 확인
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 0.0.0.0으로 바인딩하여 Docker 외부 접근 허용
    app.run(host='0.0.0.0', port=5000)