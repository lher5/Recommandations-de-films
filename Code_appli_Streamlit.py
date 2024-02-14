# Import des librairies utiles
import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# Paramètre d'affichage de l'application
st.set_page_config(layout='wide')

# Lien pour afficher les affiches de film
url = 'https://image.tmdb.org/t/p/original'

# Import des bases que l'ont va utiliser
movieFrance_full_drop = pd.read_csv("movieFrance_full_dropV2.csv")
all_merge = pd.read_csv("all_merge.csv")

# Sidebar pour les filtres de sélection
with st.sidebar:
    # Header de la sidebar
    st.header("Indiquez vos préférences ici pour avoir les meilleures recommandations")

    # Création d'un formulaire de préférences
    with st.form("Quels-sont vos préférences ?"):

        # Filtre film préféré
        movie_option = st.selectbox("Choisissez votre film préféré :", 
                                    movieFrance_full_drop["title"], 
                                    index=None,
                                    placeholder="Tapez votre film ici")

        # Filtre acteur préféré
        actor_option = st.selectbox("Choisissez votre acteur/actrice préféré(e) :", 
                                    all_merge["primaryName"].loc[(all_merge["category"] == "actor") | (all_merge["category"] == "actress")].unique(), 
                                    index=None,
                                    placeholder="Tapez votre acteur/actrice favoris ici")

        # Filtre réalisateur préféré
        director_option = st.selectbox("Choisissez votre réalisateur/réalisatrice préféré(e) :", 
                                    all_merge["primaryName"].loc[all_merge["category"] == "director"].unique(), 
                                    index=None,
                                    placeholder="Tapez votre réalisateur/réalisatrice favoris ici")

        # Filtre réalisateur préféré
        prod_option = st.selectbox("Choisissez votre maison de production préférée :", 
                                    all_merge["production_companies_name"].unique(), 
                                    index=None,
                                    placeholder="Tapez votre maison de production favorite ici")

        # Bouton de soumission du formulaire
        submit_button = st.form_submit_button("Je veux mes recommandations")

