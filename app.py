import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Finanzas Pro Cloud", layout="wide", page_icon="☁️")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)
# Asegúrate de poner tu URL real aquí
URL_HOJA = "https://docs.google.com/spreadsheets/d/AQUI_VA_TU_URL_COMPLETA/edit"

def cargar_datos_flujo():
    try:
        df = conn.read(spreadsheet=URL_HOJA, worksheet="Datos", usecols=[0, 1, 2, 3, 4])
        df = df.dropna(how="all")
        if not df.empty:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['Fecha', 'Concepto', 'Categoría', 'Tipo', 'Monto'])

def cargar_datos_balance():
    try:
        df = conn.read(spreadsheet=URL_HOJA, worksheet="Balance", usecols=[0, 1, 2, 3, 4])
        df = df.dropna(how="all")
        if not df.empty:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['Fecha', 'Cuenta', 'Clasificación', 'Categoría', 'Monto'])

def guardar_movimiento(df_actual, fecha, concepto, categoria, tipo, monto, worksheet):
    nuevo = pd.DataFrame({
        df_actual.columns[0]: [pd.to_datetime(fecha).strftime("%Y-%m-%d")], 
        df_actual.columns[1]: [concepto], 
        df_actual.columns[2]: [categoria], 
        df_actual.columns[3]: [tipo], 
        df_actual.columns[4]: [monto]
    })
    df_actualizado = pd.concat([df_actual, nuevo], ignore_index=True)
    conn.update(spreadsheet=URL_HOJA, worksheet=worksheet, data=df_actualizado)
    return df_actualizado

# --- INTERFAZ PRINCIPAL ---
st.title("☁️ Plataforma de Análisis Financiero")

df_flujo = cargar_datos_flujo()
df_balance = cargar_datos_balance()

# Estructura de pestañas
tab_dashboard, tab_balance, tab_proyecciones = st.tabs(["📊 Flujo de Efectivo", "⚖️ Balance General", "🔮 Modelado Financiero"])

# ==========================================
# PESTAÑA 1: FLUJO DE EFECTIVO (Ingresos y Gastos)
# ==========================================
with tab_dashboard:
    col_input, col_dash = st.columns([1, 3])
    
    with col_input:
        st.subheader("📝 Registrar Flujo")
        fecha_flujo = st.date_input("Fecha", datetime.now(), key="f_flujo")
        tipo_flujo = st.radio("Tipo", ["Gasto", "Ingreso"], horizontal=True, key="t_flujo")
        
        if tipo_flujo == "Ingreso":
            cat_flujo = st.selectbox("Categoría", ["Nómina", "Inversiones", "Negocio", "Otros"], key="c_flujo")
        else:
            cat_flujo = st.selectbox("Categoría", ["Vivienda", "Alimentos", "Transporte", "Servicios", "Ocio", "Salud", "Educación", "Deuda"], key="c_flujo")
            
        concepto_flujo = st.text_input("Concepto", key="con_flujo")
        monto_flujo = st.number_input("Monto ($)", min_value=0.0, format="%.2f", key="m_flujo")
        
        if st.button("Guardar en Flujo", type="primary", use_container_width=True):
            if monto_flujo > 0:
                with st.spinner('Sincronizando...'):
                    guardar_movimiento(df_flujo, fecha_flujo, concepto_flujo, cat_flujo, tipo_flujo, monto_flujo, "Datos")
                st.success("¡Sincronizado!")
                st.rerun()

    with col_dash:
        if not df_flujo.empty:
            c1, c2, c3 = st.columns(3)
            ingresos_totales = df_flujo[df_flujo['Tipo'] == 'Ingreso']['Monto'].sum()
            gastos_totales = df_flujo[df_flujo['Tipo'] == 'Gasto']['Monto'].sum()
            flujo_caja = ingresos_totales - gastos_totales
            
            c1.metric("Ingresos Históricos", f"${ingresos_totales:,.2f}")
            c2.metric("Gastos Históricos", f"${gastos_totales:,.2f}")
            c3.metric("Flujo de Caja", f"${flujo_caja:,.2f}", delta=float(flujo_caja))
            
            st.subheader("Tendencia de Flujo de Efectivo")
            df_grouped = df_flujo.groupby([df_flujo['Fecha'].dt.to_period('M'), 'Tipo'])['Monto'].sum().unstack(fill_value=0).reset_index()
            if 'Ingreso' not in df_grouped.columns: df_grouped['Ingreso'] = 0.0
            if 'Gasto' not in df_grouped.columns: df_grouped['Gasto'] = 0.0
            df_grouped['Fecha'] = df_grouped['Fecha'].dt.to_timestamp()
            
            fig_trend = px.bar(df_grouped, x='Fecha', y=['Ingreso', 'Gasto'], barmode='group', color_discrete_map={'Ingreso':'#00CC96', 'Gasto':'#EF553B'})
            st.plotly_chart(fig_trend, use_container_width=True)

