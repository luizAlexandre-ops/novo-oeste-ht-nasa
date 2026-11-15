from pathlib import Path
import requests

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

PASTA_DESTINO = RAIZ_PROJETO / "dados" / "mars" / "mola"

URL_BASE = (
    "https://pds-geosciences.wustl.edu/"
    "mgs/urn-nasa-pds-mgs_mola_topography_derived/"
    "meg128/"
)

ARQUIVOS = [
    "megt44n180hb.img",
    "megt44n180hb.xml",
    "megt44n180hb.lbl",
    "megt44n180hb.hdr"
]

def baixar(url, destino):

    if destino.exists():
        print(f"{destino.name} já existe. Pulando download.")
        return

    arquivo_temporario = destino.with_suffix(
        destino.suffix + ".part"
    )

    print(f"Iniciando download: {url}")

    try:
        resposta = requests.get(
            url,
            stream=True,
            timeout=60
        )

        resposta.raise_for_status()

        with open(arquivo_temporario, "wb") as arquivo:

            for bloco in resposta.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:
                    arquivo.write(bloco)

        arquivo_temporario.replace(destino)

        print(f"Download concluído: {destino.name}")

    except requests.RequestException as erro:

        print(f"Erro ao baixar {destino.name}: {erro}")

        if arquivo_temporario.exists():
            arquivo_temporario.unlink()

def baixar_dados_marte():

    PASTA_DESTINO.mkdir(
        parents=True,
        exist_ok=True
    )

    for nome_arquivo in ARQUIVOS:

        url = URL_BASE + nome_arquivo

        destino = PASTA_DESTINO / nome_arquivo

        baixar(url, destino)

if __name__ == "__main__":

    baixar_dados_marte()

    print("\nColeta de dados de Marte finalizada.")
