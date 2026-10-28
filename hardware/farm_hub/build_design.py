"""Generate the review draft. Run with the Python supplied with KiCad 10."""
from pathlib import Path
import uuid, json, csv
import pcbnew as p
from layout_config import BOARD_WIDTH,BOARD_HEIGHT,MOUNTING_HOLES,REFERENCE_POSITIONS,XIAO_HEADERS,ETH_HEADERS

ROOT = Path(__file__).resolve().parent
NAME = 'SILOAD REV A'
LIB = Path(r'C:\Program Files\KiCad\10.0\share\kicad\footprints')
uid = lambda: str(uuid.uuid4())
sheet = uid()
spec = [
 ('J1','XIAO_LEFT',XIAO_HEADERS[0],XIAO_HEADERS[1],7,['ETH_CSn',None,None,None,None,None,'ETH_RESETn'],['D0_GPIO1','D1_GPIO2','D2_GPIO3','D3_GPIO4','D4_GPIO5','D5_GPIO6','D6_GPIO43']),
 ('J2','XIAO_RIGHT',XIAO_HEADERS[0]+15.24,XIAO_HEADERS[1],7,[None,'GND','+3V3','SPI_MOSI','SPI_MISO','SPI_SCK','ETH_INTn'],['5V_USB','GND','3V3','D10_GPIO9','D9_GPIO8','D8_GPIO7','D7_GPIO44']),
 ('J3','W5500_LEFT',ETH_HEADERS[0],ETH_HEADERS[1],6,['GND','GND','SPI_MOSI','SPI_SCK','ETH_CSn','ETH_INTn'],['GND','GND','MOSI','SCLK','CSn','INTn']),
 ('J4','W5500_RIGHT',ETH_HEADERS[0]+20.32,ETH_HEADERS[1],6,['GND','+3V3','+3V3',None,'ETH_RESETn','SPI_MISO'],['GND','3V3','3V3','NC','RSTn','MISO']),
 ('C1','100nF_50V_ceramic_THT',62,82,2,['+3V3','GND'],['1','2']),
 ('C2','10uF_16V_electrolytic_THT',69,82.5,2,['+3V3','GND'],['+','-']),
]
board=p.BOARD()
board.SetCopperLayerCount(2)
board.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
nets={}
for name in sorted({n for s in spec for n in s[5] if n}):
 n=p.NETINFO_ITEM(board,name); board.Add(n); nets[name]=n

def pos(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def line(x1,y1,x2,y2,layer=p.Edge_Cuts,width=.05):
 s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_SEGMENT); s.SetStart(pos(x1,y1)); s.SetEnd(pos(x2,y2)); s.SetLayer(layer); s.SetWidth(p.FromMM(width)); board.Add(s)
def text(t,x,y,size=1,layer=p.F_SilkS):
 a=p.PCB_TEXT(board); a.SetText(t); a.SetPosition(pos(x,y)); a.SetTextSize(pos(size,size)); a.SetTextThickness(p.FromMM(.15)); a.SetLayer(layer); board.Add(a)

x1=50+BOARD_WIDTH;y1=50+BOARD_HEIGHT
for a,b,c,d in [(50,50,x1,50),(x1,50,x1,y1),(x1,y1,50,y1),(50,y1,50,50)]: line(a,b,c,d)
text(NAME,86,81.5,1.1)
text('Farm hub',86,84.2,.8)
text('DRAFT - CHECK MODULE FIT',77.5,88,.8,p.Dwgs_User)
text('USB-C',65.65,50.9,.8)
text('RJ45',89.05,50.9,.8)
text('3V3 ONLY',89.05,73,.8)
# Approximate module envelopes, deliberately on a documentation layer.
for x0,y0,x1,y1 in [(56.75,48.97,74.53,70.467),(76.55,48.98,101.55,77.48)]:
 for a,b,c,d in [(x0,y0,x1,y0),(x1,y0,x1,y1),(x1,y1,x0,y1),(x0,y1,x0,y0)]: line(a,b,c,d,p.Dwgs_User,.1)