# En fonction des sélections, filtrer le dataframe
if submit_button:
    mask_maison_prod = all_merge["production_companies_name"] == prod_option
    mask_acteur_producteur = ((all_merge["primaryName"] == actor_option) | (all_merge["primaryName"] == director_option))

    # Dataframe tenant compte des filtres utilisateur
    all_merge_filter = all_merge.loc[(mask_acteur_producteur) | (mask_maison_prod)]

    # Film préféré
    filmPrefere = movie_option

    # Dataframe des films en tenant compte des critères de sélection
    movie_filter = movieFrance_full_drop.loc[movieFrance_full_drop["tconst"].isin(all_merge_filter["tconst"])]

    # Header
    st.markdown(f"<h1 style='text-align: center'>Voici vos recommandations pour le film {movie_option}</h1>", unsafe_allow_html=True)

    # Diviseur
    st.divider()
    
    # Standardiser les valeurs
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    dfStandard = scaler.fit_transform(movieFrance_full_drop.select_dtypes("number"))
    dfStandard = pd.DataFrame(dfStandard, columns=movieFrance_full_drop.select_dtypes("number").columns)

    from scipy.sparse import csr_matrix

    # Garde en mémoire l'index du film préféré
    index = movieFrance_full_drop.loc[movieFrance_full_drop["title"] == filmPrefere].index[0]

    # Création d'une matrice sur le dataframe normalisé
    matrix = csr_matrix(dfStandard)

    # Création du modéle avec les paramètres souhaité
    model = NearestNeighbors(metric="cosine", algorithm="brute")

    # Entraînement du modèle
    model.fit(matrix)

    # Garde en mémoire les distances et indexes des 20 films les plus proches
    distances, indices = model.kneighbors(dfStandard.iloc[index, :].values.reshape(1,-1), n_neighbors=21)

    # Création de listes pour stocker les films et les distances
    movie = []
    distance = []

    # Boucle et aplatissement de la liste distances (évite d'avoir des sous_listes)
    for i in range(0, len(distances.flatten())):

        # Si la distance est différente de 0
        if i != 0:

            # J'ajoute l'index du film dans la liste movieet la distance dans la liste distance
            movie.append(movieFrance_full_drop.index[indices.flatten()[i]])
            distance.append(distances.flatten()[i])    

    # Transformation en Séries pandas
    m=pd.Series(movie,name='movie')
    d=pd.Series(distance,name='distance')

    # Concaténation des séries pour faire un dataframe
    recommend = pd.concat([m,d], axis=1)

    # Trie des valeurs sur les distances par ordre croissant 
    recommend = recommend.sort_values('distance',ascending=True)

    # Filtrer les films recommandés avec les critères de préférences
    recommend_filter = recommend.loc[recommend["movie"].isin(movie_filter.index)]

    # Structure du corps de la page
    row1, row2, row3, row4, row5, row6 = st.columns(3), st.columns(3), st.columns(3), st.columns(3), st.columns(3), st.columns(3)

    if recommend_filter.shape[0] > 5:
        for i, col in zip(range(0,recommend_filter.shape[0]), row1 + row2 + row3 + row4 + row5 + row6):
            with col.container():
                col1, col2 = st.columns(2)
                col1.image(url + movieFrance_full_drop[movieFrance_full_drop.index == recommend_filter["movie"].iloc[i]]['poster_path'].values[0], use_column_width="auto")
            with col2:
                st.header(movieFrance_full_drop[movieFrance_full_drop.index == recommend_filter["movie"].iloc[i]]["title"].values[0])
                st.write("Date : " , movieFrance_full_drop[movieFrance_full_drop.index == recommend_filter["movie"].iloc[i]]["startYear"].values[0])
                st.write("Runtime : ", movieFrance_full_drop[movieFrance_full_drop.index == recommend_filter["movie"].iloc[i]]["runtimeMinutes"].values[0], "min")
    else:
        with st.sidebar:
            st.header(":red[🚨 Vos critères ne sont pas tous en adéquation ou le système n'a pas suffisamment de films à vous proposer avec vos critères. Le système s'est basé uniquement sur votre film préfré 🚨]")

        # Boucle pour afficher chaque film à recommander non filtré
        for i, col in zip(range(0,recommend.shape[0]), row1 + row2 + row3 + row4 + row5 + row6):
            with col.container():
                col1, col2 = st.columns(2)
                col1.image(url + movieFrance_full_drop[movieFrance_full_drop.index == recommend["movie"].iloc[i]]['poster_path'].values[0], use_column_width="auto")
            with col2:
                st.header(movieFrance_full_drop[movieFrance_full_drop.index == recommend["movie"].iloc[i]]["title"].values[0])
                st.write("Date : " , str(movieFrance_full_drop[movieFrance_full_drop.index == recommend["movie"].iloc[i]]["startYear"].values[0]))
                st.write("Durée : ", str(movieFrance_full_drop[movieFrance_full_drop.index == recommend["movie"].iloc[i]]["runtimeMinutes"].values[0]), "min")
                st.write("Note IMDb : ", str(movieFrance_full_drop[movieFrance_full_drop.index == recommend["movie"].iloc[i]]["averageRating"].values[0]))
else:
    # Header de l'app
    st.markdown(f"<h1 style='text-align: center'>La liste de tous les films</h1>", unsafe_allow_html=True)

    # Diviseur
    st.divider()

    # Structure du corps de la page
    row1, row2, row3, row4, row5, row6 = st.columns(3), st.columns(3), st.columns(3), st.columns(3), st.columns(3), st.columns(3)
    for i, col in zip(range(len(movieFrance_full_drop)), row1 + row2 + row3 + row4 + row5 + row6):
        with col.container():
            col1, col2 = st.columns(2)
            col1.image(url + movieFrance_full_drop.iloc[i]['poster_path'], use_column_width="auto")
        with col2:
            st.header(movieFrance_full_drop.iloc[i]['title'])
            st.write("Realease Date : " + str(movieFrance_full_drop.iloc[i]['startYear']))
            st.write("Runtime : " + str(movieFrance_full_drop.iloc[i]['runtimeMinutes']) + " min")
            st.write("Note IMDb : " + str(movieFrance_full_drop.iloc[i]['averageRating']))