"""Generate precise SVG and editable diagrams.net XML from one layout."""
from pathlib import Path
from html import escape
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def build(name):
    is_signal=name=='signalledger'
    title='SignalLedger' if is_signal else 'ContractForge'
    accent='#14745f' if is_signal else '#a55b32'
    pale='#eef7f0' if is_signal else '#fbf3e9'
    ink='#172f32';muted='#637b7c';line='#d9e4e3';ai='#b37733'
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1160" viewBox="0 0 1600 1160" role="img" aria-label="{title} layered implementation architecture">',
         '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#47676b"/></marker><marker id="ai-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#b37733"/></marker></defs>',
         '<rect width="1600" height="1160" fill="#f8faf9"/>']
    mx=ET.Element('mxfile',host='app.diagrams.net',version='24.7.17')
    dia=ET.SubElement(mx,'diagram',id=name,name='Implementation architecture')
    model=ET.SubElement(dia,'mxGraphModel',dx='1600',dy='1160',grid='1',gridSize='10',page='1',pageWidth='1600',pageHeight='1160')
    root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    counter=0
    node_boxes=[]
    def xml_node(x,y,w,h,label,style):
        nonlocal counter
        counter+=1;id=f'n{counter}'
        cell=ET.SubElement(root,'mxCell',id=id,value=label,style=style,vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
        return id
    def text(x,y,words,size=14,fill=ink,weight=400):
        svg.append(f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(words)}</text>')
    def label(x,y,words,size=14,fill=ink,weight=400,w=850):
        text(x,y,words,size,fill,weight)
        xml_node(x,y-size,w,size+10,words,f'text;html=0;align=left;verticalAlign=middle;fontSize={size};fontColor={fill};fontStyle={1 if weight>=600 else 0};strokeColor=none;fillColor=none;')
    def rect(x,y,w,h,fill,stroke=line,rx=12,dashed=False):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"'+(' stroke-dasharray="7 6"' if dashed else '')+'/>')
    def group(x,y,w,h,title,fill='#fff',dashed=False):
        rect(x,y,w,h,fill,line,14,dashed)
        xml_node(x,y,w,h,'',f'rounded=1;arcSize=5;fillColor={fill};strokeColor={line};dashed={int(dashed)};')
        label(x+20,y+30,title,11,muted,700,w-30)
    def node(x,y,w,h,title,lines,kind='component',color=accent):
        if kind=='store':
            svg.append(f'<path d="M{x} {y+15} A{w/2} 15 0 0 1 {x+w} {y+15} V{y+h-15} A{w/2} 15 0 0 1 {x} {y+h-15} Z" fill="white" stroke="{line}" stroke-width="1.5"/>')
            svg.append(f'<ellipse cx="{x+w/2}" cy="{y+15}" rx="{w/2}" ry="15" fill="{pale}" stroke="{line}" stroke-width="1.5"/>')
        else:
            rect(x,y,w,h,'#fff',line,9)
            svg.append(f'<rect x="{x}" y="{y+12}" width="4" height="{h-24}" rx="2" fill="{color}"/>')
        title_y=y+43 if kind=='store' else y+27
        text(x+17,title_y,title,15,ink,700)
        for i,l in enumerate(lines):text(x+17,title_y+25+i*19,l,11,muted)
        node_id=xml_node(x,y,w,h,title+'\n\n'+'\n'.join(lines),f'{"shape=cylinder3;boundedLbl=1;" if kind=="store" else "rounded=1;arcSize=10;"}whiteSpace=wrap;html=0;fillColor=#ffffff;strokeColor={color};fontColor={ink};fontSize=13;align=left;spacingLeft=15;verticalAlign=middle;')
        node_boxes.append((x,y,w,h,node_id))
    def edge(points,label_text='',lx=None,ly=None,optional=False):
        color=ai if optional else '#47676b'
        path='M'+' L'.join(f'{x} {y}' for x,y in points)
        svg.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.8" marker-end="url(#{"ai-arrow" if optional else "arrow"})"'+(' stroke-dasharray="6 5"' if optional else '')+'/>')
        nonlocal counter
        counter+=1
        cell=ET.SubElement(root,'mxCell',id=f'e{counter}',value='',style=f'edgeStyle=orthogonalEdgeStyle;rounded=1;endArrow=block;strokeColor={color};dashed={int(optional)};',edge='1',parent='1')
        for endpoint,attr,prefix in [(points[0],'source','exit'),(points[-1],'target','entry')]:
            px,py=endpoint
            for nx,ny,nw,nh,node_id in node_boxes:
                if nx<=px<=nx+nw and ny<=py<=ny+nh and (px in (nx,nx+nw) or py in (ny,ny+nh)):
                    cell.set(attr,node_id)
                    cell.set('style',cell.get('style')+f'{prefix}X={(px-nx)/nw};{prefix}Y={(py-ny)/nh};{prefix}Dx=0;{prefix}Dy=0;')
                    break
        geo=ET.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})
        ET.SubElement(geo,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),attrib={'as':'sourcePoint'})
        ET.SubElement(geo,'mxPoint',x=str(points[-1][0]),y=str(points[-1][1]),attrib={'as':'targetPoint'})
        if len(points)>2:
            arr=ET.SubElement(geo,'Array',attrib={'as':'points'})
            for x,y in points[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
        if label_text:
            width=len(label_text)*5.8+12
            svg.append(f'<rect x="{lx-5}" y="{ly-12}" width="{width}" height="17" fill="#f8faf9" rx="3"/>')
            label(lx,ly,label_text,10,color,400,width)

    label(44,57,title+' / System architecture',34,ink,700)
    label(45,87,'Implementation view  •  v0.1.0  •  Python / FastAPI / SQLite / local Ollama',14,muted)
    label(45,119,'A reproducible local system with explicit data, model and persistence boundaries.',13,muted)
    edge([(1080,52),(1130,52)])
    label(1140,57,'Deterministic path',11,muted,w=180)
    edge([(1080,85),(1130,85)],optional=True)
    label(1140,90,'Optional model call',11,muted,w=180)
    label(1380,57,'DESIGNED BY',9,muted,700,w=170)
    label(1380,78,'Yaswanth Adari',13,ink,700,w=180)

    group(40,160,260,850,'01  INPUT BOUNDARY', '#f0f5f3')
    group(338,160,910,850,'02  LOCAL APPLICATION / ONE FASTAPI PROCESS')
    group(1280,160,280,425,'03  MODEL PROCESS', '#fbf6eb',True)
    group(1280,627,280,383,'04  FUTURE DEPLOYMENT', '#f4f5f5',True)
    group(358,220,870,170,'TRANSPORT + VALIDATION', '#f5f8fa')
    group(358,440,870,227,'DOMAIN LOGIC / PURE FUNCTIONS',pale)
    group(358,731,870,249,'PERSISTENCE + PRESENTATION','#f5f6fa')

    node(61,258,218,111,'Browser workbench',['Scenario selection','Custom JSON + run history','Download report JSON'])
    node(61,435,218,111,'Versioned input',['Lineage + measurements' if is_signal else 'Source + target contracts','Logs + changes + runbooks' if is_signal else 'Event replay batch','Typed JSON over HTTP'])
    node(61,636,218,112,'Synthetic fixtures',['Three reproducible cases','No employer data','No API key for default mode'])
    label(62,815,'Trust boundary',13,ink,700,w=215)
    for i,line_text in enumerate(['Inputs are untrusted data.','2 MiB request budget.','Localhost binding by default.','Optional bearer-token guard.']):label(62,844+i*23,line_text,11,muted,w=215)

    node(384,260,232,97,'FastAPI routes',['POST /api/investigations' if is_signal else 'POST /api/replays','Same-origin UI + JSON API'])
    node(665,260,232,97,'Pydantic contracts',['Unique IDs + acyclic DAG' if is_signal else 'Field types + bounded DSL','422 on invalid input'])
    node(946,260,256,97,'Run coordinator',['Idempotency key + SHA-256','Cache hit or execute analysis'])
    if is_signal:
        node(384,483,232,144,'Lineage + anomalies',['Ancestor / descendant traversal','Median + MAD deviation','Rank supported hypotheses','engine.py / investigate'])
        node(665,483,232,144,'Evidence retrieval',['BM25 over supplied runbooks','Relevant signals + changes','Healthy negative controls','Evidence IDs remain visible'])
        node(946,483,256,144,'AI response gate',['Pydantic response schema','Known candidate + citation IDs','Reject unsupported references','Fallback to evidence engine'],color=ai)
    else:
        node(384,483,232,144,'Contract planner',['Diff aliases / types / units','Propose bounded operations','rename / cast / scale only','engine.py / propose'])
        node(665,483,232,144,'Counterexample replay',['Deep-copy each source event','Validate target contract','Check semantic value invariants','Retain original on rejection'])
        node(946,483,256,144,'AI plan gate',['Validate operation union','Declared aliases + units only','Replay every accepted AI plan','Fallback to rule-based plan'],color=ai)
    node(1300,256,240,130,'Local Ollama',['POST /api/chat','JSON schema / stream: false','Temperature 0 / 1,600 tokens','3s connect / 60s inactivity'],color=ai)
    label(1300,426,'AI is advisory.',14,ai,700,w=230)
    for i,line_text in enumerate(['No shell, SQL, or tool execution.','Provider response ≤ 128 KiB.','Schema validity is not truth.','No model installed by the app.']):label(1300,454+i*23,line_text,11,muted,w=235)

    node(384,801,232,112,'Workbench + export',['Cited hypothesis + timeline' if is_signal else 'Pass / block + counterexamples','GET saved run by ID','JSON download from browser'])
    node(665,790,232,139,'SQLite / WAL',['reports table','Unique idempotency key','BEGIN IMMEDIATE / 15s wait','Immutable through app API'],kind='store')
    node(946,801,256,112,'Run record',['Facts + validated explanation' if is_signal else 'Plan + all replay outcomes','UUID / UTC time / input hash','No autonomous remediation' if is_signal else 'No deployment side effects'])

    edge([(279,306),(384,306)],'HTTP JSON',309,293)
    edge([(279,485),(318,485),(318,329),(384,329)])
    edge([(279,691),(318,691),(318,350),(384,350)])
    edge([(616,306),(665,306)])
    edge([(897,306),(946,306)])
    edge([(1074,357),(1074,414),(500,414),(500,483)],'validated request',712,415)
    edge([(616,552),(665,552)])
    if is_signal:
        edge([(897,540),(946,540)],optional=True)
        edge([(782,627),(782,700),(1074,700),(1074,801)],'deterministic findings',832,700)
        edge([(1202,523),(1263,523),(1263,304),(1300,304)],optional=True)
        edge([(1300,350),(1259,350),(1259,577),(1202,577)],optional=True)
        edge([(1135,627),(1135,801)],'validated AI',1139,711,True)
    else:
        edge([(560,483),(560,474),(1090,474),(1090,483)],'optional proposal request',700,464,True)
        edge([(1202,523),(1263,523),(1263,304),(1300,304)],optional=True)
        edge([(1300,350),(1259,350),(1259,577),(1202,577)],optional=True)
        edge([(946,580),(897,580)],optional=True)
        edge([(782,627),(782,700),(1074,700),(1074,801)],'validated replay outcomes',832,700)
    edge([(946,857),(897,857)])
    edge([(665,857),(616,857)])
    label(386,954,'Persistence is atomic. Concurrent retries can still duplicate model computation.',11,muted,w=810)
    label(1300,685,'Not implemented in v0.1',13,muted,700,w=240)
    future=['Managed OIDC / multi-tenancy','Durable queue + worker pool','PostgreSQL + object storage','Live pipeline connectors' if is_signal else 'Schema registry / broker I/O','OpenTelemetry / load testing']
    for i,l in enumerate(future):
        rect(1300,711+i*44,239,33,'#fff',line,5,True)
        label(1311,732+i*44,l,11,muted,w=221)
    label(1300,969,'Roadmap only; no live wiring.',11,muted,w=235)
    rect(40,1035,1520,87,'#173632','#173632',12)
    label(64,1065,'DESIGN INVARIANTS',11,'#b1d5c9',700,w=210)
    invariants=['Evidence is preserved','AI failure degrades gracefully','Rankings are hypotheses, not causal proof'] if is_signal else ['No generated code execution','No silent lossy casts','A passing sample does not prove universal safety']
    for i,t in enumerate(invariants):label(300+i*405,1084,t,13,'#eef7f3',600,w=460)
    svg.append('</svg>')
    out=ROOT/'docs/assets';out.mkdir(parents=True,exist_ok=True)
    (out/'layers.svg').write_text('\n'.join(svg))
    ET.indent(mx)
    (out/'layers.drawio').write_text(ET.tostring(mx,encoding='unicode'))

if __name__=='__main__':
    build('signalledger')
