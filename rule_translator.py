#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import codecs
from recognize import Recognize
import random

def convert_it2name(id):
    if len(str(id)) > 1:
        return "Agent[" + str(id) + "]"
    else:
        return "Agent[0" + str(id) + "]"


def read_template(filepath):
    template = {}
    template["COMINGOUT"] = {"SEER":[], "WEREWOLF":[], "POSSESSED":[]}
    template["DIVINED"] = {"HUMAN": [], "WEREWOLF":[]}
    template["ESTIMATE"] = {"SEER":[], "WEREWOLF":[], "POSSESSED":[], "VILLAGER":[]}
    template["VOTE"] = {"ALL": [], "SAME": []}
    template["REQUEST"] = {"VOTE": [], "DIVINATION": []}
    with codecs.open(filepath, "r", "utf-8") as f:
        for line in f:
            line = line.strip()

            splitted = line.split(",")
            if len(splitted) > 2:
                template[splitted[0]][splitted[1]].append(splitted[2])
    return template

# 発言の同意をするため，発言予定のものと同じ発話を取得
def get_same_talk(talkHistory, my_protocol, my_id):
    for t in talkHistory:
        if t["agent"] != my_id and t["text"] == my_protocol:
            return t
    return None

def read_chat(filepath):
    chat_lines = []
    with codecs.open(filepath, "r", "utf-8") as f:
        for line in f:
            line = line.strip()
            if len(line) > 2:
                chat_lines.append(line)
    return chat_lines


def is_all_skip(talkHistory):
    res = True
    for t in talkHistory:
        if t["text"].lower() == "skip" or t["text"].lower() == "over":
            pass
        else:
            res = False
    return res

def is_over_half_skip(talkHistory):
    skip_count = 0
    for t in talkHistory:
        if t["text"].lower() == "skip" or t["text"].lower() == "over":
            skip_count += 1
    if skip_count >= 3:
        return True
    return False

