# Perfis OrcaSlicer — Airwolf XL SchnerMod

Snapshot versionado dos presets de usuário do OrcaSlicer (2.4) para esta máquina.
**A fonte da verdade é o OrcaSlicer**: ajuste no GUI, salve, depois exporte para cá e commite.

| Pasta | Presets | Herdam de (sistema Orca, vendor *Custom*) |
|---|---|---|
| `machine/` | Airwolf XL SchnerMod 0.4 nozzle | `MyMarlin 0.4 nozzle` |
| `process/` | PLA Qualidade, PLA Velocidade, PLA Agarras, TPU Flexivel, Calibracao | `0.20mm Standard @MyMarlin` / `0.28mm Extra Draft @MyMarlin` |
| `filament/` | PLA, PETG, ABS, TPU Airwolf | `Generic <material> @System` |

Os arquivos guardam só o que difere do preset pai. Os presets do Voron 2.4 não ficam aqui
(outra máquina, outro repo).

## Sincronizar

```bash
python sync_profiles.py export   # OrcaSlicer -> repo, depois de mudar algo no GUI
python sync_profiles.py import   # repo -> OrcaSlicer (PC novo / restaurar)
```

- `import` **sobrescreve** os presets locais de mesmo nome e recusa rodar com o OrcaSlicer
  aberto (ele mantém os presets em memória e regravaria por cima). Na dúvida, `export` antes.
- PC novo: deixe o OrcaSlicer criar o perfil (wizard com *Custom Printer* / MyMarlin) antes do
  `import`, para os presets pai existirem.
- O export filtra por `compatible_printers` contendo `Airwolf XL SchnerMod 0.4 nozzle`; preset que
  sumiu do Orca gera só um aviso (apagar daqui é decisão manual).

## Chaves de host (repo público)

`print_host` e `printhost_apikey` (OctoPrint) **nunca** entram no repo: o export grava vazio e o
import preserva o valor que já existe no preset local. Em PC novo, preencha em
*Printer settings → Connection* depois do import.

## Suporte — desligado por padrão, pré-configurado

Nenhum processo liga suporte (`enable_support 0`). Quando a peça precisar, marque **Enable support**
e o resto já vem pronto. Base copiada de um projeto Bambu de figura com muito suporte
(árvore orgânica, 2026-09-29):

| Parâmetro | Valor | Nota |
|---|---|---|
| Tipo / estilo | `tree(auto)` / `default` | default + árvore = **Organic** |
| Só na mesa | **não** | figura precisa de suporte apoiado no próprio modelo |
| Ângulo limite | 19° | medido da horizontal; subir p/ 25–30 se overhang cair |
| Folga topo | camada + 0.04 mm | 0.20 → 0.24, 0.28 → 0.32 |
| Folga base / XY | 0.2 / 0.35 mm | |
| Interface | 2 topo + 2 base, espaçamento 0.5 | 0.2–0.3 = face de baixo melhor, remoção mais difícil |
| Base | `default` (oca), espaçamento 2.5 | o pai Marlin forçava rectilinear |
| Galhos | ângulo 45°, paredes auto | |
| Pontes | suportadas acima de `max_bridge_length` | `bridge_no_support 0` |

TPU mantém folgas próprias (topo 0.25, XY 0.5, ângulo 30°): suporte funde demais em flexível.
Velocidades de suporte são por máquina e não seguem o projeto Bambu (60/40 mm/s aqui).

⚠️ Ao abrir um 3MF do Bambu/MakerWorld, o Orca importa junto as configurações da impressora de
origem (velocidades/acelerações de A1/X1). Importe só a geometria ou troque para os presets
Airwolf antes de fatiar.
