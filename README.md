# acnh-turnip-gspread
あつもりのカブ価を Google Spreadsheet に記録する Discord bot

## 使い方

`@bot` はボットの名前に置き換えてください。

### カブ価登録 (+)

現在時刻のセルに `100` を記録する。

```
@bot +100
@bot + 100
@bot +１００
```

木曜午前に `100` を記録する。

```
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
@bot +100 買
@bot +買い 100
```

### 履歴を見る (hist)

カブ価の履歴を `100 100/64 32/- -/- -/- -/- -/-` のような形式で見る。

``` 
@bot hist
```

### 名前紐付け (iam)

スプレッドシート上の名前と Discord アカウントの紐付けを bot に覚えさせる。
名前は正確に入力してください (コピペ推奨)。

```
@bot iam しずえ
@bot i'm しずえ
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

`secret.env` に秘匿情報を書く。
`GSPREAD_CREDENTIAL_BASE64` は例の JSON ファイルを base64 エンコードした結果。 

```shell script
export GSPREAD_NAME=
export GSPREAD_CREDENTIAL_BASE64=
export MONGO_HOST=mongo
export MONGO_PORT=27017
export MONGO_INITDB_ROOT_USERNAME=
export MONGO_INITDB_ROOT_PASSWORD=
export MONGO_APP_USERNAME=app
export MONGO_APP_PASSWORD=
export DISCORD_BOT_TOKEN=
```

`config.yml` を書く。
TODO: `mongo_use_inmemory` を `false` にした場合は他の MongoDB 関連の設定を空にしても動くようにする。

```yaml
mongo_use_inmemory: false
mongo_database: turnip_bot
mongo_collection: name_binding
```

設定を読み込んでから `docker-compose` で起動する。

```shell script
$ . secret.env
$ docker-compose build
$ docker-compose up
```

## Contribution

PR & issue 歓迎です。Python 1 週間なのでまずいところあると思います。
