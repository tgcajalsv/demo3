"""Funciones para app streamlit demo herramienta asignación de recursos según demanda."""

import streamlit as st 
#from streamlit_folium import st_folium
import numpy as np
import pandas as pd 
import folium
import random
from shapely.geometry import Point, Polygon

# Función para asignar recursos a los cuadrantes y actualizar 'Oferta_total'
def asignar_recursos(df_necesidades, df_recursos):
    #df_necesidades = df_necesidades.rename(columns={"Id_Cuadrante":"Cuadrante"})
    # Iterar sobre cada cuadrante
    for index, row in df_necesidades.iterrows():
        cuadrante = row['Cuadrante']
        necesidad = row['Necesidad']
        #print(f"\nAsignando recursos para Cuadrante {cuadrante} con necesidad {necesidad}")
        
        # Encontrar recursos disponibles
        recursos_disponibles = df_recursos[df_recursos['Asignacion'] == 0]
        
        # Asignar recursos hasta cubrir la necesidad
        while necesidad > 0 and not recursos_disponibles.empty:
            # Tomar el primer recurso disponible
            recurso_index = recursos_disponibles.index[0]
            oferta_unitaria = recursos_disponibles.loc[recurso_index, 'Oferta Unitaria']
            
            # Asignar el recurso al cuadrante
            df_recursos.at[recurso_index, 'Asignacion'] = cuadrante
            necesidad -= oferta_unitaria
            #print(f"Asignado recurso {recurso_index} con oferta unitaria {oferta_unitaria}")
            
            # Actualizar 'Oferta_total' en el DataFrame de necesidades
            df_necesidades.at[index, 'Oferta_total'] += oferta_unitaria
            
            # Actualizar recursos disponibles
            recursos_disponibles = df_recursos[df_recursos['Asignacion'] == 0]
        
        if necesidad > 0:
            print(f"No se pudo cubrir la necesidad completa para Cuadrante {cuadrante}. Necesidad restante: {necesidad}")
        else:
            print(f"Necesidad cubierta para Cuadrante {cuadrante}")

    
    df_necesidades['Diferencia'] = df_necesidades['Oferta_total'] + df_necesidades['Cuarteles'] - df_necesidades['Necesidad']
    recursos_disponibles = df_recursos[df_recursos['Asignacion'] == 0]

    # Ordenar los cuadrantes según tengan la menor diferencia
    if not recursos_disponibles.empty:
    
        df_necesidades = df_necesidades.sort_values(by='Diferencia')


        # Iterar sobre los cuadrantes ordenados inversamente y asignar recursos remanentes
        for index, row in df_necesidades.iterrows():
            if not recursos_disponibles.empty:
                cuadrante = row['Cuadrante']  # Obtener el cuadrante
                oferta_unitaria = recursos_disponibles.iloc[0]['Oferta Unitaria']  # Obtener la oferta unitaria del primer recurso disponible
                df_necesidades.at[index, 'Oferta_total'] += oferta_unitaria  # Actualizar oferta total en el DataFrame de necesidades
                df_recursos.at[recursos_disponibles.index[0], 'Asignacion'] = cuadrante  # Asignar el cuadrante al primer recurso disponible
                recursos_disponibles = recursos_disponibles.iloc[1:]  # Remover el recurso asignado
            else:
                break  # Si no hay recursos disponibles, salir del bucle
            
    df_necesidades['Diferencia'] = df_necesidades['Oferta_total'] + df_necesidades['Cuarteles'] - df_necesidades['Necesidad']
    df_necesidades = df_necesidades.sort_values(by='Cuadrante')
            
    return df_recursos, df_necesidades

# Función para transformar polígonos
def transform_polygon(shapely_polygon, name):
    """
    Función para convertir polígono shapely en polígono folium.

    Parámetros:
    - shapely_polygon: Polígono shapely.
    - color: Color de línea (default: 'blue').
    - weight: Grosor de línea (default: 2).
    - fill_color: Color de relleno de polígono (default: 'blue').
    - fill_opacity: Opacidad de color de relleno (default: 0.4).

    Output:
    - Objeto polígono folium.
    """
    # Extraer coordenadas
    coordinates = shapely_polygon.exterior.coords.xy

    # Generar puntos 
    latitudes = list(coordinates[1])
    longitudes = list(coordinates[0])
    points = list(zip(latitudes, longitudes))

    # Definir color
    color="deepskyblue"
    fill_color="deepskyblue"

    # Crear polígono folium
    folium_polygon = folium.vector_layers.Polygon(
        locations=points,
        color=color,
        weight=2,
        fill_color=fill_color,
        fill_opacity=0.2,
        tooltip=name
    )

    return folium_polygon


# Función para etiquetas de diferencia
def label_diferencia(cuadrante, df, gdf):
    #df = df.rename(columns={"Id_Cuadrante":"Cuadrante"})

    # Definir polígono
    poligono = gdf[gdf["CUADRANTE_"]==cuadrante]["geometry"].values[0]
    center_lat = poligono.centroid.y.mean()
    center_lon = poligono.centroid.x.mean()

    # Definir diferencia
    diferencia = df[df["Cuadrante"]==cuadrante]["Diferencia"].values[0]

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