# ==========================================
# PESTAÑA 2: BALANCE GENERAL (Patrimonio)
# ==========================================
with tab_balance:
    col_in_bal, col_dash_bal = st.columns([1, 3])
    
    with col_in_bal:
        st.subheader("🏦 Registrar Cuenta")
        fecha_bal = st.date_input("Fecha de Valuación", datetime.now(), key="f_bal")
        clasificacion = st.radio("Clasificación", ["Activo (A favor)", "Pasivo (Deuda)"], horizontal=True)
        
        if "Activo" in clasificacion:
            clase = "Activo"
            categoria_bal = st.selectbox("Categoría", ["Efectivo / Banco", "Inversiones", "Bienes Raíces", "Vehículos", "Otros Activos"])
        else:
            clase = "Pasivo"
            categoria_bal = st.selectbox("Categoría", ["Tarjeta de Crédito", "Crédito Automotriz", "Hipoteca", "Préstamo Personal"])
            
        cuenta = st.text_input("Nombre de la Cuenta (Ej. Cuenta Banorte, Casa)")
        monto_bal = st.number_input("Valor Actual ($)", min_value=0.0, format="%.2f", key="m_bal")
        
        if st.button("Actualizar Balance", type="primary", use_container_width=True):
            if monto_bal > 0:
                # Si la cuenta ya existe, se podría programar una actualización, por ahora se registra como un corte histórico
                with st.spinner('Actualizando Balance...'):
                    guardar_movimiento(df_balance, fecha_bal, cuenta, clase, categoria_bal, monto_bal, "Balance")
                st.success("¡Balance Actualizado!")
                st.rerun()
                
    with col_dash_bal:
        if not df_balance.empty:
            # Para el balance, tomamos el último valor registrado de cada cuenta
            df_actual = df_balance.sort_values('Fecha').drop_duplicates(subset=['Cuenta'], keep='last')
            
            total_activos = df_actual[df_actual['Clasificación'] == 'Activo']['Monto'].sum()
            total_pasivos = df_actual[df_actual['Clasificación'] == 'Pasivo']['Monto'].sum()
            patrimonio = total_activos - total_pasivos
            
            cb1, cb2, cb3 = st.columns(3)
            cb1.metric("Total Activos", f"${total_activos:,.2f}")
            cb2.metric("Total Pasivos", f"${total_pasivos:,.2f}", delta_color="inverse")
            cb3.metric("Patrimonio Neto", f"${patrimonio:,.2f}", delta=float(patrimonio))
            
            st.subheader("Estructura Patrimonial (Gráfico de Cascada)")
            
            # Preparar datos para el Waterfall chart
            medidas = ['relative'] * len(df_actual) + ['total']
            valores = []
            textos = []
            
            for index, row in df_actual.iterrows():
                if row['Clasificación'] == 'Activo':
                    valores.append(row['Monto'])
                else:
                    valores.append(-row['Monto'])
                textos.append(row['Cuenta'])
                
            valores.append(patrimonio)
            textos.append("Patrimonio Neto")
            
            fig_waterfall = go.Figure(go.Waterfall(
                name = "Balance", orientation = "v",
                measure = medidas,
                x = textos,
                textposition = "outside",
                text = [f"${v:,.0f}" for v in valores],
                y = valores,
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
                decreasing = {"marker":{"color":"#EF553B"}},
                increasing = {"marker":{"color":"#00CC96"}},
                totals = {"marker":{"color":"#1f77b4"}}
            ))
            fig_waterfall.update_layout(waterfallgap=0.3)
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
            with st.expander("Ver Detalle de Cuentas"):
                st.dataframe(df_actual.sort_values(by=['Clasificación', 'Monto'], ascending=[True, False]), use_container_width=True)
        else:
            st.info("Registra tus cuentas bancarias, propiedades y deudas para calcular tu Patrimonio Neto.")

