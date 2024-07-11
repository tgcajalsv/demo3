"""Versión 2"""

import streamlit as st
import streamlit.components.v1 as components
import folium
#from streamlit_folium import st_folium
import numpy as np
import pandas as pd 
import geopandas as gpd
import funciones as f
import random
from shapely.geometry import Point, Polygon

st.set_page_config(page_title="Demo", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

#--------------------------------------------------------------------------------------
df1 = pd.read_excel("cuadrantes.xlsx")
df1["Cuadrante"] = df1["Id_Cuadrante"]
df2 = pd.read_excel("medios.xlsx")
df2["name"] = df2["Id_Medio"].astype(str)+'-'+df2["Medio"]
df3 = pd.read_excel("conjuntos2.xlsx")

capa = gpd.read_file("poniente.geojson")
capa["Id_Cuadrante"] = [x[-1] for x in capa["CUADRANTE_"]]
capa["Id_Cuadrante"] = capa["Id_Cuadrante"].astype(int)
#--------------------------------------------------------------------------------------
def label_diferencia(cuadrante, df, gdf):

    cuad_name = "SSC-12.0"+str(cuadrante)

    # Definir polígono
    poligono = gdf[gdf["CUADRANTE_"]==cuad_name]["geometry"].values[0]
    center_lat = poligono.centroid.y.mean()
    center_lon = poligono.centroid.x.mean()

    # Definir diferencia
    diferencia = df[df["Id_Cuadrante"]==cuadrante]["Diferencia"].values[0]

    # Definir color según diferencia
    if diferencia>=0:
        color="green"
    elif diferencia<0:
        color="red"

    # Crear etiqueta
    div_icon = folium.DivIcon(html="""
    <div style="font-family: sans-serif; color: white; background-color:"""+str(color)+"""; padding: 2px 10px; border-radius: 3px; width: 50px; text-align: center;">
        <b>"""+str(round(diferencia,2))+"""</b>
    </div>
    """)

    # Crear objeto marker
    label = folium.Marker(
        location=[center_lat, center_lon],
        icon=div_icon
    ) 

    return label  
#--------------------------------------------------------------------------------------

st.title("Seleccionar turno y medios disponibles")

options = list(df2["name"].unique())

selected = st.selectbox("Escoger medios disponibles:",options)
turno = st.selectbox("Seleccionar turno:",[1,2,3,4])

#--------------------------------------------------------------------------------------
if st.button("Calcular") ==True:

    col = "Asignacion_Cuadrante_T"+str(turno)

    df3 = df3[df3["Turno"]==turno]
    t = df2[df2[col]!=0]

    info = []
    id_conjunto = []
    tipos = []

    disponibles = list(df3["Id_Conjunto"].unique())

    for item in disponibles:

        df = df3[df3["Id_Conjunto"]==item]
        tipo = df3[df3["Id_Conjunto"]==item]["Medio"].values[0]
        personal_data = "|".join(f"Id_agente: {row['Id_agente']}, " 
                                f"Cargo: {row['Rango']} ({row['Tipo']}) " for idx, row in df.iterrows())
        info.append(personal_data)
        id_conjunto.append(item)
        tipos.append(tipo)

    len(info)

    data = pd.DataFrame({"Id_Conjunto":id_conjunto,
                        "Info":info,
                        "Medio":tipos})
    
    data["id_medio"] = data["id"].astype(str)+"-"+data["Medio"]
    
    
    dataframe1 = t
    dataframe2 = data

    # Count the number of each category in dataframe1
    counts = dataframe1['Medio'].value_counts()

    # Initialize an empty list to hold the sampled rows
    sampled_rows_list = []

    # Sample the rows from dataframe2 according to the counts
    for category, count in counts.items():
        sampled_rows = dataframe2[dataframe2['Medio'] == category].sample(n=count, replace=False)
        sampled_rows_list.append(sampled_rows)

    # Concatenate all sampled rows into a single dataframe
    sampled_df = pd.concat(sampled_rows_list).reset_index(drop=True)

    # Add 'id' column from dataframe1 to sampled_df
    if len(sampled_df) == len(dataframe1):
        sampled_df['id'] = dataframe1['Id_Medio'].values

        # Create a combined identifier column
        sampled_df['Identifier'] = sampled_df['id'].astype(str) + '-' + sampled_df['Medio']
    else:
        print("Error: The lengths of the dataframes do not match. Please check the input data.")

    conjuntos_final = dataframe1.merge(sampled_df, left_on="name", right_on="Identifier", how="left")

    # Definir coordenadas centrales
    center_lat = capa.geometry.centroid.y.mean()
    center_lon = capa.geometry.centroid.x.mean()

    # Mapa base
    mapa = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
    )

    # Agregar capa cuadrantes, la constante en todos los mapas a ser renderizados
    for x in range(0,len(capa)):
        f.transform_polygon(capa["geometry"].iloc[x],capa["CUADRANTE_"].iloc[x]).add_to(mapa)

    # Agregar diferencia
    for x in list(df1["Cuadrante"].unique()):
        print(x)
        label_diferencia(x,df1,capa).add_to(mapa)

    # Function to determine the icon type based on the 'Medio_x' value
    def get_icon(medio):
        if medio == 'RPT':
            return folium.Icon(color='darkblue', icon='car', prefix='fa')
        elif medio == 'MTT':
            return folium.Icon(color='blue', icon='motorcycle', prefix='fa')
        else:
            return folium.Icon(color='gray')

    # Initialize the map centered around the average coordinates
    #map_center = [data['Latitude'].mean(), data['Longitude'].mean()]
    #m = folium.Map(location=map_center, zoom_start=12)
    coords = f.predefined_coords

    cuads = []

    # Add markers to the map
    for index, row in conjuntos_final.iterrows():
        id_ = row['Id_Conjunto']
        print(id_)
        cuad_name = "SSC-12.0"+str(row['Asignacion_Cuadrante_T1'])
        cuads.append(cuad_name)
        if cuad_name not in cuads:
            coord = coords[cuad_name][0]
        else:
            coord = coords[cuad_name][1]
        icon = get_icon(row['Medio_x'])
        print(cuad_name)

        html = df3[df3["Id_Conjunto"]==id_][["Id_agente","Rango","Tipo"]].to_html(
            classes="table table-striped table-hover table-condensed table-responsive"
        )

        popup = folium.Popup(html)

        folium.Marker(
            location=coord,
            popup=popup,
            icon=icon
        ).add_to(mapa)
    
    
    map_html = mapa._repr_html_()

    # Mostrar mapa
    components.html(map_html, width=1200, height=750)

else:
    components.html(turno1.html)
