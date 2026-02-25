import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# Configuración
st.set_page_config(page_title="Finanzas Pro Cloud", layout="wide", page_icon="☁️")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Pega aquí TU dirección completa de Google Sheets entre las comillas
URL_HOJA = "https://docs.google.com/spreadsheets/d/14G5YVHmww4ZR3PMPeQFQSJ81FWOOGLvWmAYZ-9OytAw/edit?gid=0#gid=0"

def cargar_datos():
    try:
        # Le indicamos explícitamente qué hoja leer con el parámetro 'spreadsheet'
        df = conn.read(spreadsheet=URL_HOJA, worksheet="Datos", usecols=[0, 1, 2, 3, 4])
        df = df.dropna(how="all")
        if not df.empty:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(columns=['Fecha', 'Concepto', 'Categoría', 'Tipo', 'Monto'])

def guardar_movimiento(df_actual, fecha, concepto, categoria, tipo, monto):
    nuevo = pd.DataFrame({
        'Fecha': [pd.to_datetime(fecha).strftime("%Y-%m-%d")], 
        'Concepto': [concepto], 
        'Categoría': [categoria], 
        'Tipo': [tipo], 
        'Monto': [monto]
    })
    df_actualizado = pd.concat([df_actual, nuevo], ignore_index=True)
    # Le indicamos explícitamente dónde actualizar
    conn.update(spreadsheet=URL_HOJA, worksheet="Datos", data=df_actualizado)
    return df_actualizado

# --- INTERFAZ PRINCIPAL ---
st.title("☁️ Plataforma de Análisis Financiero")

df = cargar_datos()

# Crear pestañas para organizar la información
tab_dashboard, tab_proyecciones = st.tabs(["📊 Dashboard Operativo", "🔮 Modelado y Proyecciones"])

# ==========================================
# PESTAÑA 1: DASHBOARD Y REGISTRO
# ==========================================
with tab_dashboard:
    col_input, col_dash = st.columns([1, 3])
    
    with col_input:
        st.subheader("📝 Registrar")
        fecha = st.date_input("Fecha", datetime.now())
        tipo = st.radio("Tipo", ["Gasto", "Ingreso"], horizontal=True)
        
        if tipo == "Ingreso":
            cat = st.selectbox("Categoría", ["Nómina", "Inversiones", "Negocio", "Otros"])
        else:
            cat = st.selectbox("Categoría", ["Vivienda", "Alimentos", "Transporte", "Servicios", "Ocio", "Salud", "Educación", "Deuda"])
            
        concepto = st.text_input("Concepto")
        monto = st.number_input("Monto ($)", min_value=0.0, format="%.2f")
        
        if st.button("Guardar en la Nube", type="primary", use_container_width=True):
            if monto > 0:
                with st.spinner('Sincronizando con Google Sheets...'):
                    guardar_movimiento(df, fecha, concepto, cat, tipo, monto)
                st.success("¡Sincronizado!")
                st.rerun()

    with col_dash:
        if not df.empty:
            # KPIs Rápidos
            c1, c2, c3 = st.columns(3)
            ingresos_totales = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
            gastos_totales = df[df['Tipo'] == 'Gasto']['Monto'].sum()
            flujo_caja = ingresos_totales - gastos_totales
            
            c1.metric("Ingresos Históricos", f"${ingresos_totales:,.2f}")
            c2.metric("Gastos Históricos", f"${gastos_totales:,.2f}")
            c3.metric("Flujo de Caja", f"${flujo_caja:,.2f}", delta=float(flujo_caja))
            
            # Gráfico de tendencias
            st.subheader("Tendencia de Flujo de Efectivo")
            
            # 1. Asegurar que los montos sean numéricos (previene errores de lectura de Sheets)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
            
            # 2. Agrupación
            df_grouped = df.groupby([df['Fecha'].dt.to_period('M'), 'Tipo'])['Monto'].sum().unstack(fill_value=0).reset_index()
            
            # 3. Validación de columnas (El parche para evitar el ValueError)
            if 'Ingreso' not in df_grouped.columns:
                df_grouped['Ingreso'] = 0.0
            if 'Gasto' not in df_grouped.columns:
                df_grouped['Gasto'] = 0.0
                
            df_grouped['Fecha'] = df_grouped['Fecha'].dt.to_timestamp()
            
            # 4. Generar gráfico
            fig_trend = px.bar(df_grouped, x='Fecha', y=['Ingreso', 'Gasto'], barmode='group', color_discrete_map={'Ingreso':'#00CC96', 'Gasto':'#EF553B'})
            st.plotly_chart(fig_trend, use_container_width=True)

