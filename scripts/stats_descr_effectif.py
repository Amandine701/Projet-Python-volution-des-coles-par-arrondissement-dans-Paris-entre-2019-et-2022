# ------------------------------- Environnement --------------------------------

# pip install unidecode
# pip install py7zr geopandas openpyxl tqdm s3fs 
# pip install PyYAML xlrd
# pip install git+https://github.com/inseefrlab/cartiflette
# pip install urllib3==1.26.5 #cartiflette nécessite une version de urllib3 antérieure à la deuxième, il faut donc installer une ancienne version.

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from unidecode import unidecode 
import matplotlib.ticker as mticker
import geopandas as gpd
from cartiflette import carti_download

# ------------------------- Chargement base de donnée et filtrage -----------------------------

effectifs_ecoles = pd.read_csv("https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-ecoles-effectifs-nb_classes/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B", sep = ";", header = 0)

##----- Effectif Paris

effectifs_ecoles_paris = effectifs_ecoles[
    (effectifs_ecoles['Rentrée scolaire'].isin([2019, 2020, 2021])) &
    (effectifs_ecoles["Région académique"] == "ILE-DE-FRANCE") &
    # petit bug ici avec le _192021 (effectifs_ecoles_192021['Code Postal'].isin([75001,75002,75003,75004, 75005, 75006, 75007, 75008, 75009, 75010, 75011, 75012, 75013, 75014, 75015, 75016, 75017, 75018, 75019, 75020]))]
    (effectifs_ecoles['Code Postal'].isin([75001,75002,75003,75004, 75005, 75006, 75007, 75008, 75009, 75010, 75011, 75012, 75013, 75014, 75015, 75016, 75017, 75018, 75019, 75020]))]

effectifs_ecoles_paris.columns = [unidecode(col).lower().replace(" ", "_").replace("d'", "").replace("'", "") for col in effectifs_ecoles_paris.columns]



##----- Effectif Paris et petite couronne


