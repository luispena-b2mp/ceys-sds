import csv, os, re, urllib.parse, glob

def unique(seq):
    out=[]
    seen=set()
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def section(text, start_pat, end_pat):
    m=re.search(start_pat,text,re.I)
    if not m:
        return ""
    start=m.start()
    tail=text[start:]
    e=re.search(end_pat,tail,re.I)
    return tail[:e.start()] if e else tail[:7000]

def classes_from_hcodes(hcodes):
    out=[]
    def add(x):
        if x not in out: out.append(x)
    for h in hcodes:
        if h.startswith("EUH"): 
            continue
        try:
            n=int(re.sub(r"\D","",h)[:3])
        except:
            continue
        if h in {"H200","H201","H202","H203","H204","H205"}: add("Explosivo")
        if h in {"H220","H221","H222","H223","H224","H225","H226","H228","H229"}: add("Inflamable")
        if h in {"H270","H271","H272"}: add("Oxidante")
        if h in {"H280","H281"}: add("Gas comprimido")
        if h in {"H290","H314","H318"}: add("Corrosivo")
        if h in {"H302","H312","H315","H317","H319","H332","H335","H336"}: add("Irritante")
        if h in {"H300","H301","H310","H311","H330","H331"}: add("Tóxico")
        if h in {"H304","H334","H340","H341","H350","H351","H360","H360F","H360D","H360FD","H361","H361F","H361D","H362","H370","H371","H372","H373"}:
            add("Peligroso para la salud")
        if h in {"H400","H410","H411","H412","H413"}: add("Perjudicial para el medio ambiente")
    return out[:5]

pdf_by_sku={}
for p in glob.glob("*.pdf"):
    base=os.path.basename(p)
    if "_FDS_" not in base.upper():
        continue
    m=re.match(r"(\d+)",base)
    if m:
        pdf_by_sku[m.group(1)]=base

rows=[]
for path in sorted(glob.glob("extracted_text/*_FDS_*.txt")):
    name=os.path.basename(path)
    m=re.match(r"(\d+)",name)
    if not m: 
        continue
    sku=m.group(1)
    text=open(path,encoding="utf-8",errors="ignore").read()
    sec2=section(text,r"SECCI[ÓO]N\s*2|2\.\s*Identificaci[oó]n de los peligros",r"SECCI[ÓO]N\s*3|3\.\s*Composici")
    sec14=section(text,r"SECCI[ÓO]N\s*14|14\.\s*Informaci[oó]n relativa al transporte",r"SECCI[ÓO]N\s*15|15\.\s*Informaci[oó]n reglamentaria")
    hcodes=unique(re.findall(r"\b(?:EUH|H)\d{3}[A-Z]?\b",sec2))
    unnums=unique(["UN"+x for x in re.findall(r"\b(?:UN|ONU)\s?(\d{4})\b",sec14,re.I)])
    h_non_euh=[h for h in hcodes if not h.startswith("EUH")]
    regs=[]
    if h_non_euh: regs.append("SGA")
    if unnums: regs.append("Transporte")
    if not regs: regs=["No aplicable"]
    classes=classes_from_hcodes(hcodes)
    pdf=pdf_by_sku.get(sku,"")
    raw=""
    if pdf:
        raw="https://raw.githubusercontent.com/luispena-b2mp/ceys-sds/main/"+urllib.parse.quote(pdf,safe="")
    rows.append({
        "SKU":sku,
        "REG1":regs[0] if len(regs)>0 else "",
        "REG2":regs[1] if len(regs)>1 else "",
        "REG3":"",
        "REG4":"",
        "REG5":"",
        "GHS1":classes[0] if len(classes)>0 else "",
        "GHS2":classes[1] if len(classes)>1 else "",
        "GHS3":classes[2] if len(classes)>2 else "",
        "GHS4":classes[3] if len(classes)>3 else "",
        "GHS5":classes[4] if len(classes)>4 else "",
        "HAZMAT_ASPECT":"ID de regulación de la ONU" if unnums else "",
        "HAZMAT_VALUE":unnums[0] if unnums else "",
        "SDS_URL":raw,
        "H1":hcodes[0] if len(hcodes)>0 else "",
        "H2":hcodes[1] if len(hcodes)>1 else "",
        "H3":hcodes[2] if len(hcodes)>2 else "",
        "H4":hcodes[3] if len(hcodes)>3 else "",
        "H5":hcodes[4] if len(hcodes)>4 else "",
    })

fields=["SKU","REG1","REG2","REG3","REG4","REG5","GHS1","GHS2","GHS3","GHS4","GHS5","HAZMAT_ASPECT","HAZMAT_VALUE","SDS_URL","H1","H2","H3","H4","H5"]
with open("COMPLIANCE_EXTRACT.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {len(rows)} rows")
