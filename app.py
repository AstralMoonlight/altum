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
            
            # Datos para comprobación
            sum_atras = df_calc['Atras'].sum()
            sum_adelante = df_calc['Adelante'].sum()
            val_aritmetica = sum_atras - sum_adelante # (Σ Atrás - Σ Adelante)
            
            cota_final_calc = df_calc.iloc[-1]['Cota_Calc']
            desnivel = cota_final_calc - cota_inicio # (Cota Final - Cota Inicial)
            
            # ERROR MATEMÁTICO (Debe ser 0)
            discrepancia_matematica = val_aritmetica - desnivel
            
            # ERROR DE CIERRE (Topográfico)
            error_cierre = cota_final_calc - cota_llegada

            # Chequeo estricto (tolerancia de redondeo de Python 0.002)
            check_ok = abs(discrepancia_matematica) < 0.002
            
            # --- RESULTADOS VISUALES ---
            st.divider()
            st.subheader("1. Análisis de Errores")
            
            # FILA 1: ERROR MATEMÁTICO
            st.markdown("**A. Comprobación Aritmética (Validación de planilla)**")
            col_a1, col_a2, col_a3 = st.columns(3)
            col_a1.metric("Σ Atrás - Σ Adelante", f"{val_aritmetica:.3f}")
            col_a2.metric("Cota Final - Inicial", f"{desnivel:.3f}")
            
            # AQUÍ MOSTRAMOS LA DISCREPANCIA (EL ERROR)
            col_a3.metric(
                label="Discrepancia (Debe ser 0)", 
                value=f"{discrepancia_matematica:.4f}",
                delta="Error Matemático" if not check_ok else "Correcto",
                delta_color="inverse"
            )
            
            if not check_ok:
                st.error(f"❌ **ERROR CRÍTICO:** Tienes una diferencia matemática de **{discrepancia_matematica:.4f}**. Revisa si sumaste mal o escribiste mal algún número en el Excel.")
            else:
                st.success("✅ **Matemática Correcta:** La planilla está bien calculada.")
                
                # --- SOLO SI LA MATEMÁTICA ESTÁ BIEN, SEGUIMOS ---
                st.divider()
                st.markdown("**B. Error de Cierre Topográfico**")
                
                col_b1, col_b2, col_b3 = st.columns(3)
                col_b1.metric("Cota Calculada", f"{cota_final_calc:.3f}")
                col_b2.metric("Cota Real (Llegada)", f"{cota_llegada:.3f}")
                
                # AQUÍ MOSTRAMOS EL ERROR DE CIERRE
                col_b3.metric(
                    label="Error de Cierre", 
                    value=f"{error_cierre:.4f} m",
                    delta="Exceso" if error_cierre > 0 else "Defecto",
                    delta_color="off" # Off para que sea gris/neutro, o "normal" para rojo/verde
                )

                st.divider()
                st.subheader("2. Compensación y Resultados Finales")
                
                dist_total = df_calc.iloc[-1]['Dist_Acum']
                
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

    except Exception as e:
        st.error(f"Error leyendo el archivo: {e}")