# Coordenadas predefinidas para marcadores de medios en cuadrantes        
predefined_coords = {
    "SSC-12.01": [
        (13.711347, -89.245041), (13.706200, -89.243542), (13.709451, -89.238279),
        (13.704066, -89.229599), (13.704913, -89.238732)
    ],
    "SSC-12.02": [
        (13.699606, -89.244572), (13.696846, -89.242720), (13.698806, -89.234116),
        (13.689046, -89.240456), (13.685677, -89.242013)
    ],
    "SSC-12.03": [
        (13.685677, -89.242013), (13.697569, -89.219173), (13.685726, -89.232846),
        (13.687617, -89.225779), (13.687219, -89.220658)
    ],
    "SSC-12.04": [
        (13.725679, -89.234178), (13.723589, -89.230900), (13.716674, -89.242525),
        (13.715828, -89.237916), (13.714186, -89.233000)
    ],
    "SSC-12.05": [
        (13.714917, -89.228318), (13.712130, -89.221146), (13.710296, -89.226053),
        (13.724232, -89.226808), (13.721665, -89.219862)
    ],
    "SSC-12.06": [
        (13.719245, -89.212841), (13.720272, -89.207782), (13.711397, -89.216087),
        (13.706115, -89.219485), (13.708023, -89.215181)
    ],
    "SSC-12.07": [
        (13.724232, -89.248930), (13.720345, -89.254064), (13.714184, -89.251422),
        (13.718291, -89.251271), (13.708169, -89.251195)
    ]
}


def get_predefined_point(polygon_id, index):
    # Coordenadas pre definidas en polígonos
    coords = predefined_coords.get(polygon_id, [])
    if index < len(coords):
        return coords[index]
    else:
        return None  # En caso de no haber suficientes puntos
    
def create_popup_content(id_conjunto, conjuntos):
    rows = conjuntos[conjuntos['Id_Conjunto'] == id_conjunto]
    if rows.empty:
        return "No data available"
    
    conjunto = rows.iloc[0]['Id_Conjunto']
    grupo = rows.iloc[0]['Grupo']
    personal_data = ", ".join(f"{row['Rango']} ({row['Tipo']})" for idx, row in rows.iterrows())
    popup_content = (f"Personal: {personal_data}<br>"
                     f"Número de grupo: {grupo}<br>"
                     f"Número de conjunto: {conjunto}")
    return popup_content
        
# Función para agregar medios asignados
def viz_medios(df, id_medio, predefined_coords, polygon_counter, id_conjunto, turno):
    tipo = df[df["Id_Medio"] == id_medio]["Medio"].values[0]
    cuadrante = df[df["Id"] == id_medio]["Asignacion_Cuadrante_T"+str(turno)].values[0]

    if tipo == "RPT":
        icon = "car"
        color = "darkblue"
    elif tipo == "MTT":
        icon = "motorcycle"
        color = "blue"
    
    # Agregar un contador de cantidad de marcadores por cuadrante
    polygon_id = cuadrante  
    coord = get_predefined_point(polygon_id, polygon_counter[polygon_id])
    if coord:
        polygon_counter[polygon_id] += 1
        popup_content = create_popup_content(id_conjunto)
        marcador = folium.Marker(
            location=coord, 
            draggable=True,
            popup=f'ID:',
            icon=folium.Icon(icon=icon, color=color, prefix='fa')
        )
        return marcador
    else:
        return None  # En caso de coordenadas no válidas
    


# Función para generar mapa
def mapa_medios(gdf,df_asignados, df_cuadrantes):
    # Definir coordenadas centrales
    center_lat = gdf.geometry.centroid.y.mean()
    center_lon = gdf.geometry.centroid.x.mean()

    # Mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
    )

    # Agregar capa cuadrantes
    for x in range(0,len(gdf)):
        transform_polygon(gdf["geometry"].iloc[x],gdf["CUADRANTE_"].iloc[x]).add_to(m)

    # Agregar diferencia
    for x in list(gdf["CUADRANTE_"].unique()):
        label_diferencia(x,df_cuadrantes,gdf).add_to(m)

    # Agregar marcadores de medios asignados según coordenadas predefinidas
    medios_asignados = df_asignados[df_asignados["Asignacion"] != 0]
    polygon_counter = {key: 0 for key in predefined_coords.keys()}
    for x in list(medios_asignados["Id"]):
        marker = viz_medios(df_asignados, x, predefined_coords, polygon_counter)
        if marker:
            marker.add_to(m)

    return m

turno=1

def asignar_conjuntos(df3, jefe, agentes_seleccionados, id_conjunto,medio,asignacion):
    # Actualizar Id_Conjunto para jefe
    df3.loc[df3['Id_agente'] == jefe['Id_agente'], 'Id_Conjunto'] = id_conjunto
    df3.loc[df3['Id_agente'] == jefe['Id_agente'], 'Medio'] = medio
    df3.loc[df3['Id_agente'] == jefe['Id_agente'], 'Asignacion_Medios'] = asignacion
    df3.loc[df3['Id_agente'] == jefe['Id_agente'], 'Turno'] = turno
    
    # Actualizar Id_Conjunto para los agentes seleccionados
    for _, agente in agentes_seleccionados.iterrows():
        df3.loc[df3['Id_agente'] == agente['Id_agente'], 'Id_Conjunto'] = id_conjunto
        df3.loc[df3['Id_agente'] == agente['Id_agente'], 'Medio'] = medio
        df3.loc[df3['Id_agente'] == agente['Id_agente'], 'Asignacion_Medios'] = asignacion
        df3.loc[df3['Id_agente'] == agente['Id_agente'], 'Turno'] = turno
    
    return df3
