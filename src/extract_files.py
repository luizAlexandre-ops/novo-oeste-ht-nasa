import requests, pathlib

def baixar(url, destino="dados"):
    pathlib.Path(destino).mkdir(parents=True, exist_ok=True)
    caminho = pathlib.Path(destino) / url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(caminho, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return caminho

base = "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/"
for nome in ["ldem_75s_120m.lbl", "ldem_75s_120m.img"]: 
    baixar(base + nome)
