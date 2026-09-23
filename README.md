# jev / ljw98-Laya

鍩轰簬 [Laya](https://github.com/NandhaKishorM/laya)锛堥潪鑷洖褰?System 1 鍐崇瓥妯″瀷锛夌殑鏈湴 Web 鎺у埗鍙帮細璐翠竴娈垫枃鏈紝鍑轰竴閬撶被鍨嬪寲闂锛屼竴娆″墠鍚戝緱鍒扮瓟妗堜笌缃俊搴︺€?
- 浠撳簱锛歨ttps://github.com/ljw98/Laya
- 闀滃儚鍚嶏細`ljw98/Laya`
- 榛樿绔彛锛歚8787`
- 浠ｇ爜鍦ㄤ粨搴擄紱**妯″瀷 zip 鏀惧湪 GitHub Releases**锛堝崟鏂囦欢杩滆秴 100MB锛屼笉鑳借繘 git锛?
```text
jev/
鈹溾攢鈹€ index.html / app.css / app.js   # Web 鐣岄潰
鈹溾攢鈹€ server.py                       # Flask API
鈹溾攢鈹€ download_models.py              # HF 鎴?GitHub Releases 涓嬭浇
鈹溾攢鈹€ Dockerfile / docker-compose.yml
鈹溾攢鈹€ requirements.txt
鈹溾攢鈹€ examples/demo_cli.py
鈹溾攢鈹€ logs/                           # gitignore
鈹溾攢鈹€ releases/                       # 鏈湴鎵撳寘 zip锛坓itignore锛夛紝鐢ㄤ簬浼?Release
鈹斺攢鈹€ laya-main/                      # Laya 婧愮爜 + models/
    鈹溾攢鈹€ laya/
    鈹斺攢鈹€ models/
        鈹溾攢鈹€ laya/
        鈹溾攢鈹€ laya-multilingual/
        鈹斺攢鈹€ laya-typed-decisions/
```

## 鑾峰彇妯″瀷鏉冮噸

### 鏂瑰紡 1锛欸itHub Releases锛堢粰鐢ㄦ埛鐩存帴涓嬶級

鏈粨搴?`releases/` 宸叉墦濂戒笁涓?zip锛堟墦鍖呮満鏈湴锛夛細

| 鏂囦欢 | 绾﹀ぇ灏?|
|---|---|
| `releases/laya.zip` | 742 MB |
| `releases/laya-multilingual.zip` | 572 MB |
| `releases/laya-typed-decisions.zip` | 742 MB |

涓婁紶鍒?GitHub Release锛堢ず渚?tag `v1.0.0`锛屼粨搴撳悕浠ヤ綘瀹為檯涓哄噯锛夛細

```powershell
# 缃戦〉锛歊eleases 鈫?Draft 鈫?涓婁紶涓婅堪涓変釜 zip
# 鎴?gh锛堥渶宸茬櫥褰曪級锛?gh release create v1.0.0 `
  releases/laya.zip `
  releases/laya-multilingual.zip `
  releases/laya-typed-decisions.zip `
  --repo ljw98/Laya `
  --title "Laya model weights" `
  --notes "Checkpoints for ljw98/Laya console"
```

鐢ㄦ埛涓嬭浇锛堣В鍘嬪埌 `laya-main/models/<瀵瑰簲鍚嶅瓧>/`锛夛細

```powershell
python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0
# 鎴栨墜鍔細
# 瑙ｅ帇 laya.zip            -> laya-main/models/laya/
# 瑙ｅ帇 laya-multilingual.zip -> laya-main/models/laya-multilingual/
# 瑙ｅ帇 laya-typed-decisions.zip -> laya-main/models/laya-typed-decisions/
```

### 鏂瑰紡 2锛欻ugging Face

```powershell
python download_models.py --hf-endpoint https://hf-mirror.com
```

## 蹇€熷紑濮?
### Docker

```powershell
# 1) 鍑嗗鏉冮噸锛堜换閫変竴绉嶏級
python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0
python download_models.py --hf-endpoint https://hf-mirror.com
# 鎴?$env:LAYA_MODEL_MODE="auto"

# 2) 鍚姩
docker-compose up -d --build

# 3) 鎵撳紑
# http://127.0.0.1:8787
```

瀵煎嚭闀滃儚锛?
```powershell
docker save -o ljw98-Laya-latest.tar ljw98/Laya:latest
docker load -i ljw98-Laya-latest.tar
```

### 鏈満 Python

```powershell
pip install -r requirements.txt
pip install -e ./laya-main
python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0
python server.py
```

## 閰嶇疆

| 鐜鍙橀噺 | 鍚箟 | 榛樿 |
|---|---|---|
| `LAYA_HOST` / `LAYA_PORT` | 鐩戝惉鍦板潃 | `0.0.0.0:8787` |
| `MODEL_DIR` | 鏉冮噸鏍圭洰褰?| `./laya-main/models` |
| `LAYA_MODEL_MODE` | `local` 浠呮湰鍦?/ `auto` 缂哄け鑷姩涓嬭浇 | `local` |
| `HF_ENDPOINT` | Hugging Face 绔偣锛堝彲濉暅鍍忥級 | 瀹樻柟 |

鏉冮噸鐩綍缁撴瀯锛堟瘡涓鏌ョ偣闇€瀹屾暣锛夛細

```text
laya-main/models/<name>/
  rl_agent_config.json
  model.safetensors
  tokenizer/tokenizer.json
  tokenizer/tokenizer_config.json
  encoder/config.json
```

`<name>` 鈭?`laya` | `laya-multilingual` | `laya-typed-decisions`銆?
## Web 鐢ㄦ硶

1. 閫夋嫨妯″瀷锛堝崟妯″瀷椹荤暀锛屽垏鎹㈡椂鍔犺浇/鍗歌浇锛?2. 绮樿创鍐呭
3. 鍑轰竴閬撻锛坄choice` / `score` / `noul`锛?4. 寮€濮嬪垎鏋?
| type | 杈撳嚭 | 閫傚悎 |
|---|---|---|
| `choice` | 閫夐」 + 姒傜巼 + 缃俊搴?| 鎰忓浘銆侀儴闂ㄣ€佽瘽棰?|
| `score` | 鏈熸湜妗ｄ綅 + 鍒嗗竷 | 绱ф€ュ害銆佸嵄瀹崇瓑绾?|
| `noul` | P(鎴愮珛) 0~1 | 鏄惁閫€娆俱€佹槸鍚﹂挀楸?|

鍑洪鍘熷垯锛氶棶銆屾枃鏈噷鍐欎簡浠€涔堛€嶏紝灏戦棶銆屽績閲屾€庝箞鎯炽€嶃€傚伐鍗曞垎璇娿€佸唴瀹瑰畨鍏ㄣ€佹彁绀烘姢鏍忔洿绋炽€?
## HTTP API

### `GET /api/health`

```json
{ "ready": true, "resident": "multilingual", "model_mode": "local", "backend": "laya" }
```

### `GET /api/models`

妫€鏌ョ偣鍒楄〃锛堟槸鍚︽湰鍦板畬鏁淬€佹槸鍚﹀綋鍓嶉┗鐣欙級銆?
### `POST /api/model/select`

```json
{ "model": "english" | "multilingual" | "typed" }
```

鍔犺浇鐩爣妯″瀷骞跺嵏杞戒笂涓€涓紙鍗曟ā鍨嬮┗鐣欙級銆?
### `POST /api/model/unload`

鍗歌浇褰撳墠椹荤暀妯″瀷銆?
### `POST /api/predict`

```json
{
  "model": "multilingual",
  "state": { "text": "璇蜂粖澶╅€€娆撅紝鍚﹀垯鍙栨秷璁㈤槄銆? },
  "questions": {
    "q1": {
      "type": "choice",
      "instructions": "瀹㈡埛鎯宠浠€涔堬紵",
      "criteria": { "閫€娆?: null, "鎶€鏈敮鎸?: null, "鍏朵粬": null }
    }
  }
}
```

| 瀛楁 | 璇存槑 |
|---|---|
| `model` | `english` \| `multilingual` \| `typed` |
| `state` | 瀵硅薄鎴栧瓧绗︿覆 |
| `questions.*.type` | `choice` \| `score` \| `noul` |
| `questions.*.instructions` | 闂鏂囨湰 |
| `questions.*.criteria` | choice锛歚{"鏍囩": "璇存槑"}`锛泂core锛氭暟缁勪綆鈫掗珮锛沶oul 鍙渷鐣?|

## 妯″瀷瀵圭収

| API | 鐩綍 | 鐗圭偣 |
|---|---|---|
| `english` | `models/laya` | ModernBERT-large锛岃嫳鏂囨渶鍑?|
| `multilingual` | `models/laya-multilingual` | mmBERT锛屼腑鏂?澶氳鏇寸ǔ |
| `typed` | `models/laya-typed-decisions` | typed-decisions 寰皟 |

涓枃寤鸿榛樿 `multilingual`銆?
## 鍐呭瓨璇存槑

- **鍗曟ā鍨嬮┗鐣?*锛屼笉浼氫笁涓竴璧峰姞杞姐€?- 鍔犺浇 1 涓鏌ョ偣鏃惰繘绋?RSS 澶х害 **1.8鈥?GB**锛坒p32 鏉冮噸 + PyTorch锛夈€?- 鍒囨崲妯″瀷浼氬嵏杞戒笂涓€涓紱Python 鍒嗛厤鍣ㄥ彲鑳戒粛淇濈暀鏁扮櫨 MB锛屽睘姝ｅ父銆?
## 鑳藉姏杈圭晫

- 鍐烽棬/涓昏棰橈紙鎯呮劅鍙樺寲銆佸績鐞嗘帹鏂級闆舵牱鏈彲鑳芥帴杩戦殢鏈猴紱涓ヨ們涓氬姟璇峰井璋冿紙瑙?`laya-main/notebooks/`锛夈€?- 閫夐」寰堝锛堢害 >50锛夋椂闇€璋冨ぇ token 棰勭畻鎴?`predict_shortlist`銆?- 鏉冮噸璁稿彲瑙?Laya 涓婃父锛圓pache 2.0锛夈€?
## 涓婁紶 GitHub 鏃舵敞鎰?
- **涓嶈鎻愪氦** `laya-main/models/**/model.safetensors`銆乣*.tar`銆乣logs/`锛堝凡鍦?`.gitignore`锛夈€?- 浠撳簱淇濇寔浠ｇ爜 + 鏂囨。鍗冲彲锛涚敤鎴风敤 `download_models.py` 鎴?`LAYA_MODEL_MODE=auto` 鍙栨潈閲嶃€?- `laya-main/` 涓?Laya 婧愮爜锛圓pache 2.0锛夛紝涓婃父锛歨ttps://github.com/NandhaKishorM/laya

## License

- 鏈」鐩?Web/API 澹筹細闅忎粨搴撶害瀹?- Laya 婧愮爜涓庢潈閲嶏細Apache 2.0锛圕onvai Innovations锛?
