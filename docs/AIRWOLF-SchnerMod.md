# Contexto técnico — Airwolf3D “SchnerMod”

> Documento consolidado para ser usado como contexto em Claude Code, especialmente ao editar firmware Marlin, perfis Cura, OctoPrint/Octolapse e investigar qualidade de impressão.
>
> **Regra importante:** não assumir parâmetros nem sugerir mudanças de firmware sem preservar os dados abaixo e explicar riscos. A impressora é uma Airwolf XL antiga bastante modificada, portanto valores “padrão de Ender 3” não são diretamente aplicáveis.
>
> Origem: notas consolidadas de conversas anteriores (ChatGPT), importadas para o repo em 2026-06-25. Resumo operacional do firmware está no [CLAUDE.md](../CLAUDE.md).

---

## Estado em 2026-11-05: máquina parada

**Este bloco e o [CLAUDE.md](../CLAUDE.md) prevalecem sobre o resto do documento**, que é em grande parte um retrato de junho de 2026.

- A Airwolf está **sem uso por ora**; a Voron 2.4 é a impressora principal.
- **Sem host:** o Raspberry Pi 4 foi para a Voron. OctoPrint, OctoDash e Octolapse estão aposentados aqui. Imprimir por cartão SD; G-code por USB direto do PC, a 115200, ou pela tela touch.
- **Slicer:** OrcaSlicer, não Cura (presets em `slicer/orcaslicer/`, altura Z já em 160 mm).
- **`M206 X-19`:** último valor lido da máquina (`M503` de 2026-08-01). O `X-16` do backup de junho está velho. O último dump salvo no repo ainda é o de junho. **Rodar `M503` antes de qualquer `M502`.**
- **Calibrado, segundo commits:** Linear Advance K 0.04, Junction Deviation 0.09, modelo MPC com bico de latão. Os defaults compilados foram sincronizados em 2026-08-01 a 2026-08-03.
- **Não calibrado:** frequência do shaper FT_MOTION (37 Hz é placeholder).
- **Mecânica sem correção:** folga no carro X; Z ainda em barra roscada, com a troca por fuso T8 parada desde 2026-08-05.

---

## ⚠️ Correções verificadas contra o código-fonte (2026-06-25)

> Retrato de junho, mantido como histórico. Os valores compilados atuais estão no [CLAUDE.md](../CLAUDE.md).

Os valores de `M503` abaixo refletem a **EEPROM viva** da máquina. O firmware compilado
(`Marlin/Configuration*.h`) tem **defaults diferentes** em vários pontos — porque
`EEPROM_SETTINGS` está habilitado, então `M500` sobrescreve os defaults e `M502` os
restaura. **Editar `Configuration.h` não muda a máquina rodando até um `M502` ou flash
com EEPROM resetada.** Divergências confirmadas no código atual:

| Parâmetro | Compilado (`Configuration*.h`) | EEPROM viva (M503 do doc) |
|---|---|---|
| PID hotend | Kp 12.54 / Ki 0.88 / Kd 44.63 | Kp 12.92 / Ki 0.84 / Kd 49.60 |
| PID mesa | bedKp 50.57 / bedKi 7.35 / bedKd 231.93 | P95.54 / I18.66 / D326.11 |
| Offset Z da sonda | −3.88 (`NOZZLE_TO_PROBE_OFFSET`) | −2.93 (`M851`) |
| Aceleração print / travel | 3000 / 5000 | 1200 / 1200 (`M204 P/T`) |
| Sensor de runout | **habilitado** no firmware | **desligado** na EEPROM (`M412 S0`) |

Itens **conferidos e consistentes** com o código: board, drivers TMC2209 X/Y/Z/E0,
steps `{66.6666, 66.6666, 2560, 454.13}`, feedrate E limitado a 25 mm/s, correntes
X/Y/Z 1200 mA, junction deviation 0.05, fade height 10 mm, mesh bilinear 5×5,
`EEPROM_SETTINGS`, `LIN_ADVANCE` (compilado, K0 em runtime), `ARC_SUPPORT`,
`AUTOTEMP` (compilado — não ativar por acidente), `PID_FAN_SCALING` desligado,
`CONFIG_EXPORT` comentado.

