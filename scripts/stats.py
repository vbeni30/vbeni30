"""Builds dist/stats.svg (repos, stars, followers, top languages) with the Geist font embedded.
Runs inside GitHub Actions. Set MOCK=1 to render sample numbers without calling the API."""
import base64, html, json, os, sys, urllib.request

USER = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "vbeni30"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/stats.svg"
INK, MUTED, ACCENT, CARD, BORDER = "#E6EDF3", "#8B949E", "#58A6FF", "#161B22", "#30363D"
SHADES = ["#58A6FF", "#79C0FF", "#388BFD", "#A5D6FF", "#6E7681"]

def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-stats", "Accept": "application/vnd.github+json",
                                               **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def collect():
    if os.environ.get("MOCK"):
        return dict(repos=14, stars=9, followers=6, following=5, langs={"TypeScript": 5200, "JavaScript": 2100, "Python": 1700, "CSS": 800, "HTML": 400})
    u = api(f"https://api.github.com/users/{USER}")
    repos, page = [], 1
    while page <= 5:
        chunk = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += chunk
        if len(chunk) < 100: break
        page += 1
    own = [r for r in repos if not r.get("fork")]
    langs = {}
    for r in own[:40]:
        try:
            for k, v in api(r["languages_url"]).items(): langs[k] = langs.get(k, 0) + v
        except Exception:
            pass
    return dict(repos=len(own), stars=sum(r.get("stargazers_count", 0) for r in own),
                followers=u.get("followers", 0), following=u.get("following", 0), langs=langs)

def font(w):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "assets", "fonts", f"geist-{w}.woff2"), "rb") as f:
        return base64.b64encode(f.read()).decode()

def render(d):
    W, H = 960, 330
    esc = lambda t: html.escape(str(t), quote=False)
    body = f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="{CARD}" stroke="{BORDER}" stroke-width="1.5"/>'
    metrics = [("Repositories", d["repos"]), ("Stars earned", d["stars"]), ("Followers", d["followers"]), ("Following", d["following"])]
    colw = (W - 80) / 4
    for i, (label, val) in enumerate(metrics):
        x = 40 + i * colw
        body += f'<text x="{x:.0f}" y="96" font-size="54" font-weight="600" letter-spacing="-0.03em" fill="{INK}">{esc(val)}</text>'
        body += f'<text x="{x:.0f}" y="128" font-size="17" fill="{MUTED}">{label}</text>'
    body += f'<rect x="40" y="160" width="{W-80}" height="1.5" fill="{BORDER}"/>'
    langs = sorted(d["langs"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs) or 1
    top = langs[:4]; rest = sum(v for _, v in langs[4:])
    if rest: top.append(("Other", rest))
    body += f'<text x="40" y="206" font-size="17" font-weight="600" fill="{INK}">Top languages</text>'
    if not langs:
        body += f'<text x="40" y="250" font-size="17" fill="{MUTED}">No public code yet.</text>'
    else:
        bx, bw, by = 40, W - 80, 224
        body += f'<clipPath id="c"><rect x="{bx}" y="{by}" width="{bw}" height="14" rx="7"/></clipPath><g clip-path="url(#c)">'
        x = bx
        for i, (name, v) in enumerate(top):
            w = bw * v / total
            body += f'<rect x="{x:.1f}" y="{by}" width="{w+0.5:.1f}" height="14" fill="{SHADES[i % len(SHADES)]}"/>'
            x += w
        body += '</g>'
        lx = 40
        for i, (name, v) in enumerate(top):
            pct = f"{100 * v / total:.0f}%"
            body += f'<rect x="{lx}" y="272" width="10" height="10" rx="3" fill="{SHADES[i % len(SHADES)]}"/>'
            body += f'<text x="{lx+18}" y="282" font-size="16" fill="{INK}">{esc(name)}<tspan fill="{MUTED}"> {pct}</tspan></text>'
            lx += 18 + len(name) * 9.2 + 52
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
<title>GitHub stats for {esc(USER)}</title>
<style>
@font-face{{font-family:'Geist';font-weight:400;src:url(data:font/woff2;base64,{font(400)}) format('woff2');}}
@font-face{{font-family:'Geist';font-weight:600;src:url(data:font/woff2;base64,{font(600)}) format('woff2');}}
text{{font-family:'Geist',system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;}}
@media (prefers-color-scheme: light){{
[fill="#E6EDF3"]{{fill:#1F2328}}[fill="#8B949E"]{{fill:#57606A}}[fill="#B6BEC8"]{{fill:#424A53}}
[fill="#58A6FF"]{{fill:#0969DA}}[fill="#161B22"]{{fill:#F6F8FA}}[fill="#30363D"]{{fill:#D0D7DE}}
[stroke="#58A6FF"]{{stroke:#0969DA}}[stroke="#30363D"]{{stroke:#D0D7DE}}[stop-color="#58A6FF"]{{stop-color:#0969DA}}
[fill="#79C0FF"]{{fill:#218BFF}}[fill="#A5D6FF"]{{fill:#80CCFF}}[fill="#388BFD"]{{fill:#0550AE}}[fill="#6E7681"]{{fill:#8C959F}}
}}
</style>
{body}
</svg>'''

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(collect()))
    print("wrote", OUT)
