import pandas as pd


def remove_punctuations(string: str):
    punctuations = ",'[]"
    new_string = string
    for punctuation in punctuations:
        new_string = new_string.replace(punctuation, "")

    return new_string


def extract_bow(doc):
    words = doc.split(" ")
    bow = {}
    for word in words:
        try:
            bow[word] += 1
        except:
            bow[word] = 1

    return bow


def compute_tf(bow):
    doc_len = sum([bow[key] for key in bow])
    tf = {}

    for key in bow:
        tf[key] = bow[key] / doc_len

    return tf


def compute_tfidf(df, tf):
  tfidf = {}
  for key in tf:
    idf = df[df['Term'] == key]['IDF'].item()
    tfidf[key] = idf * tf[key]

  return tfidf


def evaluate_tfidf(input_string, df):
  string = remove_punctuations(input_string)
  bow = extract_bow(string)
  tf = compute_tf(bow)

  return compute_tfidf(df, tf)


# Just for test purpose
if __name__ == "__main__":
    df = pd.read_csv('../data/tfidf_mapel.csv')
    input_string = "['sejarah', 'geografi']"

    print(evaluate_tfidf(input_string, df))
