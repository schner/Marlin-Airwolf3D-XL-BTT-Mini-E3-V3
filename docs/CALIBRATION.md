# Calibração pós-firmware (Airwolf XL / SchnerMod)

Guia das torres e testes necessários depois da rodada de firmware de 2026-06-25
(merge do Marlin oficial + FT_MOTION + MPC + features novas).

> **Faça nesta ordem.** Cada passo depende do anterior estar estável. Não pule a térmica.
>
> **Segurança:** sem silicone sock, o hotend é térmico-marginal. Nunca afrouxe Thermal
> Protection. Faça `M503` e guarde ANTES de qualquer `M500`/`M502`.

---

## 0. Antes de tudo — flashar e conferir

1. Copiar `.pio/build/STM32G0B1RE_btt/firmware.bin` pra raiz do SD → inserir → ligar.
2. Conferir versão e que subiu: `M115`.
3. Backup do estado atual da EEPROM: `M503` (salvar a saída num arquivo).
4. **Importante:** o PID do hotend foi substituído por MPC. Até calibrar o MPC (passo 1),
   o controle de temperatura usa o modelo *default* (genérico) — pode oscilar. **Não
   imprima antes do passo 1.**

---

## 1. MPC — autotune da térmica (substitui o PID)  · SEM torre

MPC usa um modelo físico do hotend. Precisa medir o modelo na *tua* máquina.

```gcode
M104 S0          ; garantir hotend frio (temperatura ambiente)
M106 S0          ; fan de peça desligado
M306 T           ; AUTOTUNE do MPC — aquece, mede, calcula o modelo (alguns minutos)
M306             ; ver o modelo resultante
M500             ; gravar na EEPROM
```

- Rodar com o hotend **montado como vai imprimir** (sem sock, do jeito que é) — o modelo
  inclui a perda térmica real.
- Ambiente parado (sem vento/ventilador externo) durante o autotune.

### Validação (o motivo de ter ido pra MPC)
```gcode
M104 S205        ; aquecer
M109 S205        ; esperar estabilizar
M106 S255        ; fan de peça 100%
M105             ; ler temp algumas vezes (ou olhar o gráfico do OctoPrint)
```
Esperado: segurar perto de **205 °C** mesmo com fan total — sem a queda pra 198–199 que o
PID tinha. Se ainda cair muito, é hardware (cartucho/duto/fan), não firmware.

Menu LCD: `MPC_EDIT_MENU` e `MPC_AUTOTUNE_MENU` estão ligados → dá pra rodar/editar pela tela.

---

## 2. FT_MOTION — frequência do shaper  · TORRE DE RINGING

FT_MOTION suprime ghosting/ringing, mas precisa da **frequência de ressonância real** de
cada eixo. Sem acelerômetro (ADXL345), o método é a **torre de ringing** + medir.

### 2a. Gerar a torre (OpenSCAD → STL)

