"""Create deterministic SYNTHETIC Cookie-Cats-shaped experiment data."""
from pathlib import Path
import numpy as np
import pandas as pd
BASE=Path(__file__).resolve().parents[1]

def generate(n_per_group=45000,seed=44):
    rng=np.random.default_rng(seed)
    groups=np.array(['gate_30']*n_per_group+['gate_40']*n_per_group)
    rng.shuffle(groups)
    control=groups=='gate_30'
    p1=np.where(control,.448,.444)
    p7=np.where(control,.192,.181)
    r1=rng.binomial(1,p1).astype(bool)
    r7=rng.binomial(1,p7).astype(bool)
    rounds=rng.negative_binomial(1.3,.073,len(groups))
    rounds[0]=49854  # visible demo outlier; retain in data and document it
    return pd.DataFrame({'userid':np.arange(10001,10001+len(groups)),
                          'version':groups,'sum_gamerounds':rounds,
                          'retention_1':r1,'retention_7':r7})

if __name__=='__main__':
    x=generate();x.to_csv(BASE/'data/raw/cookie_cats.csv',index=False)
    print(f'SYNTHETIC experiment: {len(x):,} players -> data/raw/cookie_cats.csv')
