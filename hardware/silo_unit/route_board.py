"""Two-layer routing with via support and pin-proximity penalty for 64x40mm SILOAD LOAD CELL REV A."""
from pathlib import Path
import math, heapq
import pcbnew as p
from layout_config import BOARD_WIDTH, BOARD_HEIGHT, SCREW_HEAD_DIAMETER

ROOT = Path(__file__).resolve().parent
PATH = ROOT / 'SILOAD LOAD CELL REV A.kicad_pcb'
b = p.LoadBoard(str(PATH))
STEP = 0.2
W = round(BOARD_WIDTH / STEP) + 1
H = round(BOARD_HEIGHT / STEP) + 1
LAYERS = [p.F_Cu, p.B_Cu]


def to_grid(v):
    return (round((p.ToMM(v.x) - 50) / STEP), round((p.ToMM(v.y) - 50) / STEP))


def to_pos(v):
    return p.VECTOR2I(p.FromMM(50 + v[0] * STEP), p.FromMM(50 + v[1] * STEP))


def index(x, y):
    return y * W + x


def disk(grid, x, y, r, value):
    for yy in range(max(0, math.floor(y - r)), min(H, math.ceil(y + r) + 1)):
        for xx in range(max(0, math.floor(x - r)), min(W, math.ceil(x + r) + 1)):
            if (xx - x) ** 2 + (yy - y) ** 2 <= r * r:
                grid[index(xx, yy)] = value


pads = {}
obstacles = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        pt = to_grid(pad.GetPosition())
        size = pad.GetSize()
        r = max(p.ToMM(size.x), p.ToMM(size.y)) / 2
        is_hole = fp.GetReference().startswith('H')
        net = pad.GetNetCode()
        if net:
            pads.setdefault(net, []).append((pt, pad.GetPosition()))
        obstacles.append((pt, r, is_hole, net))

tracks = []
vias = []


def make_grids(net):
    grids = [bytearray(W * H), bytearray(W * H)]
    via_blocked = bytearray(W * H)
    halo = bytearray(W * H)
    for g in grids + [via_blocked]:
        for x in range(W):
            for y in [0, 1, 2, H - 1, H - 2, H - 3]:
                g[index(x, y)] = 1
        for y in range(H):
            for x in [0, 1, 2, W - 1, W - 2, W - 3]:
                g[index(x, y)] = 1
    for (x, y), r, is_hole, n in obstacles:
        if is_hole:
            for g in grids + [via_blocked]:
                disk(g, x, y, (SCREW_HEAD_DIAMETER / 2 + 0.35) / STEP, 1)
        else:
            disk(via_blocked, x, y, (r + 0.55) / STEP, 1)
            if n != net:
                for g in grids:
                    disk(g, x, y, (r + 0.42) / STEP, 1)
                disk(halo, x, y, (r + 0.85) / STEP, 1)
    for pts, n, l_idx in tracks:
        for x, y in pts:
            if n != net:
                disk(grids[l_idx], x, y, 0.48 / STEP, 1)
                disk(via_blocked, x, y, 0.65 / STEP, 1)
    for vx, vy, n in vias:
        if n != net:
            for g in grids + [via_blocked]:
                disk(g, vx, vy, 0.65 / STEP, 1)
    return grids, via_blocked, halo


def multi_astar_2layer(tree_nodes, target_nodes, grids, via_blocked, halo, prefer_layer=0):
    directions = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    targets = {node[0]: j for j, node in enumerate(target_nodes)}
    for pt, _ in tree_nodes:
        for g in grids:
            disk(g, pt[0], pt[1], 0.8, 0)
    for pt in targets:
        for g in grids:
            disk(g, pt[0], pt[1], 0.8, 0)

    def heuristic(pt):
        return min(
            14 * min(abs(pt[0] - t[0]), abs(pt[1] - t[1])) + 10 * abs(abs(pt[0] - t[0]) - abs(pt[1] - t[1]))
            for t in targets
        )

    queue = []
    costs = {}
    parents = {}
    roots = {}
    for i, (pt, _) in enumerate(tree_nodes):
        for l_idx in [0, 1]:
            init_cost = 0 if l_idx == prefer_layer else 12
            state = (pt[0], pt[1], l_idx, -1)
            costs[state] = init_cost
            roots[state] = i
            heapq.heappush(queue, (init_cost + heuristic(pt), init_cost, state))

    while queue:
        _, cost, state = heapq.heappop(queue)
        if cost != costs.get(state):
            continue
        x, y, l_idx, old_dir = state
        pt = (x, y)
        if pt in targets:
            j = targets[pt]
            path = [(x, y, l_idx)]
            cur = state
            while cur in parents:
                cur = parents[cur]
                path.append((cur[0], cur[1], cur[2]))
            i = roots[cur]
            return path[::-1], i, j

        grid = grids[l_idx]
        allowed = range(8) if old_dir < 0 else [old_dir, (old_dir + 1) % 8, (old_dir - 1) % 8]
        for direction in allowed:
            dx, dy = directions[direction]
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= W or ny < 0 or ny >= H or grid[index(nx, ny)]:
                continue
            if dx and dy and (grid[index(x + dx, y)] or grid[index(x, y + dy)]):
                continue
            step_cost = (14 if dx and dy else 10) + (15 if old_dir >= 0 and old_dir != direction else 0)
            if halo[index(nx, ny)]:
                step_cost += 22
            nc = cost + step_cost
            ns = (nx, ny, l_idx, direction)
            if nc < costs.get(ns, 10**9):
                costs[ns] = nc
                parents[ns] = state
                roots[ns] = roots[state]
                heapq.heappush(queue, (nc + heuristic((nx, ny)), nc, ns))

        other_l = 1 - l_idx
        if not via_blocked[index(x, y)] and not grids[other_l][index(x, y)]:
            nc = cost + 65
            ns = (x, y, other_l, -1)
            if nc < costs.get(ns, 10**9):
                costs[ns] = nc
                parents[ns] = state
                roots[ns] = roots[state]
                heapq.heappush(queue, (nc + heuristic(pt), nc, ns))
    return None


