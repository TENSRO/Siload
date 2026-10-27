from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json
r=Path(__file__).resolve().parent;v=r/'visuals'
d=json.loads((r/'drc.json').read_text());assert not d['violations'] and not d['unconnected_items'] and not d['schematic_parity']
images=['SILOAD REV A-hero-logo.png','SILOAD REV A-top-logo.png','SILOAD REV A-02-connectors.png','SILOAD REV A-03-detail.png']
visual_files=[v/p for p in images+['SILOAD REV A-studio-branded.blend','SILOAD REV A-detailed-branded.glb','README.md','board-details.json']]+list((v/'meshes').glob('*.json'))
scripts=[r/p for p in ['studio_render.py','finish_studio.py','brand_studio.py','logo_in_scene.py']]
branding=list((r/'branding').glob('*'))
files=visual_files+scripts+branding
files+=[p for p in r.iterdir() if p.is_file() and (p.suffix in ['.kicad_pro','.kicad_pcb','.kicad_sch','.kicad_sym','.csv','.md'] or p.name in ['fp-lib-table','sym-lib-table','erc.rpt','drc.json','SILOAD REV A-schema.pdf','SILOAD REV A-layout.svg'])]
files+=list((r/'SILOAD.pretty').glob('*'))
files+=[r/p for p in ['build_design.py','apply_logo.py','export_logo_library.py','vectorize_logo.py','layout_config.py','route_board.py','finalize_docs.py']]
assert all(p.exists() and p.stat().st_size for p in files)
dest=r/'SILOAD REV A-branded.zip'
with ZipFile(dest,'w',ZIP_DEFLATED) as archive:
 for p in dict.fromkeys(files):archive.write(p,p.relative_to(r))
print(dest,round(dest.stat().st_size/1024**2,1),'MiB')
