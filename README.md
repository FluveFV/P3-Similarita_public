# P3-Similarita

Specifiche e contesto:
- ```tipologia```: product-template
-  ```dominio```: PA

Implementazione di funzione di similarità tra organizzazioni per facilitare processi decisionali sulle tassonomie di progetti Family in Italia e Family Audit. 
Il codice è pensato per simulare un'interazione con i dati tramite linea di comando per facilitare l'adattamento a front end / interfaccia.

I due script ```SimilaritaComuni.py``` e ```SimilaritaAziende.py``` forniscono automaticamente le seguenti statistiche riguardanti i piani dei rispettivi domini:

- similarità tramite scelta di parametri per i Comuni coinvolti. Per i Comuni, è possibile scegliere un parametro o una combinazione di parametri (anche tutti) tra
  - Azioni eseguite (voci della tassonomia)
  - Anni di attività
  - Macroambiti dei piani
  - Campi dei piani
  - Distanza dal Capoluogo
  - Saldo popolazione 1992-2022
  - Popolazione (al 2022)
  - Densità (ab. / $$km^2$$ )
  - Altitudine
  
- similarità tramite scelta di parametri per le organizzazioni coinvolte. Per le organizzazioni coinvolte, è possibile scegliere un parametro, una combinazione di parametri o tutti tra:
  - Azioni eseguite (voci della tassonomia)
  - Anni di attività
  - Macroambiti dei piani
  - Campi dei piani
  - Dimensione dell'organizzazione
  - Settore dell'organizzazione
  - Popolazione residente nel Comune dell'organizzazione
  - Composizione statistica dell'organico (percentuale di uomini e donne impiegate*; part-time, età media, e altre 90 variabili sull'organico aziendale)
 
*Non sono stati collezionati dati di genere non binario dalle organizzazioni e dall'agenzia per la Coesione Sociale. 