**Gotcha de serial:** o firmware usa `SERIAL_PORT 2` / `BAUDRATE 115200`, mas o
`platformio.ini` tem `monitor_speed = 250000`. O monitor do PIO **não** casa com o
firmware; OctoPrint/host conecta a **115200**.

---

## 1. Identidade e objetivo da máquina

- Nome no Cura: `Airwolf3D-SchnerMod`
- Nome reportado pelo firmware: `Airwolf-XL-V4.7.6`
- Base mecânica: Airwolf 3D XL modificada
- Cinemática: cartesiana
- Uso atual:
  - PLA e calibração de qualidade;
  - peças funcionais;
  - objetivo futuro: peças automotivas mais resistentes, com interesse em PETG, ABS, ASA, PA6+GF, PC e Tritan;
  - timelapses com OctoPrint + Octolapse.
- A máquina ainda está em fase de calibração fina: não tratar valores de retração, Linear Advance, velocidade e fluxo como definitivamente “fechados”.

---

## 2. Hardware conhecido

### Eletrônica e controle

- Placa: **BTT SKR Mini E3 V3.0**
- Drivers: **TMC2209** em X, Y, Z e E0.
- Firmware: **Marlin bugfix-2.1.x**, compilado em `10/12/2024`.
- Ambiente de compilação: PlatformIO.
- `platformio.ini`:
  - environment padrão: `STM32G0B1RE_btt`
  - monitor speed: `250000`
- Comunicação atual:
  - `SERIAL_PORT 2`
  - `BAUDRATE 115200`
  - `SERIAL_PORT_2 -1`
- Host: nenhum desde que o Raspberry Pi 4 foi para a Voron (antes: OctoPrint + OctoDash + Logitech C920).
- Tela touch presente.

### Movimento e hotend

- Extrusor: **Bulldog XL**, configuração **direct drive**.
- Hotend: **E3D V6**.
- Filamento: 1,75 mm.
- Nozzle atual: **0,4 mm**.
- Sensor de nivelamento: **BLTouch**.
- Mesa: aquecida; placa magnética dupla face, com lado rugoso e liso.

### Geometria/área útil

- No Cura havia:
  - X: 275 mm
  - Y: 200 mm
  - Z: 170 mm
- O firmware reporta área de trabalho:
  - X: 0–275 mm
  - Y: 0–200 mm
  - Z: 0–160 mm
- **Ajuste pendente/importante no Cura:** configurar altura Z para **160 mm**, não 170 mm, para impedir que o slicer gere peças acima do limite real.
- Área “full” reportada pelo firmware:
  - X mínimo: -16 mm
  - Y mínimo: 0 mm
  - Z mínimo: 0 mm
  - X máximo: 275 mm
  - Y máximo: 200 mm
  - Z máximo: 160 mm
- Home offset:
  - `M206 X-19.00 Y0.00 Z0.00` (`M503` de 2026-08-01; era `X-16.00` em junho).
- Offset de sonda:
  - `M851 X38.00 Y0.00 Z-3.43` (`M503` de 2026-08-01; era Z-2.93 em junho).

---

## 3. Firmware e fontes disponíveis

Há cópias locais dos arquivos:

- `Configuration.h`
- `Configuration_adv.h`
- `platformio.ini`
- `config.ini`
- `definition_changes.zip` do Cura

Principais características confirmadas:

- Board: `BOARD_BTT_SKR_MINI_E3_V3_0`
- Drivers configurados:
  - `X_DRIVER_TYPE TMC2209`
  - `Y_DRIVER_TYPE TMC2209`
  - `Z_DRIVER_TYPE TMC2209`
  - `E0_DRIVER_TYPE TMC2209`
