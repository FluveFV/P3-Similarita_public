import os
import pandas as pd
import numpy as np
from fuzzywuzzy import process
from scipy.spatial.distance import pdist
import pprint
from collections import OrderedDict
from tqdm import tqdm
from itertools import combinations
from functools import reduce
####################################
#Preparazione dati (303ms)
piani_aziendali = pd.read_parquet('data/piani_aziendali.gzip')
tassonomia = pd.read_csv('data/tassonomia_aziende.csv', sep=';')
organico = pd.read_csv('data/organico_aziende_mean.csv')
settore = pd.read_csv('data/settore_aziende.csv', sep='|')
fp = 'outputOrganizzazioni/'
os.makedirs(fp, exist_ok=True)

####################################
# INPUT: selezione parametri per similarità
#In questo caso, è necessario limitare la scelta a una serie di parametri standard: 
# proposte nel seguente dizionario:
#In questo caso, è necessario limitare la scelta a una serie di parametri standard: 
# proposte nel seguente dizionario:
scelte = {
    'Azioni eseguite (voci della tassonomia)':'Label 0', 
    'Anni di attività':'anno_compilazione', 
    'Macroambiti dei piani': 'codice_macro',
    # Sono solo 5 possibilità di codice_macro per azione, quindi non molto utile su piani numerosi (molti enti saranno molto simili)
    'Campi dei piani': 'numero_codice_campo',
    'Settore dell\'organizzazione':'CODATECO_aggregato',
    'Dimensione dell\'organizzazione':'DIMENSIONE', 
    'Popolazione residente nel Comune dell\'organizzazione':'popolazione_classi_ordinali', 
    'Composizione statistica dell\'organico': 'organico'  #non esiste una colonna "organico" nei dati, ma serve un parametro per indicare tutti i dati sull'organico
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

# unfreeze per compilare automaticamente tutti i parametri
# parametri = ['Anni di attività',
#     'Azioni eseguite (voci della tassonomia)',
#     'Campi dei piani',
#     "Composizione statistica dell'organico",
#     "Dimensione dell'organizzazione",
#     'Macroambiti dei piani',
#     "Popolazione residente nel Comune dell'organizzazione",
#     "Settore dell'organizzazione"]

chiavi = [process.extractOne(i, scelte.keys())[0] for i in set(parametri)]
variabili = [scelte[c] for c in chiavi]
print('Parametri individuati:')
pprint.pp(chiavi)
print()

user_input = input('ID dell\'organizzazione di interesse (e.g. 25848641, 12303699, 24460126, 12344629, 11420379...):') 

# unfreeze per compilare automaticamente un utente
# user_input  = "25848641"
match, score = process.extractOne(user_input, piani_aziendali.IDOrganizzazione.tolist())

####################################
# Calcolo delle similarità (13.17s)

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
    return intersection / union if union else 0  # else nel remoto caso in cui vengano in futuro aggiunte organizzazioni senza azioni

parametri = {v:k for k, v in scelte.items()}
def similarità_numerica(v, data):    
    if v == 'organico':
        v = [i for i in organico.columns.tolist() if i.startswith('T') or i.startswith('F')]
    
    colname = f"similarità_{parametri[v if isinstance(v, str) else 'organico'].lower()}"

    ids = data['IDOrganizzazione'].tolist()
    vectors = data[v].values if isinstance(v, list) else data[[v]].values

    distances = pdist(vectors)
    pairs = list(combinations(ids, 2))

    records = [(id1, id2, dist) for (id1, id2), dist in zip(pairs, distances)]
    
    df = pd.DataFrame(records, columns=['IDOrganizzazione_1', 'IDOrganizzazione_2', colname])
    df[colname] = 1 / (1 + (df[colname].values - df[colname].min()) / (df[colname].max() - df[colname].min()))
    
    return df

def similarità_categoriale(v, data):
    J = []
    
    for i in data.index:
        for j in data.index:            
            if i < j:
                id1 = data.loc[i, 'IDOrganizzazione']
                id2 = data.loc[j, 'IDOrganizzazione']
                sim = jaccard_similarity(data.loc[i, v], data.loc[j, v])                
                J.append((id1,id2,sim))    
    df = pd.DataFrame(J, columns=['IDOrganizzazione_1','IDOrganizzazione_2', f'similarità_{parametri[v].lower()}'])    
    return df
# agg è un dataframe composto da un'aggregazione delle azioni per organizzazione:
    # per ogni riga - un'organizzazione e le liste di valori categoriali o numerici associategli
agg = piani_aziendali.groupby(["IDOrganizzazione"]).agg(set).reset_index()   #Si prendono gli elementi in una lista associati a un ente
if not match in agg.IDOrganizzazione.to_list():
    print('Organizzazione non identificata. Input:', match)
    exit()

agg = pd.merge(agg, settore, how = 'left').drop_duplicates(subset='IDOrganizzazione', keep='last')
agg = agg.merge(organico, how='outer')
variabili_no_org = [i for i in list(variabili) if not i.startswith('organico')]
columns = list(set(variabili_no_org + (organico.columns.tolist() if 'organico' in variabili else []) + ['IDOrganizzazione']))
agg = agg[columns]

l = []

for v in tqdm(variabili):    
    tipo = 'numerico' if v in ['organico', 'popolazione_classi_ordinali'] else 'categoriale'    
    r = similarità_categoriale(v, agg) if tipo == 'categoriale' else similarità_numerica(v, agg)
    l.append(r)    
similarita = reduce(lambda left, right: pd.merge(left, right, how='left', on=['IDOrganizzazione_1', 'IDOrganizzazione_2']), l)
l = []

# Calcolo medie

similarita['similarità_Media generale'] = (similarita.filter(like='similarità_').fillna(0).mean(axis=1)).round(3)

avg_piani = set(['anno_compilazione', 'ID_tassonomia','codice_campo', 'codice_macro'])
if len( avg_piani & set(variabili)) >= 2: #se ci sono almeno due elementi tra i parametri e i piani ha senso fare una media
    var = [('similarità_'+parametri[i]).lower() for i in avg_piani & set(variabili)]    
    similarita['similarità Media Piani delle organizzazioni'] = (similarita[var].fillna(0).mean(axis=1)).round(3)

avg_caratteristiche = set(['organico', 'popolazione_classi_ordinali', 'CODATECO_aggregato', 'DIMENSIONE'])
if len( avg_caratteristiche & set(variabili)) >= 2:
    var = [('similarità_'+parametri[i]).lower() for i in avg_caratteristiche & set(variabili)]
    similarita['similarità Media caratteristiche delle organizzazioni'] = (similarita[var].fillna(0).mean(axis=1)).round(3)


# Salvataggio dati 

os.makedirs(fp, exist_ok=True)
similarita.sort_values(by='similarità_Media generale').drop_duplicates(inplace=True)
########## Freeze / Cambia questa parte per salvare tutte le similarità o tienila nel codice per mantenere solo quelle che contengono l'organizzazione focus. 
similarita = similarita[(similarita.IDOrganizzazione_1 == match) | (similarita.IDOrganizzazione_2 == match)].sort_values(by='similarità_Media generale', ascending=False)
########################
similarita.to_csv(f'{fp}similarita_organizzazioni.csv', index=False)
print(f'Dataset con similarità (per parametri {chiavi}) prodotto e salvato in {fp}similarita_organizzazioni.csv')
l = []
