import requests
import pathlib
import earthaccess

def baixar(url, destino="data"):

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


# LOLA - Modelo digital de elevação
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
        destino="data"
    )


# Iluminação lunar
url_iluminacao_lua = (
    "https://pgda.gsfc.nasa.gov/data/MoonIllumination/"
    "AVGVISIB_85S_060M_201608.TIF"
)

baixar(
    url_iluminacao_lua,
    destino="data"
)


# LOLA - Regiões permanentemente sombreadas (PSR)
url_psr = (
    "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
    "LPSR_80S_20MPP_ADJ.TIF"
)

baixar(
    url_psr,
    destino="data"
)

# Diviner - temperatura média e máxima anuais (polo sul)
base_diviner = (
    "https://pds-geosciences.wustl.edu/"
    "lro/urn-nasa-pds-lro_diviner_derived1/"
    "data_derived_prp/"
)

for nome in ["dlre_prp_south.tab", "dlre_prp_south.xml"]:
    baixar(
        base_diviner + nome,
        destino="data"
    )

# # NASA Earthdata - temperatura (MOD11C3) e neve (MOD10CM), Terra/MODIS
# earthaccess.login(persist=True)   # pede usuário e senha do Earthdata na 1ª vez

# periodo = ("2025-01-01", "2025-12-31")

# for sigla, versao in [("MOD11C3", "061"), ("MOD10CM", "61")]:
#     resultados = earthaccess.search_data(
#         short_name=sigla,
#         version=versao,
#         temporal=periodo,
#     )
#     print(sigla, "-", len(resultados), "arquivos encontrados")

#     earthaccess.download(resultados, "data")