- Auto Bed Leveling habilitado.
- EEPROM habilitada.
- PID de hotend e mesa habilitados.
- Proteção térmica habilitada.
- `PID_FAN_SCALING` está desabilitado no firmware atual.
- `AUTOTEMP` está compilado, mas não há indicação de uso no G-code normal. Não ativar por acidente.
- Linear Advance está disponível.
- Arc support habilitado no firmware, mas não é necessário ativar Arc Welder no Cura neste momento.
- `CONFIG_EXPORT` está comentado/desabilitado.
- Build atual é Marlin bugfix-2.1.x e não deve ser atualizado apenas “por atualizar”; preservar configuração e validar todas as funções após qualquer recompilação.

### Capacidades reportadas por M115

- EEPROM: habilitada
- Auto leveling: habilitado
- Z probe: habilitado
- Leveling data: habilitado
- Thermal protection: habilitada
- Babystepping: habilitado
- SD: habilitado
- Runout capability aparece como suportada, porém sensor está desligado na EEPROM
- Sem `CONFIG_EXPORT` ativo no firmware

---

## 4. EEPROM / parâmetros ativos observados por M503

> Estes eram os valores ativos antes do último PID autotune. Alguns podem ter sido alterados depois; conferir sempre com `M503` antes de editar ou concluir algo.

### Steps por mm

```gcode
M92 X66.67 Y66.67 Z2560.00 E454.13
```

- E-steps já haviam sido calibrados anteriormente.
- Não alterar E-steps para “resolver” stringing, blobs ou underextrusion visual sem um teste de extrusão controlado.

### Limites de velocidade

```gcode
M203 X300.00 Y300.00 Z5.00 E25.00
```

Ponto importante:
- O firmware limita o extrusor a **25 mm/s**.
- Por isso, uma retração configurada no Cura em 35 mm/s será limitada pelo firmware a 25 mm/s.
- Para consistência, perfis novos devem usar **25 mm/s** de retract e prime, a menos que o `M203 E` seja deliberadamente revisado e testado.

### Aceleração

```gcode
M201 X3000.00 Y3000.00 Z100.00 E5000.00
M204 P1200.00 R500.00 T1200.00
M205 B20000.00 S0.00 T0.00 J0.05
```

Interpretação:
- aceleração de impressão: 1200 mm/s²
- aceleração de travel: 1200 mm/s²
- aceleração de retração: 500 mm/s²
- junction deviation: 0,05 mm
- durante a calibração, o Cura deve deixar **Acceleration Control** e **Jerk Control** desligados para não sobrescrever esses valores sem intenção.

### Corrente dos drivers

```gcode
M906 X1200 Y1200 Z1200
M906 T0 E800
```

- Não modificar corrente sem validar temperatura de motores/drivers e torque real.
- E0: 800 mA.
- X/Y/Z: 1200 mA.

### Stepping mode

```gcode
M569 S1 X Y Z
M569 S1 T0 E
```

### Filamento

```gcode
M200 S0 D1.75
```

- Volumetric extrusion está desativada.

### Runout

```gcode
M412 S0 D0.00
```

- Sensor de fim de filamento desativado.

---

## 5. Nivelamento e Z-offset

### Mesh atual reportado

```text
      0      1      2      3      4
0 +0.157 +0.054 +0.002 +0.057 +0.131
1 +0.169 +0.107 +0.057 +0.068 +0.100
2 +0.124 +0.047 +0.004 +0.036 +0.043
3 +0.081 +0.029 -0.038 -0.034 -0.037
4 +0.033 -0.053 -0.089 -0.101 -0.099
```

- Tipo: Bilinear 5×5.
- Leveling está ligado.
- Fade height: 10 mm.
- Variação total aproximada do mesh: **0,27 mm**.
- É utilizável; não é um motivo para trocar tudo ou assumir falha de impressão.
- A cama parece ter tendência gradual: região superior/esquerda mais alta e inferior/direita mais baixa.

### Como usar o mesh no Start G-code

