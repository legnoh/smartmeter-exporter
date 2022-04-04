smartmeter-exporter
====

[![Badge](https://img.shields.io/badge/docker-legnoh/smartmeter--exporter-blue?logo=docker&link=https://hub.docker.com/r/legnoh/smartmeter-exporter)](https://hub.docker.com/r/legnoh/smartmeter-exporter)

<img src="https://user-images.githubusercontent.com/706834/160298533-026fd0e3-2312-4387-9829-b92d13b1e2af.png">

- スマートメーターから瞬時電力計測値(W)/瞬時電流計測値(A)を取得する Prometheus Exporter です。
- この Exporter はローム社の [BP35C2](https://www.rohm.co.jp/products/wireless-communication/specified-low-power-radio-modules/bp35c2-product) での起動を確認しています。

Usage
----

### Bルートサービスの契約

- お住まいの地域管轄の電力会社から、上記サービスの申込を行います。
  - 例: 関東の場合 -> [電力メーター情報発信サービス（Bルートサービス）| 東京電力パワーグリッド](https://www.tepco.co.jp/pg/consignment/liberalization/smartmeter-broute.html)
  - 電力自由化で別の電力会社と契約した場合も、送配電担当の会社(=自由化前の会社)宛に申込みます。
  - 「供給（受電）地点特定番号」の確認が必要です。電力会社のWebサイトなどから事前に確認してください。
- 申込完了後、IDが郵便、パスワードがメールで送付されてきます。

### BP35C2 の準備

1. [BP35C2 スタートアップマニュアル](https://fscdn.rohm.com/jp/products/databook/applinote/module/wireless/bp35c2_startupmanual_ug-j.pdf) に従って、セットアップを完了してください。
  - TeraTerm を使う部分は、 macOS であれば [minicom](https://salsa.debian.org/minicom-team/minicom) を使うことで同等の操作が可能です。
    ```sh
    brew install minicom
    minicom -b 115200 -D /dev/tty.usbserial-XXXXXXXX
     ```
  - ただし、ファームウェアの更新はWindowsが必須で必要です。
    - 最近(2022/03)買った BP35C2 であれば、予め最新のファームウェアになってました。
      - そのため、Windows 環境がなければスキップしてください。
1. BP35C2 の表示形式を変更し、16進 ASCII 表示にします(メモリに書込まれるので初回のみでOK)。
    ```sh
    # ROPT の結果が「00」の場合は変更しておく
    > ROPT
    OK 00
    > WOPT 01
    OK
    # TeraTerm or minicom を閉じる
    ```

### 起動(Python)

ソースコードを clone し、依存解決、環境変数の追加を行った後で起動してください。

```
# install pipenv(&python3)
brew install pipenv

# download
git clone https://github.com/legnoh/smartmeter-exporter.git
cd smartmeter-exporter
pipenv install

# config
cp example.env .env
vi .env

# exec
pipenv run main
```

### 起動(Docker/WIP)

- macOS/Windows では、Docker にUSBデバイスをパスさせることができないので起動できません。
  - [Can I pass through a USB device to a container? | FAQ | Docker Documentation](https://docs.docker.com/desktop/faqs/#can-i-pass-through-a-usb-device-to-a-container)
- そのため、コンテナでの実行は Linux 環境のみに限定されます。

```sh
# config
vi .env

SMARTMETER_ID=""
SMARTMETER_PASSWORD=""
SMARTMETER_DEVICE="/dev/ttyUSB0"
SMARTMETER_LOGLEVEL=10 #10:DEBUG 20:INFO
SMARTMETER_GET_INTERVAL=10
PORT=8000

# exec
docker run -p 8000:8000 --env-file='.env' --device=/dev/ttyUSB0:/dev/ttyUSB0 legnoh/smartmeter-exporter
```

Metrics
----

|Name|Type|Desc|
|----|----|----|
|`power_consumption_watt`|Gauge|瞬時電力計測値(W)|
|`power_consumption_ampare_r`|Gauge|瞬時電流計測値 R相(mA)|
|`power_consumption_ampare_t`|Gauge|瞬時電流計測値 T相(mA)|

Appendix
----

- [電力メーター情報発信サービス（Bルートサービス）｜電力自由化への対応｜東京電力パワーグリッド株式会社](https://www.tepco.co.jp/pg/consignment/liberalization/smartmeter-broute.html)
- [BP35C2 - データシートと製品詳細 | ローム株式会社 - ROHM Semiconductor](https://www.rohm.co.jp/products/wireless-communication/specified-low-power-radio-modules/bp35c2-product)
  - [BP35C2 スタートアップマニュアル](https://fscdn.rohm.com/jp/products/databook/applinote/module/wireless/bp35c2_startupmanual_ug-j.pdf)(pdf)
  - [BP35C0/BP35C2 コマンドリファレンス (パスワードが必要)](https://micro.rohm.com/jp/download_support/wi-sun/software/data/other/bp35c0_bp35c2_commandmanual_tr-j.pdf)(pdf)
    - パスワードの確認方法はスタートアップマニュアルに記載されています。
- [エコーネット規格 | ECHONET](https://echonet.jp/spec_v113_lite/)
  - [第2部 ECHONET Lite 通信ミドルウェア仕様](https://echonet.jp/wp/wp-content/uploads/pdf/General/Standard/ECHONET_lite_V1_13_jp/ECHONET-Lite_Ver.1.13_02.pdf)(pdf)
    - P3-1: `第3章 電文構成(フレームフォーマット)`
  - [APPENDIX ECHONET 機器オブジェクト詳細規定](https://echonet.jp/wp/wp-content/uploads/pdf/General/Standard/Release/Release_N/Appendix_Release_N.pdf)(pdf)
    - P3-307: `3.3.25 低圧スマート電力量メータクラス規定`
- [Minicom / minicom · GitLab](https://salsa.debian.org/minicom-team/minicom)
  - [minicom(1) - Linux man page](https://linux.die.net/man/1/minicom)
  - [ROHM BP35C2 + Bルート + Net-SNMP + Zabbixで電力監視 – Studio JamPack](https://jamfunk.jp/wp/works/svtools/pwrtb/)
- [スマートメーターの情報を最安ハードウェアで引っこ抜く - Qiita](https://qiita.com/rukihena/items/82266ed3a43e4b652adb)
