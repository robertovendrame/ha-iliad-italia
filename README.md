# Iliad Italia for Home Assistant

Custom integration non ufficiale per Home Assistant che legge i dati dell'Area Personale Iliad Italia.

> Stato: **testata con account Iliad reali**, inclusa la configurazione contemporanea di due SIM/account nella stessa istanza Home Assistant.

## Versione corrente

La prima release pubblica prevista è **v0.3.0**.

Le versioni pubblicate tramite GitHub Releases diventano il riferimento per installazione e aggiornamento tramite HACS, così Home Assistant non deve dipendere direttamente dallo stato corrente del branch `main`.

## Funzioni

Ogni account/SIM configurato crea un device separato con:

- Credito disponibile (`EUR`)
- Dati utilizzati (`GB`)
- Dati residui (`GB`)
- Dati totali calcolati (`GB`), ottenuti come usati + residui
- Percentuale dati utilizzati
- Percentuale dati residui
- Ultimo aggiornamento riuscito
- Binary sensor **Dati in esaurimento**
- Binary sensor **Credito basso**
- Pulsante **Aggiorna ora** per forzare un refresh immediato

L'integrazione supporta:

- più SIM/account Iliad nella stessa istanza Home Assistant;
- installazione della stessa integrazione su più istanze Home Assistant;
- configurazione da UI tramite `config_flow`;
- riautenticazione quando le credenziali non sono più valide;
- riconfigurazione del nome della SIM e delle credenziali;
- sessioni/cookie separati per ogni account configurato;
- intervallo di aggiornamento configurabile per ogni SIM da **1 a 24 ore**;
- refresh manuale per singola SIM;
- soglie dati configurabili per ogni SIM;
- soglia credito configurabile per ogni SIM;
- diagnostica Home Assistant senza username o password;
- identificativi stabili senza esporre in chiaro l'ID Iliad negli `unique_id`.

## Installazione tramite HACS

La repository è strutturata come custom repository HACS di tipo **Integration**.

1. Apri HACS.
2. Vai nelle repository personalizzate / **Custom repositories**.
3. Aggiungi `https://github.com/robertovendrame/ha-iliad-italia`.
4. Seleziona la categoria **Integration**.
5. Installa **Iliad Italia**.
6. Riavvia Home Assistant.
7. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Iliad Italia**.

Quando viene pubblicata una nuova GitHub Release, HACS può rilevarla come aggiornamento installabile.

## Ciclo di release

Il repository contiene un workflow GitHub Actions dedicato alle release.

Per pubblicare una versione:

1. aggiorna `custom_components/iliad_ita/manifest.json` con la nuova versione;
2. sposta le modifiche da `Unreleased` alla relativa sezione in `CHANGELOG.md`;
3. verifica che il workflow **Validate** sia verde;
4. apri **Actions → Release → Run workflow**;
5. inserisci la versione senza prefisso `v`, per esempio `0.3.0`.

Il workflow controlla che la versione richiesta coincida con quella del manifest, estrae automaticamente le note dal changelog e crea la release/tag `vX.Y.Z`.

## Installazione manuale

Copia la cartella:

`custom_components/iliad_ita`

in:

`/config/custom_components/iliad_ita`

Riavvia Home Assistant e vai in:

**Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Iliad Italia**

Per ogni SIM inserisci:

- un nome libero, ad esempio `SIM Casetta`, `SIM Lavoro`, `SIM Backup`;
- ID utente Iliad;
- password Iliad.

Le credenziali vengono salvate nella config entry di Home Assistant e non devono essere inserite nel repository.

## Multi-SIM

Ogni account Iliad usa una sessione HTTP con cookie dedicati. Questo evita che due SIM configurate nella stessa istanza Home Assistant condividano o sovrascrivano la sessione di autenticazione.

Il comportamento multi-SIM è stato verificato con due account Iliad reali contemporaneamente nella stessa istanza Home Assistant.

Lo stesso account non può essere aggiunto due volte nella stessa istanza, mentre la stessa integrazione può essere usata su istanze Home Assistant differenti.

## Opzioni per ogni SIM

Apri l'integrazione in **Impostazioni → Dispositivi e servizi**, seleziona la SIM e apri **Configura**.

Sono disponibili quattro opzioni indipendenti per ogni account:

- **Soglia dati residui (GB)** — default `10 GB`;
- **Soglia dati residui (%)** — default `10%`;
- **Soglia credito (€)** — default `5 €`;
- **Intervallo aggiornamento (ore)** — default `6`, configurabile da `1` a `24` ore.

Il binary sensor **Dati in esaurimento** passa a `on` quando viene raggiunta **almeno una** delle due soglie dati configurate: GB residui oppure percentuale residua.

Il binary sensor **Credito basso** passa a `on` quando il credito disponibile è minore o uguale alla soglia configurata.

Le soglie correnti sono esposte anche come attributi dei binary sensor, così possono essere usate facilmente in dashboard e automazioni.

## Dati calcolati

`Dati totali calcolati`, `Dati utilizzati percentuale` e `Dati residui percentuale` sono valori derivati localmente da Home Assistant a partire dai dati usati e residui restituiti dall'Area Personale Iliad. Non sono valori aggiuntivi forniti direttamente da Iliad.

Questo mantiene il parser semplice e permette di avere subito indicatori più utili per dashboard e automazioni.

## Diagnostica

Home Assistant può generare i dati diagnostici della singola config entry. La diagnostica include stato del coordinator, intervallo configurato, opzioni e valori già parsati, ma **non include ID utente Iliad o password**.

È pensata per rendere più semplice il debug di eventuali problemi futuri senza chiedere agli utenti di condividere credenziali.

## Come funziona

La versione corrente non usa API Iliad pubbliche documentate. Effettua il login all'Area Personale e legge la pagina:

`https://www.iliad.it/account/consumi-e-credito`

Il parser interpreta l'HTML della pagina e normalizza i valori di traffico in GB. Modifiche al portale Iliad possono quindi richiedere un aggiornamento dell'integrazione.

## Compatibilità

Sviluppata e testata con riferimento a Home Assistant 2026.8.x.

## Validazione

La repository contiene una GitHub Action che esegue:

- controllo sintassi Python;
- HACS Action, categoria `integration`;
- Home Assistant Hassfest.

## Roadmap immediata

Prossimi dati/funzioni da valutare, **solo se recuperabili in modo affidabile dalla pagina Iliad reale**:

- data di rinnovo;
- giorni al rinnovo;
- offerta/piano;
- plafond dati ufficiale;
- numero linea o altro identificativo utile;
- consumo medio giornaliero;
- GB/giorno disponibili fino al rinnovo;
- previsione di esaurimento prima del rinnovo.

La parte di previsione dipende dalla disponibilità di una data di rinnovo affidabile: non verranno introdotti selettori HTML ipotetici o dati inventati.

## Origine e attribuzione

Il progetto nasce dallo studio del componente GPL-3.0 `masoneff3/ha_iliad_ita`, che ha dimostrato la fattibilità del login e del recupero dei dati dall'Area Personale Iliad.

Questa implementazione è stata riscritta con architettura Home Assistant moderna: config entries, config flow, client asincrono, DataUpdateCoordinator, supporto multi-account, unique ID e device dedicati.

Repository di riferimento:
`https://github.com/masoneff3/ha_iliad_ita`

## Licenza

GPL-3.0. Vedi `LICENSE`.

Iliad e i relativi marchi appartengono ai rispettivi proprietari. Questo progetto non è affiliato né approvato da Iliad Italia S.p.A.
