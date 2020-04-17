# acnh-turnip-gspread
あつもりのカブ価を Google Spreadsheet に記録する Discord bot

## 使い方

`@bot` はボットの名前に置き換えてください。

### カブ価登録 (+ or 数字)

現在時刻のセルに `100` を記録する。午前 5 時前は前日として扱わます。

```
@bot 100
@bot 100
@bot １００
@bot +100
@bot + 100
@bot +１００
```

木曜午前に `100` を記録する。

```
@bot 100 木曜AM
@bot 100 木曜am
@bot １００　木曜ＡＭ
@bot １００　木ＡＭ
@bot １００　木午前
@bot 木AM 100
@bot 木ａｍ　１００
@bot +100 木曜AM
@bot +100 木曜am
@bot +１００　木曜ＡＭ
@bot +１００　木ＡＭ
@bot +１００　木午前
@bot +木AM 100
@bot +木ａｍ　１００
```

買値を登録する。

```
@bot 100 買
@bot +100 買
@bot +買い 100
```

### 履歴を見る (hist)

カブ価の履歴を `100 100/64 32/- -/- -/- -/- -/-` のような形式で見る。

``` 
@bot hist
```

### 名前紐付け (im)

スプレッドシート上の名前と Discord アカウントの紐付けを bot に覚えさせる。
名前は正確に入力してください (コピペ推奨)。

```
@bot im しずえ
```

### 名前紐付けの確認 (who)

スプレッドシート上の名前と Discord アカウントの紐付けを確認する。

```
@bot who
```

### オウム返し (echo)

リプライの内容をそのまま言わせる。テスト用です。

```
@bot echo hello
```

### 起動確認 (空のメッセージ)

テスト用です。

```
@bot
```

### 一括登録

未実装

### 型の判定

未実装

## 起動方法

テスト用の以下のものを用意してください。

- スプレッドシート
  - 内容は本番のものをコピーしておく
- Discord サーバー
- https://gspread.readthedocs.io/en/latest/oauth2.html で発行される credentials が書かれた JSON

### docker-compose を使う場合

`secret.env` に秘匿情報を書く。

```shell script
export GSPREAD_NAME= # URLから推測できるスプレッドシートの名前
export GSPREAD_CREDENTIAL_BASE64= # credentials 入り JSON を base64 encode したもの (ここどうにかしたい)
export MONGO_HOST=mongo # docker-compose.yml を使うとこうなる
export MONGO_PORT=27017 # 同上
export MONGO_INITDB_ROOT_USERNAME= # `root` とか
export MONGO_INITDB_ROOT_PASSWORD= # 適当に決める
export MONGO_APP_USERNAME= # アプリが使う MongoDB のアカウント名 (`app` とか)
export MONGO_APP_PASSWORD= # 適当に決める
export DISCORD_BOT_TOKEN= # Discord bot のトークン
```

`config.yml` に秘匿する必要がない設定を書く。
TODO: `mongo_use_inmemory` を `false` にした場合は他の MongoDB 関連の設定を空にしても動くようにする。

```yaml
mongo_use_inmemory: false # ローカル開発用に用意したが true にして動くかは未確認。
mongo_database: turnip_bot
mongo_collection: name_binding
```

設定を読み込んでから `docker-compose` で起動する。`sudo` を使う場合は `-E` オプションを忘れない。

```shell script
$ . secret.env
$ docker-compose build
$ docker-compose up
```

### docker-compose を使わない場合

1. 上と同じように `secret.env` と `config.yml` を書く
  - MongoDB の項目は適当なダミー値とする
1. `main` メソッドをいじって `pymongo_inmemory` を使うようにする (たぶん見ればわかる)
1. `Pipfile` の `python_version` で指定されているバージョンの Python を用意する
1. `pipenv install`
1. `pipenv run python3 main.py` で起動

## スプレッドシートに書く場所の決定方法

- `なまえ` に一致するセルがある列から登録されたユーザー名を見つける
- `買値` に一致するセルがある行から期間を見つける
- 更新リクエストではそれらの交差するセルに書き込む

具体的には `table.py` を参照。

## Contribution

PR & issue 歓迎です。Python 歴 1 週間なのでまずいところあると思います。
