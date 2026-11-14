import rasterio, numpy as np

caminho = "dados/AVGVISIB_85S_060M_201608.TIF"

with rasterio.open(caminho) as src:
    dados = src.read(1, masked=True)

    escala = src.scales[0]
    offset = src.offsets[0]

    iluminacao = dados.astype(np.float32) * escala + offset

    iluminacao_pct = iluminacao * 100

    valores = iluminacao_pct.compressed()

    print("Iluminação solar (%)")
    print("Mínimo:", np.min(valores))
    print("Máximo:", np.max(valores))
    print("Média:", np.mean(valores))
    print("Mediana:", np.median(valores))