import requests
import pathlib

def baixar(url, destino="dados"):

    pasta = pathlib.Path(destino)
    pasta.mkdir(parents=True, exist_ok=True)

    caminho = pasta / url.split("/")[-1]

    if caminho.exists():
        print(f"{caminho} já existe, pulando download.")
        return caminho

    print(f"Iniciando download: {url}")

    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        with open(caminho, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print(f"Download concluído: {caminho}")

    return caminho

base_lua = (
    "https://pds-geosciences.wustl.edu/"
    "lro/lro-l-lola-3-rdr-v1/"
    "lrolol_1xxx/data/lola_gdr/polar/img/"
)

arquivos_lua = [
    "ldem_75s_120m.lbl",
    "ldem_75s_120m.img"
]

for nome in arquivos_lua:
    baixar(
        base_lua + nome,
        destino="dados"
    )

url_iluminacao_lua = (
    "https://pgda.gsfc.nasa.gov/data/MoonIllumination/"
    "AVGVISIB_85S_060M_201608.TIF"
)

baixar(
    url_iluminacao_lua,
    destino="dados"
)