Após `G28`, o firmware pode desabilitar o leveling, então o Start G-code deve reativar o mesh salvo:

```gcode
M420 S1
```

- Não rodar `G29` em toda impressão sem motivo.
- Fazer novo mesh quando houver alteração mecânica, mudança de superfície/placa, mexida no BLTouch, no hotend/nozzle ou sintomas claros de primeira camada incoerente.
- Para diagnosticar mesh:
  - `M420 V`
  - `M851`
  - `M503`

### Z offset

Valor atual visto:

```gcode
M851 X38.00 Y0.00 Z-2.93
```

- O Z-offset é sensível à troca de nozzle, superfície, chapa magnética e ajuste mecânico.
- Não copiar esse número como “universal” após qualquer alteração física.

---

## 6. Temperatura, PID e erro térmico recente

### PID antigo, antes do autotune

```gcode
M301 P9.90 I0.52 D47.33
```

### Problema observado

Ao tentar imprimir com alvo de 205 °C, a temperatura ficou por volta de 198–199 °C, enquanto a mesa sustentava 60 °C. O Marlin acionou corretamente:

```text
Error:Thermal Runaway, system stopped! Heater_ID: E0
```

- Isso aconteceu durante aquecimento/impressão e é uma proteção de segurança.
- **Não desabilitar nem afrouxar Thermal Runaway para “resolver”.**
- Possíveis fatores físicos a verificar sempre:
  - cartucho aquecedor firme no bloco;
  - termistor bem fixado e sem cabo quebrado/mau contato;
  - silicone sock presente e em bom estado;
  - fan de dissipador do hotend funcionando;
  - duto do fan de peça não soprando diretamente no heater block;
  - conectores e fios sem mau contato.

### PID autotune mais recente

Foi executado autotune em 205 °C e ele retornou:

```cpp
#define DEFAULT_Kp 12.92
#define DEFAULT_Ki 0.84
#define DEFAULT_Kd 49.60
```

Comandos recomendados para aplicar/gravar:

```gcode
M301 P12.92 I0.84 D49.60
M500
M503
```

- **Estado a confirmar:** não foi compartilhado o `M503` final depois de aplicar/gravar. Antes de qualquer outra decisão, verificar se o firmware passou a reportar:
  
```gcode
M301 P12.92 I0.84 D49.60
```

- Para persistência em caso de `M502`, também atualizar no `Configuration.h`:

```cpp
#define DEFAULT_Kp 12.92
#define DEFAULT_Ki 0.84
#define DEFAULT_Kd 49.60
```

### Teste térmico recomendado após aplicar PID

```gcode
M106 S255
M109 S205
G4 S180
M107
```

- O objetivo é confirmar estabilidade com fan de peça em 100%.
- Esperado: manter próximo de 205 °C, sem queda sustentada para 198–199 °C.
- Caso continue caindo de forma relevante, investigar hardware/duto/fan antes de imprimir.

### PID da mesa

Valor observado:

```gcode
M304 P95.54 I18.66 D326.11
```

- A mesa sustentava 60 °C corretamente no log do erro.
- Não é prioridade no momento.

---

## 7. Linear Advance

### Estado atual confirmado

```gcode
M900 K0.00
```

- Linear Advance está **desligado** na EEPROM.
- Em algum teste anterior foi usado `M900 K0.05`, mas isso não ficou salvo ou foi revertido.
- Não usar `K0.05` como valor definitivo sem calibração específica.
- Para o próximo processo de qualidade, manter **K=0** até realizar uma calibração correta de Linear Advance/Pressure Advance.

### Se quiser testar um valor temporário

```gcode
M900 K0.05
```

### Para gravar na EEPROM

```gcode
M900 K0.05
M500
```

Mas isso só deve ser feito depois de validar por teste. Para o perfil atual de qualidade, a orientação é manter `M900 K0`/sem comando M900.

---

## 8. Cura — máquina

### Configurações de máquina que devem permanecer