### Esempi di dati, input e output
I dati sono disponibili nella cartella [data](https://github.com/FluveFV/P3-Similarita/tree/main/data). 
All'interno delle cartelle [outputComuni](https://github.com/FluveFV/P3-Similarita/tree/main/outputComuni) e [outputAziende]() sono presenti i risultati attesi del codice. 

Attualmente durante l'esecuzione del codice si richiedono i seguenti input che variano in base alla disponibilità nei dati. L'input viene automaticamente ricollegato alle possibili scelte di variabili nel dataset tramite la libreria ```fuzzywuzzy```.
#### Codice per similarità tra Comuni:
|Natura dell'input|Tipo di formato dell'input|Example|
|---|---|---|
|Parametri per la similarità|testo|vengono forniti gli esempi durante l'esecuzione|
|Nome dell'organizzazione (Comune / IDOrganizzazione)|testo|_idem_ sopra|

Viene quindi calcolata la similarità tra ogni Comune e tutti gli altri Comuni in base ai parametri selezionati dall'utente, e si produce un dataset che verrà salvato automaticamente nella cartella di output. 

- La similarità tramite parametri di variabili categoriali (ad es. l'insieme di azioni compiute da un Comune o un'organizzazione) viene calcolata tramite la metrica di [Jaccard](https://en.wikipedia.org/wiki/Jaccard_index).
- La similarità tramite parametri di variabili numeriche (ad es. l'altitudine di un Comune, oppure le percentuali di donne in un'Organizzazione) viene calcolata tramite la distanza euclidea tra due punti nello spazio delle variabili. 

Nel caso in cui più di un parametro venga selezionato, viene calcolata la media tra le similarità media dei parametri in generale e la similarità **divisa per tipologia di dato**, risultando in un indice riassuntivo della similarità. La singola similarità per parametro rimane ovviamente consultabile. 


### Come eseguire il codice:
1. Prima di eseguire il codice, assicurarsi di aver installato le versioni compatibili di Python e delle sue dipendenze in [requisiti](https://github.com/FluveFV/P3-Similarita/blob/main/requirements.txt).
2. Nella posizione desiderata, aprire il terminale ed eseguire il download della repo:
```gh repo clone FluveFV/P3-Similarita.git```
3. Di seguito, utilizzare python per eseguire il singolo script, ad es. :
```python SimilaritaComuni.py```
4. Seguire le istruzioni sullo schermo in contemporanea alla lettura del codice per simulare un'interazione da linea di comando con i dati. Il codice è stato commentato appositamente. Assicurarsi di stare inserendo i valori nel formato richiesto o non verranno considerati correttamente. 

--- 
🇺🇸-🏴󠁧󠁢󠁥󠁮󠁧󠁿 ENGLISH

## Specifications and Context
- `kind`: product-template  
- `ai`: NLP  
- `domain`: PA  

Implementation of an **organization similarity** function to support decision-making processes on the taxonomies of Family projects in Italy and Family Audit.  
The code is designed to simulate a command-line interaction with the data, to make it easier to adapt to a front-end/interface.

The two scripts, `SimilaritaComuni.py` and `SimilaritaAziende.py`, automatically produce the following statistics for the plans in their respective domains:

- **Similarity based on parameters for Municipalities.**  
  You can choose one parameter or any combination (up to all) from:
  - Actions performed (taxonomy entries)  
  - Years of activity  
  - Macro-areas of the plans  
  - Plan fields  
  - Population balance (1992–2022)  
  - Distance from the Province capital
  - Population (in 2022)
  - Density (hab. / $km^2$ )
  - Altitude  

- **Similarity based on parameters for Organizations.**  
  You can choose one parameter, any combination of parameters, or all, from:
  - Actions performed (taxonomy entries)  
  - Years of activity  
  - Macro-areas of the plans  
  - Plan fields
  - Sector of the organization
  - Population residing in the same Municipality as the organization
  - Statistical composition of staff (percentage of men and women employed*; part-time, average age, plus 90 other variables on company staffing)

  *Note: Non-binary gender data were not collected by the organizations or the Agency for Social Cohesion.

---

## Example Data, Input & Output

- All raw data are in the [data](https://github.com/FluveFV/P3-Similarita/tree/main/data) folder.  
- The expected results of each script are in [outputComuni](https://github.com/FluveFV/P3-Similarita/tree/main/outputComuni) and `[outputAziende]()`.


When you run the scripts, they will prompt for inputs that depend on what’s available in the data.  

User input is automatically matched to the closest available variable names using `fuzzywuzzy`.

### Similarity for Municipalities

| Input Type                         | Input Format | Example                         |
|------------------------------------|--------------|---------------------------------|
| Parameters for similarity          | text         | (examples are shown at runtime) |
| Name of the organization (Municipality / IDorganizzazione)| text |_idem_ above|


Then, the similarity between each Municipality (or organization) and all the other Municipalities (or organizations, respectively) is computed based on the parameters chosen by the user, and a dataset will be automatically saved in the output folder.

- Similarity between parameters that represent categorical variables (e.g. the set of actions executed by Municipalities or organizations) is computed using the [Jaccard index](https://en.wikipedia.org/wiki/Jaccard_index).
- Similarity between numerical variables (e.g. the altitude of a Municipality or the percentage of women in an organization) is computed using the euclidean distance between two points in feature space.

In the event that more than one parameter is selected, an average similarity between parameters is computed, resulting in a summary index of similarities. The individual similarities obviously remain available in the output.

---

## How to Run the Code

1. Make sure you have compatible versions of Python and all dependencies listed in [requirements](https://github.com/FluveFV/P3-Similarita/blob/main/requirements.txt).  
2. In your terminal, navigate to the folder where you want to work and clone/download the repo:
```gh repo clone FluveFV/P3-Similarita.git```
3. Then, use python to execute the script such as in:
```python SimilaritaComuni.py```
4. Follow the instructions on the screen (which will be in Italian) to simulate an interaction by command line with data. I advise to also look at the commented code in the meantime, ensuring to insert values in the format requested.






