defs=[]; instances=[]; wires=[]; labels=[]; ncs=[]
schem_positions=[(45.72,55.88),(105.41,55.88),(170.18,55.88),(234.95,55.88),(170.18,110.49),(234.95,110.49)]
footprints={}; ids={}
for idx,(ref,value,x,y,count,connections,pinnames) in enumerate(spec):
 identifier=uid(); ids[ref]=identifier
 if ref.startswith('J'):
  libname='Connector_PinSocket_2.54mm'
  fpname=f'PinSocket_1x0{count}_P2.54mm_Vertical'
 else:
  libname='Capacitor_THT'
  fpname='C_Disc_D5.0mm_W2.5mm_P2.50mm' if ref=='C1' else 'CP_Radial_D5.0mm_P2.00mm'
 fp=p.FootprintLoad(str(LIB/(libname+'.pretty')),fpname)
 fp.SetFPIDAsString(libname+':'+fpname)
 fp.SetReference(ref); fp.SetValue(value); fp.SetPosition(pos(x,y))
 fp.SetPath(p.KIID_PATH('/'+sheet+'/'+identifier))
 for pad in fp.Pads():
  net=connections[int(pad.GetNumber())-1]
  if net: pad.SetNet(nets[net])
 fp.Reference().SetTextSize(pos(.8,.8)); fp.Reference().SetTextThickness(p.FromMM(.12))
 fp.Value().SetVisible(False)
 board.Add(fp); footprints[ref]=fp
 sx,sy=schem_positions[idx]
 symbol_name=ref+'_socket' if ref.startswith('J') else ref+'_capacitor'
 pins=[]
 for k,pinname in enumerate(pinnames):
  py=-k*2.54
  pins.append(f'(pin passive line (at -10.16 {py} 0) (length 5.08) (name "{pinname}" (effects (font (size 1 1)))) (number "{k+1}" (effects (font (size 1 1)))))')
 defs.append(f'''(symbol "SILOAD:{symbol_name}"
 (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
 (property "Reference" "{ref[0]}" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
 (property "Value" "{value}" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
 (symbol "{symbol_name}_0_1" (rectangle (start -5.08 1.27) (end 15.24 {-count*2.54+1.27}) (stroke (width .254) (type default)) (fill (type background))))
 (symbol "{symbol_name}_1_1" {''.join(pins)}))''')
 instances.append(f'''(symbol (lib_id "SILOAD:{symbol_name}") (at {sx} {sy} 0) (unit 1)
 (in_bom yes) (on_board yes) (dnp no) (uuid "{identifier}")
 (property "Reference" "{ref}" (at {sx} {sy-5} 0) (effects (font (size 1.27 1.27))))
 (property "Value" "{value}" (at {sx} {sy-2.5} 0) (effects (font (size 1.27 1.27))))
 (property "Footprint" "{libname}:{fpname}" (at {sx} {sy} 0) (effects (font (size 1 1)) hide))
 {''.join(f'(pin "{k+1}" (uuid "{uid()}"))' for k in range(count))}
 (instances (project "{NAME}" (path "/{sheet}" (reference "{ref}") (unit 1)))))''')
 for k,net in enumerate(connections):
  px=round(sx-10.16,4); py=round(sy+k*2.54,4); lx=round(px-7.62,4)
  if net:
   wires.append(f'(wire (pts (xy {lx} {py}) (xy {px} {py})) (stroke (width 0) (type default)) (uuid "{uid()}"))')
   labels.append(f'(label "{net}" (at {lx} {py} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{uid()}"))')
  else:
   ncs.append(f'(no_connect (at {px} {py}) (uuid "{uid()}"))')

for ref,x,y in MOUNTING_HOLES:
 fp=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5')
 fp.SetReference(ref); fp.SetValue('M2.5'); fp.SetPosition(pos(x,y)); fp.Value().SetVisible(False); board.Add(fp)
 fp.SetAttributes(fp.GetAttributes() | p.FP_BOARD_ONLY)

notes=[('Complete XIAO + Wio stack plugs into J1/J2; radio wiring stays inside stack.',30,30),
 ('USB-C on XIAO supplies power. W5500 is supplied directly from XIAO 3V3.',30,35),
 ('ARCELI header spacing provisionally 20.32 mm; check physical module before manufacture.',30,145),
 ('J3/J4 pin 1 is at RJ45 end, module viewed from above. NC stays open.',30,150),
 ('Carrier does not reroute LoRa control pins. Firmware must match actual stack variant.',30,155),
 ('C1/C2: local Ethernet supply decoupling. PoE not implemented in this draft.',30,160)]
note_text=''.join(f'(text "{t}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid()}"))' for t,x,y in notes)
sch=f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid "{sheet}") (paper "A4")
 (title_block (title "SILOAD REV A - Farm hub carrier") (date "2026-10-27") (rev "A DRAFT") (comment 1 "CHECK MODULE FIT BEFORE FABRICATION"))
 (lib_symbols {''.join(defs)})
 {''.join(wires)} {''.join(labels)} {''.join(ncs)} {note_text} {''.join(instances)}
 (sheet_instances (path "/" (page "1"))))'''
(ROOT/(NAME+'.kicad_sch')).write_text(sch,encoding='utf-8')
(ROOT/'SILOAD.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+''.join(d.replace('"SILOAD:', '"') for d in defs)+')',encoding='utf-8')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "SILOAD") (type "KiCad") (uri "${KIPRJMOD}/SILOAD.kicad_sym") (options "") (descr "SILOAD carrier connectors")))',encoding='utf-8')
for fp in board.GetFootprints():
 if fp.GetReference() in REFERENCE_POSITIONS:fp.Reference().SetPosition(pos(*REFERENCE_POSITIONS[fp.GetReference()]))
if (ROOT/'branding'/'SiLoad-logo.json').exists():
 from apply_logo import apply
 apply(board)
p.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),board)
(ROOT/(NAME+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':NAME+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':.2,'min_track_width':.2,'min_hole_clearance':.25,'min_copper_edge_clearance':.3}}}},indent=2),encoding='utf-8')
with (ROOT/'BOM.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['Reference','Quantity','Description','Footprint'])
 w.writerow(['J1,J2',2,'Female header 1x7 2.54mm; height must clear Wio stack','PinSocket_1x07_P2.54mm_Vertical'])
 w.writerow(['J3,J4',2,'Female header 1x6 2.54mm; ARCELI spacing provisional','PinSocket_1x06_P2.54mm_Vertical'])
 w.writerow(['C1',1,'100nF 50V ceramic through-hole','Disc D5.0mm P2.50mm'])
 w.writerow(['C2',1,'10uF 16V radial electrolytic; pin 1 is positive','Radial D5.0mm P2.00mm'])
 w.writerow(['Mounting hardware',4,'M2.5 screws, head diameter <=5mm; spacers to match enclosure','2.7mm mounting holes'])
print('Created schematic, project, PCB placement draft and BOM in',ROOT)