- G-code flavor: Marlin.
- Heated bed: habilitado.
- Number of extruders: 1.
- Nozzle size: 0,4 mm.
- Compatible material diameter: 1,75 mm.
- Extruder offsets: X=0, Y=0.
- Cooling fan number: 0.
- Origin at center: desabilitado.
- Dimensões:
  - X 275
  - Y 200
  - **Z deve ser corrigido para 160**
- Head offsets relatados na máquina Cura:
  - X min: -16
  - Y min: 0
  - X max: 10
  - Y max: 10
  - Gantry height deve acompanhar a altura útil real, 160 mm.
- Aplicar extruder offsets ao G-code: habilitado.

### Extrusão no Cura

- **Relative Extrusion está OFF**.
- Portanto o Start G-code deve usar `M82`, não `M83`.
- Não misturar `M83` no Start G-code com Cura configurado para extrusão absoluta sem entender a consequência.

---

## 9. Start G-code atual recomendado

Usar este como base, enquanto Cura estiver com `Relative Extrusion = OFF`:

```gcode
; Modos esperados pelo Cura
G90
M82

; Home
G28

; Reativa mesh salva após o home
M420 S1

; Afasta o bico da mesa
G1 Z15 F6000

; Prime simples
G92 E0
G1 E3 F300
G92 E0
```

### Observações

- Não incluir `G29` a cada impressão por padrão.
- Não incluir `M83` enquanto Cura usa extrusão absoluta.
- Não incluir `M900 K0.05` até Linear Advance ser calibrado.
- Caso queira forçar Linear Advance desligado de forma explícita no início, pode adicionar:

```gcode
M900 K0
```

mas não é obrigatório se a EEPROM continua em K0.

### End G-code recomendado

```gcode
M104 S0
M140 S0

G92 E0
G1 E-2 F1800

G91
G1 Z10 F3000
G90

G28 X0 Y0

M84
```

Observações:
- Esse end code desliga hotend e mesa, faz retração de 2 mm, sobe 10 mm, estaciona X/Y e desliga motores.
- Verificar se `G28 X0 Y0` é mecanicamente seguro para a peça e para o setup de câmera. Se houver risco de colisão em peças muito altas, substituir por um park manual seguro.
- Não adicionar movimentos de Z-hop no Cura só para timelapse.

---

## 10. OctoPrint e Octolapse

> Aposentados nesta máquina desde que o Raspberry Pi 4 foi para a Voron. Seção mantida para quando houver um host de novo.

### Contexto

- OctoPrint em Raspberry Pi 4.
- Câmera C920.
- Octolapse será usado para timelapse.

### Princípios para não piorar a qualidade

- `Z Hop When Retracted` no Cura: **OFF**.
- O Octolapse já pode adicionar movimentos de estabilização/foto; somar Z-hop em todas as retrações aumenta:
  - tempo de impressão;
  - stringing;
  - blobs;
  - chance de marcas de travel.
- Configurar Octolapse com atenção em:
  - printer profile correto;
  - posição segura de snapshot;
  - retraction/prime gerenciado apenas uma vez;
  - stabilization/smart triggers;
  - posição de câmera e foco;
  - evitar posição de snapshot que faça o bico passar sobre a peça com risco de tocar.
- Ainda não há dump das configurações de Octolapse. Não assumir valores de stabilization ou snapshot position.

---

## 11. Perfis Cura atuais e estratégia

### Regra de gestão de perfis

- Não editar o perfil original `Precisão` diretamente.
- Criar cópias customizadas.
- Perfis pretendidos:
  1. `PLA - Qualidade - 0.20 - Airwolf`
  2. `PLA - Rápido Seguro - 0.24 - Airwolf`

### Estado do perfil “Precisão” visto no Cura

O diálogo de mudanças mostrou os valores-base do perfil `Precisão` versus mudanças temporárias:

