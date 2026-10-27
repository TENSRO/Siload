from pathlib import Path
import pcbnew as p
r=Path(__file__).resolve().parent;b=p.LoadBoard(str(r/'SILOAD REV A.kicad_pcb'))
fp=next(f for f in b.GetFootprints() if f.GetReference()=='LOGO1')
directory=r/'SILOAD.pretty';directory.mkdir(exist_ok=True)
plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP);plugin.FootprintSave(str(directory),fp)
(r/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "SILOAD") (type "KiCad") (uri "${KIPRJMOD}/SILOAD.pretty") (options "") (descr "SiLoad branding")))')
print('Saved reusable logo footprint and local library table.')
