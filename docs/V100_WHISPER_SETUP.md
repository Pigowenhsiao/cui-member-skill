# V100 Whisper 使用方式

## 連線資訊
- IP: `192.168.0.140`
- User: `x`
- Key: `~/.ssh/id_rsa`
- GPU: 3x Tesla V100-SXM2-32GB

## 首次設定（一次性）
```bash
# 安裝 faster-whisper
ssh -i ~/.ssh/id_rsa x@192.168.0.140 "pip install --break-system-packages faster-whisper"

# 下載 static ffmpeg
ssh -i ~/.ssh/id_rsa x@192.168.0.140 "mkdir -p ~/bin && curl -sL https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz | tar xJ -C ~/bin --strip-components=1 --wildcards '*/ffmpeg'"
```

## 轉換流程

### 1. 上傳音訊
```bash
rsync -av -e "ssh -i ~/.ssh/id_rsa" --progress <audio.mp3> x@192.168.0.140:/tmp/
```

### 2. 執行轉換
```bash
ssh -i ~/.ssh/id_rsa x@192.168.0.140 "export PATH=\$HOME/bin:\$PATH && cd /tmp && python3 -c \"
from faster_whisper import WhisperModel
model = WhisperModel('medium', device='cuda', compute_type='float16')
segments, info = model.transcribe('<file.mp3>', language='zh', beam_size=5)
print(f'語言: {info.language}, 時長: {info.duration:.1f}s')
with open('<file.txt>', 'w') as f:
    for seg in segments:
        f.write(seg.text)
print('完成')
\""
```

### 3. 下載文字稿
```bash
rsync -av -e "ssh -i ~/.ssh/id_rsa" --progress x@192.168.0.140:/tmp/<file.txt> <local_dest>/
```

## 快速指令汇总
```bash
# 上傳
rsync -av -e "ssh -i ~/.ssh/id_rsa" --progress <audio.mp3> x@192.168.0.140:/tmp/

# 轉換（medium, zh）
ssh -i ~/.ssh/id_rsa x@192.168.0.140 "export PATH=\$HOME/bin:\$PATH && cd /tmp && python3 -c \"
from faster_whisper import WhisperModel
m = WhisperModel('medium', device='cuda', compute_type='float16')
segs, info = m.transcribe('$(basename <audio.mp3>)', language='zh', beam_size=5)
print(info.language, info.duration)
with open('$(basename <audio.mp3> .mp3).txt','w') as f:
    for s in segs: f.write(s.text)
\""

# 下載
rsync -av -e "ssh -i ~/.ssh/id_rsa" --progress x@192.168.0.140:/tmp/<file.txt> ./
```
