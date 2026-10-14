import base64
import copy
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import zipfile
from .model import Document, Shape, History

BG, PANEL, FG, ACCENT = '#202226', '#2c2f34', '#e5e7eb', '#4c9aff'
TOOLS = [('select','Selecionar · V'),('nodes','Editar pontos · N'),('rect','Retângulo · R'),('ellipse','Elipse · E'),('line','Linha · L'),('bezier','Bézier · B'),('text','Texto · T')]
COLORS = ['#ffffff','#b3b3b3','#666666','#202020','#ff4444','#ff9900','#ffe600','#88dd00','#22c55e','#00cccc','#00aaff','#2255ff','#7733ff','#cc22ff','#ff0088','#a0522d']

class Editor:
    def __init__(self, root):
        self.root = root
        self.doc, self.history = Document(), History()
        self.path = None
        self.saved = self.doc.dumps()
        self.selected = None
        self.tool = 'select'
        self.zoom, self.ox, self.oy = .48, 70, 35
        self.start = self.last = None
        self.drag_node = None
        self.changed_drag = False
        self.curve = []
        self.fill, self.stroke = '#22c55e', '#202020'
        self.status = tk.StringVar(value='Pronto. Desenhe uma forma ou abra um projeto .cdvector.')
        root.title('cdvector — Novo projeto')
        root.geometry('1400x900')
        root.minsize(1000,650)
        root.configure(bg=BG)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame',background=PANEL)
        style.configure('TLabel',background=PANEL,foreground=FG)
        style.configure('TButton',background=PANEL,foreground=FG,padding=7)
        style.map('TButton',background=[('active','#41464e')])
        style.configure('TEntry',fieldbackground='#383c43',foreground=FG)
        menu=tk.Menu(root)
        filemenu=tk.Menu(menu,tearoff=False)
        for label,cmd,key in [('Novo',self.new,'Ctrl+N'),('Abrir projeto',self.open,'Ctrl+O'),('Salvar',self.save,'Ctrl+S'),('Salvar como',lambda:self.save(True),''),('Exportar SVG',self.export,''),('Ver prévia CDR',self.preview_cdr,'')]:
            filemenu.add_command(label=label,command=cmd,accelerator=key)
        menu.add_cascade(label='Arquivo',menu=filemenu)
        edit=tk.Menu(menu,tearoff=False)
        for label,cmd in [('Desfazer',self.undo),('Refazer',self.redo),('Duplicar',self.duplicate),('Excluir',self.delete)]:edit.add_command(label=label,command=cmd)
        menu.add_cascade(label='Editar',menu=edit)
        menu.add_command(label='Sobre',command=lambda:messagebox.showinfo('cdvector 0.1','Editor vetorial independente para desktop.\nCDR: apenas prévia. Exportação: SVG.\nNão é uma cópia completa do CorelDRAW.'))
        root.config(menu=menu)
        top=ttk.Frame(root,padding=6);top.pack(fill='x')
        for label,cmd in [('Novo',self.new),('Abrir',self.open),('Salvar',self.save),('Exportar SVG',self.export),('↶',self.undo),('↷',self.redo),('−',lambda:self.set_zoom(self.zoom/1.2)),('+',lambda:self.set_zoom(self.zoom*1.2)),('Ajustar página',self.fit)]:ttk.Button(top,text=label,command=cmd).pack(side='left',padx=2)
        ttk.Label(top,text='  cdvector  /  0.1',font=('Segoe UI',12,'bold')).pack(side='right')
        body=ttk.Frame(root);body.pack(fill='both',expand=True)
        left=ttk.Frame(body,padding=5);left.pack(side='left',fill='y')
        self.buttons={}
        for key,label in TOOLS:
            b=ttk.Button(left,text=label,command=lambda k=key:self.choose(k));b.pack(fill='x',pady=2);self.buttons[key]=b
        ttk.Button(left,text='Excluir',command=self.delete).pack(fill='x',pady=(22,2))
        ttk.Button(left,text='Duplicar',command=self.duplicate).pack(fill='x',pady=2)
        ttk.Label(left,text='Bézier: 4 cliques\ninício → controle 1\n→ controle 2 → fim\n\nPan: botão do meio\nZoom: roda do mouse\nEsc: cancelar',justify='left').pack(pady=20)
        right=ttk.Frame(body,width=220,padding=12);right.pack(side='right',fill='y');right.pack_propagate(False)
        ttk.Label(right,text='PROPRIEDADES',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,14))
        self.info=tk.StringVar(value='Nenhum objeto selecionado')
        ttk.Label(right,textvariable=self.info,wraplength=190).pack(anchor='w',pady=5)
        ttk.Button(right,text='Cor de preenchimento',command=lambda:self.pick_color(False)).pack(fill='x',pady=3)
        ttk.Button(right,text='Cor do contorno',command=lambda:self.pick_color(True)).pack(fill='x',pady=3)
        ttk.Button(right,text='Sem preenchimento',command=lambda:self.color('none')).pack(fill='x',pady=3)
        ttk.Label(right,text='Espessura do contorno (px)').pack(anchor='w',pady=(15,4))
        self.width=tk.StringVar(value='1.5');ttk.Entry(right,textvariable=self.width).pack(fill='x')
        ttk.Label(right,text='Tamanho do texto (px)').pack(anchor='w',pady=(10,4))
        self.fontsize=tk.StringVar(value='24');ttk.Entry(right,textvariable=self.fontsize).pack(fill='x')
        ttk.Button(right,text='Aplicar ao selecionado',command=self.apply).pack(fill='x',pady=8)
        ttk.Button(right,text='Editar texto',command=self.edit_text).pack(fill='x',pady=3)
        ttk.Button(right,text='Trazer à frente',command=lambda:self.layer(True)).pack(fill='x',pady=(18,3))
        ttk.Button(right,text='Enviar para trás',command=lambda:self.layer(False)).pack(fill='x',pady=3)
        ttk.Label(right,text='PÁGINA 1\nA3 · 297 × 420 mm\n\nCDR abre como prévia.\nObjetos editáveis são salvos\nem .cdvector e exportados\nem SVG.',wraplength=190).pack(anchor='w',pady=25)
        self.canvas=tk.Canvas(body,bg='#56595f',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        palette=ttk.Frame(root,padding=4);palette.pack(fill='x')
        ttk.Label(palette,text='Preenchimento · ').pack(side='left')
        for color in COLORS:
            b=tk.Button(palette,bg=color,activebackground=color,width=3,relief='flat',command=lambda c=color:self.color(c));b.pack(side='left',padx=1)
            b.bind('<Button-3>',lambda e,c=color:self.color(c,True))
        ttk.Label(root,textvariable=self.status,padding=6).pack(fill='x')
        for event,fn in [('<Button-1>',self.down),('<B1-Motion>',self.motion),('<ButtonRelease-1>',self.up),('<MouseWheel>',self.wheel),('<Button-4>',lambda e:self.wheel(e,1)),('<Button-5>',lambda e:self.wheel(e,-1)),('<Button-2>',self.pan_start),('<B2-Motion>',self.pan_move)]:self.canvas.bind(event,fn)
        for seq,fn in [('<Control-n>',self.new),('<Control-o>',self.open),('<Control-s>',self.save),('<Control-z>',self.undo),('<Control-y>',self.redo),('<Control-d>',self.duplicate),('<Delete>',self.delete),('<Escape>',self.cancel)]:root.bind(seq,lambda e,f=fn:self.shortcut(e,f))
        root.bind('<Key>',self.key)
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.after(100,self.fit)

    def shortcut(self,e,fn):
        if isinstance(e.widget,(tk.Entry,ttk.Entry,tk.Text)):return
        fn();return 'break'

    def key(self,e):
        if isinstance(e.widget,(tk.Entry,ttk.Entry,tk.Text)) or e.state & 4:return
        keys={'v':'select','n':'nodes','r':'rect','e':'ellipse','l':'line','b':'bezier','t':'text'}
        if e.char.lower() in keys:self.choose(keys[e.char.lower()])

    def choose(self,tool):
        self.cancel();self.tool=tool
        self.status.set(dict(TOOLS)[tool]+' — '+('Clique nos quatro pontos da curva.' if tool=='bezier' else 'Clique e arraste na página.'))
        self.draw()

    def point(self,e):return [(e.x-self.ox)/self.zoom,(e.y-self.oy)/self.zoom]
    def screen(self,p):return [p[0]*self.zoom+self.ox,p[1]*self.zoom+self.oy]
    def obj(self):return self.doc.shapes[self.selected] if self.selected is not None and self.selected<len(self.doc.shapes) else None
    def remember(self):self.history.record(self.doc)
    def title(self):self.root.title(f'cdvector — {self.path.name if self.path else "Novo projeto"}'+(' *' if self.doc.dumps()!=self.saved else ''))

    def draw(self):
        c=self.canvas;c.delete('all')
        c.create_rectangle(self.ox+5,self.oy+5,self.ox+self.doc.width*self.zoom+5,self.oy+self.doc.height*self.zoom+5,fill='#34363a',outline='')
        c.create_rectangle(self.ox,self.oy,self.ox+self.doc.width*self.zoom,self.oy+self.doc.height*self.zoom,fill='white',outline='#999')
        for i,s in enumerate(self.doc.shapes):
            p=[v for pair in s.points for v in self.screen(pair)]
            fill='' if s.fill=='none' else s.fill;stroke='' if s.stroke=='none' else s.stroke
            kw={'tags':('object',f's{i}')}
            if s.kind in ('rect','ellipse'):
                method=c.create_rectangle if s.kind=='rect' else c.create_oval
                method(*p,fill=fill,outline=stroke,width=s.width*self.zoom,**kw)
            elif s.kind in ('line','bezier'):
                if stroke and s.width>0:c.create_line(*[v for pair in s.samples() for v in self.screen(pair)],fill=stroke,width=max(.1,s.width*self.zoom),**kw)
            else:
                if fill:c.create_text(*p,text=s.text,anchor='nw',font=('Arial',-max(1,int(s.size*self.zoom))),fill=fill,**kw)
        s=self.obj()
        if s:
            x,y,r,b=s.bounds();a=self.screen((x,y));d=self.screen((r,b))
            c.create_rectangle(*a,*d,outline=ACCENT,dash=(4,3))
            if self.tool=='nodes':
                if s.kind=='bezier':c.create_line(*[v for pair in s.points for v in self.screen(pair)],fill='#8ab4ff',dash=(3,3))
                for p in s.points:
                    sx,sy=self.screen(p);c.create_rectangle(sx-4,sy-4,sx+4,sy+4,fill='white',outline=ACCENT)
            self.info.set(f'{s.kind} · objeto {self.selected+1}\nX {x:.1f}  Y {y:.1f}\nL {r-x:.1f}  A {b-y:.1f} px')
        else:self.info.set(f'{len(self.doc.shapes)} objetos\nNenhum objeto selecionado')
        for p in self.curve:
            x,y=self.screen(p);c.create_oval(x-4,y-4,x+4,y+4,fill=ACCENT,outline='')
        c.create_rectangle(0,0,c.winfo_width(),20,fill=PANEL,outline='')
        for n in range(0,int(self.doc.width)+1,100):
            x=self.ox+n*self.zoom
            if x>0:c.create_line(x,13,x,20,fill='#aaa');c.create_text(x+3,7,text=str(n),anchor='w',fill='#ddd',font=('Arial',8))
        self.title()

    def hit(self,e):
        for item in reversed(self.canvas.find_overlapping(e.x-4,e.y-4,e.x+4,e.y+4)):
            for tag in self.canvas.gettags(item):
                if tag.startswith('s') and tag[1:].isdigit():return int(tag[1:])
        return None

    def params(self):
        try:
            width=float(self.width.get());size=float(self.fontsize.get())
            if not math.isfinite(width) or not math.isfinite(size) or not 0<=width<=1000 or not 1<=size<=2000:raise ValueError()
            return width,size
        except ValueError:
            messagebox.showerror('Valor inválido','Espessura: 0–1000. Texto: 1–2000.');return None

    def down(self,e):
        self.canvas.focus_set();p=self.point(e);self.last=p;self.changed_drag=False
        if self.tool in ('select','nodes'):
            s=self.obj()
            if self.tool=='nodes' and s:
                for j,q in enumerate(s.points):
                    if math.dist(p,q)<9/self.zoom:self.drag_node=j;return
            self.selected=self.hit(e)
            if self.obj():self.width.set(str(self.obj().width));self.fontsize.set(str(self.obj().size))
            self.draw();return
        params=self.params()
        if not params:return
        width,size=params
        if self.tool=='bezier':
            self.curve.append(p)
            if len(self.curve)==4:
                self.remember();self.doc.shapes.append(Shape('bezier',self.curve.copy(),'none',self.stroke,width));self.selected=len(self.doc.shapes)-1;self.curve=[]
            self.draw();return
        if self.tool=='text':
            text=simpledialog.askstring('Texto','Digite o texto:',parent=self.root)
            if text:
                self.remember();self.doc.shapes.append(Shape('text',[p],self.fill,self.stroke,width,text,size));self.selected=len(self.doc.shapes)-1
            self.draw();return
        self.remember();self.start=p
        self.doc.shapes.append(Shape(self.tool,[p,p.copy()],self.fill if self.tool!='line' else 'none',self.stroke,width))
        self.selected=len(self.doc.shapes)-1;self.draw()

    def motion(self,e):
        p=self.point(e);s=self.obj()
        if not s or self.last is None:return
        if self.start is not None:s.points[1]=p
        elif self.tool in ('select','nodes'):
            if not self.changed_drag:self.remember();self.changed_drag=True
            if self.drag_node is not None:s.points[self.drag_node]=p
            else:s.move(p[0]-self.last[0],p[1]-self.last[1])
        self.last=p;self.draw()

    def up(self,e):
        if self.start is not None and self.obj() and math.dist(*self.obj().points)<1:
            self.doc=self.history.undo(self.doc);self.history.redo_stack.clear();self.selected=None
        self.start=self.last=None;self.drag_node=None;self.draw()

    def cancel(self):
        if self.start is not None:
            self.doc=self.history.undo(self.doc);self.history.redo_stack.clear();self.selected=None
        self.start=self.last=None;self.drag_node=None;self.curve=[];self.draw()
    def pan_start(self,e):self.pan=(e.x,e.y)
    def pan_move(self,e):
        self.ox+=e.x-self.pan[0];self.oy+=e.y-self.pan[1];self.pan=(e.x,e.y);self.draw()
    def wheel(self,e,direction=None):
        self.set_zoom(self.zoom*(1.15 if (direction if direction else e.delta)>0 else 1/1.15),e.x,e.y)
    def set_zoom(self,z,x=None,y=None):
        x=self.canvas.winfo_width()/2 if x is None else x;y=self.canvas.winfo_height()/2 if y is None else y
        p=((x-self.ox)/self.zoom,(y-self.oy)/self.zoom);self.zoom=max(.05,min(8,z));self.ox=x-p[0]*self.zoom;self.oy=y-p[1]*self.zoom
        self.status.set(f'Zoom {self.zoom*100:.0f}%');self.draw()
    def fit(self):
        w,h=self.canvas.winfo_width(),self.canvas.winfo_height();self.zoom=max(.05,min((w-70)/self.doc.width,(h-70)/self.doc.height));self.ox=(w-self.doc.width*self.zoom)/2;self.oy=35;self.draw()
    def color(self,color,outline=False):
        if outline:self.stroke=color
        else:self.fill=color
        if self.obj():
            self.remember();setattr(self.obj(),'stroke' if outline else 'fill',color)
        self.draw()
    def pick_color(self,outline):
        color=colorchooser.askcolor(parent=self.root)[1]
        if color:self.color(color,outline)
    def apply(self):
        params=self.params()
        if params and self.obj():self.remember();self.obj().width,self.obj().size=params;self.draw()
    def edit_text(self):
        s=self.obj()
        if s and s.kind=='text':
            text=simpledialog.askstring('Texto','Texto:',initialvalue=s.text,parent=self.root)
            if text is not None:self.remember();s.text=text;self.draw()
    def layer(self,front):
        if self.obj():
            self.remember();s=self.doc.shapes.pop(self.selected);self.doc.shapes.insert(len(self.doc.shapes) if front else 0,s);self.selected=len(self.doc.shapes)-1 if front else 0;self.draw()
    def delete(self):
        if self.obj():self.remember();self.doc.shapes.pop(self.selected);self.selected=None;self.draw()
    def duplicate(self):
        if self.obj():
            self.remember();s=copy.deepcopy(self.obj());s.move(20,20);self.doc.shapes.append(s);self.selected=len(self.doc.shapes)-1;self.draw()
    def undo(self):self.cancel();self.doc=self.history.undo(self.doc);self.selected=None;self.draw()
    def redo(self):self.cancel();self.doc=self.history.redo(self.doc);self.selected=None;self.draw()
    def confirm(self):
        if self.doc.dumps()==self.saved:return True
        answer=messagebox.askyesnocancel('Alterações não salvas','Salvar as alterações antes de continuar?')
        return self.save() if answer else answer is False
    def close(self):
        if self.confirm():self.root.destroy()
    def new(self):
        if not self.confirm():return
        self.doc=Document();self.history=History();self.path=None;self.saved=self.doc.dumps();self.selected=None;self.curve=[];self.fit()
    def open(self):
        if not self.confirm():return
        path=filedialog.askopenfilename(filetypes=[('Projeto cdvector','*.cdvector')])
        if not path:return
        try:
            doc=Document.loads(Path(path).read_text(encoding='utf-8'))
            self.doc=doc;self.history=History();self.path=Path(path);self.saved=doc.dumps();self.selected=None;self.curve=[];self.fit()
        except Exception as exc:messagebox.showerror('Não foi possível abrir',str(exc))
    def save(self,saveas=False):
        path=str(self.path) if self.path and not saveas else filedialog.asksaveasfilename(defaultextension='.cdvector',filetypes=[('Projeto cdvector','*.cdvector')])
        if not path:return False
        try:
            target=Path(path);temp=target.with_name(target.name+'.tmp');temp.write_text(self.doc.dumps(),encoding='utf-8');temp.replace(target)
            self.path=target;self.saved=self.doc.dumps();self.title();self.status.set('Projeto salvo.');return True
        except OSError as exc:messagebox.showerror('Erro ao salvar',str(exc));return False
    def export(self):
        path=filedialog.asksaveasfilename(defaultextension='.svg',filetypes=[('SVG','*.svg')])
        if path:
            try:Path(path).write_text(self.doc.svg(),encoding='utf-8');self.status.set('SVG exportado.')
            except OSError as exc:messagebox.showerror('Erro',str(exc))
    def preview_cdr(self):
        path=filedialog.askopenfilename(filetypes=[('CorelDRAW','*.cdr')])
        if not path:return
        try:
            with zipfile.ZipFile(path) as z:
                name='previews/page1.png' if 'previews/page1.png' in z.namelist() else 'previews/thumbnail.png'
                if z.getinfo(name).file_size>20_000_000:raise ValueError('Prévia muito grande.')
                data=z.read(name)
            win=tk.Toplevel(self.root);win.title('Prévia CDR — imagem, sem objetos editáveis')
            photo=tk.PhotoImage(data=base64.b64encode(data))
            if max(photo.width(),photo.height())>1000:photo=photo.subsample(math.ceil(max(photo.width(),photo.height())/1000))
            label=tk.Label(win,image=photo,bg='white');label.image=photo;label.pack()
            ttk.Label(win,text='Somente a prévia embutida. Este arquivo não foi convertido em vetores.',padding=10).pack()
        except Exception as exc:messagebox.showerror('Prévia indisponível',str(exc))

def main():
    root=tk.Tk();Editor(root);root.mainloop()