class RuleTranslator:
    def __init__(self):
        self.r = Recognize("data/")
        self.template = read_template("data/translate_template.txt")
        self.chat = read_chat("data/chat.txt")
        self.greeting = read_chat("data/greeting.txt")
        self.day = 0
        self.talk_history = []
        self.my_id = None
        self.my_role = None
        self.co_role = None
        self.divine_results = []


    def set_gamesetting(self, json):
        if json["gameSetting"] is not None:
            random.seed(json["gameSetting"]["randomSeed"] + json["gameInfo"]["agent"])


    def set_gameinfo(self, json):
        if json["gameInfo"] is not None:
            self.my_id = json["gameInfo"]["agent"]
            self.my_role = json["gameInfo"]["roleMap"][str(self.my_id)]
            self.day = json["gameInfo"]["day"]


    def add_talk_history(self, json):
        for t in json["talkHistory"]:
            if t not in self.talk_history:
                self.talk_history.append(t)

    def _choice_reason(self, protocol_text):
        if "VOTE" in protocol_text:
            player = protocol_text.split(" ")[1]
            player_idx = int(player.replace("Agent[", "").replace("]", ""))

            # 自分が人狼 or 狂人COしているかどうか
            if self.co_role == "WEREWOLF" or self.co_role == "POSSESSED":
                return random.choice(["これで終わり！", "楽勝だったね！", "これで勝ちだね。", "たぶんこれでいいと思う！", "そういうわけで、",
                                      "言うまでもないかもしれないけど、"])
            # 自分が占い師COしているかどうか
            if self.co_role == "SEER":
                if (player, "HUMAN") in self.divine_results and self.day == 0:
                    return random.choice(["占い結果は白だったけど、パワープレイは怖いから、", "パワープレイ防止ってことで、"])
                elif (player, "HUMAN") in self.divine_results:
                    return random.choice(["占い結果は白だったけど、もうわけわかんないから、"])
                elif (player, "WEREWOLF") in self.divine_results:
                    return random.choice(["占いの結果が人狼だったから、", "占い結果が黒だったから、", "じゃあ人狼に投票するってことで、",
                                          "占いの結果の通り、"])
            # 占い師COしていない場合
            if self.co_role != "SEER":
                myname = convert_it2name(self.my_id)

                for t in self.talk_history:
                    # 発話ログを検索して自分を投票先にしているものがあれば
                    if "VOTE " + myname in t["text"] and t["day"] == self.day and t["agent"] == player_idx:
                        return random.choice(["ぼくに投票するって言うのはおかしいから、", "投票先がぼくって言うのは意味不明だよ。", "ぼくに投票するって言うならしょうがないね。"])
                    elif  "DIVINED " + myname + " WEREWOLF" in t["text"] and t["day"] == self.day and t["agent"] == player_idx:
                        return random.choice(["ぼくを人狼って言う占い師は偽物だから、", "ぼくに黒判定を出した占い師は嘘つきだから、", "偽物の占い師は明らかだよね。"])
                    elif "DIVINED" + myname + " HUMAN" in t["text"] and t["day"] == self.day and t["agent"] == player_idx:
                        return "ぼくに白判定を出したけど、人狼の可能性もあるから、"
            return random.choice(["ちょっと表情が硬い気がするから、", "とりあえず直感で、", "なんか雰囲気がおかしい気がするから、",
                                  "何か企んでそうな顔してるし、", "ちょっと挙動不審だし、", "さっきから目が泳いでるから、"])




    def to_text(self, protocol_text, json):
        if len(json["talkHistory"]) == 0 and protocol_text.lower() == "skip" and self.day == 0:
            return random.choice(self.greeting)

        if protocol_text.lower() == "skip" and self.day == 0 and len(json["talkHistory"]) > 0:
            if json["talkHistory"][-1]["turn"] == 0:
                return random.choice(self.chat)

        if len(json["talkHistory"]) == 0 and protocol_text.lower() == "skip" and is_all_skip(json["talkHistory"]):
            return random.choice(self.chat)

        protocol_text = protocol_text.strip()
        if "{" in protocol_text:
            return protocol_text

        if protocol_text.lower() == "skip" or protocol_text.lower() == "over":
            if len(json["orgTalkHistory"]) > 0:
                for orgt in json["orgTalkHistory"]:
                    if ">>" + convert_it2name(self.my_id) in orgt["text"] and "？" in orgt["text"] and ("誰" in orgt["text"] or "だれ" in orgt["text"]):
                        text = ">>" + convert_it2name(orgt["agent"]) + " "
                        return text + random.choice(["さっき言ったばっかだよ！", "ぼくの話ちゃんと聞いてた？さっき言ったでしょ！", "なんか適当に質問してない？さっき言ったとこだよ。", "さっきぼく言ったよ？"])
            return protocol_text


        if is_over_half_skip(json["talkHistory"]):
            return "Skip"


        if "REQUEST" in protocol_text:
            if "DIVINATION" in protocol_text:
                div_target = protocol_text.split("DIVINATION ")[1].split(")")[0]
                t = random.choice(self.template["REQUEST"]["DIVINATION"])
                t = t.replace("《AGENTNAME》", div_target)
                return t
            elif "VOTE" in protocol_text:
                vote_target = protocol_text.split("VOTE ")[1].split(")")[0]
                t = random.choice(self.template["REQUEST"]["VOTE"])
                t = t.replace("《AGENTNAME》", vote_target)
                return t
            else:
                return random.choice(self.chat)

        elif "CO" in protocol_text:
            role = protocol_text.split(" ")[-1]
            if role == "SEER" or role == "POSSESSED" or role == "WEREWOLF":
                t = random.choice(self.template["COMINGOUT"][role])
                self.co_role = role
                return t
            else:
                return random.choice(self.chat)

        elif "ESTIMATE" in protocol_text:
            player = protocol_text.split(" ")[1]
            role = protocol_text.split(" ")[2]
            t = random.choice(self.template["ESTIMATE"][role])
            t = t.replace("《AGENTNAME》", player)
            return t

        elif "VOTE" in protocol_text:
            player = protocol_text.split(" ")[1]
            t = random.choice(self.template["VOTE"]["ALL"])
            t = t.replace("《AGENTNAME》", player)
            # 理由を追加
            t = self._choice_reason(protocol_text) + t
            # 0日目の場合は雑談に変更
            if self.day == 0:
                t = random.choice(self.chat)

            # 直前の発話にこれから言う内容と同じものがあった場合，同意に変更
            same_talk = get_same_talk(json["talkHistory"], protocol_text, self.my_id)
            if same_talk is not None:
                t = ">>" + convert_it2name(same_talk["agent"]) + " " + random.choice(self.template["VOTE"]["SAME"])
                t = t.replace("《AGENTNAME》", player)
            return t

        elif "DIVINED" in protocol_text:
            player = protocol_text.split(" ")[1]
            species = protocol_text.split(" ")[2]
            t = random.choice(self.template["DIVINED"][species])
            t = t.replace("《AGENTNAME》", player)
            self.divine_results.append((player, species))
            return t
        else:
            return random.choice(self.chat)


    def to_protocol(self, json):
        # ささやきは削除
        if json['whisperHistory'] is not None:
            json['whisperHistory'] = []

        # 通常発言の処理
        if json['talkHistory'] is not None:
            #もとの発話を保存
            json['orgTalkHistory'] = copy.deepcopy(json['talkHistory'])
            translated_talk = []

            for t in json['talkHistory']:
                self.day = t["day"] # 日付を取得しておく
                if t["text"].lower() == "over" or t["text"].lower() == "skip":
                    translated_talk.append(t)
                else:
                    res = self.r.recognize(t["text"], t["agent"])
                    if len(res) == 0:
                        t["text"] = "Skip"
                        translated_talk.append(t)
                    elif len(res) == 1:
                        t["text"] = res[0]
                        translated_talk.append(t)
                    else:
                        for s in res:
                            tmp = copy.deepcopy(t)
                            tmp["text"] = s
                            translated_talk.append(tmp)
            json["talkHistory"] = translated_talk
        return json