Cole no [OpenSCAD](https://openscad.org), aperte **F6** (render) e exporte STL:

```scad
// Torre de ringing / ressonância — imprimir em modo vaso (spiralize)
side   = 22;    // base (mm) — pequena pra ter cantos frequentes
height = 60;    // alta o bastante pra medir as ondulações
linear_extrude(height) square([side, side], center = true);
```

Um quadrado oco: em cada canto de 90° o cabeçote inverte rápido e gera as "ondas"
(ringing) na parede seguinte — é o que se mede.

> Alternativa pronta: qualquer STL "Ringing Tower" / "Resonance Test" do Printables/Thingiverse
> serve. O quadrado acima é o mínimo que funciona.

### 2b. Fatiar no Cura (config do TESTE, não de produção)

- **Spiralize Outer Contour (modo vaso): ON** → parede única contínua, velocidade constante.
- **Print Speed: constante e conhecida**, ex. **100 mm/s** (anote — entra na conta).
- **Acceleration Control: ON, aceleração ALTA** (ex. 3000–5000) → ringing pronunciado.
- **Jerk/Junction: alto** (ex. JD 0.1) pra excitar bem os cantos.
- Layer height 0.2, sem fan ou pouco fan, 1 perímetro.

**Desligar o shaper durante o teste** (medir a ressonância crua da máquina):
```gcode
M493 S1          ; FT Motion ativo
M493 C0          ; shaper = NONE em X e Y (sem axis = aplica nos dois)
```

### 2c. Medir e calcular

Na parede logo depois de um canto, meça a distância entre cristas das ondulações (λ, em mm).
Quanto mais paralelas/regulares, melhor. Faça pra uma parede que se move em **X** e outra em **Y**.

```
frequência (Hz) = velocidade de impressão (mm/s) ÷ λ (mm)
```
Ex.: impresso a 100 mm/s, ondas a cada 2,5 mm → **40 Hz**.

### 2d. Aplicar (M493) e gravar

Sintaxe deste firmware: `C` = tipo de shaper (1 = ZV), `A` = frequência (Hz), letra de eixo
(X/Y) seleciona; sem eixo = ambos. `M493` sozinho mostra a config atual.

```gcode
M493 X C1 A<freqX>     ; ex: M493 X C1 A42
M493 Y C1 A<freqY>     ; ex: M493 Y C1 A38
M493                   ; conferir
M500                   ; gravar
```
(`C1` = ZV, que é o default. Pra menos vibração residual dá pra testar `C8` = MZV, mas ZV é o ponto de partida.)

Também dá pra ajustar pela tela: menu **Fixed-Time Motion** (`FT_MOTION_MENU` está ligado).

> ⚠️ FT_MOTION é BETA e pesado. No teu STM32G0 (M0+ 64 MHz, sem FPU) pode engasgar em alta
> velocidade. Se notar travadas/perda de passo/teto de velocidade baixo, o plano B é voltar
> pro Input Shaping (reverter os 2 commits de motion). Compilar não garante performance em runtime.

---

## 3. Linear Advance / Pressure Advance — fator K  · TORRE/PADRÃO DE LA

Reduz bojo de canto e melhora o seam, principalmente em velocidade. Com FT_MOTION o K
continua sendo setado por **`M900 K`** (mesmo do Linear Advance — o firmware avisa isso no build).

### 3a. Gerar o padrão de teste
Use o gerador oficial: **marlinfw.org/tools/lin_advance/k-factor.html**
- Preencha: bed **275 × 200**, nozzle 0.4, filamento 1.75, temperaturas do teu PLA.
- Faixa sugerida pra direct drive (Bulldog + V6): **K 0 a 0.1, passo 0.01**.
- Baixe o `.gcode` gerado (ele já emite `M900 K` por faixa) e imprima direto.

### 3b. Ler e aplicar
Escolha a faixa onde os cantos ficam mais limpos (sem bojo nem falha).
```gcode
M900 K<valor>     ; ex: M900 K0.04
M500
```

---

## 4. Validação final  · BENCHY / CUBO

Com MPC + frequência FT + K aplicados:

1. Imprimir um **cubo de calibração (20 mm)** ou **3DBenchy** com o perfil PLA Qualidade 0.20.
2. Durante a 1ª camada, ajustar altura ao vivo com **babystep** (já grava no Z-offset —
   `BABYSTEP_ZPROBE_OFFSET` ligado). Depois `M500`.
3. Avaliar: ghosting (efeito do FT_MOTION), cantos, seam, dimensional, e o gráfico de
   temperatura (efeito do MPC).
4. Mudar **uma variável por vez** a partir daqui.

---

## Referência rápida de comandos

```gcode
M503                 ; dump da config/EEPROM ativa
M306 T  / M306       ; autotune MPC / ver modelo
M493                 ; ver config FT_MOTION
M493 X C1 A<f>       ; X: shaper ZV, frequência f
M493 Y C1 A<f>       ; Y: shaper ZV, frequência f
M900 K<v>            ; fator K (Linear Advance / FT_MOTION)
M500 / M501 / M502   ; gravar / recarregar / resetar EEPROM (M502 com MUITO cuidado)
M412 S1              ; ligar sensor de filamento
```

> Ordem de ataque ao diagnosticar: térmica/MPC → frequência FT → K → 1ª camada/Z-offset → resto.
