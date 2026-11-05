# EEPROM backup (M503) — pré-M502, 2026-06-25

Snapshot da EEPROM **antes** do `M502` (reset) que acompanhou a rodada de firmware
FT_MOTION/MPC. Guardado como referência de restauração.

> ⚠️ **Backup antigo.** A calibração de julho e agosto de 2026 veio depois dele. Um `M503`
> de 2026-08-01 mostrou `M206 X-19` e `M851 Z-3.43`, não os `X-16` e `Z-2.93` abaixo.
> Preferir um `M503` novo; depois de reaplicar o offset, conferir o X com `G28` + `G1 X0`
> antes de qualquer `G29`.

## O que restaurar do backup (valores ainda válidos)

| G-code | Valor | Restaurar? |
|---|---|---|
| Bed PID | `M304 P95.54 I18.66 D326.11` | ✅ sim — mesa ainda usa PID, estava tunado |
| Z-probe offset | `M851 Z-2.93` | ✅ ponto de partida (sock não muda a ponta) → depois babystep |
| Home offset | `M206 X-16` | ✅ **OBRIGATÓRIO** — sem ele o G29 manda o probe além do fim de curso do X e **bate no chassi**. Re-aplicar após qualquer M502, ANTES de homing/G29 |
| Load/unload | `M603 L80.00 U100.00` | ⚙️ opcional |
| Hotend PID | `M301 P12.92 I0.84 D49.60` | ❌ **não** — hotend agora é MPC (`M306 T`) |
| Accel / feedrate / JD | M201/M203/M204/M205 antigos | ❌ não — usar os tetos novos do M502 |
| Linear Advance | `M900 K0.05` | ❌ não — recalibrar K do zero |
| Mesh 5×5 | grid abaixo | ⚙️ re-rodar `G29` (melhor) ou colar do backup |

## Dump completo

```gcode
; Steps per unit:
M92 X66.67 Y66.67 Z2560.00 E454.13
; Max feedrates (units/s):
M203 X300.00 Y300.00 Z5.00 E25.00
; Max Acceleration (units/s2):
M201 X3000.00 Y3000.00 Z100.00 E5000.00
; Acceleration (P print R retract T travel):
M204 P1200.00 R500.00 T1200.00
; Advanced (J junc_dev):
M205 B20000.00 S0.00 T0.00 J0.05
; Home offset:
M206 X-16.00 Y0.00 Z0.00
; Auto Bed Leveling (5x5 mesh):
M420 S1 Z10.00 ; Leveling ON
G29 W I0 J0 Z0.15672
G29 W I1 J0 Z0.05437
G29 W I2 J0 Z0.00164
G29 W I3 J0 Z0.05711
G29 W I4 J0 Z0.13094
G29 W I0 J1 Z0.16883
G29 W I1 J1 Z0.10711
G29 W I2 J1 Z0.05711
G29 W I3 J1 Z0.06805
G29 W I4 J1 Z0.10047
G29 W I0 J2 Z0.12352
G29 W I1 J2 Z0.04656
G29 W I2 J2 Z0.00359
G29 W I3 J2 Z0.03562
G29 W I4 J2 Z0.04266
G29 W I0 J3 Z0.08133
G29 W I1 J3 Z0.02938
G29 W I2 J3 Z-0.03781
G29 W I3 J3 Z-0.03352
G29 W I4 J3 Z-0.03703
G29 W I0 J4 Z0.03328
G29 W I1 J4 Z-0.05344
G29 W I2 J4 Z-0.08859
G29 W I3 J4 Z-0.10109
G29 W I4 J4 Z-0.09875
; Material heatup presets:
M145 S0 H185.00 B45.00 F255
M145 S1 H240.00 B110.00 F255
; Hotend PID (obsolete — now MPC):
M301 P12.92 I0.84 D49.60
; Bed PID:
M304 P95.54 I18.66 D326.11
; Z-Probe Offset:
M851 X38.00 Y0.00 Z-2.93
; Stepper driver current:
M906 X1200 Y1200 Z1200
M906 T0 E800
; Driver stepping mode:
M569 S1 X Y Z
M569 S1 T0 E
; Linear Advance:
M900 K0.05
; Filament load/unload:
M603 L80.00 U100.00
; Filament runout sensor:
M412 S0 D0.00 ; Sensor OFF
```
