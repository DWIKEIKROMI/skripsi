import pickle
import re
import string

from flask import Flask
from flask_mysqldb import MySQL, MySQLdb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.metrics import accuracy_score
# NLTK
import nltk
# Sastrawi
from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
    StopWordRemoverFactory
)
from imblearn.over_sampling import RandomOverSampler

import warnings
warnings.filterwarnings("ignore")
nltk.download("punkt")

df = pd.read_excel("train.xlsx")
df.drop(["no", "nama"], axis=1, inplace=True)
nama_prodi = pd.DataFrame(df['prodi'].copy())
orig_df = df.copy()
text_cols = df.select_dtypes(exclude="int64").columns

# 1. Make all text into lowercase
for col in text_cols:
    df[col] = df[col].apply(lambda text: text.lower())

# 2. Removing numbers (excluding: penghasilan)
for col in text_cols[:-1]:
    df[col] = df[col].apply(lambda text: re.sub(r"\d+", "", text))

# 3. Removing punctuation
for col in text_cols:
    df[col] = df[col].apply(
        lambda text: text.translate(str.maketrans("", "", string.punctuation))
    )

# 4. Removing all whitespace
for col in text_cols:
    df[col] = df[col].str.strip()

# implement tokenizer
def tokenizer(text):
    text = nltk.tokenize.word_tokenize(text)
    text = str.join(" ", text)
    return text

for col in text_cols:
    df[col] = df[col].apply(tokenizer)

factory = StopWordRemoverFactory()
# stopwords = factory.get_stop_words()
# print(stopwords)
# Removing all the stopwords
stop_words = factory.create_stop_word_remover()
for col in text_cols:
    df[col] = df[col].apply(lambda text: stop_words.remove(text))

# Dump dataframe
pickle.dump(df, open('train_data.pkl', 'wb'))

# LabelEncoder(Prodi,Ibu,Ayah,Penghasilan)

cols = ["prodi", "ibu", "ayah", "penghasilan"]
le = LabelEncoder()

for col in cols:
    le.fit(df[col])
    df[col] = le.transform(df[col])

# TfIdf Vectorizer(Minat,Bakat,Mapel)

cols = ["minat", "bakat", "mapel"]
vectorizer = TfidfVectorizer()
for col in cols:
    vectorizer.fit(df[col])
    df[col] = vectorizer.transform(df[col]).toarray()

# Scaling with MinMaxScaler

cols = ["nilai", "ibu", "ayah", "penghasilan"]
scaler = MinMaxScaler()
scaler.fit(df[cols])
df[cols] = scaler.transform(df[cols])

# Modelling(RandomForest)

# Feature and Target
X = df.drop(["prodi"], axis=1)
y = df["prodi"]
nama_prodi['id_prodi'] = y.copy()

# Oversampling with imblearn

sampler = RandomOverSampler()
X, y = sampler.fit_resample(X, y)

# Train and Accuracy

# split into train set and test set with 30% test size
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)
# fit the model
model = RandomForestClassifier(random_state=42, criterion='entropy')
model.fit(X_train, y_train)

pickle.dump(model, open('model.pkl', 'wb'))

y_pred = model.predict(X_test)
print("Accuracy: {:.2f}".format(accuracy_score(y_test, y_pred)))
# print(f'y_pred: {y_pred}')
#
# print(f'predict: {y_pred[:3]}')
# print(np.take(df, y_pred[:5], 0)['prodi'])

# Solusi ambil 3 rekomendasi
# docs: https://stackoverflow.com/questions/63123025/randomforestclassifier-get-top-n-predictions-and-respective-probabilities


# -----------------------
# Manual Random Forest

# from random_forest import RandomForest, accuracy
#
# clf = RandomForest(n_trees=100)
# clf.fit(X_train, y_train)
#
# y_pred = clf.predict(X_test)
# print("Accuracy: {:.2f}".format(accuracy(y_test, y_pred)))