```text
Enable Bridge Settings: True
Build Plate Adhesion Type: skirt
Support Placement: buildplate
Minimum Support Area: 10
Support Overhang Angle: 70
Combing Mode: infill
Retraction Speed: 35
Retraction Distance: 0.8
Top Layers: 6
Initial Printing Temperature: 190
Printing Temperature: 200
Final Printing Temperature: 185
Enable Fluid Motion: True
Outer Wall Speed: 45
Initial Layer Speed: 25
Infill Speed: 100
Wall Line Count: 3
Infill Before Walls: True
```

Alguns desses valores devem ser corrigidos nos perfis novos abaixo.

### Perfil 1 — PLA Qualidade 0.20

Objetivo: Benchy, calibração, peças visíveis, encaixes e peças pequenas.

#### Quality

```text
Layer Height: 0.20 mm
Initial Layer Height: 0.24 mm
Line Width: 0.40 mm
Initial Layer Line Width: 100%
```

#### Walls

```text
Wall Line Count: 3
Wall Thickness: 1.20 mm
Outer Wall Wipe Distance: 0.2 mm
Optimize Wall Printing Order: ON
Wall Ordering: Inside To Outside
Infill Before Walls: OFF
```

#### Top/Bottom

```text
Top Layers: 6
Bottom Layers: 4
Top Thickness: 1.20 mm
Bottom Thickness: 0.80 mm
Top/Bottom Pattern: Lines
Monotonic Top/Bottom Order: ON (opcional, recomendado para acabamento)
```

#### Infill

```text
Infill Density: 20%
Infill Pattern: Gyroid
Infill Overlap Percentage: 10%
Infill Before Walls: OFF
```

- Para Benchy pode usar 15–20%.

#### Material

```text
Printing Temperature: 200 °C
Initial Printing Temperature: 205 °C
Final Printing Temperature: 200 °C
Build Plate Temperature: 60 °C
Build Plate Temperature Initial Layer: 60 °C
Flow: 100%
Initial Layer Flow: 100%
```

Observação:
- Esse perfil deve ser usado somente após confirmar estabilidade do novo PID em 205 °C.
- Não reduzir temperatura apenas para esconder um erro de Thermal Runaway.

#### Speed

```text
Print Speed: 50 mm/s
Outer Wall Speed: 35 mm/s
Inner Wall Speed: 50 mm/s
Infill Speed: 60 mm/s
Top/Bottom Speed: 35 mm/s
Travel Speed: 150 mm/s

Initial Layer Speed: 20 mm/s
Initial Layer Print Speed: 20 mm/s
Initial Layer Travel Speed: 60 mm/s
Skirt/Brim Speed: 20 mm/s
```

#### Travel / Retraction

```text
Enable Retraction: ON
Retract at Layer Change: OFF

Retraction Distance: 0.8 mm
Retraction Speed: 25 mm/s
Retraction Retract Speed: 25 mm/s
Retraction Prime Speed: 25 mm/s

Retraction Extra Prime Amount: 0
Retraction Minimum Travel: 1.0 mm

Combing Mode: Within Infill
Max Comb Distance With No Retract: 0

Retract Before Outer Wall: ON

Avoid Printed Parts When Traveling: OFF
Avoid Supports When Traveling: OFF

Z Hop When Retracted: OFF
```

Observação:
- Já foi usado 1,0 mm / 35 mm/s em testes.
- Para a configuração atual, **0,8 mm / 25 mm/s** é a base mais coerente porque o firmware limita E a 25 mm/s.
- Não usar retração de 5 mm: isso apareceu em um perfil “Agarras” antigo e é excessivo para este direct drive.

#### Cooling

```text
Enable Print Cooling: ON
Initial Fan Speed: 0%
Regular Fan Speed: 100%
Maximum Fan Speed: 100%
Regular Fan Speed at Layer: 2
Regular Fan Speed at Height: 0.3 mm
Minimum Layer Time: 8 s
Minimum Speed: 10 mm/s
Lift Head: OFF
```

#### Outros

```text
Enable Bridge Settings: ON
Enable Fluid Motion: OFF
Enable Coasting: OFF
Relative Extrusion: OFF
Arc Welder: OFF
Group Outer Walls: ON
```

