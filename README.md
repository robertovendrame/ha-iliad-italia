# Iliad Italia for Home Assistant

Custom integration non ufficiale per Home Assistant che legge i dati dell'Area Personale Iliad Italia.

> Stato: **testata con account Iliad reali**, inclusa la configurazione contemporanea di due SIM/account nella stessa istanza Home Assistant.

## Funzioni

Ogni account/SIM configurato crea un device separato con:

- Credito disponibile (`EUR`)
- Dati utilizzati (`GB`)
- Dati residui (`GB`)
- Dati totali calcolati (`GB`), ottenuti come usati + residui
- Percentuale dati utilizzati
- Percentuale dati residui
- Ultimo aggiornamento riuscito
- Pulsante **Aggiorna ora** per forzare un refresh immediato

L'integrazione supporta:

- più SIM/account Iliad nella stessa istanza Home Assistant;
- installazione della stessa integrazione su più istanze Home Assistant;
- configurazione da UI tramite `config_flow`;
- riautenticazione quando le credenziali non sono più valide;
- riconfigurazione del nome della SIM e delle credenziali;
- sessioni/cookie separati per ogni account configurato;
- aggiornamento cloud automatico ogni 6 ore;
- refresh manuale per singola SIM;
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

## Dati calcolati

`Dati totali calcolati`, `Dati utilizzati percentuale` e `Dati residui percentuale` sono valori derivati localmente da Home Assistant a partire dai dati usati e residui restituiti dall'Area Personale Iliad. Non sono valori aggiuntivi forniti direttamente da Iliad.

Questo mantiene il parser semplice e permette di avere subito indicatori più utili per dashboard e automazioni.

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

Prossimi dati/funzioni da valutare, se presenti nella pagina Iliad o recuperabili in modo affidabile:

- data di rinnovo;
- giorni al rinnovo;
- offerta/piano;
- plafond dati ufficiale;
- numero linea o altro identificativo utile;
- soglie configurabili e binary sensor di allarme;
- stima consumo medio e proiezione fino al rinnovo.

## Origine e attribuzione

Il progetto nasce dallo studio del componente GPL-3.0 `masoneff3/ha_iliad_ita`, che ha dimostrato la fattibilità del login e del recupero dei dati dall'Area Personale Iliad.

Questa implementazione è stata riscritta con architettura Home Assistant moderna: config entries, config flow, client asincrono, DataUpdateCoordinator, supporto multi-account, unique ID e device dedicati.

Repository di riferimento:
`https://github.com/masoneff3/ha_iliad_ita`

## Licenza

GPL-3.0. Vedi `LICENSE`.

Iliad e i relativi marchi appartengono ai rispettivi proprietari. Questo progetto non è affiliato né approvato da Iliad Italia S.p.A.
