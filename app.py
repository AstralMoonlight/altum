import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="ALTUM | Topografía", page_icon="📐")

def procesar_nivelacion(df, cota_inicial, cota_llegada_teorica):
    # Crear listas para almacenar los resultados paso a paso
    # Esto simula el cálculo manual fila por fila
    resultados = []
    
    # Variables de estado
    ai_actual = 0
    cota_actual = cota_inicial
    dist_acumulada = 0
    
    # Procesamos la primera fila (Punto de inicio)
    # Asumimos que la primera fila TIENE que tener una vista ATRÁS para arrancar
    primera_atras = df.iloc[0]['Atras']
    ai_actual = cota_actual + primera_atras
    
    # Guardamos datos fila 0
    resultados.append({
        "AI": ai_actual,
        "Cota_Calc": cota_actual,
        "Dist_Acum": 0
    })
    
    # Iteramos desde la segunda fila (índice 1) hasta el final
    for i in range(1, len(df)):
        fila = df.iloc[i]
        
        # 1. Distancias
        d_parcial = fila['Distancia'] if pd.notna(fila['Distancia']) else 0
        dist_acumulada += d_parcial
        
        lect_inter = fila['Intermedia']
        lect_adel = fila['Adelante']
        lect_atras = fila['Atras']
        
        # 2. Cálculo de Cota
        nueva_cota = 0
        nueva_ai = None # Por defecto no hay nueva AI a menos que sea punto de cambio
        
        if pd.notna(lect_inter):
            # Es lectura INTERMEDIA
            nueva_cota = ai_actual - lect_inter
            nueva_ai = ai_actual # La AI se mantiene (solo visual)
            
        elif pd.notna(lect_adel):
            # Es lectura ADELANTE (Punto de cambio o final)
            nueva_cota = ai_actual - lect_adel
            
            # Verificamos si es un Punto de Cambio (tiene Adelante Y Atrás)
            if pd.notna(lect_atras):
                # Calculamos la NUEVA AI para los siguientes puntos
                ai_actual = nueva_cota + lect_atras
                nueva_ai = ai_actual
            else:
                # Es el punto final, no hay nueva AI
                nueva_ai = None
        else:
            # Caso de error en datos
            nueva_cota = 0 
            
        resultados.append({
            "AI": nueva_ai,
            "Cota_Calc": nueva_cota,
            "Dist_Acum": dist_acumulada
        })
        
    # Convertimos resultados a DataFrame y unimos
    df_res = pd.DataFrame(resultados)
    df_final = pd.concat([df.reset_index(drop=True), df_res], axis=1)
    
    return df_final

# --- INTERFAZ GRÁFICA ---
st.title("📐 ALTUM")
st.caption("Sistema de Cálculo y Compensación de Nivelación Geométrica")

uploaded_file = st.file_uploader("Sube tu registro (.xlsx)", type=['xlsx'])

# Enlace para descargar plantilla si el usuario no tiene una
st.info("El Excel debe tener las columnas: `Punto`, `Distancia`, `Atras`, `Intermedia`, `Adelante`")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Configuración de parámetros
        col_config1, col_config2 = st.columns(2)
        with col_config1:
            cota_inicio = st.number_input("Cota Inicial (BM)", value=725.000, format="%.3f")
        with col_config2:
            cota_llegada = st.number_input("Cota Llegada Real (Para cierre)", value=725.000, format="%.3f")

        if st.button("Calcular Nivelación", type="primary"):
            
            # 1. Procesar Datos
            df_calc = procesar_nivelacion(df, cota_inicio, cota_llegada)
            
            # 2. Comprobación Aritmética
            sum_atras = df_calc['Atras'].sum()
            sum_adelante = df_calc['Adelante'].sum()
            error_aritmetico = sum_atras - sum_adelante
            
            cota_final_calc = df_calc.iloc[-1]['Cota_Calc']
            desnivel = cota_final_calc - cota_inicio
            
            # 3. Visualización de Errores
            st.divider()
            st.subheader("1. Comprobación de Campo")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Σ Vistas Atrás", f"{sum_atras:.3f}")
            col2.metric("Σ Vistas Adelante", f"{sum_adelante:.3f}")
            col3.metric("Dif. Sumas", f"{error_aritmetico:.3f}")
            col4.metric("Dif. Cotas", f"{desnivel:.3f}")
            
            if abs(error_aritmetico - desnivel) < 0.002:
                st.success("✅ **Validación Exitosa:** El cálculo matemático cierra correctamente.")
            else:
                st.error("❌ **Error Matemático:** Revisa si escribiste mal algún número en el Excel.")

            # 4. Compensación
            st.divider()
            st.subheader("2. Compensación de Error")
            
            error_cierre = cota_final_calc - cota_llegada
            dist_total = df_calc.iloc[-1]['Dist_Acum']
            
            st.write(f"**Error de Cierre:** {error_cierre:.4f} m")
            st.write(f"**Distancia Total:** {dist_total:.2f} m")
            
            if dist_total > 0:
                # Fórmula: k = -Error / Distancia Total
                k = -error_cierre / dist_total
                
                # Aplicar compensación: C = k * Dist_Acum
                df_calc['Compensacion'] = df_calc['Dist_Acum'] * k
                df_calc['Cota_Compensada'] = df_calc['Cota_Calc'] + df_calc['Compensacion']
                
                # Formatear tabla para mostrar
                st.dataframe(df_calc.style.format({
                    "Atras": "{:.3f}", "Intermedia": "{:.3f}", "Adelante": "{:.3f}",
                    "AI": "{:.3f}", "Cota_Calc": "{:.3f}",
                    "Compensacion": "{:.4f}", "Cota_Compensada": "{:.3f}"
                }, na_rep=""), use_container_width=True)
                
                # Botón de descarga
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_calc.to_excel(writer, index=False, sheet_name='Compensacion')
                
                st.download_button(
                    label="💾 Descargar Tabla Compensada (Excel)",
                    data=buffer.getvalue(),
                    file_name="Nivelacion_ALTUM.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.warning("No se puede compensar: La distancia total es 0.")
                
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo: {e}")