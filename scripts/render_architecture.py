"""Icon-based architecture drawings matching the supplied visual reference."""
from pathlib import Path
import base64
import xml.etree.ElementTree as ET
from html import escape

ROOT=Path(__file__).resolve().parents[1]

class Drawing:
    def __init__(self, directory, title, width=1600, height=1150):
        self.directory=directory;self.width=width;self.height=height
        self.layers=[[],[],[]];self.ids={};self.count=0
        self.xml=ET.Element('mxfile',host='app.diagrams.net',version='24.7.17')
        d=ET.SubElement(self.xml,'diagram',name=title,id=title.lower().replace(' ','-'))
        g=ET.SubElement(d,'mxGraphModel',grid='1',gridSize='10',page='1',pageWidth=str(width),pageHeight=str(height))
        self.root=ET.SubElement(g,'root');ET.SubElement(self.root,'mxCell',id='0');ET.SubElement(self.root,'mxCell',id='1',parent='0')

    def cell(self,x,y,w,h,value,style,parent='1'):
        self.count+=1;id='n'+str(self.count)
        c=ET.SubElement(self.root,'mxCell',id=id,value=value,style=style,vertex='1',parent=parent)
        ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
        return id

    def text(self,x,y,label,size=15,color='#17202b',weight=400,align='start',layer=2,xml=True):
        self.layers[layer].append(f'<text x="{x}" y="{y}" text-anchor="{align}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(label)}</text>')
        if xml:
            w=max(70,len(label)*size*.65)
            self.cell(x-w/2 if align=='middle' else x,y-size,w,size+8,label,
                      f'text;html=0;align={"center" if align=="middle" else "left"};fontSize={size};fontColor={color};fontStyle={int(weight>=600)};strokeColor=none;fillColor=none;')

    def boundary(self,x,y,w,h,label,color='#596578',fill='#ffffff',dashed=False):
        dash=' stroke-dasharray="8 5"' if dashed else ''
        self.layers[0].append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{color}" stroke-width="1.2"{dash}/>')
        self.cell(x,y,w,h,'',f'rounded=0;fillColor={fill};strokeColor={color};dashed={int(dashed)};')
        self.text(x+15,y+25,label,15,color,700,layer=0)

    def node(self,key,cx,y,icon,labels,kind=None):
        # The invisible parent groups each icon with its labels for editing.
        width=230;height=144;x=cx-width/2
        group=self.cell(x,y,width,height,'','group;strokeColor=none;fillColor=none;')
        self.ids[key]=(group,x,y,width,height)
        if kind=='db':
            self.layers[2].append(f'<path d="M{cx-42} {y+17} A42 14 0 0 1 {cx+42} {y+17} V{y+70} A42 14 0 0 1 {cx-42} {y+70} Z" fill="#f3f6f7" stroke="#344b60" stroke-width="2"/><ellipse cx="{cx}" cy="{y+17}" rx="42" ry="14" fill="#e9eff4" stroke="#344b60" stroke-width="2"/>')
            self.cell(width/2-42,0,84,84,'','shape=cylinder3;boundedLbl=1;fillColor=#f3f6f7;strokeColor=#344b60;',group)
        elif kind in {'json','model'}:
            fill='#f0f4f8' if kind=='json' else '#f5f0fc';stroke='#506479' if kind=='json' else '#8667b8'
            self.layers[2].append(f'<rect x="{cx-42}" y="{y}" width="84" height="84" rx="{8 if kind=="json" else 42}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            self.text(cx,y+51,'{ }' if kind=='json' else 'AI',30,stroke,700,'middle',xml=False)
            self.cell(width/2-42,0,84,84,'{ }' if kind=='json' else 'AI',f'{"rounded=1" if kind=="json" else "ellipse"};fillColor={fill};strokeColor={stroke};fontSize=30;fontColor={stroke};fontStyle=1;',group)
        else:
            content=base64.b64encode((self.directory/'icons'/f'{icon}.png').read_bytes()).decode()
            self.layers[2].append(f'<image x="{cx-42}" y="{y}" width="84" height="84" href="data:image/png;base64,{content}"/>')
            self.cell(width/2-42,0,84,84,'',f'shape=image;imageAspect=0;aspect=fixed;image=data:image/png,{content};',group)
        for i,line in enumerate(labels):
            self.text(cx,y+107+i*20,line,15 if i==0 else 13,'#17202b' if i==0 else '#526071',700 if i==0 else 400,'middle',xml=False)
            self.cell(0,88+i*20,width,25,line,f'text;html=0;align=center;fontSize={15 if i==0 else 13};fontStyle={1 if i==0 else 0};fontColor={"#17202b" if i==0 else "#526071"};strokeColor=none;fillColor=none;',group)

    def edge(self,source,target,points,label='',label_at=None,dashed=False,both=False):
        color='#65768a' if dashed else '#252e39'
        path='M'+' L'.join(f'{x} {y}' for x,y in points)
        attrs=(' stroke-dasharray="6 5"' if dashed else '')+(' marker-start="url(#back)"' if both else '')
        self.layers[1].append(f'<path d="{path}" stroke="{color}" stroke-width="1.4" fill="none" marker-end="url(#arrow)"{attrs}/>')
        self.count+=1
        style=f'edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;endFill=1;strokeColor={color};strokeWidth=1.2;dashed={int(dashed)};'+('startArrow=block;startFill=1;' if both else '')
        attrs={'id':'e'+str(self.count),'value':'','edge':'1','parent':'1'}
        for name,key,p,prefix in [('source',source,points[0],'exit'),('target',target,points[-1],'entry')]:
            if key:
                id,x,y,w,h=self.ids[key];attrs[name]=id
                style+=f'{prefix}X={(p[0]-x)/w};{prefix}Y={(p[1]-y)/h};{prefix}Dx=0;{prefix}Dy=0;{prefix}Perimeter=0;'
        attrs['style']=style;c=ET.SubElement(self.root,'mxCell',**attrs)
        geo=ET.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
        for p,label_type in [(points[0],'sourcePoint'),(points[-1],'targetPoint')]:
            ET.SubElement(geo,'mxPoint',x=str(p[0]),y=str(p[1]),attrib={'as':label_type})
        arr=ET.SubElement(geo,'Array',attrib={'as':'points'})
        for x,y in points[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
        if label:
            x,y=label_at;w=len(label)*7+12
            self.layers[2].append(f'<rect x="{x-5}" y="{y-15}" width="{w}" height="21" fill="#ffffff"/>')
            self.text(x,y,label,13,color,600)

    def save(self,stem):
        start=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#252e39"/></marker><marker id="back" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M10 0 L0 5 L10 10 Z" fill="#252e39"/></marker></defs><rect width="100%" height="100%" fill="white"/>'
        (self.directory/(stem+'.svg')).write_text(start+'\n'.join(sum(self.layers,[]))+'</svg>')
        ET.indent(self.xml)
        (self.directory/(stem+'.drawio')).write_text(ET.tostring(self.xml,encoding='unicode'))


def cloud(root,name):
    signal=name=='signalledger';title='SignalLedger' if signal else 'ContractForge'
    d=Drawing(root/'docs/assets',title+' AWS target',1600,1190)
    d.text(40,45,title+' — AWS deployment blueprint',30,weight=700)
    d.text(40,75,'Proposed architecture • cloud services and adapters are not provisioned in v0.1',14,'#76542a')
    d.boundary(290,260,1250,825,'AWS Cloud / one Region','#586675')
    d.boundary(535,365,650,690,'VPC • two Availability Zones','#865aab')
    d.boundary(560,412,600,156,'Public subnets','#578341','#fbfdf9')
    d.boundary(560,605,600,201,'Private application subnets','#47759b','#fcfdff')
    d.boundary(560,847,600,184,'Private database subnets','#47759b','#fcfdff')
    d.node('browser',800,103,'browser',['Engineer workbench','Investigate incidents' if signal else 'Inspect migration replay'])
    d.node('github',130,281,'github',['GitHub Actions','Tests + container build'])
    d.node('input',130,638,None,['Telemetry producers' if signal else 'Contracts + events','Metric / lineage exports' if signal else 'Versioned JSON + samples'],kind='json')
    d.node('ecr',365,322,'ecr',['Amazon ECR','Versioned images'])
    d.node('auth',1300,280,'cognito',['Amazon Cognito','Sign-in / bearer tokens'])
    d.node('alb',800,438,'elb',['Application Load Balancer','TLS ingress'])
    d.node('app',800,648,'fargate',['Amazon ECS on Fargate','FastAPI + lineage / evidence engine' if signal else 'FastAPI + migration / replay engine'])
    d.node('model',1300,491,'bedrock',['Amazon Bedrock','Evidence-grounded explanations' if signal else 'Restricted migration proposals'])
    d.node('storage',1300,736,'s3',['Amazon S3','Evidence / run attachments' if signal else 'Replay inputs / counterexamples'])
    d.node('db',800,883,'rds',['Amazon RDS for PostgreSQL','Runs / idempotency / audit metadata'])
    d.node('logs',1300,919,'cloudwatch',['Amazon CloudWatch','Application logs + alarms'])
    d.edge('browser','alb',[(800,239),(800,438)],'HTTPS requests',(813,314),both=True)
    d.edge('browser','auth',[(842,143),(1300,143),(1300,280)],'Sign in / JWT',(1012,134),both=True)
    d.edge('github','ecr',[(172,322),(245,322),(245,365),(323,365)],'Push image',(175,302),dashed=True)
    d.edge('ecr','app',[(407,365),(487,365),(487,690),(758,690)],'Deploy container',(547,683),dashed=True)
    d.edge('input','alb',[(172,680),(445,680),(445,591),(683,591),(683,481),(758,481)],'Submit JSON',(265,670))
    d.edge('alb','app',[(800,574),(800,648)],('HTTP :8011' if signal else 'HTTP :8012'),(817,603))
    d.edge('app','model',[(842,670),(1210,670),(1210,533),(1258,533)],'Grounded inference' if signal else 'Generate plan',(976,660),both=True)
    d.edge('app','storage',[(842,706),(1237,706),(1237,778),(1258,778)],'Read / write artifacts',(978,698),both=True)
    d.edge('app','logs',[(842,734),(1198,734),(1198,961),(1258,961)],'Logs / metrics',(1210,926))
    d.edge('app','db',[(800,792),(800,883)],'Read / write runs',(817,837),both=True)
    d.text(40,1120,'Service calls use task IAM roles and VPC endpoints; subnet groups summarize AZ A + AZ B.',12,'#526071')
    d.text(40,1144,'Solid arrows: application traffic     Dashed arrows: CI / image delivery     Security groups and endpoint resources omitted for readability.',12,'#526071')
    d.text(40,1168,'Current runnable implementation: FastAPI + SQLite + local Ollama. See implementation.png and CLOUD_DESIGN.md.',12,'#526071')
    d.save('architecture')


def local(root,name):
    signal=name=='signalledger';title='SignalLedger' if signal else 'ContractForge'
    d=Drawing(root/'docs/assets',title+' implementation',1600,1090)
    d.text(40,45,title+' — runnable implementation',30,weight=700)
    d.text(40,76,'Implemented components • synthetic fixtures included • optional local model inference',14,'#526071')
    d.boundary(292,263,1000,658,'Python application / local host or Docker container','#587088')
    d.boundary(335,326,912,260,'FastAPI process','#75968b','#fcfefc')
    d.boundary(335,641,912,230,'Persistence and reports','#7891a8','#fcfdff')
    d.node('browser',135,380,'browser',['Browser workbench','Scenarios / history / export'])
    d.node('fixtures',135,694,None,['JSON inputs','Metrics / lineage / notes' if signal else 'Contracts / replay events'],kind='json')
    d.node('ci',485,118,'github',['GitHub Actions','Test workflow included'])
    d.node('docker',970,118,'docker',['Docker image','Packaging files included'])
    d.node('api',505,380,'fastapi',['FastAPI routes','Typed input + request limits'])
    d.node('engine',960,380,'python',['Investigation engine' if signal else 'Migration + replay engine','Lineage / anomalies / citations' if signal else 'Typed DSL / semantic invariants'])
    d.node('model',1435,380,None,['Local Ollama','Optional structured generation'],kind='model')
    d.node('store',550,697,None,['SQLite / WAL','Saved runs + idempotency'],kind='db')
    d.node('report',1020,697,None,['Report JSON','Evidence + traceable hypotheses' if signal else 'Accepted / quarantined events'],kind='json')
    d.edge('browser','api',[(177,422),(463,422)],'HTTP / JSON',(265,411),both=True)
    d.edge('fixtures','api',[(177,736),(253,736),(253,548),(505,548),(505,524)],'Validate request',(300,539))
    d.edge('api','engine',[(547,422),(918,422)],'Run analysis',(666,411))
    d.edge('engine','model',[(1002,422),(1393,422)],'Schema-constrained inference',(1080,411),dashed=True,both=True)
    d.edge('engine','report',[(960,524),(960,620),(1020,620),(1020,697)],'Validated result',(979,611))
    d.edge('report','store',[(978,739),(592,739)],'Atomic save',(709,728))
    d.edge('api','store',[(505,524),(505,602),(550,602),(550,697)],'Read run / retry lookup',(565,629),both=True)
    d.text(1370,606,'Unknown AI output',13,'#526071',600)
    d.text(1370,627,'→ explicit fallback',13,'#526071')
    d.text(340,969,'The AI adapter cannot execute commands or mutate infrastructure.',15,'#526071')
    d.text(340,995,('29' if signal else '33')+' backend tests; provider transport tested with mock responses.',13,'#526071')
    d.text(340,1020,'Live Ollama model inference has not been tested in the authoring environment.',13,'#526071')
    d.save('implementation')


if __name__=='__main__':
    cloud(ROOT,'signalledger')
    local(ROOT,'signalledger')
