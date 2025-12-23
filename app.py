import os
import subprocess
import pandas as pd
from flask import Flask, request, render_template, jsonify, Response
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
        subtitle_choice = request.form.get('subtitle_type', 'dual')
        save_method = request.form.get('save_method', 'download')
        
        if not files or files[0].filename == '':
            return jsonify({"messages": [("Error", "파일을 선택하지 않았습니다.")]}), 400

        results = []
        download_data = None

        for file in files:
            if file and allowed_file(file.filename):
                final_srt_filename = file.filename.rsplit('.', 1)[0] + '.srt'
                try:
                    df = pd.read_excel(file, engine='openpyxl')
                    srt_content = create_srt_content(df, platform, subtitle_choice)
                    
                    # 실시간 로그 모니터링을 위해 파일명 출력
                    print(f"[PROCESS] Target: {final_srt_filename}", flush=True)

                    if save_method == 'nas':
                        output_path = os.path.join(OUTPUT_FOLDER, final_srt_filename)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(srt_content)
                        results.append(("Success", f"'{final_srt_filename}' NAS 저장 완료."))
                    else:
                        download_data = {"content": srt_content, "filename": final_srt_filename}
                        results.append(("Success", f"'{final_srt_filename}' 변환 성공! 🟢"))
                except Exception as e:
                    results.append(("Error", f"'{file.filename}' 처리 오류: {str(e)}"))
            else:
                 results.append(("Error", f"'{file.filename}'은 지원하지 않는 형식입니다."))

        return jsonify({
            "messages": results,
            "download": download_data if save_method == 'download' else None
        })
    return render_template('index.html')

@app.route('/logs.html')
def logs_page():
    return render_template('logs.html')

def generate_docker_logs():
    # 아래 줄의 마지막 인자를 새로운 docker-compose.yml의 container_name인 'test_srt'로 수정했습니다.
    process = subprocess.Popen(
        ['docker', 'logs', '-f', '--tail', '50', 'lr-srt_converter'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    while True:
        line = process.stdout.readline()
        if not line: break
        
        tag = "INFO"
        if "POST / HTTP/1.1\" 200" in line: tag = "SUCCESS"
        elif "POST / HTTP/1.1\" 400" in line: tag = "FAILED"
        elif "[PROCESS] Target:" in line: tag = "FILE"
        
        yield f"data: {tag}|{line.strip()}\n\n"

@app.route('/stream-logs')
def stream_logs():
    return Response(generate_docker_logs(), mimetype='text/event-stream')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000)