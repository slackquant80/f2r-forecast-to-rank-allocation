from __future__ import annotations
import io, math, zipfile
from xml.sax.saxutils import escape
import pandas as pd

F2R_UNIVERSE=["SPY","QQQ","IWM","EFA","EEM","VNQ","DBC","IEF","TLT","EWY","GLD"]
STATUS_ORDER={"HISTORY":0,"OFFICIAL":1,"PREVIEW":2}

def _book(holdings:list[dict], label:str)->dict[str,float]:
    b={a:0.0 for a in F2R_UNIVERSE}
    for r in holdings or []:
        a=str(r.get("asset") or r.get("asset_id") or "").strip()
        if not a: continue
        if a not in b: raise RuntimeError(f"{label}: asset outside F2R universe: {a}")
        w=float(r.get("target_weight") or r.get("weight") or 0.0)
        if not math.isfinite(w) or w < -1e-12: raise RuntimeError(f"{label}: invalid weight {a}={w}")
        b[a]+=w
    if abs(sum(b.values())-1.0)>1e-8: raise RuntimeError(f"{label}: weights do not sum to one: {sum(b.values())}")
    return b

def build_portfolio_history(allocation_history:pd.DataFrame, official:dict, preview:dict)->pd.DataFrame:
    rows=[]
    if allocation_history is not None and not allocation_history.empty:
        for p,g in allocation_history.groupby("signal_month",sort=True):
            book={a:0.0 for a in F2R_UNIVERSE}
            for _,r in g.iterrows():
                a=str(r["asset_id"]); w=float(r["target_weight"])
                if a not in book: raise RuntimeError(f"history {p}: asset outside F2R universe: {a}")
                book[a]+=w
            if abs(sum(book.values())-1.0)>1e-8: raise RuntimeError(f"history {p}: weights do not sum to one")
            holding=str(g.iloc[0].get("holding_month") or "")
            rows.append({"Status":"HISTORY","Signal Month":str(p),"Holding Month":holding,**book})
    op=str(official.get("signal_period") or "")
    if op:
        rows=[r for r in rows if r["Signal Month"]!=op]
        rows.append({"Status":"OFFICIAL","Signal Month":op,"Holding Month":str(official.get("holding_month") or ""),**_book(official.get("holdings",[]),f"Official {op}")})
    if bool(preview.get("available")):
        pp=str(preview.get("signal_period") or "")
        rows=[r for r in rows if r["Signal Month"]!=pp]
        rows.append({"Status":"PREVIEW","Signal Month":pp,"Holding Month":str(preview.get("prospective_holding_month") or ""),**_book(preview.get("holdings",[]),f"Preview {pp}")})
    rows=sorted(rows,key=lambda r:(r["Signal Month"],STATUS_ORDER.get(r["Status"],0)),reverse=True)
    return pd.DataFrame(rows,columns=["Status","Signal Month","Holding Month",*F2R_UNIVERSE])

def display_percent(df:pd.DataFrame)->pd.DataFrame:
    out=df.copy()
    out["Status"]=out["Status"].map(lambda x:"PREVIEW · PROVISIONAL" if str(x)=="PREVIEW" else str(x))
    for a in F2R_UNIVERSE:
        out[a]=out[a].map(lambda x:f"{100*float(x):.1f}%")
    return out

def _col(n:int)->str:
    s=""
    while n:
        n,r=divmod(n-1,26); s=chr(65+r)+s
    return s

def _sheet_xml(rows:list[list],pct_cols:set[int],widths:list[float],freeze_cols:int=3)->str:
    rr=[]
    for ri,row in enumerate(rows,1):
        cells=[]
        for ci,val in enumerate(row,1):
            ref=f"{_col(ci)}{ri}"
            if ri>1 and ci in pct_cols:
                cells.append(f'<c r="{ref}" s="1"><v>{float(val):.16g}</v></c>')
            else:
                st=' s="2"' if ri==1 else ''
                cells.append(f'<c r="{ref}"{st} t="inlineStr"><is><t>{escape("" if val is None else str(val))}</t></is></c>')
        rr.append(f'<row r="{ri}">{"".join(cells)}</row>')
    cols='<cols>'+''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i,w in enumerate(widths,1))+'</cols>'
    pane=f'<pane xSplit="{freeze_cols}" ySplit="1" topLeftCell="{_col(freeze_cols+1)}2" activePane="bottomRight" state="frozen"/>'
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0">'+pane+'</sheetView></sheetViews>'+cols+'<sheetData>'+''.join(rr)+'</sheetData></worksheet>'

def portfolio_history_xlsx_bytes(df:pd.DataFrame)->bytes:
    cols=["Status","Signal Month","Holding Month",*F2R_UNIVERSE]
    data=[cols]+[[r[c] for c in cols] for _,r in df.iterrows()]
    meta=[["Field","Value"],["Definition","F2R fixed 11-ETF target history"],["Preview","PREVIEW is provisional, appears at the top when active, and is excluded from realized performance"],["Official","Current Official is included for direct operational spreadsheet use"],["Universe order",", ".join(F2R_UNIVERSE)]]
    content='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'''
    rels='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    wb='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Portfolio History" sheetId="1" r:id="rId1"/><sheet name="Metadata" sheetId="2" r:id="rId2"/></sheets></workbook>'''
    wbr='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    styles='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><numFmts count="1"><numFmt numFmtId="164" formatCode="0.0%"/></numFmts><fonts count="2"><font><sz val="10"/><name val="Aptos"/><family val="2"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Aptos"/><family val="2"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF334155"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content); z.writestr('_rels/.rels',rels); z.writestr('xl/workbook.xml',wb); z.writestr('xl/_rels/workbook.xml.rels',wbr); z.writestr('xl/styles.xml',styles)
        z.writestr('xl/worksheets/sheet1.xml',_sheet_xml(data,set(range(4,15)),[11,12,12]+[9]*11))
        z.writestr('xl/worksheets/sheet2.xml',_sheet_xml(meta,set(),[24,88],1))
    return bio.getvalue()