def segment(a, c, net, layer, width):
    if a == c:
        return
    t = p.PCB_TRACK(b)
    t.SetStart(a)
    t.SetEnd(c)
    t.SetWidth(p.FromMM(width))
    t.SetLayer(layer)
    t.SetNetCode(net)
    b.Add(t)


def add_via(pt, net):
    v = p.PCB_VIA(b)
    v.SetPosition(to_pos(pt))
    v.SetWidth(p.FromMM(0.6))
    v.SetDrill(p.FromMM(0.3))
    v.SetNetCode(net)
    b.Add(v)
    vias.append((pt[0], pt[1], net))


def exact_link(a, c):
    dx = c.x - a.x
    dy = c.y - a.y
    diagonal = min(abs(dx), abs(dy))
    middle = p.VECTOR2I(a.x + (diagonal if dx >= 0 else -diagonal), a.y + (diagonal if dy >= 0 else -diagonal))
    return [a, middle, c]


def net_priority(net_code):
    name = b.FindNet(net_code).GetNetname().lstrip('/')
    if name in ['HX_AN', 'HX_AP', 'HX_DT', 'HX_SCK', 'MUX_A', 'MUX_B', 'ONEWIRE_DQ']:
        return (0, len(pads[net_code]), name)
    if name.startswith('LC') and ('_AN' in name or '_AP' in name):
        return (1, len(pads[net_code]), name)
    return (2, len(pads[net_code]), name)


order = sorted(pads, key=net_priority)
for net in order:
    name = b.FindNet(net).GetNetname().lstrip('/')
    nodes = pads[net]
    tree = [nodes[0]]
    remaining = nodes[1:]
    prefer_l = 1 if (name in ['+3V3', 'LC_EN', 'MUX_B'] or name.endswith('_AP')) else 0
    while remaining:
        grids, via_blocked, halo = make_grids(net)
        res = multi_astar_2layer(tree, remaining, grids, via_blocked, halo, prefer_layer=prefer_l)
        if not res:
            raise RuntimeError('Unable to route ' + name)
        path, i, j = res
        _, exact_start = tree[i]
        _, exact_end = remaining[j]

        runs = [[path[0]]]
        for pt in path[1:]:
            if pt[2] == runs[-1][-1][2]:
                runs[-1].append(pt)
            else:
                add_via((pt[0], pt[1]), net)
                runs.append([pt])

        for r_idx, run in enumerate(runs):
            l_idx = run[0][2]
            layer = LAYERS[l_idx]
            pts_2d = [(x, y) for x, y, _ in run]
            reduced = [pts_2d[0]]
            for k in range(1, len(pts_2d) - 1):
                if (pts_2d[k][0] - pts_2d[k - 1][0], pts_2d[k][1] - pts_2d[k - 1][1]) != (
                    pts_2d[k + 1][0] - pts_2d[k][0],
                    pts_2d[k + 1][1] - pts_2d[k][1],
                ):
                    reduced.append(pts_2d[k])
            if len(pts_2d) > 1:
                reduced.append(pts_2d[-1])

            start_vec = exact_link(exact_start, to_pos(reduced[0])) if r_idx == 0 else [to_pos(reduced[0])]
            end_vec = exact_link(to_pos(reduced[-1]), exact_end) if r_idx == len(runs) - 1 else [to_pos(reduced[-1])]
            coords = start_vec + [to_pos(v) for v in reduced[1:-1]] + end_vec
            for a, c in zip(coords, coords[1:]):
                segment(a, c, net, layer, 0.3)
            tracks.append((pts_2d, net, l_idx))

        tree.append(remaining.pop(j))
    print('Routed', name, flush=True)

b.BuildConnectivity()
p.SaveBoard(str(PATH), b)
print('Saved routed draft with', len(vias), 'vias.')
