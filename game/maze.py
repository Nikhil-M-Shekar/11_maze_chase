import random
from collections import deque

CELL = 44

def generate_maze(cols, rows):
    visited = [[False]*cols for _ in range(rows)]
    walls = [[[True,True,True,True] for _ in range(cols)] for _ in range(rows)]
    def neighbors(r,c):
        dirs=[(-1,0,0,1),(1,0,1,0),(0,1,2,3),(0,-1,3,2)]
        res=[]
        for dr,dc,wd,od in dirs:
            nr,nc=r+dr,c+dc
            if 0<=nr<rows and 0<=nc<cols and not visited[nr][nc]:
                res.append((nr,nc,wd,od))
        return res
    stack=[(0,0)]
    visited[0][0]=True
    while stack:
        r,c=stack[-1]
        nbrs=neighbors(r,c)
        if nbrs:
            nr,nc,wd,od=random.choice(nbrs)
            walls[r][c][wd]=False
            walls[nr][nc][od]=False
            visited[nr][nc]=True
            stack.append((nr,nc))
        else:
            stack.pop()
    return walls

def bfs(walls, start, goal, rows, cols):
    """Return next step direction from start toward goal using BFS."""
    sr,sc=start; gr,gc=goal
    queue=deque([(sr,sc,[])])
    visited={(sr,sc)}
    dir_map={0:(-1,0),1:(1,0),2:(0,1),3:(0,-1)}
    opp={0:1,1:0,2:3,3:2}
    while queue:
        r,c,path=queue.popleft()
        if r==gr and c==gc:
            return path[0] if path else None
        for d,(dr,dc) in dir_map.items():
            if not walls[r][c][d]:
                nr,nc=r+dr,c+dc
                if (nr,nc) not in visited and 0<=nr<rows and 0<=nc<cols:
                    visited.add((nr,nc))
                    queue.append((nr,nc,path+[(dr,dc)]))
    return None


def shortest_path(walls, start, goal, rows, cols):
    """Return the list of cells from start to goal (inclusive) using BFS."""
    dir_map = {0: (-1, 0), 1: (1, 0), 2: (0, 1), 3: (0, -1)}
    prev = {start: None}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur == goal:
            break
        r, c = cur
        for d, (dr, dc) in dir_map.items():
            if not walls[r][c][d]:
                nxt = (r + dr, c + dc)
                if nxt not in prev and 0 <= nxt[0] < rows and 0 <= nxt[1] < cols:
                    prev[nxt] = cur
                    queue.append(nxt)
    if goal not in prev:
        return []
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return path[::-1]
