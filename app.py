import os
from flask import Flask, request, render_template
from converter import process_xlsx_file

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
        platform = request.form.get('platform', 'youtube') # 기본값 유튜브
        subtitle_choice = request.form.get('subtitle_type', 'Human Translation')
        
        if not files or files[0].filename == '':
            return render_template('index.html', messages=[("Error", "파일을 선택하지 않았습니다.")])

        results = []
        for file in files:
            if file and allowed_file(file.filename):
                original_filename = file.filename
                temp_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                file.save(temp_upload_path) 

                # 확장자 변경 (.xlsx -> .srt)
                final_srt_filename = original_filename.rsplit('.', 1)[0] + '.srt'
                
                # 변환 실행
                success, message = process_xlsx_file(
                    temp_upload_path, 
                    OUTPUT_FOLDER, 
                    platform=platform,
                    subtitle_column=subtitle_choice,
                    final_srt_filename=final_srt_filename 
                )
                
                results.append(("Success" if success else "Error", message))
                os.remove(temp_upload_path)
            else:
                 results.append(("Error", f"'{file.filename}'은 지원하지 않는 파일 형식입니다."))

        return render_template('index.html', messages=results)
        
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000)