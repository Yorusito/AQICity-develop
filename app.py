import pandas as pd
import networkx as nx
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# Cargar los datos y crear el grafo
data = pd.read_csv('globalairpollution.csv')
air_quality_columns = ['AQI Value', 'Ozone AQI Value', 'PM2.5 AQI Value']


G = nx.Graph()
city_air_quality = {}

def calculate_average(row):
    return sum([row[column] for column in air_quality_columns]) / len(air_quality_columns)

for i, row in data.iterrows():
    source_node = row['Country'] + '-' + row['City']
    G.add_node(source_node)
    city_air_quality[source_node] = calculate_average(row[air_quality_columns])

for source_node in G.nodes:
    for target_node in G.nodes:
        if source_node != target_node:
            difference = abs(city_air_quality[source_node] - city_air_quality[target_node])
            weight = 1 / (difference + 0.1)  # Usar la diferencia directamente como peso
            G.add_edge(source_node, target_node, weight=weight)

# Implementación algoritmo de Dijkstra
def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph.nodes}
    distances[start] = 0
    visited = set()

    while len(visited) < len(graph.nodes):
        current_node = min((node for node in graph.nodes if node not in visited), key=lambda x: distances[x])
        visited.add(current_node)

        for neighbor in graph.neighbors(current_node):
            new_distance = distances[current_node] + graph[current_node][neighbor]['weight']
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance

    return distances





@app.route('/', methods=['GET', 'POST'])
def mostrar_resultados():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json(force=True)
            source_node = data.get('source_node', '')
            desired_country = data.get('desired_country', '')
            excluded_country = data.get('excluded_country', '')
        else:
            source_node = request.form['source_node']
            desired_country = request.form['desired_country']
            excluded_country = request.form['excluded_country']
    else:
        # Valores predeterminados
        source_node = ''
        desired_country = ''
        excluded_country = ''

    # Obtener la lista de países disponibles
    countries = sorted(set(country.split('-')[0] for country in G.nodes))

    # Calcular distancias y resultados según los valores proporcionados
    distances = dijkstra(G, source_node)

    # Almacenar los resultados en variables
    distancias_desde_source = distances
    sorted_distances = sorted(distances.items(), key=lambda x: x[1])
    min_distance = float('inf')
    min_distance_city = None

    for city, distance in distances.items():
        if city != source_node:
            if distance < min_distance:
                min_distance = distance
                min_distance_city = city

    min_distance_result = (min_distance_city, min_distance)

    promedio_calidad_aire_fuente = city_air_quality.get(source_node, None)

    resultados_filtrados_deseado = [(target, distances[target]) for target in G.nodes if source_node != target and target.startswith(desired_country)]
    resultados_filtrados_no_deseado = [(target, distances[target]) for target in G.nodes if source_node != target and not target.startswith(excluded_country)]
    resultados_filtrados_no_deseado.sort(key=lambda x: x[1], reverse=True)

 
    if request.is_json:
        return jsonify({
            'source_node': source_node,
            'distancias_desde_source': distancias_desde_source,
            'sorted_distances': sorted_distances,
            'min_distance_result': min_distance_result,
            'resultados_filtrados_deseado': resultados_filtrados_deseado,
            'resultados_filtrados_no_deseado': resultados_filtrados_no_deseado,
            'excluded_country': excluded_country,
            'countries': countries,
            'promedio_calidad_aire_fuente': promedio_calidad_aire_fuente 
        })
    else:
        return render_template('resultados.html',
                               source_node=source_node,
                               distancias_desde_source=distancias_desde_source,
                               sorted_distances=sorted_distances,
                               min_distance_result=min_distance_result,
                               resultados_filtrados_deseado=resultados_filtrados_deseado,
                               resultados_filtrados_no_deseado=resultados_filtrados_no_deseado,
                               excluded_country=excluded_country,
                               countries=countries,
                               promedio_calidad_aire_fuente=promedio_calidad_aire_fuente)
    

# Dentro de la función generate_random_distances en el servidor
@app.route('/generateRandomDistances', methods=['POST'])
def generate_random_distances():
    if request.is_json:
        data = request.get_json(force=True)
        source_node = data.get('source_node', '')
        desired_country = data.get('desired_country', '')
        excluded_country = data.get('excluded_country', '')
    else:
        source_node = request.form['source_node']
        desired_country = request.form['desired_country']
        excluded_country = request.form['excluded_country']

    # Generar distancias aleatorias para demostrar el funcionamiento de Dijkstra
    random_distances = {target: random.uniform(1, 10) for target in G.nodes if source_node != target}

    # Calcular el país-ciudad con la menor distancia basada en la comparación de promedios
    min_distance_result_random = min(random_distances.items(), key=lambda x: x[1])

    # Filtrar y ordenar los resultados para el país deseado basado en las distancias aleatorias
    resultados_filtrados_deseado_random = [(target, random_distances[target]) for target in G.nodes if source_node != target and target.startswith(desired_country)]
    resultados_filtrados_deseado_random.sort(key=lambda x: x[1])

    # Filtrar y ordenar los resultados para el país no deseado basado en las distancias aleatorias
    resultados_filtrados_no_deseado_random = [(target, random_distances[target]) for target in G.nodes if source_node != target and not target.startswith(excluded_country)]
    resultados_filtrados_no_deseado_random.sort(key=lambda x: x[1], reverse=True)

    if request.is_json:
        return jsonify({
            'random_distances': random_distances,
            'min_distance_result_random': min_distance_result_random,
            'resultados_filtrados_deseado_random': resultados_filtrados_deseado_random,
            'resultados_filtrados_no_deseado_random': resultados_filtrados_no_deseado_random
        })
    else:
        return render_template('resultados.html',
                               random_distances=random_distances,
                               min_distance_result_random=min_distance_result_random,
                               resultados_filtrados_deseado_random=resultados_filtrados_deseado_random,
                               resultados_filtrados_no_deseado_random=resultados_filtrados_no_deseado_random)

if __name__ == '__main__':
    app.run()
