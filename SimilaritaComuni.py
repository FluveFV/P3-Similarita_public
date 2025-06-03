import os
import pandas as pd
import numpy as np
from fuzzywuzzy import process
from tqdm import tqdm
from scipy.stats import linregress
from collections import OrderedDict
import pprint
from functools import reduce

####################################
# Preparazione dati (387ms)
dati_geografici = pd.read_excel('data/altimetrie.xlsx').rename(columns={'PRO_COM':'codice_istat'})

piani_comunali = pd.read_parquet('data/piani_comunali.gzip')
piani_comunali['data_det_assegnazione'] = pd.to_datetime(piani_comunali.data_det_assegnazione)
piani_comunali = pd.merge(piani_comunali, dati_geografici[['NOME', 'codice_istat']], on = 'codice_istat')
irvapp = pd.read_stata('data/AIxPA 1992-2022 FINAL VERSION.dta').rename(columns={'codicecomune':'codice_istat'})
irvapp = pd.merge(irvapp, dati_geografici[['NOME', 'codice_istat']], on = 'codice_istat')

fp = 'outputComuni/'

####################################
# Scelta dei parametri di similarità
#In questo caso, è necessario limitare la scelta a una serie di parametri standard: 
# proposte nel seguente dizionario:#In questo caso, è necessario limitare la scelta a una serie di parametri standard: 
# proposte nel seguente dizionario:
scelte = {
    'Azioni eseguite (voci della tassonomia)':'ID_tassonomia', 
    'Anni di attività':'anno_compilazione', 
    'Macroambiti dei piani': 'codice_macro', # Sono solo 5 possibilità di codice_macro per azione, quindi non molto utile su piani numerosi (molti enti saranno molto simili)
    'Campi dei piani': 'codice_campo',    
    'Distanza dal Capoluogo':'distanza_1',
    'Saldo popolazione 1992-2022':'saldo_popolazione',  
    'Popolazione (al 2022)':'popolomedia',
    'Densità (ab. / km2)':'densita',
    'Altitudine':'MEDIA'
}
scelte = OrderedDict(sorted(scelte.items(), key=lambda t: t[0]))

parametri = []
print('Parametri disponibili:')
pprint.pp(list(scelte.keys()), indent=4,)
print()
print('Inserire un parametro per identificare la similarità \n(premere Invio per aggiungere un altro parametro)\n(inserire END per terminare)')

while True:
    entry = input()  
    if entry.strip() == "END":
        break
    parametri.append(entry.strip())

chiavi = [process.extractOne(i, scelte.keys())[0] for i in set(parametri)]
variabili = [ scelte[c] for c in chiavi]
print('Parametri individuati:')
pprint.pp(chiavi)
print()

drop = ['comune_breve', 'ID_piano', 'ID_azione', 'titolo',
       'obiettivo', 'descrizione', 'assessorato', 'tipologia_partnership',
       'altre_organizzazioni_coinvolte', 'indicatore', 'azione', 'codice',
       'descrizione_codice_macro', 'descrizione_codice_campo',
       'ID_organizzazione', 'premessa', 'valutazione_globale', 'status',
       'comune_x', 'dimensione', 'num_det_assegnazione',
       'data_det_assegnazione', 'numero_registro_family_trentino',
       'num_det_revoca', 'data_det_revoca', 'COD_REG', 'COD_PRO', 'ALT_MAX', 'RANGE', 'ALT_MIN', 'MEDIANA', 'STD',
       'comune_y',]

user_input = input('Comune di interesse (e.g. Todi, Padova, Alghero, Cavedago...):') 
choices = [(name, 'piani_comunali') for name in piani_comunali.NOME.unique()] + \
          [(name, 'irvapp') for name in irvapp.NOME.unique()]

match, score = process.extractOne(user_input, [name for name, _ in choices])
source = next(src for name, src in choices if name == match)

mask = globals()[source].NOME == match
globals()[source][mask].NOME.values[0]

####################################
# Calcolo della similarità, diviso per dati categoriali e dati numerici (2.88s)
piani_group = piani_comunali.groupby(["comune_breve", "codice_istat"]).agg(set).reset_index()
stat_irvapp = irvapp.sort_values(by=['codice_istat','anno']).drop_duplicates('codice_istat', keep='last')
agg_irvapp = irvapp.groupby(['codice_istat']).agg(list).reset_index()

agg = pd.merge(piani_group.drop(columns='NOME'), dati_geografici, on='codice_istat', how='outer')
agg = pd.merge(agg, stat_irvapp.drop(columns='NOME'), on = 'codice_istat', how='left')
agg = agg[~(agg.altitudine.isna() & agg.ID_azione.isna())].drop(columns=drop)
agg = agg[agg.NOME.isin(piani_comunali.NOME.to_list() + [match])]
agg_irvapp = agg_irvapp[agg_irvapp['codice_istat'].isin(agg.codice_istat)]

# importante: se per qualche motivo non c'è nei dati aggregati il comune, non si può proseguire
try:
    assert match in agg.NOME.to_list()
except:
    print('Organizzazione non identificata. Input:', match)
    exit()