#### Support / adhesion

```text
Support Placement: Touching Buildplate
Support Overhang Angle: 70°
Minimum Support Area: 10 mm²
Build Plate Adhesion: Skirt
Skirt Line Count: 1
Skirt Height: 3
Skirt Distance: 3 mm
Skirt/Brim Minimum Length: 250 mm
```

- Não ativar suporte globalmente. Habilitar apenas em peças que realmente precisem.

### Perfil 2 — PLA Rápido Seguro 0.24

Objetivo: protótipos, caixas, peças maiores e peças funcionais simples, mantendo confiabilidade.

Partir do perfil Qualidade e trocar somente:

```text
Layer Height: 0.24 mm
Initial Layer Height: 0.28 mm

Printing Temperature: 205 °C
Initial Printing Temperature: 210 °C
Final Printing Temperature: 205 °C
Build Plate Temperature: 60 °C

Print Speed: 70 mm/s
Outer Wall Speed: 45 mm/s
Inner Wall Speed: 65 mm/s
Infill Speed: 75 mm/s
Top/Bottom Speed: 45 mm/s
Travel Speed: 180 mm/s

Initial Layer Speed: 25 mm/s
Initial Layer Print Speed: 25 mm/s
Initial Layer Travel Speed: 70 mm/s
Skirt/Brim Speed: 25 mm/s
```

Manter o restante igual ao Qualidade:

```text
3 paredes
6 top layers
4 bottom layers
0.8 mm retração
25 mm/s retract/prime
Combing Within Infill
Fan 100% a partir da camada 2
Z-hop OFF
Fluid Motion OFF
Coasting OFF
```

### Perfil “Agarras” antigo

Havia um perfil voltado a agarras/peças resistentes com, entre outros, `retraction_amount = 5`. Esse valor não deve ser mantido no direct drive atual.

Para peças funcionais resistentes, a direção geral é:

```text
Walls: 4–5
Infill: >=30% (dependendo da peça/carga)
Nozzle: 0.4 atual
Retração: manter base 0.8–1.0 mm, nunca 5 mm sem motivo técnico muito específico
```

Antes de imprimir materiais técnicos, criar perfis próprios com temperatura, mesa, fan, enclosure e limites de velocidade adequados. Não reutilizar perfil PLA sem revisão.

---

## 12. Problemas e sintomas já observados

Histórico relevante:

- Primeira camada irregular durante processos de mesh/Z-offset.
- Strings e pequenas bolinhas após travels/retraction.
- Possível underextrusion/falhas na cabine de Benchy.
- Fan ligado causou preocupação/instabilidade térmica.
- Com `M900 K0.05` houve testes, mas o K não está persistido nem calibrado.
- E-steps já foram calibrados.
- Perfil Cura anterior possuía velocidades muito altas:
  - print 120 mm/s;
  - infill 120 mm/s;
  - inner wall 120 mm/s;
  - travel 120 mm/s.
- Esses valores não são a referência atual de qualidade. Para V6 clássico + direct drive, começar nos perfis Qualidade/Rápido Seguro acima.

### Hipóteses a priorizar ao diagnosticar

1. Temperatura/PID/fan path antes de mexer em fluxo.
2. Velocidade e limite de vazão antes de aumentar flow.
3. Retração/combing antes de ativar coasting.
4. Z-offset/mesh apenas quando defeito é de primeira camada.
5. Linear Advance apenas após estabilidade de temperatura, fluxo e velocidade.
6. Não usar mudanças simultâneas em muitos parâmetros; testar uma variável por vez.

---

## 13. Rotina recomendada de diagnóstico

### Antes de qualquer calibração de qualidade

1. Confirmar PID atual com `M503`.
2. Confirmar mesh com `M420 V`.
3. Confirmar Z offset com `M851`.
4. Verificar que `M900` está no valor intencional, hoje K0.
5. Conferir se Cura está com:
   - Z = 160;
   - M82/extrusão absoluta;
   - sem Z-hop;
   - sem Fluid Motion;
   - sem Coasting;
   - velocidades corretas.
