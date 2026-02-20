"""Servicio de búsqueda semántica basado en embeddings + FAISS."""  # Describe qué hace este módulo.

from __future__ import annotations  # Permite anotar tipos con strings en versiones anteriores de Python.

import json  # Proporciona utilidades para leer el archivo de configuración.
import os  # Facilita construir rutas de archivos.

import faiss  # Biblioteca para búsquedas vectoriales eficientes.
import pandas as pd  # Maneja el catálogo como DataFrame.
from django.conf import settings  # Da acceso a BASE_DIR y otras configuraciones de Django.
from sentence_transformers import SentenceTransformer  # Modelo que genera embeddings semánticos.

ARTEFACTS_DIR = os.path.join(settings.BASE_DIR, "core", "ia", "artefactos")  # Carpeta donde viven los artefactos entrenados.

with open(os.path.join(ARTEFACTS_DIR, "config.json"), encoding="utf-8") as cfg_file:  # Abre la configuración del modelo.
    CONFIG = json.load(cfg_file)  # Carga los parámetros (p. ej. nombre del modelo) en memoria.

MODEL = SentenceTransformer(CONFIG["model_name"])  # Instancia el modelo de embeddings una vez.
INDEX = faiss.read_index(os.path.join(ARTEFACTS_DIR, "faiss.index"))  # Carga el índice FAISS preconstruido.
CATALOGO = pd.read_csv(os.path.join(ARTEFACTS_DIR, "productos.csv"))  # Lee el catálogo de productos como DataFrame.


def buscar_productos(query: str, k: int = 5) -> list[dict]:  # Interfaz pública de búsqueda.
    query = (query or "").strip()  # Normaliza la consulta y maneja None.
    if not query:  # Si no queda texto útil, no hay nada que buscar.
        return []  # Devuelve lista vacía inmediatamente.

    emb = MODEL.encode([query], normalize_embeddings=True).astype("float32")  # Convierte la consulta en un embedding normalizado.
    distancias, indices = INDEX.search(emb, k)  # Consulta el índice FAISS para obtener los k vecinos más cercanos.

    resultados: list[dict] = []  # Acumulará los elementos encontrados.
    for score, idx in zip(distancias[0], indices[0]):  # Itera sobre cada par distancia/índice retornado.
        if idx < 0:  # FAISS usa -1 cuando no encuentra suficientes resultados.
            continue  # Ignora índices inválidos.
        fila = CATALOGO.iloc[int(idx)].to_dict()  # Extrae la fila correspondiente del catálogo y la convierte en dict.
        fila["score"] = float(score)  # Añade el score (similitud) como campo extra.
        resultados.append(fila)  # Agrega el resultado a la lista.

    return resultados  # Devuelve la colección final de coincidencias.
