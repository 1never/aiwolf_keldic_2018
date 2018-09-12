#!/usr/bin/env python3
import re
import codecs
"""
自然言語発話を認識する．
認識するのはプロトコルをベース
・カミングアウト ("CO",  "役職名")
・投票先 ("VOTE",  "投票先")
・占い結果  ("DIVINED", "占い先(agent_id)", "結果")
・役職推定 ESTIMATE ("誰", "役職") 未実装
・雑談 ("CHAT") 未実装
・確認 CONFIRM (確認先, 内容(CO or VOTE or DIVINED or ESTIMATE or CHAT)) 未実装
・依頼 REQUEST (依頼先(agent or all or role), 内容(CO or VOTE or DIVINED or OTHER)) 未実装
"""

def convert_it2name(id):
    if len(str(id)) > 1:
        return "Agent[" + str(id) + "]"
    else:
        return "Agent[0" + str(id) + "]"

class Recognize:
    def __init__(self, data_dic):
        self.self_list = self.read_list(data_dic + "selfList.txt")
        self.delete_list = self.read_list(data_dic + "deleteList.txt")
        self.role_list = self.read_list(data_dic + "role_list.txt")
        self.suffix_list = self.read_list(data_dic + "suffixList.txt")

        self.co_regex = self.read_regex(data_dic + "co_regex.txt")
        self.divine_regex_rule = self.read_regex_rule(data_dic + "divine_regex_rule.txt")
        self.divine_regex = self.read_regex(data_dic + "divine_regex.txt")
        self.vote_regex = self.read_regex(data_dic + "vote_regex.txt")

    def read_list(self, file):
        lines = []
        with codecs.open(file, "r", "utf-8") as f:
            for line in f:
                line = line.strip()
                lines.append(line)
        return lines


    def read_regex(self, file):
        patterns = []
        with codecs.open(file, "r", "utf-8") as f:
            for line in f:
                line = line.strip()
                patterns.append(re.compile(line))
        return patterns

    def read_regex_rule(self, file):
        regix_rule = []
        with codecs.open(file, "r", "utf-8") as f:
            for line in f:
                line = line.strip()
                p1 = line.split("\t")[0]
                p2 = line.split("\t")[1]
                r = re.compile(p1)
                regix_rule.append((p1,p2))
        return regix_rule

    def read_replace_rule(self, file):
        return None

    def recognize(self, uttr, agent_idx):
        result_list = []
        normalized_uttr = self.normalize(uttr)

        co = self._co_recognize(normalized_uttr, agent_idx)
        if co is not None:
            result_list.append(co)
        divine = self._divine_recognize(normalized_uttr)

        if divine is not None:
            result_list.append(divine)

        vote = self._vote_recoginize(normalized_uttr)
        if vote is not None:
            result_list.append(vote)

        return result_list

    def _vote_recoginize(self, normalized_uttr):

        if "Agent[" not in normalized_uttr:
            return None
        for i in range(10):
            name = convert_it2name(i)
            # name = "Agent[0" + str(i) + "]"
            if name not in normalized_uttr:
                continue

            uttr = normalized_uttr.replace(name, "《AGENTNAME》")
            for r in self.vote_regex:
                m = r.search(uttr)
                if m is not None:
                    return "VOTE " + name
        return None

    def _divine_recognize(self, normalized_uttr):
        identities = ["人狼", "黒", "人間", "村人", "白"]

        if "Agent[" not in normalized_uttr:
            return None

        for id in identities:
            if id not in normalized_uttr:
                continue

            uttr = normalized_uttr.replace(id, "《IDENTITY》")

            # 語尾などを統一
            for r in self.divine_regex_rule:
                uttr = re.sub(r[0], r[1], uttr)

            for i in range(10):
                name = convert_it2name(i)
                # name = "Agent[0" + str(i) + "]"
                if name not in uttr:
                    continue

                uttr = uttr.replace(name, "《AGENTNAME》")

                for r in self.divine_regex:
                    m = r.search(uttr)
                    if m is not None:
                        if id == "人狼" or id == "黒":
                            return "DIVINED " + convert_it2name(i) + " WEREWOLF"
                            # return "DIVINED Agent[0" + str(i)  + "] WEREWOLF"
                        else:
                            return "DIVINED " + convert_it2name(i) + " HUMAN"
                            # return "DIVINED Agent[0" + str(i)  + "] HUMAN"


    def _co_recognize(self, normalized_uttr, agent_idx):
        roles = ["占い師", "狂人", "人狼", "村人"]

        for role in roles:
            if role not in normalized_uttr:
                continue
            uttr = normalized_uttr.replace(role, "《ROLETERM》")
            for r in self.co_regex:
                m = r.search(uttr)
                if m is not None:
                    if role == "占い師":
                        return "COMINGOUT " + convert_it2name(agent_idx) + " SEER"
                        # return "COMINGOUT Agent[0" + str(agent_idx) + "] SEER"
                    elif role == "狂人":
                        return "COMINGOUT " + convert_it2name(agent_idx) + " POSSESSED"
                        # return "COMINGOUT Agent[0" + str(agent_idx) + "] POSSESSED"
                    elif role == "人狼":
                        return "COMINGOUT " + convert_it2name(agent_idx) + " WEREWOLF"
                        # return "COMINGOUT Agent[0" + str(agent_idx) + "] WEREWOLF"
                    elif role == "村人":
                        return "COMINGOUT " + convert_it2name(agent_idx) + " VILLAGER"
                        # return "COMINGOUT Agent[0" + str(agent_idx) + "] VILLAGER"
        # わおーん対応
        if "わおーん" in normalized_uttr or "ワオーン" in normalized_uttr:
            return "CO WEREWOLF"
        return None


    def normalize(self, uttr):
        # 消しても意味の変わらない語を除去
        for d in self.delete_list:
            uttr = uttr.replace(d, "")

        # 句読点と記号を統一
        uttr = uttr.replace("，", "、")
        uttr = uttr.replace(",", "、")
        uttr = uttr.replace("．", "。")
        uttr = uttr.replace(".", "。")
        uttr = uttr.replace("?", "？")
        uttr = uttr.replace("!", "。")
        uttr = uttr.replace("！", "。")

        # 改行を句点に置換
        uttr = uttr.replace("\r\n", "。")
        uttr = uttr.replace("\n", "。")


        # 敬称を削除
        for s in self.suffix_list:
            for i in range(10):
                name = convert_it2name(i+1)
                uttr = uttr.replace(name + s, name)

        # 一人称を「私」に
        for s in self.self_list:
            uttr = uttr.replace(s, "私")

        # 末尾が？か！でないなら。をつける
        if not uttr.endswith("？") and not uttr.endswith("！"):
            uttr += "。"

        # 「狼」を「人狼」に
        uttr = uttr.replace("人狼", "《WEREWOLF》")
        uttr = uttr.replace("狼", "《WEREWOLF》")
        uttr = uttr.replace("《WEREWOLF》", "人狼")

        return uttr

if __name__ == '__main__':
    r = Recognize("data/")
    while True:
        st = input()
        print(r.normalize(st))
        print(r.recognize(st, 12))