# ==========================================
# PESTAÑA 3: MODELADO FINANCIERO (Sin cambios)
# ==========================================
with tab_proyecciones:
    st.header("Modelos de Amortización y Deuda")
    col_hipoteca, col_tc = st.columns(2)
    # --- MODELO HIPOTECARIO ---
    with col_hipoteca:
        st.subheader("🏠 Simulador de Hipoteca / Préstamo")
        capital = st.number_input("Capital del Préstamo ($)", value=1000000.0, step=50000.0)
        tasa_anual = st.number_input("Tasa de Interés Anual (%)", value=11.5, step=0.5)
        anios = st.slider("Plazo (Años)", min_value=1, max_value=30, value=20)
        
        if capital > 0 and tasa_anual > 0:
            tasa_mensual = (tasa_anual / 100) / 12
            meses_totales = anios * 12
            cuota_mensual = capital * (tasa_mensual * (1 + tasa_mensual)**meses_totales) / ((1 + tasa_mensual)**meses_totales - 1)
            st.metric("Cuota Mensual Fija", f"${cuota_mensual:,.2f}")
            
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
            fig_hipoteca = px.area(df_amort, x='Mes', y=['Interés', 'Capital'], color_discrete_sequence=['#EF553B', '#00CC96'])
            st.plotly_chart(fig_hipoteca, use_container_width=True)

    # --- MODELO DE TARJETA DE CRÉDITO ---
    with col_tc:
        st.subheader("💳 Proyección de Tarjeta de Crédito")
        deuda_tc = st.number_input("Deuda Actual TDC ($)", value=25000.0, step=1000.0)
        tasa_tc_anual = st.number_input("CAT / Tasa Anual TDC (%)", value=45.0, step=1.0)
        pago_mensual = st.number_input("Pago Mensual Proyectado ($)", value=1500.0, step=100.0)
        
        tasa_tc_mensual = (tasa_tc_anual / 100) / 12
        interes_primer_mes = deuda_tc * tasa_tc_mensual
        
        if pago_mensual <= interes_primer_mes and deuda_tc > 0:
            st.error(f"⚠️ Tu pago mensual debe ser mayor a los intereses generados (${interes_primer_mes:,.2f}).")
        elif deuda_tc > 0:
            saldo_tc = deuda_tc
            meses_tc = 0
            interes_acumulado_tc = 0
            historial_tc = []
            
            while saldo_tc > 0 and meses_tc < 240:
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
                
            st.success(f"Liquidarás la deuda en **{meses_tc} meses**.")
            st.warning(f"Total de intereses pagados: **${interes_acumulado_tc:,.2f}**")
            
            df_tc = pd.DataFrame(historial_tc)
            fig_tc = px.line(df_tc, x='Mes', y='Saldo', markers=True)
            fig_tc.update_traces(line_color='red')
            st.plotly_chart(fig_tc, use_container_width=True)