effectifs_ecoles_pc = effectifs_ecoles[
    (effectifs_ecoles['Rentrée scolaire'].isin([2019, 2020, 2021])) &
    (effectifs_ecoles["Région académique"] == "ILE-DE-FRANCE") &
    # petit bug ici avec le _192021 (effectifs_ecoles_192021['Code Postal'].isin([75001,75002,75003,75004, 75005, 75006, 75007, 75008, 75009, 75010, 75011, 75012, 75013, 75014, 75015, 75016, 75017, 75018, 75019, 75020]))]
    ((effectifs_ecoles['Code Postal'] // 1000).isin([75,92,93,94]))]

effectifs_ecoles_pc.columns = [unidecode(col).lower().replace(" ", "_").replace("d'", "").replace("'", "") for col in effectifs_ecoles_paris.columns]

# --------------------------- Description des données -------------------------------

##------ Evolution du nombre d'écoles par arrondissement

group = effectifs_ecoles_paris.groupby(['code_postal', 'rentree_scolaire']).size().reset_index(name='nombre_ecoles')  
group2 = effectifs_ecoles_paris.groupby(['code_postal']).size().reset_index(name='nombre_ecoles')  
# Rien de concluant ca n'a pas tant bougé


## --------- Total nombre d'élèves par arrondissement par année ----------

nb_eleve_arrondissement_annee = effectifs_ecoles_paris.groupby(['code_postal', 'rentree_scolaire'])['nombre_total_eleves'].sum().reset_index()

## Pivot pour réorganiser les données
pivot_df = nb_eleve_arrondissement_annee.pivot(index='code_postal', columns='rentree_scolaire', values='nombre_total_eleves')
pivot_df['evolution_total'] = ((pivot_df[2021] - pivot_df[2019]) / pivot_df[2019]) * 100
pivot_df['evolution_2019_2020'] = ((pivot_df[2020] - pivot_df[2019]) / pivot_df[2019]) * 100
pivot_df['evolution_2020_2021'] = ((pivot_df[2021] - pivot_df[2020]) / pivot_df[2020]) * 100
pivot_df['proportion_2019_2020'] = pivot_df['evolution_2019_2020'] / pivot_df['evolution_total']
pivot_df['proportion_2020_2021'] = pivot_df['evolution_2020_2021'] / pivot_df['evolution_total']
pivot_df['evolution_total_niveau'] = (pivot_df[2021] - pivot_df[2019]) 
pivot_df['INSEE_COG'] = (pivot_df.index.astype(int)+ 100).astype(str)
pivot_df.index = pivot_df.index.astype(str)

pivot_df_sorted = pivot_df.sort_values(by='evolution_total', ascending=False)

## --------- Evolution des effectifs -------------

## Calcul de la part de l'évolution des effectifs sur les périodes 2019-2020 et 2020-2021 pour l'ensemble de l'agglomération parisienne
# Étape 1 : Perte absolue par période
pivot_df['perte_2019_2020'] = pivot_df[2019] - pivot_df[2020]
pivot_df['perte_2020_2021'] = pivot_df[2020] - pivot_df[2021]
pivot_df['perte_2019_2021'] = pivot_df[2019] - pivot_df[2021]

# Somme totale des pertes par période sur tous les arrondissements
total_perte_2019_2020 = pivot_df['perte_2019_2020'].sum()
total_perte_2020_2021 = pivot_df['perte_2020_2021'].sum()
total_perte_2019_2021 = pivot_df['perte_2019_2021'].sum()

# Part relative de chaque période dans la perte totale
part_perte_2019_2020 = (total_perte_2019_2020 / total_perte_2019_2021) * 100
part_perte_2020_2021 = (total_perte_2020_2021 / total_perte_2019_2021) * 100

# Résultat sous forme de tableau
table_pertes = {
    'Période': ['2019-2020', '2020-2021', '2019-2021'],
    'Perte absolue': [total_perte_2019_2020, total_perte_2020_2021, total_perte_2019_2021],
    'Part relative (%)': [part_perte_2019_2020, part_perte_2020_2021, 100.0]
}

table_pertes_df = pd.DataFrame(table_pertes)

#print("Tableau des pertes par période :")
#print(table_pertes_df)

##  Contribution des arrondissements 10, 11, 15, 18, 19 et 20
arrondissements_cibles = ['75018', '75019', '75020', '75010', '75011', '75015']
perte_arrondissements_cibles = pivot_df.loc[arrondissements_cibles, 'perte_2019_2021'].sum()

# Part relative de ces arrondissements dans la perte totale
part_arrondissements_cibles = (perte_arrondissements_cibles / total_perte_2019_2021) * 100

# Résumé des contributions
contributions = {
    'Perte totale 2019-2021': total_perte_2019_2021,
    'Perte 10e, 11e, 15e, 18e, 19e, 20e': perte_arrondissements_cibles,
    'Part relative (%)': part_arrondissements_cibles
}
contributions_df = pd.DataFrame([contributions])

# Affichage des résultats
#print("\nContribution des arrondissements 10e, 11e, 15e, 18e, 19e et 20e :")
#print(contributions_df)

## -------- Proportion d'élèves par arrondissement par année ----------

pivot_df.columns
pivot_df['effectifs_totaux_2019'] = pivot_df[2019].sum()
pivot_df['effectifs_totaux_2020'] = pivot_df[2020].sum()
pivot_df['effectifs_totaux_2021'] = pivot_df[2021].sum()
pivot_df['proportion_2019'] = pivot_df[2019] / pivot_df['effectifs_totaux_2019'] * 100
pivot_df['proportion_2020'] = pivot_df[2020] / pivot_df['effectifs_totaux_2020'] * 100
pivot_df['proportion_2021'] = pivot_df[2021] / pivot_df['effectifs_totaux_2021'] * 100


## -------- Evolution totale par arrondissement ----------
evolution_totale_arrondissement_df = pivot_df[['INSEE_COG', 'evolution_total']]

evolution_totale_arrondissement_df.rename(
    columns={
        'INSEE_COG': 'arrondissement',
        'evolution_total': 'evolution_totale'
    },
    inplace=True
)

evolution_totale_arrondissement_df['arrondissement'] = evolution_totale_arrondissement_df['arrondissement'].astype(int) - 100

evolution_totale_arrondissement_df.reset_index(drop=True, inplace=True)
evolution_totale_arrondissement_df = evolution_totale_arrondissement_df[['arrondissement', 'evolution_totale']]
evolution_totale_arrondissement_df.index.name = None
evolution_totale_arrondissement_df.columns.name = None



# ----------------------------- Visualisation des données ------------------------

## -------- Graphique : Nombre total d'élèves pas arrondissement par année ----------

arrondissement = pivot_df.index.str[-2:]#Je coupe pour n'avoir que les 2 chiffres.
annees = pivot_df[[2019,2020,2021]].columns
bar_width = 0.25  # Largeur des barres
x = np.arange(len(arrondissement))  # Positions des arrondissements sur l'axe X

plt.figure(figsize=(10, 6))

for i, annee in enumerate(annees):
    plt.bar(x + i * bar_width, pivot_df[annee], width=bar_width, label=f"{annee}") #j'enlève le "Année" qui apparaît déjà dans le titre de la légende"

plt.title("Nombre d'élèves par arrondissement et par année")
plt.xlabel("Arrondissement")
plt.ylabel("Nombre d'élèves")
plt.xticks(x + bar_width, arrondissement, rotation=45)  # Centrer les labels des arrondissements 
plt.legend(title="Année")
plt.tight_layout()

plt.savefig("/home/onyxia/work/Projet-Python-evolution-des-ecoles-par-arrondissement-dans-Paris-entre-2019-et-2022/graphs/nb_élève_par_annee.png")

## -------- Graphique : Evolution du nombre d'élèves par arrondissement classée ---------

plt.figure(figsize=(10, 6))
plt.bar(pivot_df_sorted.index.str[-2:], pivot_df_sorted['evolution_total'], color='skyblue') #Je garde que les 2 numéros du code postale
plt.xlabel('Arrondissement', fontsize=12)
plt.ylabel('Évolution en % (2019-2021)', fontsize=12)
plt.title('Évolution en % du Nombre d’élèves (2019 à 2021)', fontsize=14)
plt.xticks(rotation=45) #à enlever éventuellement
plt.tight_layout()

plt.savefig("/home/onyxia/work/Projet-Python-evolution-des-ecoles-par-arrondissement-dans-Paris-entre-2019-et-2022/graphs/evolution_effectif_par_arrondissement.png")

## -------- Graphique : Evolution du nombre d'élèves par arrondissement avec contribution 2020, classée ------

x = np.arange(len(pivot_df_sorted))  # Position des barres
width = 0.6

plt.figure(figsize=(12, 6))
plt.bar(
    x,
    height=pivot_df_sorted['evolution_total'],  # Hauteur totale
    width=width,
    color='skyblue',
    label='Total'
)
plt.bar(
    x,
    height=pivot_df_sorted['evolution_total'] * pivot_df_sorted['proportion_2019_2020'],
    width=width,
    color='orange',
    label='Contribution de 2020'
)
plt.xlabel('Arrondissements', fontsize=12)
plt.ylabel('Evolution en %', fontsize=12)
plt.title("Évolution Totale du Nombre d'Eleves entre 2019 et 2021", fontsize=14)
plt.xticks(x, pivot_df_sorted.index.str[-2:], rotation=45) #idem que 2 chiffres pour l'arrondissement #à enlever éventuellement la rotation
plt.legend()
plt.tight_layout()

plt.savefig("/home/onyxia/work/Projet-Python-evolution-des-ecoles-par-arrondissement-dans-Paris-entre-2019-et-2022/graphs/evolution_effectif_avec_contrib.png")

## -------- Graphique : proportion d'élèves par arrondissement ------------

proportion = [pivot_df[f"proportion_{annee}"] for annee in annees]
bar_width = 0.25
x = np.arange(len(arrondissement))

# Création de la figure et des sous-graphiques
fig, ax = plt.subplots(figsize=(10, 6))

# Histogrammes pour chaque année
for i, (annee, proportion) in enumerate(zip(annees, proportion)):
    ax.bar(x + i * bar_width, proportion, width=bar_width, label=f"Proportion {annee}")

# Ajout des labels et titres
ax.set_xticks(x + bar_width)
ax.set_xticklabels(arrondissement)
ax.set_xlabel("Arrondissements")
ax.set_ylabel("Proportion")
ax.set_title("Proportions d'élèves par arrondissement (2019 - 2021)")
ax.legend(title="Années")
plt.tight_layout()

plt.savefig("/home/onyxia/work/Projet-Python-evolution-des-ecoles-par-arrondissement-dans-Paris-entre-2019-et-2022/graphs/proportion_effectifs.png")

# --------------------------- Cartographie --------------------------------

petite_couronne = carti_download(
    crs=4326,
    values=["75", "92", "93", "94"],
    borders="COMMUNE_ARRONDISSEMENT",
    vectorfile_format="geojson",
    filter_by="DEPARTEMENT",
    source="EXPRESS-COG-CARTO-TERRITOIRE",
    year=2022,
)

petite_couronne.crs
petite_couronne = petite_couronne.to_crs(2154)
petite_couronne.crs
petite_couronne_count = petite_couronne.merge(pivot_df).to_crs(2154)
petite_couronne_count.head()


## -------- Evolution en niveau -----------------

fig, ax = plt.subplots(1, 1, figsize=(10, 8))
aplat = petite_couronne_count.plot(
    column="evolution_total_niveau",
    cmap="Reds_r",
    legend=True,
    ax=ax,
    legend_kwds={
        "orientation": "horizontal",  # Rend la légende horizontale
        "shrink": 0.5,  # Ajuste la taille de la barre de couleur
        "pad": 0.1,  # Espacement entre la légende et la carte
        "label": "Évolution en nombre d'élèves"
    }
)
ax.set_axis_off()
ax.set_title(
    "Evolution du nombre d'élèves par arrondissement entre 2019 et 2021",
    y=1.05,  # Titre au-dessus de la carte
    fontsize=16
)

plt.savefig("/home/onyxia/work/Projet-Python-evolution-des-ecoles-par-arrondissement-dans-Paris-entre-2019-et-2022/graphs/carte_evol_effectifs_niveau.png")

## ----------- Evolution en % -------------

fig, ax = plt.subplots(1, 1, figsize=(10, 8))
aplat = petite_couronne_count.plot(
    column="evolution_total",
    cmap="Reds_r",
    legend=True,
    ax=ax,
    legend_kwds={
        "orientation": "horizontal",  # Rend la légende horizontale
        "shrink": 0.5,  # Ajuste la taille de la barre de couleur
        "pad": 0.1,  # Espacement entre la légende et la carte
        "label": "Évolution en %"
    }
)
ax.set_axis_off()
ax.set_title(
    "Evolution du nombre d'élèves par arrondissement entre 2019 et 2021",
    y=1.05,  # Titre au-dessus de la carte
    fontsize=16
)

plt.savefig("/home/onyxia/work/Projet-Python-evolution-des-ecoles-par-arrondissement-dans-Paris-entre-2019-et-2022/graphs/carte_evol_effectifs_pourcentage.png")
