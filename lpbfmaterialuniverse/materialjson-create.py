import pandas as pd
import json

# Excel dosyasını oku
df = pd.read_excel('LPBF_Material_Universe.xlsx')

# Her sütunu listeye dönüştür
material_data = {}
for col in df.columns:
    # NaN olmayanları al, stringe çevir, baştaki/sondaki boşlukları kırp
    items = [str(x).strip() for x in df[col].dropna()]
    material_data[col.strip()] = items

# JSON olarak kaydet
with open('materialData.json', 'w', encoding='utf-8') as f:
    json.dump(material_data, f, ensure_ascii=False, indent=2)