6. Fazer teste de estabilidade térmica com fan em 100%.
7. Imprimir um Benchy com perfil Qualidade 0.20.
8. Avaliar:
   - primeira camada;
   - parede externa;
   - stringing;
   - bridge/teto da cabine;
   - seam;
   - dimensional;
   - temperatura real no gráfico.
9. Alterar somente uma variável por vez.

### G-codes úteis

```gcode
M503       ; dump EEPROM/config ativa
M115        ; versão/capacidades
M420 V      ; exibe mesh e estado do leveling
M851        ; exibe offset BLTouch
M900        ; exibe Linear Advance
M500        ; grava EEPROM
M502        ; reseta EEPROM para defaults compilados — usar com muito cuidado
M107        ; fan peça OFF
M106 S255   ; fan peça 100%
M104 S205   ; define hotend 205 sem esperar
M109 S205   ; define hotend 205 e espera
M303 E0 S205 C8 U1 ; PID autotune de hotend
```

---

## 14. Segurança e restrições

- Nunca recomendar desligar Thermal Runaway.
- Nunca recomendar `M502` sem:
  1. backup completo de `M503`;
  2. entender que offsets, PID, mesh e configurações salvas serão perdidos/revertidos.
- Não elevar temperatura máxima, corrente de drivers, aceleração, feedrate de extrusor ou potência de heater sem validar fisicamente o hardware.
- Não assumir que a capacidade térmica do E3D V6 permite alta vazão apenas porque o Cura aceita velocidade alta.
- Para ABS/ASA/PA/PC e materiais com fibra:
  - avaliar temp sensor/hotend real;
  - isolamento e controle de chamber;
  - ventilação;
  - emissão de vapores;
  - necessidade de nozzle adequado, especialmente para materiais abrasivos;
  - limites mecânicos e elétricos.
- PA6+GF e outros filamentos com carga abrasiva exigem nozzle resistente; não usar nozzle de latão comum como solução padrão.

---

## 15. Informações ainda faltantes / a coletar

Para tornar as recomendações mais precisas, obter:

1. `M503` depois do PID novo ser aplicado, para confirmar `M301 P12.92 I0.84 D49.60`.
2. Gráfico ou log do teste de 205 °C com `M106 S255`.
3. Export do perfil Cura final (`.curaprofile`) de Qualidade e Rápido Seguro.
4. Configuração exportada do Octolapse:
   - printer profile;
   - stabilization;
   - snapshot trigger;
   - snapshot position;
   - camera settings.
5. Fotos do duto de fan e do bloco do E3D V6, para verificar se o fan de peça está atingindo o heater block.
6. Resultado de Benchy com o perfil Qualidade novo.
7. Material/marca exata do PLA e se está seco, especialmente se stringing persistir.
8. Tipo/potência/tensão do cartucho aquecedor e termistor usado no E3D V6.
9. Verificação se há silicone sock no heater block.
10. Se há enclosure/ambiente fechado e como isso afeta o fan/cooling.

---

## 16. Resumo operacional imediato

Estado recomendado neste momento:

```text
Firmware:
- mesh salvo e M420 S1 após G28
- Linear Advance K0
- aplicar e confirmar novo PID: P12.92 I0.84 D49.60
- não usar M502

Cura:
- Z max 160 mm
- extrusão absoluta / M82
- perfil PLA Qualidade 0.20 como baseline
- 0.8 mm retração, 25 mm/s retract/prime
- combing Within Infill
- Z-hop OFF
- Fluid Motion OFF
- Coasting OFF
- fan 100% da camada 2 em diante
- print speed 50 mm/s
- outer wall 35 mm/s
- travel 150 mm/s

Octolapse:
- configurar snapshot/stabilization sem adicionar Z-hop global no Cura
- validar que movimentos de snapshot não criam blobs e não batem na peça
```
