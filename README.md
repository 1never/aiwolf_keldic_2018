# aiwolf_keldic_2018

CEDEC2018で開催された第４回人狼知能大会 自然言語部門に参加したエージェントプログラムです．
プロトコル部門のエージェントとサーバの間を中継し，プロトコルと自然言語を相互翻訳することでプロトコル部門のエージェントを自然言語部門で動作させます．

* 動作環境
	* Python 3.5.3で動作確認済みです．

* エージェントの実行方法
	* 人狼知能プラットフォーム0.4.xのサーバプログラムを実行する必要があります
	* サーバプログラムの実行後 ./run.pyを実行します．その際，サーバとプロトコル部門エージェントの両方の接続先を指定します．
	    * 例： $python ./run.py -mp localhost -mh 10001 -sh localhost -sp 10000
    * 最後に，プロトコル部門のエージェントを -mh, -shで指定した接続先に接続します

* その他
    * サーバとの通信に関する部分のコードはk-haradaさんのAIWolfPy (https://github.com/k-harada/AIWolfPy) を大いに参考にしています．