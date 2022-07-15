import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
    StopWordRemoverFactory
)

from two import nama_prodi

COLUMNS = ['minat', 'bakat', 'mapel', 'nilai', 'ibu', 'ayah', 'penghasilan']
COL_TO_LABEL = ["ibu", "ayah", "penghasilan"]
COL_TO_VECTOR = ["minat", "bakat", "mapel"]
COL_TEXT = ['minat', 'bakat', 'mapel', 'ibu', 'ayah', 'penghasilan']

loaded_model = pickle.load(open('model.pkl', 'rb'))
train_data = pickle.load(open('train_data.pkl', 'rb'))

factory = StopWordRemoverFactory()
stop_words = factory.create_stop_word_remover()


def hitung_nilai_rata2(request_form):
    daftar_mapel = request_form.getlist('map')
    jumlah_nilai = 0.0
    for mapel in daftar_mapel:
        nilai = float(request_form.get(f'n{mapel}', 0))
        jumlah_nilai += nilai
    return jumlah_nilai / len(daftar_mapel)


def process_input(data):
    print(f'data: {data}')
    df = pd.DataFrame.from_dict(data)

    for col in COL_TEXT:
        df[col] = df[col].apply(lambda text: stop_words.remove(text))

    label_encoder = LabelEncoder()
    for col in COL_TO_LABEL:
        label_encoder.fit(train_data[col])
        df[col] = label_encoder.transform(df[col])

    vectorizer = TfidfVectorizer()
    for col in COL_TO_VECTOR:
        vectorizer.fit(train_data[col])
        df[col] = vectorizer.transform(df[col]).toarray()

    # prediksi = loaded_model.predict(df)
    proba = loaded_model.predict_proba(df)
    # print(f'probability: {proba}')

    # ambil 3 teratas
    predictions = loaded_model.classes_[np.argsort(proba)[:, :-3 - 1:-1]]
    rekomendasi = np.take(nama_prodi, predictions[0], 0)['prodi']
    # print(f'rekomendasi; {rekomendasi.to_dict()}')

    # Daftar nama prodi sesuai data training
    hasil = rekomendasi
    # print(f'hasil: {hasil}')
    return hasil
