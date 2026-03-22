import os, json, base64, urllib.request, urllib.parse

user  = os.environ["GH_USER"]
token = os.environ["GH_TOKEN"]
min_s = int(os.environ["MIN_STARS"])

def gh(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def fetch_b64(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = r.read()
            ct   = r.headers.get_content_type() or "image/png"
            return f"data:{ct};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return ""

q    = f"type:pr author:{user} is:merged -user:{user}"
data = gh(f"https://api.github.com/search/issues?q={urllib.parse.quote(q)}&per_page=100&sort=updated")

repo_map = {}
for item in data.get("items", []):
    u = item["repository_url"]
    repo_map[u] = repo_map.get(u, 0) + 1

rows = []
for repo_url, pr_count in repo_map.items():
    try:
        rd = gh(repo_url)
    except Exception:
        continue
    if rd.get("stargazers_count", 0) <= min_s:
        continue
    rows.append((rd["stargazers_count"], pr_count, rd))

rows.sort(reverse=True)
rows = rows[:10]

for _, _, rd in rows:
    rd["_avatar_b64"] = fetch_b64(rd["owner"]["avatar_url"] + "&s=64")

LANG_COLORS = {
    "Python":"#3572A5","JavaScript":"#f1e05a","TypeScript":"#2b7489",
    "C":"#555555","C++":"#f34b7d","C#":"#178600","Java":"#b07219",
    "Go":"#00ADD8","Rust":"#dea584","PHP":"#4F5D95","Ruby":"#701516",
    "Shell":"#89e051","HTML":"#e34c26","CSS":"#563d7c","Kotlin":"#A97BFF",
    "Swift":"#ffac45","Dart":"#00B4AB","Lua":"#000080","Nix":"#7e7eff",
    "PowerShell":"#012456",
}

# rank 1=gold, 2=silver, 3=bronze, 4+=visible muted
RANK_COLORS = ["#e8a020", "#aaaaaa", "#a07050", "#3a3a3a", "#3a3a3a",
               "#3a3a3a", "#3a3a3a", "#3a3a3a", "#3a3a3a", "#3a3a3a"]

def lang_color(lang): return LANG_COLORS.get(lang, "#5a5650")
def esc(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
def fmt_stars(n): return f"{n/1000:.1f}k" if n >= 1000 else str(n)
def trim(s, m=60): s = s or "No description."; return s[:m-1]+"..." if len(s)>m else s

W        = 800
PAD_X    = 22
ROW_H    = 58
HEADER_H = 60
FOOTER_H = 36
n        = len(rows)
total_h  = HEADER_H + n * ROW_H + FOOTER_H

L = []
L.append(f'<svg width="{W}" height="{total_h}" viewBox="0 0 {W} {total_h}" '
         f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">')
L.append(f'<rect width="{W}" height="{total_h}" fill="#080808"/>')

# Header
L.append(f'<text x="{PAD_X}" y="22" font-family="\'DM Mono\',monospace" font-size="10" fill="#5a5650" letter-spacing="1">// CONTRIBUTIONS</text>')
L.append(f'<text x="{PAD_X}" y="50" font-family="Impact,\'Arial Narrow\',sans-serif" font-size="26" font-weight="700" fill="#ede8df" letter-spacing="2">CONTRIBUTIONS</text>')
L.append(f'<text x="242" y="50" font-family="\'DM Mono\',monospace" font-size="13" fill="#5a5650"> · {esc(user)}</text>')
L.append(f'<line x1="{PAD_X}" y1="{HEADER_H}" x2="{W-PAD_X}" y2="{HEADER_H}" stroke="#222222" stroke-width="1"/>')

# Rows
for i, (stars, prs, rd) in enumerate(rows):
    y        = HEADER_H + i * ROW_H
    is_last  = (i == n - 1)
    owner    = esc(rd["owner"]["login"])
    name     = esc(rd["name"])
    desc     = esc(trim(rd.get("description") or ""))
    lang     = rd.get("language") or ""
    star_s   = fmt_stars(stars)
    pr_s     = f"{prs} PR{'s' if prs>1 else ''} merged"
    repo_url = esc(rd["html_url"])
    avatar   = rd.get("_avatar_b64", "")
    cx       = PAD_X
    cy       = y + ROW_H // 2

    L.append(f'<a href="{repo_url}" target="_blank">')
    L.append(f'<rect x="0" y="{y}" width="{W}" height="{ROW_H}" fill="#111111"/>')
    if not is_last:
        L.append(f'<line x1="{PAD_X}" y1="{y+ROW_H}" x2="{W-PAD_X}" y2="{y+ROW_H}" stroke="#222222" stroke-width="1"/>')

    # Rank
    L.append(f'<text x="{cx+10}" y="{cy+5}" font-family="Impact,\'Arial Narrow\',sans-serif" font-size="15" fill="{RANK_COLORS[i]}" text-anchor="middle">{i+1}</text>')

    # Avatar
    av_x = cx + 26
    av_y = cy - 16
    L.append(f'<clipPath id="av{i}"><rect x="{av_x}" y="{av_y}" width="32" height="32" rx="6"/></clipPath>')
    L.append(f'<rect x="{av_x}" y="{av_y}" width="32" height="32" rx="6" fill="#222222"/>')
    if avatar:
        L.append(f'<image href="{avatar}" x="{av_x}" y="{av_y}" width="32" height="32" clip-path="url(#av{i})"/>')

    # Text
    tx = av_x + 32 + 14
    owner_w = len(owner) * 6.4 + 14
    L.append(f'<text x="{tx}" y="{cy-4}" font-family="\'DM Mono\',monospace" font-size="11" fill="#5a5650">{owner} /</text>')
    L.append(f'<text x="{tx+owner_w}" y="{cy-4}" font-family="\'DM Mono\',monospace" font-size="11" fill="#ede8df">{name}</text>')
    L.append(f'<text x="{tx}" y="{cy+12}" font-family="\'DM Mono\',monospace" font-size="10" fill="#5a5650">{desc}</text>')

    # Right side: stars (rightmost) → language (middle) → PR pill (leftmost)
    rx_edge = W - PAD_X

    # Stars — rightmost
    L.append(f'<text x="{rx_edge}" y="{cy+4}" font-family="\'DM Mono\',monospace" font-size="11" fill="#5a5650" text-anchor="end">&#9733; {star_s}</text>')
    star_left = rx_edge - (len(star_s) + 2) * 6.8

    # Language — middle
    if lang:
        lang_x   = star_left - len(lang) * 6.4 - 26
        L.append(f'<circle cx="{lang_x}" cy="{cy}" r="5" fill="{lang_color(lang)}"/>')
        L.append(f'<text x="{lang_x+10}" y="{cy+4}" font-family="\'DM Mono\',monospace" font-size="10" fill="#5a5650">{esc(lang)}</text>')
        pr_right = lang_x - 18
    else:
        pr_right = star_left - 18

    # PR pill — leftmost
    pr_w = len(pr_s) * 6.2 + 20
    pr_x = pr_right - pr_w
    L.append(f'<rect x="{pr_x}" y="{cy-10}" width="{pr_w}" height="17" rx="8" fill="rgba(232,160,32,0.07)" stroke="rgba(232,160,32,0.3)" stroke-width="1"/>')
    L.append(f'<text x="{pr_x+pr_w/2:.0f}" y="{cy+3}" font-family="\'DM Mono\',monospace" font-size="9" letter-spacing="1" fill="#e8a020" text-anchor="middle">{pr_s}</text>')

    L.append('</a>')

# Footer
fy = total_h - FOOTER_H + 6
L.append(f'<line x1="{PAD_X}" y1="{fy}" x2="{W-PAD_X}" y2="{fy}" stroke="#2a2a2a" stroke-width="1"/>')
L.append(f'<text x="{PAD_X}" y="{fy+18}" font-family="\'DM Mono\',monospace" font-size="9" fill="#5a5650">// repos with more than {min_s} stars · sorted by stars · auto-updated weekly</text>')
L.append(f'<text x="{W-PAD_X}" y="{fy+18}" font-family="\'DM Mono\',monospace" font-size="9" fill="#5a5650" text-anchor="end">{esc(user)}.github.io</text>')

L.append('</svg>')

with open("contributions.svg", "w") as f:
    f.write("\n".join(L))

print(f"Done: {len(rows)} entries.")