# ==========================================
# PESTAÑA 2: MODELADO FINANCIERO
# ==========================================
with tab_proyecciones:
    st.header("Modelos de Amortización y Deuda")
    
    col_hipoteca, col_tc = st.columns(2)
    
    # --- MODELO HIPOTECARIO / PRÉSTAMOS ---
    with col_hipoteca:
        st.subheader("🏠 Simulador de Hipoteca / Préstamo")
        st.markdown("Calcula el cuadro de amortización para deuda a largo plazo.")
        
        capital = st.number_input("Capital del Préstamo ($)", value=1000000.0, step=50000.0)
        tasa_anual = st.number_input("Tasa de Interés Anual (%)", value=11.5, step=0.5)
        anios = st.slider("Plazo (Años)", min_value=1, max_value=30, value=20)
        
        if capital > 0 and tasa_anual > 0:
            tasa_mensual = (tasa_anual / 100) / 12
            meses_totales = anios * 12
            
            # Cálculo de cuota fija
            cuota_mensual = capital * (tasa_mensual * (1 + tasa_mensual)**meses_totales) / ((1 + tasa_mensual)**meses_totales - 1)
            
            st.metric("Cuota Mensual Fija", f"${cuota_mensual:,.2f}")
            
            # Generar cuadro de amortización (Vectorizado para rendimiento)
            meses = np.arange(1, meses_totales + 1)
            intereses = np.zeros(meses_totales)
            amortizacion = np.zeros(meses_totales)
            saldo = np.zeros(meses_totales)
            
            saldo_actual = capital
            for i in range(meses_totales):
                interes_mes = saldo_actual * tasa_mensual
                amort_mes = cuota_mensual - interes_mes
                saldo_actual -= amort_mes
                
                intereses[i] = interes_mes
                amortizacion[i] = amort_mes
                saldo[i] = max(0, saldo_actual)
                
            df_amort = pd.DataFrame({'Mes': meses, 'Interés': intereses, 'Capital': amortizacion, 'Saldo Restante': saldo})
            
            # Visualización del área de pago
            fig_hipoteca = px.area(df_amort, x='Mes', y=['Interés', 'Capital'], title="Composición del Pago a lo largo del tiempo", color_discrete_sequence=['#EF553B', '#00CC96'])
            st.plotly_chart(fig_hipoteca, use_container_width=True)

    # --- MODELO DE TARJETA DE CRÉDITO ---
    with col_tc:
        st.subheader("💳 Proyección de Tarjeta de Crédito")
        st.markdown("Calcula el tiempo de liquidación según tu aportación mensual.")
        
        deuda_tc = st.number_input("Deuda Actual TDC ($)", value=25000.0, step=1000.0)
        tasa_tc_anual = st.number_input("CAT / Tasa Anual TDC (%)", value=45.0, step=1.0)
        pago_mensual = st.number_input("Pago Mensual Proyectado ($)", value=1500.0, step=100.0)
        
        tasa_tc_mensual = (tasa_tc_anual / 100) / 12
        interes_primer_mes = deuda_tc * tasa_tc_mensual
        
        if pago_mensual <= interes_primer_mes and deuda_tc > 0:
            st.error(f"⚠️ Tu pago mensual debe ser mayor a los intereses generados (${interes_primer_mes:,.2f}) para poder liquidar la deuda.")
        elif deuda_tc > 0:
            saldo_tc = deuda_tc
            meses_tc = 0
            interes_acumulado_tc = 0
            historial_tc = []
            
            while saldo_tc > 0 and meses_tc < 240: # Límite de 20 años para evitar loops infinitos
                meses_tc += 1
                interes_mes = saldo_tc * tasa_tc_mensual
                interes_acumulado_tc += interes_mes
                
                if saldo_tc + interes_mes < pago_mensual:
                    pago = saldo_tc + interes_mes
                    saldo_tc = 0
                else:
                    pago = pago_mensual
                    saldo_tc = saldo_tc + interes_mes - pago
                    
                historial_tc.append({'Mes': meses_tc, 'Saldo': saldo_tc, 'Interés Pagado': interes_acumulado_tc})
                
            st.success(f"Liquidarás la deuda en **{meses_tc} meses** ({meses_tc/12:.1f} años).")
            st.warning(f"Total de intereses pagados al final: **${interes_acumulado_tc:,.2f}**")
            
            df_tc = pd.DataFrame(historial_tc)
            fig_tc = px.line(df_tc, x='Mes', y='Saldo', title="Curva de Liquidación de Deuda", markers=True)
            fig_tc.update_traces(line_color='red')

            st.plotly_chart(fig_tc, use_container_width=True)
