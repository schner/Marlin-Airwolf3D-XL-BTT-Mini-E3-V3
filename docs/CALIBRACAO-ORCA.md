# Calibração via OrcaSlicer — Airwolf XL SchnerMod

Ordem oficial do OrcaSlicer (`orcaslicer.com/wiki/guides/calibration_guide`), adaptada
a esta máquina (Marlin + BP6 + direct drive Bulldog + FT_MOTION).

> **Use o processo `Calibracao @Airwolf` em TODOS os testes.**
> Ele tem ironing, scarf seam e fuzzy skin desligados — essas features *mascaram*
> exatamente o que se está tentando medir.

> **Runout:** testes de calibração extrudam devagar e já causaram falso positivo.
> Se pausar sozinho, desligue antes do teste e religue depois:
> `M412 S0` … teste … `M412 S1` + `M500`.

---

## Ordem

| # | Teste | Por que nesta posição | Onde grava |
|---|---|---|---|
| 1 | **Temperatura** | muda a viscosidade → afeta todos os outros | perfil do filamento |
| 2 | **Max Volumetric Speed** | define o teto de velocidade real | perfil do filamento |
| 3 | **Pressure Advance** | compensa pressão; depende de temp+vazão | EEPROM (`M900 K`) |
| 4 | **Flow Rate** | precisão dimensional, com o resto já estável | perfil do filamento |
| 5 | **Retraction** | stringing residual, depois de flow+PA | perfil do filamento |
| 6 | **Cornering** | Junction Deviation | EEPROM (`M205 J`) |
| 7 | **Input Shaping** | ⚠️ ver nota — nesta máquina é FT_MOTION | EEPROM (`M493`) |
| 8 | **VFA** | ressonância por velocidade (opcional) | — |

---

## 1. Temperatura

- **Calibration → Temperature**
- Faixa PLA: **190 → 230**, passo 5 (PETG 230-260, ABS 235-265)
- **Ler:** melhor bloco = menos stringing, melhor ponte/overhang, sem bolha.
  Preferir o **mais baixo** que ainda tenha boa adesão de camada.
- **Aplicar:** `nozzle_temperature` no perfil do filamento (Orca já sugere ao final).

## 2. Max Volumetric Speed

- **Calibration → Max Volumetric Speed**
- Faixa: **5 → 24 mm³/s**, passo 0.5
- ⚠️ Antes de rodar, o `filament_max_volumetric_speed` do perfil precisa estar **alto**
  (está em 30) senão ele limita o próprio teste.
- **Ler:** subir até onde a superfície fica rugosa/opaca/falhada = limite.
- **Aplicar:** `filament_max_volumetric_speed` = **~90% do achado**.
  Esperado neste hotend (copper BP6 + latão + sock): **12-16 mm³/s**.
- 🔑 A partir daí o Orca **limita toda velocidade** por vazão automaticamente.

## 3. Pressure Advance

- **Calibration → Pressure Advance** → método **PA Tower** ou **PA Line**
- Direct drive: **Start 0 · End 0.10 · Step 0.005**
- Marlin usa **`M900 K`** (o Orca sabe pelo flavor marlin2).
- **Ler:** faixa com largura de linha uniforme no canto — sem bojo (K baixo), sem
  falha/gap (K alto).
- **Aplicar:** `M900 K<valor>` + `M500`. Espelhar em `Configuration_adv.h` (`ADVANCE_K`).
- Valor atual: **K0.04** (chutado, não calibrado).

## 4. Flow Rate

- **Calibration → Flow Rate** → **YOLO (Recommended)** (1 impressão só)
- **Ler:** bloco de topo mais liso — sem gaps (sub) e sem cristas (sobre). Luz rasante ajuda.
- **Aplicar:** `filament_flow_ratio` no perfil do filamento.

## 5. Retraction

- **Calibration → Retraction test**
- Direct drive: **Start 0 · End 2mm · Step 0.1**
- **Ler:** menor retração que ainda elimina o stringing.
- **Aplicar:** `filament_retraction_length`. Atual: **1.2mm @ 45 mm/s**.

## 6. Cornering (Junction Deviation)

- **Calibration → Cornering**
- Marlin usa **Junction Deviation** (`M205 J`), não jerk clássico.
- Modelo: **Ringing Tower**. Faixa: **Start 0.02 → End 0.25**. Atual: **0.08**.
- 🔴 **NÃO usar Start 0.000** (o default do diálogo). O Marlin aceita apenas
  `J` entre **0.01 e 0.3**; abaixo disso ele responde
  `Error:?J out of range (0.01 to 0.3)` e **aborta a impressão em andamento**.
- **Ler:** maior JD com cantos ainda limpos (sem overshoot/bojo).
- **Aplicar:** `M205 J<valor>` + `M500`.

## 7. Input Shaping — ⚠️ NÃO usar o teste do Orca

Esta máquina roda **FT_MOTION** (Marlin), que usa **`M493`** — não o `M593` do
Input Shaping clássico que o teste do Orca assume. O teste do Orca **não se aplica**.

Método correto aqui:
1. Desligar shaping: `M493 S0` (confirmar "Fixed-Time Motion disabled")
2. Imprimir torre de ringing (ver [CALIBRATION.md](CALIBRATION.md))
3. Medir λ entre ondulações → `freq = velocidade ÷ λ`
4. `M493 S1` → `M493 X C1 A<fx>` / `M493 Y C1 A<fy>` → `M500`
5. ⛔ **Não usar `M495`** sem centralizar os eixos antes — ele ignora limites de
   software e já bateu no fim de curso.

Valor atual: **37 Hz** (placeholder, não medido).

## 8. VFA (opcional)

- **Calibration → VFA** — acha velocidades que excitam ressonância (artefato fino
  na parede). Útil só depois que o resto estiver fechado.

---

## Depois de tudo

1. Voltar ao processo **PLA Qualidade @Airwolf** (com ironing + scarf seam).
2. Imprimir um **Benchy** ou cubo e comparar com o baseline.
3. Repetir **Temperatura + Flow + PA** para **cada filamento novo** (marca/cor muda).
   Vazão, cornering e shaping são da máquina — não precisam repetir por filamento.

## Referência rápida (EEPROM)

```gcode
M900 K<v>       ; pressure advance
M205 J<v>       ; junction deviation (cornering)
M493            ; ver config FT_MOTION
M493 X C1 A<f>  ; shaper ZV + frequência no eixo X
M412 S0 / S1    ; runout off/on (durante testes lentos)
M500            ; gravar
M503            ; conferir
```

### ⚠️ Pegadinha do M412 (bug do Marlin upstream)

`M412 L<n>` **sozinho não funciona** — o parser só entra no bloco de escrita se vir
`R`, `S`, `D` ou `H`; o `L` ficou de fora dessa lista (`M412.cpp`, `parser.seen("RS"...)`).
Mandar só `L` cai no ramo de relatório e o valor é **silenciosamente ignorado**.

Sempre mandar junto com `S`:

```gcode
M412 S1 L30     ; correto — S1 entra no bloco, L30 é aplicado
M500
M412            ; confirmar "Motion distance 30.00mm"
```

### ⚠️ EEPROM manda, não o firmware compilado

Vários valores (runout D/L, PID/MPC, offsets, accel, JD, K) vivem na **EEPROM**.
Reflashar **não** os altera — só `M502` (que apaga tudo, incluindo mesh e `M206`).
Ao mudar um default em `Configuration*.h`, aplicar também o G-code equivalente + `M500`.
