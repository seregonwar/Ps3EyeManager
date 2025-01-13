# PS3 Eye Manager - Installer

Questo installer automatico configura tutto il necessario per utilizzare PS3 Eye Manager.

## Requisiti

- Windows 10/11 (64-bit)
- Connessione internet
- Privilegi di amministratore

## Cosa installa

1. **Python** (se non presente)
   - Python 3.11 o superiore
   - pip (gestore pacchetti Python)

2. **Dipendenze Python**
   - numpy
   - opencv-python
   - PyQt5
   - comtypes
   - pywin32

3. **Driver e Software**
   - OBS Studio con Virtual Camera
   - Unity Capture (driver webcam virtuale alternativo)
   - FFmpeg

## Istruzioni

1. Scarica questa cartella
2. Esegui `install.bat` come amministratore
3. Attendi il completamento dell'installazione
4. Riavvia il computer
5. PS3 Eye Manager è pronto all'uso!

## Risoluzione problemi

Se incontri problemi durante l'installazione:

1. Controlla il file `install.log` nella cartella dell'installer
2. Verifica di avere una connessione internet attiva
3. Assicurati di eseguire l'installer come amministratore
4. Prova a disabilitare temporaneamente l'antivirus

## Note

- L'installazione richiede circa 1-2 GB di spazio su disco
- Il processo di installazione può richiedere alcuni minuti
- È necessario riavviare il computer dopo l'installazione

## Supporto

Se hai bisogno di aiuto:
1. Controlla la documentazione in `docs/`
2. Apri un issue su GitHub
3. Contatta il supporto tecnico
