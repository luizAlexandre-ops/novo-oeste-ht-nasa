from pathlib import Path
import math
import numpy as np
import rasterio
from rasterio.windows import Window

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

ARQUIVO_MOLA = (
    RAIZ_PROJETO
    / "dados"
    / "mars"
    / "mola"
    / "megt44n180hb.img"
)

# Centro de referência de Arcadia Planitia
LATITUDE = 39.8
LONGITUDE = 202.1

# Área de análise: 50 km x 50 km
TAMANHO_AREA_KM = 50

# Raio de referência de Marte informado no .lbl
RAIO_MARTE_M = 3_396_000

def coordenadas_para_pixel(imagem, latitude, longitude):
    """
    Converte latitude e longitude planetocêntricas
    em coordenadas de pixel do raster MOLA.

    O raster utiliza projeção cilíndrica simples,
    com meridiano central em 180 graus.
    """

    x = RAIO_MARTE_M * math.radians(longitude - 180)
    y = RAIO_MARTE_M * math.radians(latitude)

    linha, coluna = imagem.index(x, y)

    return linha, coluna

def calcular_estatisticas(dados):
    valores = dados.compressed()

    if valores.size == 0:
        print("Nenhum dado válido encontrado.")
        return

    print(f"Pixels válidos: {valores.size}")
    print(f"Elevação mínima: {valores.min():.2f} m")
    print(f"Elevação máxima: {valores.max():.2f} m")
    print(f"Elevação média: {valores.mean():.2f} m")

def analisar_mola():

    if not ARQUIVO_MOLA.exists():
        print(f"Arquivo não encontrado: {ARQUIVO_MOLA}")
        return

    with rasterio.open(ARQUIVO_MOLA) as imagem:

        print("\nInformações do raster MOLA")
        print(f"Dimensões: {imagem.width} x {imagem.height}")
        print(f"Resolução: {imagem.res}")
        print(f"NoData: {imagem.nodata}")
        print(f"CRS: {imagem.crs}")
        print(f"Transformação: {imagem.transform}")

        zeros = 0
        total = 0

        quantidade = 0
        soma = 0.0
        minimo = float("inf")
        maximo = float("-inf")

        # Leitura em blocos para economizar memória
        for _, janela in imagem.block_windows(1):

            bloco_original = imagem.read(
                1,
                window=janela,
                masked=False
            )

            zeros += np.count_nonzero(bloco_original == 0)
            total += bloco_original.size

            bloco = imagem.read(
                1,
                window=janela,
                masked=True
            )

            valores = bloco.compressed()

            if valores.size == 0:
                continue

            quantidade += valores.size
            soma += valores.sum(dtype=np.float64)

            minimo = min(minimo, valores.min())
            maximo = max(maximo, valores.max())

        print("\nVerificação dos pixels zero")
        print(f"Pixels com valor zero: {zeros}")
        print(f"Percentual de zeros: {zeros / total * 100:.4f}%")

        print("\nEstatísticas do arquivo MOLA")
        print(f"Pixels válidos: {quantidade}")
        print(f"Elevação mínima: {minimo:.2f} m")
        print(f"Elevação máxima: {maximo:.2f} m")
        print(f"Elevação média: {soma / quantidade:.2f} m")

        linha, coluna = coordenadas_para_pixel(
            imagem,
            LATITUDE,
            LONGITUDE
        )

        print("\nLocalização de Arcadia Planitia")
        print(f"Latitude: {LATITUDE}° N")
        print(f"Longitude: {LONGITUDE}° E")
        print(f"Pixel central: linha={linha}, coluna={coluna}")

        resolucao_km = abs(imagem.res[0]) / 1000

        largura = round(TAMANHO_AREA_KM / resolucao_km)
        altura = largura

        janela = Window(
            col_off=coluna - largura // 2,
            row_off=linha - altura // 2,
            width=largura,
            height=altura
        )

        # Verifica se a janela está dentro do raster
        if (
            janela.col_off < 0
            or janela.row_off < 0
            or janela.col_off + janela.width > imagem.width
            or janela.row_off + janela.height > imagem.height
        ):
            print("Erro: a área de análise ultrapassa os limites do raster.")
            return

        dados_arcadia = imagem.read(
            1,
            window=janela,
            masked=True
        )

        print("\nEstatísticas da área de referência de Arcadia Planitia")
        print(f"Tamanho do recorte: {largura} x {altura} pixels")
        print(f"Área aproximada: {largura * resolucao_km:.2f} x "
              f"{altura * resolucao_km:.2f} km")

        calcular_estatisticas(dados_arcadia)

if __name__ == "__main__":
    analisar_mola()
