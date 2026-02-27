import os
import streamlit as st
import pandas as pd
import lightgbm as lgb
import joblib
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

_BASE_DIR = os.path.join(os.path.dirname(__file__), '..')


@st.cache_data
def load_data():
    df_top = pd.read_csv(os.path.join(_BASE_DIR, 'data', 'df_topfeats.csv'))
    df_features = pd.read_csv(os.path.join(_BASE_DIR, 'data', 'df_features.csv'))
    return df_top, df_features


@st.cache_resource
def load_model():
    model_path = os.path.join(_BASE_DIR, 'reports', 'model_final.txt')
    return lgb.Booster(model_file=model_path)


@st.cache_resource
def load_numerical_transformer():
    return joblib.load(os.path.join(_BASE_DIR, 'models', 'numerical_transformer.joblib'))



def get_input(df_features):
    st.sidebar.header('Sélection des entrées')

    input_data = {}
    publisher_input = st.sidebar.selectbox('Sélectionnez l\'éditeur', df_features['Publisher'].unique())
    genre_input = st.sidebar.selectbox('Sélectionnez le genre', df_features['Genre'].unique())
    platform_input = st.sidebar.selectbox('Sélectionnez la plateforme', df_features['Platform'].unique())
    years = list(range(1980, 2031))
    year_input = st.sidebar.selectbox('Sélectionnez l\'année', years, index=years.index(2024))
    input_data['Year'] = year_input

    meta_input = st.sidebar.number_input(
        'Sélectionnez le score Metacritic',
        min_value=0.0,
        max_value=100.0,
        value=float(df_features["meta_score"].mean()),
        format="%.0f"
    )
    input_data['meta_score'] = meta_input

    user_input = st.sidebar.number_input(
        'Sélectionnez le score utilisateur',
        min_value=0.0,
        max_value=100.0,
        value=float(df_features["user_review"].mean()),
        format="%.1f"
    )
    input_data['user_review'] = user_input

    return publisher_input, genre_input, platform_input, input_data

def get_features(input_data, df_features, genre_input, platform_input):
    input_data['Global_Sales_mean_genre'] = df_features[df_features['Genre'] == genre_input]['Global_Sales_mean_genre'].mean()
    input_data['Global_Sales_mean_platform'] = df_features.loc[df_features['Platform'] == platform_input]['Global_Sales_mean_platform'].mean()
    input_data['Year_Global_Sales_mean_genre'] = input_data['Year'] * input_data['Global_Sales_mean_genre']
    input_data['Year_Global_Sales_mean_platform'] = input_data['Year'] * input_data['Global_Sales_mean_platform']

    df_input_data = pd.DataFrame(input_data, index=[0])

    cumulative_sales_genre = df_features[
        (df_features['Genre'] == genre_input) & 
        (df_features['Year'] <= input_data['Year'])
    ].sort_values('Year')['Global_Sales'].cumsum().iloc[-1]
    
    df_input_data["Cumulative_Sales_Genre"] = cumulative_sales_genre

    cumulative_sales_platform = df_features[
        (df_features['Platform'] == platform_input) & 
        (df_features['Year'] <= input_data['Year'])
    ].sort_values('Year')['Global_Sales'].cumsum().iloc[-1]
    
    df_input_data["Cumulative_Sales_Platform"] = cumulative_sales_platform

    return df_input_data

def standardization(df_input_data, publisher_input, df_top):
    numerical_features = [
        'Year', 'meta_score', 'user_review',
        'Global_Sales_mean_genre', 'Global_Sales_mean_platform', 'Year_Global_Sales_mean_genre',
        'Year_Global_Sales_mean_platform',
        'Cumulative_Sales_Genre', 'Cumulative_Sales_Platform'
    ]

    numerical_transformer = load_numerical_transformer()
    df_input_data[numerical_features] = numerical_transformer.transform(df_input_data[numerical_features])

    publisher_cols = ['Publisher_' + str(pub) for pub in df_top['Publisher'].unique()]
    for col in publisher_cols:
        df_input_data[col] = 0
    df_input_data['Publisher_' + publisher_input] = 1

    df_input_data = df_input_data.drop(['Publisher_10TACLE Studios'], axis=1)

    return numerical_features, df_input_data

def prediction_page():
    st.title("Prédiction des ventes de jeux vidéo")

    df_top, df_features = load_data()
    model = load_model()

    # CSS pour positionner l'écran de la borne d'arcade
    st.markdown(
        """
        <style>
        .arcade-container {
            position: relative;
            text-align: center;
            color: white;
            max-width: 700px;
            margin: 0 auto;
        }
        .arcade-image {
            width: 100%;
            height: auto;
        }
        .arcade-screen {
            font-family: 'Press Start 2P', cursive;
            color: #ec8853;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-size : 22px;
            position: absolute;
            top: -300px; /* Ajustez cette valeur pour positionner le texte correctement */
            left: 52%;
            transform: translate(-50%, -50%);
            width: 65%; /* Ajustez cette valeur selon vos besoins */
            height: 200px; /* Ajustez cette valeur selon vos besoins */
            display: flex;
            align-items: center;
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Afficher l'image de la borne d'arcade
    image_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'street_arcade.jpg')

    if os.path.exists(image_path):
        st.image(image_path, width=1000)
    else:
        st.write(f"Erreur : l'image {os.path.basename(image_path)} est introuvable. Vérifiez le dossier images/.")

    # Obtenir les entrées utilisateur
    publisher_input, genre_input, platform_input, input_data = get_input(df_features)

    if st.sidebar.button('Prédire'):
        # Obtenir les caractéristiques
        df_input_data = get_features(input_data, df_features, genre_input, platform_input)

        # Standardiser les données
        numerical_features, df_input_data_transformed = standardization(df_input_data, publisher_input, df_top)

        # Prédire en fonction des entrées utilisateur
        user_pred = model.predict(df_input_data_transformed)

        # Superposer la prédiction sur l'image de la borne d'arcade
        st.markdown(
        f"""
        <div class="arcade-container">
            <div class="arcade-screen">Prédiction pour les ventes:<br><br> {user_pred[0]:.4f} millions d'unités</div>
        </div>
        """, 
        unsafe_allow_html=True
        )
    else:
        st.markdown(
        f"""
        <div class="arcade-container">
            <div class="arcade-screen">Entrez les informations nécessaires pour prédire les ventes globales d'un jeu vidéo</div>
        </div>
        """, 
        unsafe_allow_html=True
        )
       # st.header("Entrez les informations nécessaires pour prédire les ventes globales d'un jeu vidéo.")
       # Ajouter le disclaimer en bas de la page
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray;'>Ce modèle est en version bêta et peut faire des erreurs. Envisagez de vérifier les informations importantes.</p>", unsafe_allow_html=True)

# Exécuter l'application
if __name__ == "__main__":
    prediction_page()
