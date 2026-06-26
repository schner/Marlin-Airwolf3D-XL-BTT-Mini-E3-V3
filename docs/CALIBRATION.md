# Calibração pós-firmware (Airwolf XL / SchnerMod)

Guia das torres e testes necessários depois da rodada de firmware de 2026-06-25
(merge do Marlin oficial + FT_MOTION + MPC + features novas).

> **Faça nesta ordem.** Cada passo depende do anterior estar estável. Não pule a térmica.
>
> **Segurança:** sock instalado (margem térmica melhorou), mas **nunca** afrouxe Thermal
> Protection. Faça `M503` e guarde ANTES de qualquer `M500`/`M502`.

---

## 0. Antes de tudo — flashar e limpar a EEPROM

1. **Backup:** `M503` → salvar a saída num arquivo (referência do Z-offset atual etc.).
2. Copiar `.pio/build/STM32G0B1RE_btt/firmware.bin` pra raiz do SD → inserir → ligar.
3. Conferir que subiu: `M115`.
4. **Limpar a EEPROM (recomendado):** o merge mudou muita coisa e trocou PID→MPC; a EEPROM
   antiga tem valores obsoletos (PID inútil com MPC, accel velha 1200). Carrega os defaults novos:
   ```gcode
   M502     ; defaults compilados (já trazem os tetos novos: E50, max accel 4000, JD 0.08, accel 3000/5000)
   M500     ; grava
   ```
   Isso também zera **Z-offset e mesh** — ambos recalibrados abaixo (Z-offset volta pro
   compilado −3.88, errado pro teu setup → re-setado no passo 3).
   *(Alternativa, se NÃO quiser M502: aplica os tetos na mão — `M203 E50` / `M201 X4000 Y4000` /
   `M204 P3000 T5000` / `M205 J0.08` / `M500`.)*
5. **Não imprima ainda** — até calibrar o MPC (passo 1) o hotend usa modelo genérico e a
   temperatura pode oscilar.

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

## 2. FT_MOTION — frequência do shaper

FT_MOTION suprime ghosting/ringing, mas precisa da **frequência de ressonância real** de
cada eixo. Dois métodos abaixo — comece pelo **A (M495)**, mais rápido.

> **ADXL345 / acelerômetro:** este Marlin **não** lê acelerômetro pra medir ressonância
> (isso é feature do Klipper, e o SKR Mini E3 V3.0 não tem pino livre pra ele). Aqui é
> manual: sweep (M495) por observação, ou torre de ringing por medição. Guarde o ADXL345
> pra fase Klipper (lá ele vai no SPI do Raspberry Pi).

### Método A — M495 (sweep, sem torre)  ·  `RESONANCE_TEST` ligado

O firmware vibra o eixo varrendo a frequência; você acha onde ressoa mais forte (mais
barulho/vibração na mesa ou na estrutura). Encoste a mão no eixo/estrutura ou observe.

```gcode
M495 X F5 T100 A60 S    ; sweep eixo X: 5 -> 100 Hz, accel/Hz 60, S = start
M496                     ; abortar a qualquer momento
M495 Y F5 T100 A60 S    ; idem eixo Y
```
- Anote a frequência aproximada do pico de vibração de cada eixo.
- Vá direto pro passo **2d** pra aplicar. Se quiser precisão, confirme com a torre (Método B).

### Método B — torre de ringing (medição visual)

#### 2a. Gerar a torre (OpenSCAD → STL)

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

## 5. Calibrações extras (opcionais, melhoram qualidade)

> **Como gerar as torres facilmente:** Cura → **Marketplace** → instala o plugin
> **"Calibration Shapes"** (5axes/fieldOfView). Adiciona modelos prontos em
> *Extensions → Part for calibration*: torre de temperatura, torre de retração, teste de
> ringing/ressonância, cubo de flow, etc. — mais simples que baixar STL avulso. Várias
> usam um post-processing script do Cura (Extensions → Post Processing) pra variar o
> parâmetro por altura.

### 5a. Flow / multiplicador de extrusão
1. Imprime um **cubo de parede única** (vaso, 1 perímetro, 0 infill/top).
2. Mede a espessura da parede com paquímetro (alvo = line width, ex. 0.40 mm).
3. `flow_novo = flow_atual × (alvo ÷ medido)`. Ajusta no Cura (Material → Flow) por material.
   - Ex.: alvo 0.40, mediu 0.42 → 100 × 0.40/0.42 = **95%**.

### 5b. Torre de temperatura (por material)
- Gera pelo plugin (Temp Tower) ou STL "SmartTempTower".
- Faixas de partida: PLA 190–215 · PETG 230–250 · ABS 235–255.
- Escolhe a temp com melhor ponte/overhang e menos stringing → grava no perfil do material.

### 5c. Retração (direct drive = simples)
- Bulldog direct: já em 0.8–1.0 mm; raramente precisa de torre.
- Stringing após acertar temperatura → torre de retração (plugin), varia 0.5–1.5 mm.
- Velocidade: o firmware agora permite até **50 mm/s** (era 25). Perfis Velocidade usam 45.

### 5d. Ordem recomendada
1. ✅ MPC (térmica) → 2. ✅ Mesh → 3. **FT freq (ringing)** → 4. **Z-offset fino (babystep)**
→ 5. Flow → 6. Temperatura → 7. **Linear Advance K** → 8. Retração (se precisar)

Sempre **uma variável por vez**, re-testa.

---

## 6. Ganhar velocidade (depois da qualidade base)

Velocidade real é limitada por: **vazão do hotend > torque dos motores > massa do cabeçote**.

### 6a. Vazão máxima (mm³/s) — A calibração de velocidade
Acha o teto real de vazão do BP6 (copper block + brass + sock):
1. Imprime uma **parede única** (vaso, 0.2 camada, 0.4 width) subindo a **velocidade** em
   degraus: 40, 60, 80, 100, 120, 140 mm/s.
2. Acha onde começa a **sub-extrudir** (falhas, superfície rugosa, extrusor "clicando").
3. `vazão_max = velocidade_boa × 0.2 × 0.4` (ex.: 100 mm/s × 0.08 = 8 mm³/s).
   Com copper + brass + sock, espera **~12–15 mm³/s** (melhor que V6 puro).
4. **Seta no Cura:** Material → **Maximum Volumetric Speed** = ~90% do máximo achado.
   Aí o Cura limita TODA velocidade pra não passar da vazão → podes subir os speeds dos
   perfis sem sub-extrudir.

> Atalho: **OrcaSlicer** tem teste "Max flow rate" embutido (menu Calibration). Dá pra usar
> só pra calibrar e seguir imprimindo no Cura.

### 6b. Limite de aceleração
Com FT_MOTION ativo, sobe a accel em degraus e procura **layer shift** (perde passo) ou
ringing forte. Gantry XL pesado + 12V limita isso — acha o teto e fica abaixo.

### 6c. Teto de hardware (quando esgotar o software)
1. **24V** (torque em alta + heating) → 2. **Bico CHT high-flow** (vazão ~20–25) →
3. **Extrusor leve** (menos massa = mais accel) → 4. **Klipper** (tira o gargalo do MCU G0).

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
