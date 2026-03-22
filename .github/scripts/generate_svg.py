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
    url = item["repository_url"]
    repo_map[url] = repo_map.get(url, 0) + 1

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

# Pre-fetch avatars as base64
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

def lang_color(lang): return LANG_COLORS.get(lang, "#555555")
def esc(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
def fmt_stars(n): return f"{n/1000:.1f}k" if n >= 1000 else str(n)
def trim(s, m=58): s = s or "No description."; return s[:m-1]+"..." if len(s)>m else s

W         = 800
PAD       = 28
ROW_H     = 58
ROW_GAP   = 5
HEADER_H  = 66
FOOTER_H  = 44
AVATAR_R  = 14
max_rows  = len(rows)
total_h   = HEADER_H + max_rows*(ROW_H+ROW_GAP) - ROW_GAP + FOOTER_H + 16

L = []
L.append(f'<svg width="{W}" height="{total_h}" viewBox="0 0 {W} {total_h}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">')
L.append(f'<rect width="{W}" height="{total_h}" rx="12" fill="#0d0d0d"/>')

# Header — big "CONTRIBUTIONS" left, "· user" muted right side
L.append(f'<text x="{PAD}" y="42" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="22" font-weight="700" fill="#ffffff" letter-spacing="-0.5">CONTRIBUTIONS</text>')
L.append(f'<text x="222" y="42" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="22" font-weight="400" fill="#333"> · {esc(user)}</text>')
L.append(f'<line x1="{PAD}" y1="58" x2="{W-PAD}" y2="58" stroke="#1e1e1e" stroke-width="1"/>')

for i,(stars,prs,rd) in enumerate(rows):
    y        = HEADER_H + i*(ROW_H+ROW_GAP)
    bg       = "#161616" if i%2==0 else "#111111"
    cx       = PAD + 22
    cy       = y + ROW_H//2
    tx       = cx + AVATAR_R + 12
    owner    = esc(rd["owner"]["login"])
    name     = esc(rd["name"])
    desc     = esc(trim(rd.get("description") or ""))
    lang     = rd.get("language") or ""
    star_s   = fmt_stars(stars)
    pr_s     = f"{prs} PR{'s' if prs>1 else ''} merged"
    repo_url = esc(rd["html_url"])
    avatar   = rd.get("_avatar_b64", "")

    L.append(f'<a href="{repo_url}" target="_blank">')
    L.append(f'  <rect x="{PAD}" y="{y+2}" width="{W-2*PAD}" height="{ROW_H-4}" rx="6" fill="{bg}"/>')

    # Rank
    L.append(f'  <text x="{PAD+11}" y="{cy+4}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="10" fill="#2e2e2e" text-anchor="middle">{i+1:02d}</text>')

    # Avatar circle + embedded image
    L.append(f'  <clipPath id="av{i}"><circle cx="{cx}" cy="{cy}" r="{AVATAR_R}"/></clipPath>')
    L.append(f'  <circle cx="{cx}" cy="{cy}" r="{AVATAR_R}" fill="#222" stroke="#2a2a2a" stroke-width="1"/>')
    if avatar:
        L.append(f'  <image href="{avatar}" x="{cx-AVATAR_R}" y="{cy-AVATAR_R}" width="{AVATAR_R*2}" height="{AVATAR_R*2}" clip-path="url(#av{i})"/>')

    # Owner / repo name
    owner_w = len(owner)*6.6 + 20
    L.append(f'  <text x="{tx}" y="{cy-5}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="11" fill="#4a4a4a">{owner} /</text>')
    L.append(f'  <text x="{tx+owner_w}" y="{cy-5}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="12" font-weight="700" fill="#e0e0e0">{name}</text>')

    # Description
    L.append(f'  <text x="{tx}" y="{cy+12}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="10" fill="#363636">{desc}</text>')

    # Right side meta
    right = W - PAD - 16

    # PR badge
    badge_w = len(pr_s)*6.5 + 18
    bx = right - badge_w
    L.append(f'  <rect x="{bx}" y="{cy-10}" width="{badge_w}" height="17" rx="4" fill="#0d1f0d"/>')
    L.append(f'  <text x="{bx+badge_w/2:.0f}" y="{cy+2}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="9" fill="#3a7a3a" text-anchor="middle">{pr_s}</text>')

    # Language dot + name
    if lang:
        lang_x = bx - len(lang)*6.5 - 20
        L.append(f'  <circle cx="{lang_x}" cy="{cy}" r="5" fill="{lang_color(lang)}"/>')
        L.append(f'  <text x="{lang_x+10}" y="{cy+4}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="10" fill="#3e3e3e">{esc(lang)}</text>')
        star_x = lang_x - 12
    else:
        star_x = bx - 12

    # Stars (star unicode U+2605 = ★, safe in SVG)
    L.append(f'  <text x="{star_x}" y="{cy+4}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="11" fill="#666" text-anchor="end">&#9733; {star_s}</text>')
    L.append('</a>')

# Footer
fy = total_h - FOOTER_H + 18
L.append(f'<line x1="{PAD}" y1="{fy-8}" x2="{W-PAD}" y2="{fy-8}" stroke="#181818" stroke-width="1"/>')
L.append(f'<text x="{PAD}" y="{fy+10}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="9" fill="#282828">// repos with more than {min_s} stars · sorted by stars · auto-updated weekly</text>')
L.append(f'<text x="{W-PAD}" y="{fy+10}" font-family="\'SF Mono\',\'Fira Code\',monospace" font-size="9" fill="#222" text-anchor="end">{esc(user)}.github.io</text>')
L.append('</svg>')

with open("contributions.svg","w") as f: f.write("\n".join(L))
print(f"Done: {max_rows} entries.")
