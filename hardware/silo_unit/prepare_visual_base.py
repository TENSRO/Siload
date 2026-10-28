from pathlib import Path
import pcbnew as p, json

r = Path(__file__).resolve().parent
v = r / 'visuals'
v.mkdir(exist_ok=True)
b = p.LoadBoard(str(r / 'SILOAD LOAD CELL REV A.kicad_pcb'))
for fp in b.GetFootprints():
    models = fp.Models()
    for i in range(len(models) - 1, -1, -1):
        if 'indicative' in models[i].m_Filename:
            models.erase(models.begin() + i)
data = {'text': [], 'tracks': []}


def capture(text):
    if text.IsVisible() and text.GetLayer() == p.F_SilkS:
        pos = text.GetPosition()
        size = text.GetTextSize()
        data['text'].append(
            {
                'text': text.GetText(),
                'position': [p.ToMM(pos.x) - 50, -(p.ToMM(pos.y) - 50)],
                'height': p.ToMM(size.y),
                'angle': text.GetTextAngle().AsDegrees(),
            }
        )


for drawing in b.GetDrawings():
    if isinstance(drawing, p.PCB_TEXT):
        capture(drawing)
for fp in b.GetFootprints():
    capture(fp.Reference())
for track in b.GetTracks():
    if isinstance(track, p.PCB_VIA):
        continue
    if track.GetLayer() == p.F_Cu:
        a = track.GetStart()
        c = track.GetEnd()
        data['tracks'].append(
            {
                'a': [p.ToMM(a.x) - 50, -(p.ToMM(a.y) - 50)],
                'b': [p.ToMM(c.x) - 50, -(p.ToMM(c.y) - 50)],
                'width': p.ToMM(track.GetWidth()),
            }
        )
(v / 'board-details.json').write_text(json.dumps(data))
p.SaveBoard(str(v / 'carrier-base.kicad_pcb'), b)
print('Prepared visual carrier base, without placeholder module models.')
