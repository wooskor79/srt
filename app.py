import os
import io
import pandas as pd
from flask import Flask, request, render_template, jsonify
from converter import create_srt_content

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = '/output'
ALLOWED_EXTENSIONS = {'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')
        platform = request.form.get('platform', 'youtube')
        subtitle_choice = request.form.get('subtitle_type', 'Human Translation')
        save_method = request.form.get('save_method', 'nas')
        
        if not files or files[0].filename == '':
            return jsonify({"messages": [("Error", "파일을 선택하지 않았습니다.")]}), 400

        results = []
        download_data = None

        for file in files:
            if file and allowed_file(file.filename):
                final_srt_filename = file.filename.rsplit('.', 1)[0] + '.srt'
                try:
                    # 파일 데이터 읽기
                    df = pd.read_excel(file, engine='openpyxl')
                    srt_content = create_srt_content(df, platform, subtitle_choice)
                    
                    if save_method == 'nas':
                        # NAS 저장 방식
                        output_path = os.path.join(OUTPUT_FOLDER, final_srt_filename)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(srt_content)
                        results.append(("Success", f"'{final_srt_filename}' NAS 저장 완료."))
                    else:
                        # 브라우저 다운로드 방식 (메시지 생성 및 데이터 준비)
                        download_data = {
                            "content": srt_content,
                            "filename": final_srt_filename
                        }
                        results.append(("Success", f"'{final_srt_filename}' 변환 성공! 곧 다운로드가 시작됩니다."))
                
                except Exception as e:
                    results.append(("Error", f"'{file.filename}' 처리 중 오류: {str(e)}"))
            else:
                 results.append(("Error", f"'{file.filename}'은 지원하지 않는 파일 형식입니다."))

        # JSON 형식으로 메시지와 다운로드 데이터를 함께 반환
        return jsonify({
            "messages": results,
            "download": download_data if save_method == 'download' else None
        })
        
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000)