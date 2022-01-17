
# Python installations

```bash
conda create --name are219 python=3.7
conda activate are219
conda config --set channel_priority strict
conda install -y matplotlib descartes geopandas fiona poppler shapely openpyxl ratelimiter boto3 pandas timezonefinder seaborn keyring
pip install purpleair
```