# SALARY DATA - ONLINE VERSION - Streamlit
# File ka naam: app.py
import streamlit as st
import sqlite3
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="SALARY DATA", page_icon="💰", layout="wide")

DB = "maj_salary_online.db"

def get_con():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS employees(
        personal_no TEXT PRIMARY KEY,
        name TEXT, father TEXT, designation TEXT, bps TEXT,
        cnic TEXT, dob TEXT, doj TEXT,
        basic REAL, house REAL, convey REAL, medical REAL,
        health_prof REAL, adhoc_2023 REAL, adhoc_2024 REAL,
        adhoc_2026 REAL, differential REAL, differential_2026 REAL,
        gpf REAL, benevolent REAL, group_ins REAL, income_tax REAL
    )""")
    con.commit()
    return con, cur

def to_num(v):
    try:
        s = str(v).replace(",", "").replace(" ", "").strip()
        if s == "" or s == "-" or s.lower() == "none":
            return 0.0
        return float(s)
    except:
        return 0.0

def fmt(v):
    try:
        v = float(str(v).replace(",", "") or 0)
        if v == int(v):
            return "{:,}".format(int(v))
        return "{:,.2f}".format(v)
    except:
        return str(v)

def parse_date(s):
    s = str(s).strip()
    if not s: return None
    for f in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, f).date()
        except:
            continue
    return None

def calc_age(dob_str):
    d = parse_date(dob_str)
    if not d: return "---"
    today = datetime.now().date()
    return str(today.year - d.year - ((today.month, today.day) < (d.month, d.day))) + " Years"

def calc_service(doj_str):
    d = parse_date(doj_str)
    if not d: return "---"
    today = datetime.now().date()
    y = today.year - d.year
    m = today.month - d.month
    dd = today.day - d.day
    if dd < 0: m -= 1
    if m < 0: y -= 1; m += 12
    return f"{y} Years, {m} Months"

def get_gross_net(r):
    # r = dict ya list
    if isinstance(r, dict):
        vals = [abs(to_num(r.get(k, 0))) for k in ["basic","house","convey","medical","health_prof","adhoc_2023","adhoc_2024","adhoc_2026","differential","differential_2026"]]
        deds = [abs(to_num(r.get(k, 0))) for k in ["gpf","benevolent","group_ins","income_tax"]]
    else:
        vals = [abs(to_num(r[i])) for i in range(8, 18)]
        deds = [abs(to_num(r[i])) for i in range(18, 22)]
    gross = sum(vals); deduct = sum(deds)
    return gross, deduct, gross - deduct

def make_pdf(row):
    # row = dict
    gross, deduct, net = get_gross_net(row)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Government of Sindh", ln=True, align="C")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "District Accounts Office Larkana", ln=True, align="C")
    pdf.cell(0, 7, "Monthly Salary Statement", ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Personal Information of Mr {row['name']} s/o {row['father']}", ln=True)
    pdf.cell(0, 6, f"Personal Number: {row['personal_no']}    Designation: {row['designation']}    BPS: {row['bps']}", ln=True)
    pdf.cell(0, 6, f"CNIC: {row['cnic']}", ln=True)
    pdf.cell(0, 6, f"Date of Birth: {row['dob']}    Age: {calc_age(row['dob'])}", ln=True)
    pdf.cell(0, 6, f"Date of Joining: {row['doj']}    Total Service: {calc_service(row['doj'])}", ln=True)
    pdf.ln(3)
    def head(t):
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(220,220,220)
        pdf.cell(0, 7, t, ln=True, fill=True)
        pdf.set_font("Arial", "", 10)
    def line(label, key):
        pdf.cell(120, 6, label, border=1)
        pdf.cell(0, 6, fmt(abs(to_num(row.get(key,0)))), ln=True, border=1, align="R")
    head("Pay and Allowances:")
    line("Basic Pay", "basic"); line("House Rent Allowance", "house"); line("Convey Allowance", "convey")
    line("Medical Allowance", "medical"); line("Health Professional", "health_prof"); line("Adhoc Relief 2023 35%", "adhoc_2023")
    line("Adhoc Relief 2024 30%", "adhoc_2024"); line("Adhoc Relief 2026 7%", "adhoc_2026"); line("Differential Allow", "differential"); line("Differential Allow 2026", "differential_2026")
    head("Deductions - General")
    line("GPF Subscription", "gpf"); line("Benevolent Fund", "benevolent"); line("Group Insurance", "group_ins"); line("Income Tax", "income_tax")
    pdf.ln(2)
    pdf.set_font("Arial", "", 10)
    pdf.cell(120, 7, "Gross Pay", border=1); pdf.cell(0, 7, fmt(gross), ln=True, border=1, align="R")
    pdf.cell(120, 7, "Total Deduction", border=1); pdf.cell(0, 7, fmt(deduct), ln=True, border=1, align="R")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(120, 8, "Net Pay  ( Gross - Deduction )", border=1); pdf.cell(0, 8, fmt(net), ln=True, border=1, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, f"Calculation: {fmt(gross)} - {fmt(deduct)} = {fmt(net)}", ln=True, align="C")
    pdf.ln(3)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 5, "* All amounts are in Pak Rupees - System generated by SALARY DATA", ln=True, align="C")
    pdf.cell(0, 5, "Software Presented By Muzafar Ali Jatoi Contact# 03337322555", ln=True, align="C")
    return bytes(pdf.output())

# ===== SESSION - PASSWORD =====
if "logged" not in st.session_state:
    st.session_state.logged = False
if "password" not in st.session_state:
    st.session_state.password = "1234"
if "show_pass" not in st.session_state:
    st.session_state.show_pass = False

# ===== LOGIN - BARA DIALOG =====
if not st.session_state.logged:
    st.markdown("<h1 style='text-align:center; color:#FFD700; font-size:60px;'>SALARY DATA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>Login Required - Password Lazmi Hai</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Username", value="Muzafar", key="login_user")
        # Show Password wala option
        show = st.checkbox("Show Password - Type karte waqt dikhe", value=st.session_state.show_pass)
        st.session_state.show_pass = show
        pwd = st.text_input("Password", value=st.session_state.password, type="text" if show else "password", key="login_pass")
        if st.button("LOGIN", use_container_width=True, type="primary"):
            if user.strip() == "Muzafar" and pwd.strip() == st.session_state.password:
                st.session_state.logged = True
                st.rerun()
            else:
                st.error(f"Username ya Password ghalat hai! Username: Muzafar, Password: {st.session_state.password}")
        st.markdown("---")
        st.subheader("Change Password")
        old = st.text_input("Old Password", type="password", key="old_p")
        new = st.text_input("New Password", type="password", key="new_p")
        conf = st.text_input("Confirm New Password", type="password", key="conf_p")
        if st.button("SAVE NEW PASSWORD", use_container_width=True):
            if old != st.session_state.password:
                st.error("Old Password ghalat hai!")
            elif len(new.strip()) < 4:
                st.warning("New Password kam se kam 4 letters ka ho!")
            elif new.strip() != conf.strip():
                st.error("New aur Confirm same nahi hai!")
            else:
                st.session_state.password = new.strip()
                st.success(f"Password change ho gaya! Naya Password: {new.strip()}")
        st.markdown("<p style='text-align:center; color:#FFD700; font-size:18px;'><b>Software Presented By Muzafar Ali Jatoi<br>Contact# 03337322555</b></p>", unsafe_allow_html=True)
    st.stop()

# ===== MAIN APP - LOGIN KE BAAD =====
st.markdown("<h1 style='text-align:center; color:#FFD700;'>SALARY DATA</h1>", unsafe_allow_html=True)
if st.button("Logout"):
    st.session_state.logged = False
    st.rerun()

# Sidebar - Shortcut Keys Right Side jaisa
with st.sidebar:
    st.markdown("### SHORTCUT KEYS")
    st.write("F1 jaisa - Yahan Button dabao")
    if st.button("💾 SAVE DATA", use_container_width=True):
        st.session_state.action = "save"
    if st.button("🔍 SEARCH", use_container_width=True):
        st.session_state.action = "search"
    if st.button("📄 DOWNLOAD PDF", use_container_width=True):
        st.session_state.action = "pdf"
    if st.button("🖨️ PRINT (PDF khol ke Ctrl+P)", use_container_width=True):
        st.session_state.action = "pdf"
    if st.button("📊 EXPORT EXCEL", use_container_width=True):
        st.session_state.action = "export"
    if st.button("👥 SHOW ALL DATA", use_container_width=True):
        st.session_state.action = "show_all"
    st.markdown("---")
    st.subheader("Change Password")
    old2 = st.text_input("Old Password", type="password", key="old2")
    new2 = st.text_input("New Password", type="password", key="new2")
    conf2 = st.text_input("Confirm", type="password", key="conf2")
    if st.button("SAVE NEW PASSWORD"):
        if old2 != st.session_state.password:
            st.error("Old ghalat hai!")
        elif new2.strip() != conf2.strip() or len(new2.strip()) < 4:
            st.error("New password sahi nahi hai!")
        else:
            st.session_state.password = new2.strip()
            st.success("Password change ho gaya!")
    st.markdown("**Presented By**<br>Muzafar Ali Jatoi<br>03337322555", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Entry / Save", "👥 All Data Together", "📈 % Increase"])

with tab1:
    con, cur = get_con()
    # Search
    st.subheader("Search")
    c1, c2 = st.columns([3, 1])
    search_id = c1.text_input("Enter ID / Personal No for Search")
    if c2.button("SEARCH & SHOW SLIP"):
        cur.execute("SELECT * FROM employees WHERE personal_no=?", (search_id.strip(),))
        r = cur.fetchone()
        if r:
            cols = ["personal_no","name","father","designation","bps","cnic","dob","doj","basic","house","convey","medical","health_prof","adhoc_2023","adhoc_2024","adhoc_2026","differential","differential_2026","gpf","benevolent","group_ins","income_tax"]
            d = dict(zip(cols, r))
            st.session_state.search_data = d
            st.success(f"Mil gaya! {d['name']}")
        else:
            st.warning("No record found!")
    # Form
    sd = st.session_state.get("search_data", {})
    def val(key, default=""):
        return str(sd.get(key, default)) if sd.get(key, "") != "" else default
    st.subheader("Employee Entry")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        pno = st.text_input("Personal No *", value=val("personal_no"))
        name = st.text_input("Name", value=val("name"))
        father = st.text_input("Father Name", value=val("father"))
        desig = st.text_input("Designation", value=val("designation"))
        bps = st.text_input("BPS", value=val("bps"))
        cnic = st.text_input("CNIC", value=val("cnic"))
        dob = st.text_input("Date of Birth (DD-MM-YYYY)", value=val("dob"), placeholder="15-05-1990")
        doj = st.text_input("Date of Joining (DD-MM-YYYY)", value=val("doj"), placeholder="01-01-2015")
    with col_b:
        basic = st.text_input("Basic Pay", value=fmt(val("basic", "0")) if val("basic") else "")
        house = st.text_input("House Rent", value=fmt(val("house", "0")) if val("house") else "")
        convey = st.text_input("Convey", value=fmt(val("convey", "0")) if val("convey") else "")
        medical = st.text_input("Medical", value=fmt(val("medical", "0")) if val("medical") else "")
        health = st.text_input("Health Prof", value=fmt(val("health_prof", "0")) if val("health_prof") else "")
        adh23 = st.text_input("Adhoc 2023", value=fmt(val("adhoc_2023", "0")) if val("adhoc_2023") else "")
        adh24 = st.text_input("Adhoc 2024", value=fmt(val("adhoc_2024", "0")) if val("adhoc_2024") else "")
        adh26 = st.text_input("Adhoc 2026", value=fmt(val("adhoc_2026", "0")) if val("adhoc_2026") else "")
    with col_c:
        diff = st.text_input("Differential", value=fmt(val("differential", "0")) if val("differential") else "")
        diff26 = st.text_input("Differential 2026", value=fmt(val("differential_2026", "0")) if val("differential_2026") else "")
        gpf = st.text_input("GPF", value=fmt(val("gpf", "0")) if val("gpf") else "")
        benev = st.text_input("Benevolent", value=fmt(val("benevolent", "0")) if val("benevolent") else "")
        group = st.text_input("Group Ins", value=fmt(val("group_ins", "0")) if val("group_ins") else "")
        tax = st.text_input("Income Tax", value=fmt(val("income_tax", "0")) if val("income_tax") else "")
    # Live Calculation
    tmp = {"basic":basic,"house":house,"convey":convey,"medical":medical,"health_prof":health,"adhoc_2023":adh23,"adhoc_2024":adh24,"adhoc_2026":adh26,"differential":diff,"differential_2026":diff26,"gpf":gpf,"benevolent":benev,"group_ins":group,"income_tax":tax}
    gross, deduct, net = get_gross_net(tmp)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Pay", fmt(gross))
    c2.metric("Total Deduction", fmt(deduct))
    c3.metric("Net Pay", fmt(net))
    c4.metric("Age / Service", f"{calc_age(dob)} / {calc_service(doj)}")
    st.info(f"Calculation: {fmt(gross)} - {fmt(deduct)} = {fmt(net)}")
    if st.button("💾 SAVE / UPDATE DATA", type="primary", use_container_width=True):
        if not pno.strip():
            st.error("Personal Number is Required!")
        else:
            vals = (pno.strip(), name, father, desig, bps, cnic, dob, doj,
                    abs(to_num(basic)), abs(to_num(house)), abs(to_num(convey)),
                    abs(to_num(medical)), abs(to_num(health)), abs(to_num(adh23)),
                    abs(to_num(adh24)), abs(to_num(adh26)), abs(to_num(diff)),
                    abs(to_num(diff26)), abs(to_num(gpf)), abs(to_num(benev)),
                    abs(to_num(group)), abs(to_num(tax)))
            cur.execute("REPLACE INTO employees VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", vals)
            con.commit()
            st.success(f"Data Saved! Gross: {fmt(gross)} | Deduction: {fmt(deduct)} | Net Pay: {fmt(net)}")
            st.session_state.search_data = {}
    # Slip + PDF
    if sd:
        st.markdown("---")
        st.subheader(f"Salary Slip - {sd.get('name','')}")
        st.write(f"**Name:** {sd.get('name')} | **Father:** {sd.get('father')} | **Designation:** {sd.get('designation')} | **BPS:** {sd.get('bps')}")
        st.write(f"**CNIC:** {sd.get('cnic')} | **DOB:** {sd.get('dob')} | **Age:** {calc_age(sd.get('dob',''))} | **Joining:** {sd.get('doj')} | **Service:** {calc_service(sd.get('doj',''))}")
        g2, d2, n2 = get_gross_net(sd)
        st.write(f"**Gross:** {fmt(g2)} | **Deduction:** {fmt(d2)} | **Net Pay:** {fmt(n2)}")
        pdf_bytes = make_pdf(sd)
        st.download_button("📄 DOWNLOAD PDF SLIP", data=pdf_bytes, file_name=f"Slip_{sd.get('personal_no')}_{sd.get('name')}.pdf", mime="application/pdf", use_container_width=True)
        st.write("Print ke liye PDF download karo, khol ke Ctrl+P dabao!")

with tab2:
    con, cur = get_con()
    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()
    if not rows:
        st.warning("Koi data nahi hai! Pehle SAVE karo!")
    else:
        cols = ["personal_no","name","father","designation","bps","cnic","dob","doj","basic","house","convey","medical","health_prof","adhoc_2023","adhoc_2024","adhoc_2026","differential","differential_2026","gpf","benevolent","group_ins","income_tax"]
        data = []
        for r in rows:
            d = dict(zip(cols, r))
            g, dd, n = get_gross_net(d)
            data.append({"Personal No": d["personal_no"], "Name": d["name"], "BPS": d["bps"], "CNIC": d["cnic"], "DOB": d["dob"], "Age": calc_age(d["dob"]), "Joining": d["doj"], "Gross": g, "Deduction": dd, "Net Pay": n})
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.write(f"Total Employees: {len(df)} | Total Gross: {fmt(df['Gross'].sum())} | Total Deduction: {fmt(df['Deduction'].sum())} | Total Net: {fmt(df['Net Pay'].sum())}")
        # Export CSV
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("📊 EXPORT EXCEL / CSV", data=csv_bytes, file_name="SALARY_DATA.csv", mime="text/csv", use_container_width=True)
        # All PDF
        if st.button("📄 DOWNLOAD ALL PDF - Sab Ka Ek Sath"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 8, "SALARY DATA - All Employees Report", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, "Government of Sindh - District Accounts Office Larkana", ln=True, align="C")
            pdf.cell(0, 6, f"Total Employees: {len(df)}", ln=True, align="C")
            pdf.ln(4)
            pdf.set_font("Arial", "B", 8)
            pdf.set_fill_color(255,215,0)
            for w, t in [(22,"Pers No"),(32,"Name"),(12,"BPS"),(28,"CNIC"),(25,"Gross"),(25,"Deduction"),(25,"Net")]:
                pdf.cell(w, 7, t, border=1, fill=True)
            pdf.ln()
            pdf.set_font("Arial", "", 8)
            for _, row2 in df.iterrows():
                pdf.cell(22, 6, str(row2["Personal No"]), border=1)
                pdf.cell(32, 6, str(row2["Name"])[:20], border=1)
                pdf.cell(12, 6, str(row2["BPS"]), border=1)
                pdf.cell(28, 6, str(row2["CNIC"]), border=1)
                pdf.cell(25, 6, fmt(row2["Gross"]), border=1, align="R")
                pdf.cell(25, 6, fmt(row2["Deduction"]), border=1, align="R")
                pdf.cell(25, 6, fmt(row2["Net Pay"]), border=1, align="R", ln=True)
            pdf.ln(4)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, f"Total Gross: {fmt(df['Gross'].sum())}  Net: {fmt(df['Net Pay'].sum())}", ln=True, align="C")
            pdf.set_font("Arial", "I", 8)
            pdf.cell(0, 5, "Software Presented By Muzafar Ali Jatoi Contact# 03337322555", ln=True, align="C")
            st.download_button("Download All PDF", data=bytes(pdf.output()), file_name="SALARY_DATA_ALL_EMPLOYEES.pdf", mime="application/pdf")

with tab3:
    st.subheader("Salary % Increase")
    inc_pno = st.text_input("Personal No (or ALL likho)", value="ALL")
    perc = st.text_input("Enter %", value="10")
    mode = st.radio("Mode", ["Basic Only", "Basic + Allowances"])
    if st.button("APPLY INCREASE", type="primary"):
        con, cur = get_con()
        p = to_num(perc)
        if p == 0:
            st.error("Percentage likho!")
        else:
            if inc_pno.strip().lower() == "all" or inc_pno.strip() == "":
                cur.execute("SELECT * FROM employees")
                rows = cur.fetchall()
            else:
                cur.execute("SELECT * FROM employees WHERE personal_no=?", (inc_pno.strip(),))
                rows = cur.fetchall()
            if not rows:
                st.warning("No record found!")
            else:
                for r in rows:
                    cols2 = ["personal_no","name","father","designation","bps","cnic","dob","doj","basic","house","convey","medical","health_prof","adhoc_2023","adhoc_2024","adhoc_2026","differential","differential_2026","gpf","benevolent","group_ins","income_tax"]
                    d = dict(zip(cols2, r))
                    new_basic = abs(to_num(d["basic"])) * (1 + p/100)
                    if mode == "Basic Only":
                        cur.execute("UPDATE employees SET basic=? WHERE personal_no=?", (round(new_basic,2), r[0]))
                    else:
                        new_vals = [round(abs(to_num(d[k])) * (1 + p/100), 2) for k in ["house","convey","medical","health_prof","adhoc_2023","adhoc_2024","adhoc_2026","differential","differential_2026"]]
                        cur.execute("UPDATE employees SET basic=?, house=?, convey=?, medical=?, health_prof=?, adhoc_2023=?, adhoc_2024=?, adhoc_2026=?, differential=?, differential_2026=? WHERE personal_no=?", (round(new_basic,2), *new_vals, r[0]))
                con.commit()
                st.success(f"{len(rows)} employee(s) increased by {p}%")

# Footer - Bilkul neeche Right Corner
st.markdown("---")
st.markdown("<p style='text-align:right; color:#FFD700; font-size:16px; font-weight:bold;'>Software Presented By Muzafar Ali Jatoi &nbsp; Contact# 03337322555</p>", unsafe_allow_html=True)
