# -*- coding: utf-8 -*-


import spacy
import gensim
import logging
import os
from nltk.stem import SnowballStemmer
import codecs

nlp = spacy.load('es')

stemmer = SnowballStemmer('spanish')

prohibited_characters = [u'\xe1', u'\xe9', u'\xed', u'\xf3', u'\xfa', u'\xf1']
punctuation = [u'\xa1', u'\u2013', u'\u2009', u'\xfc', u'\xbf', ',', '?', u'\xc2\xa1', ':', '.', ';', '!', u'\xc2\xbf',
               '"', '\'', '(', ')', u'\u2026', u'\u201c', u'\u201d']
fix_prohibited = ['a', 'e', 'i', 'o', 'u', 'n']

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def get_unicode_sentence(s):
    final_string = ""
    for c in s:
        is_prohibited = False
        for i in range(0, len(prohibited_characters)):
            if c == prohibited_characters[i]:
                final_string += fix_prohibited[i]
                is_prohibited = True
                break
        if not is_prohibited:
            for i in range(0, len(punctuation)):
                if punctuation[i] == c:
                    is_prohibited = True
                    break
        if not is_prohibited:
            final_string += c
    return final_string


class Document:
    sentences = []
    normalizedSentences = []
    path = ""
    numSentences = 0
    scores = []
    porcentaje = 0.5

    def __init__(self, path, porcentaje = 0.5):

        self.porcentaje = porcentaje
        self.path = path

        model = gensim.models.Word2Vec.load("model")

        self.word_vector = model.wv
        text = codecs.open(path, "r", encoding='utf-8').read()

        text = text.split('.')

        for line in text:
            self.scores += [0.0]
            self.numSentences += 1
            self.sentences += [line]
            temporal = Sentence(get_unicode_sentence(line.lower()))
            self.normalizedSentences += [temporal]

        self.numSentences -= 1

        self.get_important_sentences()
        self.get_summary()

    def get_score(self, s1, s2):
        score1 = 0.0

        if len(s1.sujeto) == 0:
            if len(s2.sujeto) == 0:
                score1 = 1.0
        elif len(s2.sujeto) > 0:
            for s in s1.sujeto:
                for ss in s2.sujeto:
                    try:
                        score1 += self.word_vector.similarity(s, ss)
                    except:
                        score1 += 0

            score1 = score1 / float(len(s1.sujeto) * len(s1.sujeto))

        score2 = 0.0

        if len(s1.verbos) == 0:
            if len(s2.verbos) == 0:
                score2 = 1.0
        elif len(s2.verbos) > 0:
            for v in s1.verbos:
                for vv in s2.verbos:
                    try:
                        score2 += self.word_vector.similarity(v, vv)
                    except:
                        score2 += 0

            score2 = score2 / float(len(s1.verbos) * len(s2.verbos))

        score3 = 0.0

        if len(s1.adjetivos) == 0:
            if len(s2.adjetivos) == 0:
                score3 = 1.0
            else:
                score3 = 0
        elif len(s2.adjetivos) > 0:
            for a in s1.adjetivos:
                for aa in s2.adjetivos:
                    try:
                        score3 += self.word_vector.similarity(a, aa)
                    except:
                        score3 += 0
            score3 = score3 / float(len(s1.adjetivos) * len(s2.adjetivos))
        return (score1 + score2 + score3)/3.0

    def get_important_sentences(self):
        for i in range(0, len(self.normalizedSentences)):
            for j in range(i+1, len(self.normalizedSentences)):
                temp = self.get_score(self.normalizedSentences[i], self.normalizedSentences[j])
                self.scores[i] += temp
                self.scores[j] += temp

    def get_summary(self):

        document = codecs.open("summary.txt", "w", encoding='utf-8')

        for i in range(0, len(self.scores)):
            if (self.scores[i] / float(self.numSentences - 1)) > self.porcentaje:
                document.write(self.sentences[i] + '.')


class Sentence(object):
    sujeto = []
    verbos = []
    adjetivos = []

    def __init__(self, s):
        doc = nlp(unicode(s))
        self.sujeto = []
        self.verbos = []
        self.adjetivos = []
        for token in doc:
            if token.pos_ == u'PROPN' or token.pos_ == u'NOUN':
                self.sujeto += [stemmer.stem(token.text)]
            elif token.pos_ == u'ADJ':
                self.adjetivos += [stemmer.stem(token.text)]
            elif token.pos_ == u'VERB':
                self.verbos += [stemmer.stem(token.text)]


class FriendlyDocument(object):

    def __init__(self, dirname):
        self.dirname = dirname

    def __iter__(self):
        for fname in os.listdir(self.dirname):
            for line in open(os.path.join(self.dirname, fname)):
                yield line.split()


# sentences = FriendlyDocument("normalizedDocs")

# model = gensim.models.Word2Vec(sentences, workers=2)

# model.save("model")

d = Document("test.txt", 0.3)

for i in range(0, len(d.scores)):
    print d.scores[i]/float(d.numSentences -1)

