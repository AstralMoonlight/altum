# 📐 ALTUM

**Sistema de Cálculo y Compensación de Nivelación Geométrica**

ALTUM es una aplicación web desarrollada en Python y Streamlit diseñada para automatizar el procesamiento de datos topográficos. Permite a topógrafos e ingenieros subir registros de campo en Excel, calcular cotas automáticamente, validar errores de cierre y realizar compensaciones milimétricas basadas en la distancia acumulada.

---

## 🚀 Características Principales

* **Lectura de Excel:** Carga directa de registros de campo (`.xlsx`).
* **Cálculo Automático:** Determina Altura Instrumental (AI) y Cotas para puntos de cambio e intermedios.
* **Validación Doble:** Comprobación aritmética inmediata:
    * $\sum \text{Vistas Atrás} - \sum \text{Vistas Adelante}$
    * $\text{Cota Final} - \text{Cota Inicial}$
* **Compensación de Errores:** Distribución del error de cierre proporcional a la distancia acumulada.
* **Exportación:** Descarga de la tabla final compensada lista para informes.

## 📋 Requisitos de Entrada (Excel)

Para que ALTUM procese los datos correctamente, el archivo Excel debe tener la siguiente estructura de columnas en la primera fila:

| Punto | Distancia | Atras | Intermedia | Adelante |
| :--- | :--- | :--- | :--- | :--- |
| 0 | 0 | 1.500 | | |
| 1 | 10 | | 1.200 | |
| 2 | 5 | 2.200 | | 0.890 |

> **Nota:** Las celdas sin lectura deben dejarse vacías.

## 🛠️ Instalación y Ejecución Local

Si deseas correr este proyecto en tu propia máquina:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/AstralMoonlight/altum](https://github.com/AstralMoonlight/altum)
    cd altum
    ```

2.  **Crear un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/Scripts/activate  # En Windows GitBash
    # o bien: venv\Scripts\activate en CMD
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar la aplicación:**
    ```bash
    streamlit run app.py
    ```

## 🧮 Fórmulas Utilizadas

El sistema utiliza la lógica estándar de nivelación geométrica compuesta:

1.  **Altura Instrumental:** $AI = Cota_{actual} + Lectura_{atras}$
2.  **Cota Punto:** $Cota = AI - Lectura_{adelante/intermedia}$
3.  **Factor de Compensación ($k$):**
    $$k = \frac{-(Cota_{calc} - Cota_{real})}{Distancia_{total}}$$
4.  **Cota Compensada:** $Cota_{comp} = Cota_{calc} + (k \times Distancia_{acumulada})$

## 📦 Dependencias

* [Streamlit](https://streamlit.io/) - Framework para la interfaz web.
* [Pandas](https://pandas.pydata.org/) - Manipulación de datos tabulares.
* [OpenPyXL](https://openpyxl.readthedocs.io/) - Lectura y escritura de archivos Excel.

---
*Desarrollado para agilizar procesos topográficos en terreno y gabinete.*