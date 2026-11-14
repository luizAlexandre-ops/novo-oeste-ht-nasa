from src.terrain.datasets.download import download_lola_dataset

if __name__ == "__main__":
    for path in download_lola_dataset():
        print(f"Saved {path}")