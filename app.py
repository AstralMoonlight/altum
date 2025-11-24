import streamlit as st
import pandas as pd
import io
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="ALTUM | Topografía", page_icon="📐", layout="centered")

# --- FUNCIÓN: GENERAR PLANTILLA VACÍA ---
def generar_plantilla():
    df_plantilla = pd.DataFrame(columns=["Punto", "Distancia", "Atras", "Intermedia", "Adelante"])
    # Fila de ejemplo
    df_plantilla.loc[0] = [0, 0, 1.5, None, None]
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_plantilla.to_excel(writer, index=False)
    return buffer.getvalue()

# --- FUNCIÓN: CÁLCULO DE NIVELACIÓN ---
def procesar_nivelacion(df, cota_inicial):
    resultados = []
    ai_actual = 0
    cota_actual = cota_inicial
    dist_acumulada = 0
    
    # Primera fila (Inicio)
    primera_atras = df.iloc[0]['Atras']
    ai_actual = cota_actual + primera_atras
    
    resultados.append({"AI": ai_actual, "Cota_Calc": cota_actual, "Dist_Acum": 0})
    
    # Iteración
    for i in range(1, len(df)):
        fila = df.iloc[i]
        d_parcial = fila['Distancia'] if pd.notna(fila['Distancia']) else 0
        dist_acumulada += d_parcial
        
        lect_inter = fila['Intermedia']
        lect_adel = fila['Adelante']
        lect_atras = fila['Atras']
        
        nueva_cota = 0
        nueva_ai = None
        
        if pd.notna(lect_inter):
            nueva_cota = ai_actual - lect_inter
            nueva_ai = ai_actual
        elif pd.notna(lect_adel):
            nueva_cota = ai_actual - lect_adel
            if pd.notna(lect_atras):
                ai_actual = nueva_cota + lect_atras
                nueva_ai = ai_actual
            else:
                nueva_ai = None
        
        resultados.append({"AI": nueva_ai, "Cota_Calc": nueva_cota, "Dist_Acum": dist_acumulada})
        
    df_res = pd.DataFrame(resultados)
    return pd.concat([df.reset_index(drop=True), df_res], axis=1)

# --- INTERFAZ DE USUARIO ---
st.title("📐 ALTUM")
st.markdown("### Sistema de Cálculo de Nivelación")

# 1. SECCIÓN DE CARGA
with st.expander("📂 Descargar Plantilla Excel", expanded=False):
    st.write("Usa este formato para ingresar tus datos:")
    st.download_button(
        label="📥 Bajar Plantilla (.xlsx)",
        data=generar_plantilla(),
        file_name="plantilla_altum.xlsx",
        mime="application/vnd.ms-excel"
    )

uploaded_file = st.file_uploader("Sube tu archivo de campo", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        st.write("---")
        # Parámetros básicos
        c1, c2 = st.columns(2)
        cota_inicio = c1.number_input("Cota Inicio (BM)", value=725.000, format="%.3f")
        cota_llegada = c2.number_input("Cota Llegada (Real)", value=725.000, format="%.3f")

        if st.button("🚀 Calcular", type="primary"):
            
            # --- CÁLCULOS ---
            df_calc = procesar_nivelacion(df, cota_inicio)
            
            sum_atras = df_calc['Atras'].sum()
            sum_adelante = df_calc['Adelante'].sum()
            val_aritmetica = sum_atras - sum_adelante
            
            cota_final_calc = df_calc.iloc[-1]['Cota_Calc']
            desnivel = cota_final_calc - cota_inicio
            
            # Chequeo estricto (diferencia menor a 2mm se considera error de redondeo de Python)
            check_ok = abs(val_aritmetica - desnivel) < 0.002
            
            # --- RESULTADOS ---
            st.divider()
            st.subheader("1. Validación Aritmética")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Σ Atrás - Σ Adelante", f"{val_aritmetica:.3f}")
            col2.metric("Cota Final - Inicial", f"{desnivel:.3f}")
            
            if check_ok:
                col3.success("✅ CORRECTO")
                st.caption("La comprobación matemática coincide.")
                
                # --- SI TODO ESTÁ BIEN, MOSTRAMOS COMPENSACIÓN ---
                st.divider()
                st.subheader("2. Compensación y Resultados")
                
                error_cierre = cota_final_calc - cota_llegada
                dist_total = df_calc.iloc[-1]['Dist_Acum']
                
                st.write(f"**Error de Cierre:** {error_cierre:.4f} m")
                
                if dist_total > 0:
                    k = -error_cierre / dist_total
                    df_calc['Compensacion'] = df_calc['Dist_Acum'] * k
                    df_calc['Cota_Final'] = df_calc['Cota_Calc'] + df_calc['Compensacion']
                    
                    # Tabla Final
                    st.dataframe(df_calc.style.format({
                        "Atras": "{:.3f}", "Intermedia": "{:.3f}", "Adelante": "{:.3f}",
                        "AI": "{:.3f}", "Cota_Calc": "{:.3f}", "Compensacion": "{:.4f}", "Cota_Final": "{:.3f}"
                    }, na_rep=""), use_container_width=True)
                    
                    # Gráfico Interactivo (Plotly)
                    st.subheader("📈 Perfil Longitudinal")
                    fig = px.line(df_calc, x='Dist_Acum', y='Cota_Final', markers=True,
                                  title="Perfil del Terreno Compensado",
                                  labels={"Dist_Acum": "Distancia (m)", "Cota_Final": "Cota (m)"})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Descarga Final
                    buffer_down = io.BytesIO()
                    with pd.ExcelWriter(buffer_down, engine='openpyxl') as writer:
                        df_calc.to_excel(writer, index=False)
                    
                    st.download_button("💾 Descargar Resultado Completo", data=buffer_down.getvalue(), 
                                       file_name="Reporte_ALTUM.xlsx", mime="application/vnd.ms-excel")
                else:
                    st.warning("Distancia total es 0, no se puede compensar.")
                    
            else:
                col3.error("❌ ERROR MATEMÁTICO")
                st.error("Las sumas no cuadran con el desnivel. **SE DEBE VOLVER A MEDIR** o revisar la digitación.")

    except Exception as e:
        st.error(f"Error leyendo el archivo: {e}")