#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import json
from socket import error as SocketError
import errno
import argparse
from rule_translator import RuleTranslator
import os
from recognize import Recognize
import random
from time import sleep
"""
プロトコル部門のエージェントを言語処理部門で動作させるため翻訳するエージェント．
第４回人狼知能大会出場エージェント
"""



code = 'utf-8'
if os.name == "nt":
    code = 'cp932'

def main():
    parser = argparse.ArgumentParser(description='任意のプロトコル部門のエージェントを言語処理部門で動作させるため翻訳するエージェント')
    parser.add_argument('--myhost', '-mh', type=str, default="alice",
                        help='My Host Name')
    parser.add_argument('--myport', '-mp', type=int, default=10002,
                        help='My Port')
    parser.add_argument('--shost', '-sh', type=str, default="alice",
                        help='Aiwolf Server Host Name')
    parser.add_argument('--sport', '-sp', type=int, default=10000,
                        help='Aiwolf Server Port')
    parser.add_argument('--name', '-n', type=str, default="KELDIC",
                        help='Agent Name')
    parser.add_argument('--debug', '-d', action='store_true', default=False,
                        help='Enable Debag Mode')
    parser.add_argument('--sleep', '-sl', type=float, default=0.0,
                        help='Sleep time')
    args = parser.parse_args()

    my_host = args.myhost
    my_port = args.myport

    agent_name = args.name

    aiwolf_server_host = args.shost
    aiwolf_server_port = args.sport


    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    serversock.bind((my_host, my_port)) #IPとPORTを指定してバインドします
    serversock.listen(1) #接続の待ち受けをします（キューの最大数を指定）
    clientsock, client_address = serversock.accept() #接続されればデータを格納
    for_aiws_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for_aiws_sock.connect((aiwolf_server_host, aiwolf_server_port))

    translator = RuleTranslator()
    line = ''
    while True:
        sleep(args.sleep)
        try:
            line_recv = for_aiws_sock.recv(8192).decode(code)
            if args.debug:
                print("サーバから受信:", line_recv)
            if line_recv == '':
                break
            buffer_flg = 1
            while buffer_flg == 1:
                line += line_recv
                if '}\n{' in line:
                    (line, line_recv) = line.split("\n", 1)
                    buffer_flg = 1
                else:
                    buffer_flg = 0
                # parse json
                try:
                    forj_line = line.strip()
                    obj_recv = json.loads(forj_line)
                    obj_recv_raw = forj_line + "\n"
                    line = ''
                except ValueError:
                    obj_recv = None
                    print("Valueエラー", line)
                    break

                if obj_recv is not None:
                    request = obj_recv["request"]
                    # requestがINITIALIZEで自分の役職がVILLAGERだった場合，20%の確率でPOSSESSEDに変更
                    if request == "INITIALIZE":
                        #randomのシード値を設定
                        random.seed(obj_recv["gameSetting"]["randomSeed"] + obj_recv["gameInfo"]["agent"])
                        translator.set_gamesetting(obj_recv)

                        if obj_recv["gameInfo"]["roleMap"][str(obj_recv["gameInfo"]["agent"])] == "VILLAGER":
                            if random.randrange(10) <= 2:
                                obj_recv["gameInfo"]["roleMap"][str(obj_recv["gameInfo"]["agent"])] = "POSSESSED"

                    translator.set_gameinfo(obj_recv)
                    if obj_recv["talkHistory"] is not None:
                        if len(obj_recv["talkHistory"]) > 0:
                            obj_recv = translator.to_protocol(obj_recv)
                            translator.add_talk_history(obj_recv)
                    if args.debug:
                        print("エージェントに送信:", json.dumps(obj_recv) + "\n")

                    clientsock.sendall((json.dumps(obj_recv) + "\n").encode(code))


                    # requestがFINISHだった場合初期化
                    if request == "FINISH":
                        translator = RuleTranslator()

                    if request == 'NAME':
                        # 受信するが無視する．そうしないと通信が1個ずつずれる
                        line_recv = clientsock.recv(8192).decode(code)

                        name = agent_name + "\n"
                        for_aiws_sock.sendall(name.encode(code))
                        line = ""
                    elif request == 'ROLE' or request == 'VOTE' or request == 'ATTACK' or request == 'GUARD' \
                            or request == 'DIVINE' or request == 'TALK' or request == 'WHISPER':
                        line_recv = clientsock.recv(8192).decode(code)
                        if args.debug:
                            print("エージェントから受信:", line_recv)
                        if line_recv == '':
                            break
                        line = line_recv.strip()
                        if request == "TALK" or request == "WHISPER":
                            for_send_line = translator.to_text(line, obj_recv) + "\n"
                        elif request == "VOTE" and "VOTE" in line:
                            for_send_line = line.split(" ")[-1] + "\n"
                        else:
                            for_send_line = line + "\n"
                        if args.debug:
                            print("サーバに送信：", for_send_line)
                        for_aiws_sock.sendall(for_send_line.encode(code))
                        line = ""
        except UnicodeDecodeError as e:
            print("UnicodeDecodeError")
            continue
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise
            else:
                # expected error, connection reset by server
                pass
            # close connection

            clientsock.shutdown(socket.SHUT_RDWR)
            clientsock.close()
            for_aiws_sock.shutdown(socket.SHUT_RDWR)
            for_aiws_sock.close()
            serversock.shutdown(socket.SHUT_RDWR)
            serversock.close()
            print("ソケットエラー")
            break

    clientsock.shutdown(socket.SHUT_RDWR)
    clientsock.close()
    for_aiws_sock.shutdown(socket.SHUT_RDWR)
    for_aiws_sock.close()
    serversock.shutdown(socket.SHUT_RDWR)
    serversock.close()

if __name__ == '__main__':
    main()
