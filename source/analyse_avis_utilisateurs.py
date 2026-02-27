import os
import joblib
import pandas as pd
import string
import streamlit as st
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

_BASE_DIR = os.path.join(os.path.dirname(__file__), '..')


@st.cache_resource
def _download_nltk_data():
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('wordnet', quiet=True)


@st.cache_resource
def _load_sentiment_models():
    log_reg = joblib.load(os.path.join(_BASE_DIR, 'models', 'logistic_regression_model.pkl'))
    tfidf_vectorizer = joblib.load(os.path.join(_BASE_DIR, 'models', 'tfidf_vectorizer.pkl'))
    return log_reg, tfidf_vectorizer


# Initialiser le lemmatizer
lemmatizer = WordNetLemmatizer()

# Fonction de nettoyage du texte
def clean_text(text):
    # Conversion en minuscules
    text = text.lower()

    # Suppression de la ponctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Suppression des chiffres
    text = ''.join([i for i in text if not i.isdigit()])

    # Tokenisation
    tokens = word_tokenize(text)

    # Suppression des stop words
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]

    # Lemmatisation
    tokens = [lemmatizer.lemmatize(word) for word in tokens]

    # Rejoindre les tokens nettoyés en une chaîne de caractères
    cleaned_text = ' '.join(tokens)

    return cleaned_text

# Fonction de prédiction
def predict_user_reviews(uploaded_file):
    _download_nltk_data()
    log_reg, tfidf_vectorizer = _load_sentiment_models()

    if uploaded_file is not None:
        try:
            # Lecture du fichier CSV
            data = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
            return None, None, None

        # Vérifier que la colonne 'user_review' existe
        if 'user_review' in data.columns:
            try:
                # Nettoyer les critiques utilisateur
                data['cleaned_user_review'] = data['user_review'].apply(clean_text)

                # Vectoriser les critiques utilisateur nettoyées
                X = tfidf_vectorizer.transform(data['cleaned_user_review'])

                # Faire des prédictions
                predictions = log_reg.predict(X)
                # Ajouter les prédictions au DataFrame
                data['predictions'] = predictions

                # Calculer les pourcentages de prédictions positives et négatives
                positive_percentage = (predictions == 1).mean() * 100
                negative_percentage = (predictions == 0).mean() * 100

                return data, positive_percentage, negative_percentage
            except Exception as e:
                st.error(f"Erreur lors de l'analyse des avis : {e}")
                return None, None, None
        else:
            st.warning("Le fichier CSV doit contenir une colonne 'user_review'.")
            return None, None, None
    return None, None, None