# Variabili non presenti nei dati (da calcolare)
if 'densita' in variabili and 'densita' not in agg.columns:
    
    agg['densita'] = agg['popolomedia'] / agg['SUPERFICIE (in KMQ)']
    
if 'saldo_popolazione' in variabili and 'saldo_popolazione' not in agg.columns:    
            
    x = agg_irvapp['anno'].values
    y = agg_irvapp['popolazionefineperiodo'].values
    
    reg = [linregress(x[i], y[i]) if agg_irvapp.anno.values[i] != 0 else [0,0,0,0,0] for i in range(agg_irvapp.shape[0])]
    t = pd.DataFrame(reg, 
                     columns=['slope','intercept', 'r_value', 'p_value', 'st_e'])            
    t['codice_istat'] = agg_irvapp['codice_istat'].astype(int).values
    t = t[['codice_istat', 'slope']]
    t.columns = ['codice_istat', 'saldo_popolazione']
    agg =  agg.merge(t, 
                     on='codice_istat',
                     how='left', 
                     suffixes=('', '_new'))

agg = agg[list(variabili) + ['NOME', 'codice_istat']]

parametri = {v:k for k, v in scelte.items()}
def jaccard_similarity(set1, set2):
    """
    Calcola la dimensione dell'intersezione tra due insiemi 
    divisa per la dimensione dell'unione tra due insiemi.
    Riporta uno score tra 0 e 1. Si usa questa funzione
    per calcolare la quantità di elementi in comune 
    tra due organizzazioni.
    Input: 
        - set1: insieme che rappresenta l'intersezione;
        - set2: insieme che rappresenta l'unione    
    """
    try: 
        set1 = set(set1)
        set2 = set(set2)
    except TypeError:
        return 0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return round(intersection / union, 3) if union else 0  # else nel remoto caso in cui vengano in futuro aggiunti comuni senza azioni

    
def similarità_numerica(v, data):    
    
    D = []
    index = data.index
    for i in index:
        for j in index:
            if i < j:
                id1 = data.loc[i, 'NOME']
                id2 = data.loc[j, 'NOME']
                dist = abs(data.loc[i, v] - data.loc[j, v])
                D.append((id1,id2,dist))    
    col = f'similarità_{parametri[v].lower()}'
    df =  pd.DataFrame(D, columns=['comune_1','comune_2', col])
    
    df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
    
    df[col] = 1/(1+df[col])    

    return df

def similarità_categoriale(v, data):
    J = []
    index = data.index
    for i in index:
        for j in index:
            if i < j:
                id1 = data.loc[i, 'NOME']
                id2 = data.loc[j, 'NOME']
                sim = jaccard_similarity(data.loc[i, v], data.loc[j, v])
                J.append((id1,id2,sim))    
    
    df = pd.DataFrame(J, columns=['comune_1','comune_2', f'similarità_{parametri[v].lower()}'])    
    return df

l = []

for v in tqdm(variabili):
    tipo = 'categoriale' if v in ['codice_campo', 'anno_compilazione', 'ID_tassonomia', 'codice_macro'] else 'numerico'
    r = similarità_categoriale(v, agg) if tipo == 'categoriale' else similarità_numerica(v, agg)
    l.append(r)
    
similarita = reduce(lambda left, right: pd.merge(left, right, how='left', on=['comune_1', 'comune_2']), l)
l = []
similarita['similarità_Media generale'] = (similarita.filter(like='similarità_').fillna(0).mean(axis=1)).round(3)

if len(set(['densita', 'distanza_1', 'popolomedia', 'saldo_popolazione', 'MEDIA']) & set(variabili)) >= 2: #se ci sono almeno due elementi tra i parametri e le caratteristiche
    var = [('similarità_'+parametri[i]).lower() for i in set(['densita', 'distanza_1', 'popolomedia', 'saldo_popolazione', 'ALT_MIN']) & set(variabili)]    
    similarita['similarità Media Caratteristiche comunali'] = (similarita[var].fillna(0).mean(axis=1)).round(3)
if len(set(['anno_compilazione', 'ID_tassonomia','codice_campo', 'codice_macro']) & set(variabili)) >= 2: #se ci sono almeno due elementi tra i parametri e i piani
    var = [('similarità_'+parametri[i]).lower() for i in set(['anno_compilazione', 'ID_tassonomia','codice_campo', 'codice_macro']) & set(variabili)]    
    similarita['similarità Media Piani comunali'] = (similarita[var].fillna(0).mean(axis=1)).round(3)

os.makedirs(fp, exist_ok=True)
similarita.sort_values(by='similarità_Media generale').drop_duplicates(inplace=True)
########## Cambia questa parte per salvare tutte le similarità o solo quelle che contengono l'organizzazione focus. 
similarita = similarita[(similarita.comune_1 == match) | (similarita.comune_2 == match)].sort_values(by='similarità_Media generale', ascending=False)
########################
similarita.to_csv(f'{fp}similarita_comuni.csv', index=False)
print(f'Dataset con similarità (per parametri {chiavi}) prodotto e salvato in {fp}similarita_comuni.csv')
l = []



