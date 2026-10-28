from pathlib import Path
import json
import pcbnew as p

r = Path(__file__).resolve().parent
b = p.LoadBoard(str(r / 'SILOAD LOAD CELL REV A.kicad_pcb'))
tracks = [
    {
        'a': [p.ToMM(t.GetStart().x) - 50, p.ToMM(t.GetStart().y) - 50],
        'b': [p.ToMM(t.GetEnd().x) - 50, p.ToMM(t.GetEnd().y) - 50],
        'layer': b.GetLayerName(t.GetLayer()),
        'net': t.GetNetname(),
    }
    for t in b.GetTracks()
    if not isinstance(t, p.PCB_VIA)
]
pads = [
    {
        'ref': f.GetReference(),
        'pin': pad.GetNumber(),
        'xy': [p.ToMM(pad.GetPosition().x) - 50, p.ToMM(pad.GetPosition().y) - 50],
    }
    for f in b.GetFootprints()
    for pad in f.Pads()
]
(r / 'routing-data.json').write_text(json.dumps({'tracks': tracks, 'pads': pads}, indent=2))
