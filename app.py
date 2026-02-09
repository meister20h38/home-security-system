from flask import Flask, render_template, send_file, jsonify, request
import subprocess
import os
import signal

# Flaskアプリケーションを初期化
app = Flask(__name__)

# 監視スクリプトのプロセスを格納するグローバル変数
monitoring_process = None
# 監視スクリプトのパス
SYSTEM_SCRIPT_PATH = "system.py" 
# 最新の画像ファイルパス
IMAGE_PATH = "picture.jpg"

@app.route('/')
def index():
    """
    メインの操作ページ(index.html)を表示します。
    """
    # templatesフォルダにあるindex.htmlをレンダリングします
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_monitoring():
    """
    監視プロセスを開始するAPIエンドポイント。
    """
    global monitoring_process
    if monitoring_process is None or monitoring_process.poll() is not None:
        # 監視スクリプトを新しいプロセスとして開始
        monitoring_process = subprocess.Popen(['python3', SYSTEM_SCRIPT_PATH])
        return jsonify({'status': 'success', 'message': 'Monitoring started.'})
    else:
        return jsonify({'status': 'error', 'message': 'Monitoring is already running.'})

@app.route('/stop', methods=['POST'])
def stop_monitoring():
    """
    監視プロセスを停止するAPIエンドポイント。
    """
    global monitoring_process
    if monitoring_process and monitoring_process.poll() is None:
        # プロセスに終了シグナルを送信
        monitoring_process.send_signal(signal.SIGINT) # Ctrl+Cと同じ効果
        monitoring_process.wait() # プロセスが終了するのを待つ
        monitoring_process = None
        return jsonify({'status': 'success', 'message': 'Monitoring stopped.'})
    else:
        return jsonify({'status': 'error', 'message': 'Monitoring is not running.'})

@app.route('/status')
def status():
    """
    現在の監視状態（実行中か停止中か）を返すAPIエンドポイント。
    """
    global monitoring_process
    if monitoring_process and monitoring_process.poll() is None:
        is_running = True
    else:
        is_running = False
    return jsonify({'is_running': is_running})

@app.route('/latest_image')
def latest_image():
    """
    撮影された最新の画像を返すAPIエンドポイント。
    画像がない場合は404エラーを返す。
    """
    if os.path.exists(IMAGE_PATH):
        # 画像をキャッシュしないようにヘッダーを設定
        response = send_file(IMAGE_PATH, mimetype='image/jpeg')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        # 画像がない場合はプレースホルダー画像を返すか、エラーを返す
        return send_file('placeholder.jpg', mimetype='image/jpeg', conditional=True) # 代替画像を用意する場合

if __name__ == '__main__':
    # ネットワーク内のどのデバイスからでもアクセスできるようにhost='0.0.0.0'に設定
    app.run(host='0.0.0.0', port=5000, debug=True)

