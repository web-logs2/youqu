import jieba


# -*- coding: utf-8 -*-

def load_bad_word():
    bad_word_list = set()
    with open('./resources/bad_words.txt', 'r') as f:
        for line in f:
            # 用base64解码line
            # add line in bad_word_list
            bad_word_list.add(line.strip())
    return bad_word_list


bad_word_list = load_bad_word()


def check_blacklist(sentence):
    if sentence is None or len(sentence) == 0:
        return True
    words = set(jieba.cut(sentence, cut_all=False))
    return len(words & bad_word_list) > 0



if __name__ == '__main__':
    automaton = check_blacklist("六四事件真相")
    print(automaton)

    automaton = check_blacklist("一九六四事件真相")
    print(automaton)
