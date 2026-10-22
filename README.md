# ¿Es 2026 un año récord de incendios en el Perú?

**Pregunta E · Comparación de 2026 frente a 2012–2025, por departamento.**
Curso de Capacitación en Python Intermedio para CCSS y Gestión Pública · Clase 5, «Incendios en el Perú, vistos desde el espacio» · 21 de octubre de 2026.

El presente trabajo busca responder si 2026 constituye un año récord de incendios forestales en el Perú, comparando la actividad de fuego registrada en dicho año con la del periodo 2012–2025 en cada uno de los departamentos del país. Para ello, se utilizaron los focos de calor detectados por el sensor VIIRS a bordo del satélite Suomi-NPP, a la vez que se estimó el área quemada de un incendio específico mediante el índice dNBR calculado a partir de imágenes Sentinel-2.

El tablero interactivo con los principales resultados se encuentra en [`docs/index.html`](docs/index.html), el cual puede abrirse directamente en el navegador o publicarse a través de GitHub Pages (ver la sección 9).

![Mapa de récords por departamento](outputs/figuras/mapa_record.png)

---

## 1. Respuesta a la pregunta de investigación

A partir de los resultados obtenidos, se puede afirmar que la respuesta a la pregunta planteada no es unívoca. Para el país en su conjunto, 2026 no constituye un año récord, siendo que entre el 1 de enero y el 20 de octubre se registraron 50 996 focos de calor, lo cual equivale a 0,81 veces el promedio del periodo 2012–2025 y sitúa a este año en el puesto 12 de 15. Sin embargo, sí lo sería en determinados departamentos y en un momento particular de la temporada: Arequipa y Lima superan su máximo histórico bajo las cuatro medidas empleadas, a la vez que los primeros veinte días de octubre de 2026 son los más intensos de toda la serie, tanto a nivel nacional como en nueve departamentos andinos.

## 2. Principales hallazgos

Siguiendo lo anterior, los resultados del análisis permiten identificar tres hallazgos principales, los cuales se resumen en la siguiente tabla:

| # | Hallazgo | Cifra clave |
|---|---|---|
| 1 | 2026 no constituye un récord a nivel nacional. Entre el 1 de enero y el 20 de octubre se registraron 50 996 focos VIIRS S-NPP, frente a un promedio de 62 607 en la misma ventana del periodo 2012–2025, lo cual sitúa a este año en el puesto 12 de 15, lejos del máximo alcanzado en 2024 (86 964). En ello pesa en gran medida el déficit amazónico, siendo que Huánuco, Pasco y Madre de Dios registran su cifra más baja desde 2012 (0,60; 0,55 y 0,55 veces su promedio, respectivamente). | **×0,81** el promedio |
| 2 | Arequipa y Lima presentan un récord robusto. Arequipa registra 962 focos frente a su máximo previo de 718 (2013), es decir, un 34 % más, el doble de su promedio y 4,8 desviaciones estándar por encima de la media. Por su parte, Lima registra 715 focos frente a 542 (2016), un 32 % más, con un z de 4,2. Cabe resaltar que ambos departamentos son récord bajo las tres ventanas de tiempo y también según la energía radiativa del fuego (FRP: ×2,6 y ×2,1). | **+34 %** sobre el récord previo (Arequipa) |
| 3 | Octubre de 2026 es el más intenso de la serie. Entre el 1 y el 20 de octubre se registraron 12 953 focos, 1,89 veces el promedio, superando a 2020 (12 712). Asimismo, nueve departamentos con una muestra suficiente marcan récord de octubre: Áncash (×8,2), Apurímac (×7,0), Arequipa (×5,4), Huancavelica (×4,9), Ayacucho (×4,5), Lima (×4,3), Moquegua (×2,8), Cusco (×2,6) y Junín (×2,4). Tacna también lo hace, aunque con muy pocos focos. | **12 953** focos en 20 días |

Adicionalmente, en relación con la superficie afectada, el incendio más grande de Arequipa que contaba con imágenes limpias, ubicado en Chichas (Condesuyos), habría quemado alrededor de 1 422 ha según el dNBR, aunque esta cifra varía entre 199 y 2 013 ha dependiendo del método utilizado (ver la sección 5).

<table>
<tr>
<td width="50%"><img src="outputs/figuras/franja_departamentos.png" alt="Cada departamento contra su propia historia"></td>
<td width="50%"><img src="outputs/figuras/mapa_anomalia_raster.png" alt="Ráster de anomalía de focos 2026"></td>
</tr>
</table>

![Estacionalidad nacional](outputs/figuras/estacionalidad.png)

Ahora bien, la curva mensual permite explicar la aparente contradicción entre el primer y el tercer hallazgo. En ese sentido, se observa que 2026 se mantuvo por debajo de lo normal hasta septiembre y que la actividad de fuego se disparó recién en octubre. Es decir, el récord de 2026 sería tardío y concentrado en la sierra, y no en la Amazonía.

---

## 3. Datos utilizados y sus fechas

Debe tenerse presente que todas las fuentes utilizadas son públicas y no requieren clave de acceso ni pago, siguiendo lo recomendado en la lámina «Datos que ustedes pueden usar». La siguiente tabla detalla cada una de ellas:

| Dato | Fuente | Tipo | Cobertura usada |
|---|---|---|---|
| Focos de calor 2012–2025 | NASA FIRMS, archivo anual por país `viirs-snpp_<año>_Peru.csv` | Puntos (CSV) | 1 ene 2012 – 31 dic 2025 (procesamiento estándar, versión 2) |
| Focos de calor 2026 | INPE, Programa Queimadas, CSV mensual de Sudamérica (`focos_mensal_2026MM.csv`), satélites `NPP-375` y `NPP-375D` | Puntos (CSV) | 1 ene – 20 oct 2026 (archivo de octubre actualizado el 21/10/2026) |
| Calibración | FIRMS NRT `SUOMI_VIIRS_C2_South_America_7d.csv` e INPE `focos_mensal_202509.csv` | Puntos (CSV) | 15–19 oct 2026 y septiembre de 2025 |
| Límites | INEI con UBIGEO, repositorio `juaneladio/peru-geojson` (departamental y distrital) | Polígonos | — |
| Imágenes y área quemada | Sentinel-2 L2A en Microsoft Planetary Computer (`sentinel-2-l2a`), bandas B8A, B12, B04 y SCL | **Ráster** (20 m) | 13 oct 2026 (antes) y 20 oct 2026 (después) |
| Densidad de focos | Elaboración propia a partir de los focos | **Ráster** (0,1°) | 1 ene – 20 oct de cada año |

Cabe resaltar que FIRMS todavía no publica el archivo anual de 2026 (la dirección correspondiente devuelve un error 404), razón por la cual los datos de dicho año se obtuvieron de INPE, que distribuye la información del mismo sensor. En la sección 6 se muestra que ambas fuentes registran prácticamente lo mismo.

---

## 4. Metodología

### 4.1. Flujo de trabajo

El flujo de trabajo siguió los ocho pasos presentados en la lámina «Cómo lo hice», los cuales se adaptaron a la pregunta E. En ese sentido, cada paso corresponde a un script ubicado en la carpeta `src/`:

| Paso | Script | Descripción |
|---|---|---|
| 1 · Descargar | `01_descargar.py` | Se descargan los datos de FIRMS 2012–2025, FIRMS NRT de siete días, INPE 2026 (filtrado en streaming al rectángulo del Perú, considerando que cada CSV mensual pesa entre 100 y 170 MB) y los límites del INEI. |
| 2 · Limpiar | `02_procesar_focos.py` | Se integran las fuentes, se eliminan los duplicados, las fuentes fijas y los focos fuera del Perú, y se asigna el departamento mediante un *spatial join*. Asimismo, se calibra INPE frente a FIRMS. |
| 3 · Comparar | `03_comparar.py` | Se construye el panel departamento × año en tres ventanas y con FRP, y se calculan la razón, el z, el puesto y el récord. |
| 4 · Ráster | `04_raster_densidad.py` | Se convierten los focos en rásteres de 0,1° (2026, promedio 2012–2025 y anomalía) y se vuelve a tabla con `zonal_stats`. |
| 5 · dNBR | `05_dnbr_caso.py` | Se agrupan los focos en incendios, se buscan imágenes Sentinel-2 midiendo las nubes sobre la zona, y se calculan el NBR, el dNBR, el RdNBR y las hectáreas por clase y por distrito. |
| 6 · Figuras | `06_figuras.py` | Se elaboran el mapa de récords, la franja por departamento, la serie nacional y la estacionalidad. |
| 7 · Tablero | `07_tablero.py` | Se exportan los resultados como JSON incrustado en `docs/index.html`. |

### 4.2. Decisiones metodológicas

Ahora bien, debe mencionarse que varios de los resultados dependen de decisiones de método, por lo que se considera relevante explicar cada una de ellas y su justificación:

1. **Uso de un solo sensor.** Se optó por utilizar únicamente VIIRS a bordo de Suomi-NPP (375 m), ya que es el único sensor de esta resolución que cuenta con observaciones para todos los años desde 2012. Si se sumaran NOAA-20 (desde 2018) y NOAA-21 (desde 2023), los años recientes tendrían dos o tres veces más pasadas, por lo que parecerían récord por un artefacto de la medición.
2. **Pasadas diurnas y nocturnas en INPE.** En INPE el mismo sensor aparece con dos etiquetas: `NPP-375` corresponde a los pasos diurnos (17–19 h UTC) y `NPP-375D` a los nocturnos (5–7 h UTC, órbita descendente). Considerando que FIRMS incluye ambos, se decidió sumarlos.
3. **Misma ventana del calendario en todos los años.** Debido a que 2026 aún no termina, compararlo con años completos lo subestimaría. Por ello, la ventana principal abarca del 1 de enero al 20 de octubre (último día completo en INPE), a la vez que como análisis de sensibilidad se utilizaron la temporada seca (1 jul – 20 oct) y solo el mes de octubre (1–20 oct).
4. **Eliminación de duplicados.** Se consideró que dos focos de la misma pasada ubicados a menos de 100 m entre sí corresponden a una misma detección, siendo que dos píxeles VIIRS vecinos distan alrededor de 375 m. En ese sentido, se observó que el CSV casi en tiempo real de INPE 2026 contenía un 6 % de estos duplicados, frente a alrededor de 1 % en el archivo histórico de FIRMS, y que sin eliminarlos INPE sobrecontaba un 10,7 % respecto de FIRMS. Cabe resaltar que esta regla se aplicó de igual forma a los 15 años.
5. **Exclusión de fuentes fijas.** Se construyó una máscara de 500 m alrededor de todo foco que FIRMS clasificó como volcán activo (`type=1`) u otra fuente estática (`type=2`, como industrias o quema de gas) entre 2012 y 2025, y se descartó todo foco ubicado dentro de ella, independientemente del año. De esta forma, 2026, cuyos datos no incluyen el campo `type`, recibe el mismo filtro.
6. **Asignación a departamentos.** Esta se realizó con los polígonos del INEI (`sjoin`, predicado `within`), por lo que se excluyeron los focos ubicados en el mar y en los países vecinos.
7. **Definición de récord.** Se entiende por récord que 2026 supere al máximo 2012–2025 del mismo departamento en la misma ventana. Adicionalmente, se reportan la razón entre 2026 y el promedio, el puesto entre los 15 años y la desviación z. Así, se considera que un departamento presenta un récord robusto si lo es bajo las cuatro medidas (las tres ventanas y la FRP).
8. **Muestra mínima.** Con menos de 30 focos promedio al año, como en el caso de Callao (y de Tacna en octubre), un par de quemas podría alterar el ranking. Por ello, estos casos se muestran rayados y con la etiqueta «pocas detecciones».

### 4.3. Conceptos de la clase de ráster aplicados

Por otra parte, en el desarrollo del análisis se aplicaron varios de los conceptos trabajados en la clase de ráster aplicado:

- Un ráster es una matriz con `transform` y `crs`. En ese sentido, los rásteres de densidad (`data/processed/*.tif`) se construyeron con `rasterio.transform.from_origin` sobre una grilla de 0,1° en EPSG:4326.
- El paso de ráster a tabla se realizó con `zonal_stats`, declarando el `nodata` de forma explícita (−9999) y eligiendo de manera consciente el valor de `all_touched`. Aquí se utilizó `all_touched=False`, ya que con `True` una celda de borde se sumaría a dos departamentos y el total crecería artificialmente.
- Siguiendo la idea de validar antes de creer, se verificó que la suma zonal del ráster reproduce el conteo directo de puntos, con una diferencia total de −0,6 %.
- Respecto a la diferencia entre `sum` y `mean`, el mapa de récords compara cada departamento con su propio promedio (razón), mientras que la densidad (focos por 1 000 km²) responde a otra pregunta, referida a la intensidad por superficie. Al tratarse de medidas distintas, el tablero permite alternar entre ambas.
- Las áreas departamentales y los buffers de 500 m se calcularon en un CRS métrico (EPSG:24891) y no en grados.
- Finalmente, la razón entre 2026 y el promedio se representa en escala logarítmica (log2), de modo que el doble (×2) y la mitad (×0,5) tengan el mismo peso visual.

---

## 5. Estimación del área quemada mediante dNBR: el incendio de Chichas (Arequipa)

### 5.1. Selección del incendio y de las imágenes

Debe tenerse presente que un foco de calor no permite medir superficie. Por ello, para estimar las hectáreas quemadas se tomó el departamento con récord robusto y mayor número de focos, es decir, Arequipa, y dentro de este se siguió el siguiente procedimiento:

1. En primer lugar, los focos de julio a octubre de 2026 se agruparon en incendios siguiendo la regla presentada en la lámina «Cómo lo hice», según la cual los focos ubicados a ≤ 1 km y ≤ 48 h entre sí pertenecen al mismo incendio (DBSCAN con métrica de Chebyshev sobre x e y en km y los días divididos entre 2). A partir de ello se identificaron 180 incendios.
2. En segundo lugar, se seleccionó el incendio más grande que contaba con imágenes limpias: 66 focos VIIRS registrados entre el 17 y el 18 de octubre, con centro en −15,485°, −72,984°, en los distritos de Chichas (Condesuyos) y Toro (La Unión).
3. En tercer lugar, las nubes se midieron sobre la zona del incendio con la capa SCL, considerando que el porcentaje de nubes de toda la escena podría ser engañoso al referirse a un cuadro de 110 km. Las imágenes seleccionadas fueron las siguientes:

| | Fecha | Escena | Nubes en la zona | Nubes en la escena |
|---|---|---|---|---|
| Antes | 13 oct 2026 | `S2B_MSIL2A_20261013T150719_R082_T18LYH_20261013T201523` | 0,0 % | 2,6 % |
| Después | 20 oct 2026 | `S2A_MSIL2A_20261020T150931_R082_T18LYH_20261020T222456` | 1,7 % | 11,4 % |

   Cabe resaltar que ambas imágenes pertenecen a la misma órbita relativa (R082) y a la misma cuadrícula MGRS (18LYH), por lo que coinciden píxel a píxel y comparten el mismo ángulo de visión. La lista completa de escenas evaluadas se encuentra en `outputs/tablas/dnbr_imagenes_candidatas.csv`.
4. Finalmente, se calculó el NBR = (B8A − B12) / (B8A + B12) en reflectancia, restando el desplazamiento de +1000 que incluyen los datos desde el *processing baseline* 04.00, y a partir de ello el dNBR = NBR antes − NBR después. Asimismo, se enmascararon las nubes, sombras, cirros, nieve, agua y píxeles sin dato según la capa SCL. La zona analizada abarcó 123 km², con un 98,3 % de píxeles válidos.

![dNBR del incendio de Chichas](outputs/figuras/dnbr_caso.png)

### 5.2. Sensibilidad al umbral

Ahora bien, la cantidad de hectáreas quemadas depende en gran medida del umbral utilizado, tal como se observa en la siguiente tabla:

| Método | Hectáreas |
|---|---|
| dNBR ≥ 0,27, toda la zona | 216 |
| dNBR ≥ 0,27, conectado a focos VIIRS | 199 |
| dNBR ≥ 0,10, toda la zona | 1 504 |
| **dNBR ≥ 0,10, conectado a focos VIIRS (estimación principal)** | **1 422** |
| RdNBR ≥ 69, conectado a focos VIIRS | 2 013 |

Esto coincide con la lección presentada en la lámina sobre Curahuasi: *«La computadora siempre da un número. Ustedes deciden si es creíble: fechas, nubes, umbral y zona.»* En este caso, el umbral de 0,27 deja fuera casi toda la cicatriz que puede observarse a simple vista en la imagen posterior. Esto se debería a que la mediana del NBR antes del fuego en la zona quemada era de −0,10, propia de una puna y un matorral muy ralos, siendo que un bosque denso suele superar 0,5. Con tan poca vegetación inicial, el NBR no puede caer demasiado aunque toda la zona se queme.

Considerando esto, se optó por utilizar como estimación principal el límite inferior de la «severidad baja» (0,10), contando únicamente las manchas conectadas a algún foco VIIRS (≤ 375 m), de modo que no se sumen cambios aislados por sombras o cultivos. (El RdNBR, que divide el dNBR por la raíz del NBR previo, corrige precisamente por la escasez de vegetación según Miller y Thode, 2007; en este caso da una cifra mayor y se reporta como análisis de sensibilidad.)

Por clase de severidad del USGS, la estimación principal se distribuye de la siguiente forma: 1 206 ha de severidad baja, 215 ha de severidad moderada-baja, 0,5 ha de severidad moderada-alta y 0 ha de severidad alta. Por distrito, corresponden 1 006 ha a Chichas y 416 ha a Toro (`outputs/tablas/dnbr_hectareas_distrito.csv`).

---

## 6. Validaciones

Con el fin de verificar la consistencia de los resultados, se realizaron las siguientes comprobaciones:

| Comprobación | Resultado |
|---|---|
| INPE frente al archivo FIRMS, septiembre de 2025 (tras la limpieza) | 14 119 frente a 14 071 focos: **+0,3 %** |
| INPE frente a FIRMS NRT, 15–19 de octubre de 2026 (tras la limpieza) | 2 707 frente a 2 731 focos: **−0,9 %** |
| Mismo cruce, **sin** eliminar los duplicados | +10,7 %, lo cual justifica la deduplicación |
| Ráster de 0,1° + `zonal_stats` frente al conteo directo de puntos, 2026 | 50 679 frente a 50 996: **−0,6 %** (celdas de borde) |
| Monitor del profesor: focos del 1 al 16 de octubre de 2026 frente al promedio 2012–2025 | Profesor: 12 984 focos, +126 %. Este análisis: 12 248 focos, **+115 %**. La conclusión es la misma, y la diferencia (~6 %) es del mismo orden que los duplicados de INPE que aquí se eliminaron (6 % en octubre). |

Asimismo, la bitácora de limpieza (`outputs/tablas/bitacora_limpieza.csv`) registra la cantidad de focos excluidos en cada etapa:

| Fuente | Iniciales | Duplicados | Fuente fija | Fuera del Perú | Finales |
|---|---|---|---|---|---|
| FIRMS 2012–2025 | 1 047 074 | 12 588 | 26 396 | 3 662 | 1 004 428 |
| INPE 2026 (rectángulo del Perú) | 76 320 | 1 832 | 59 | 23 433 | 50 996 |

---

## 7. Limitaciones

Sin embargo, deben reconocerse algunas limitaciones del presente análisis:

- En primer lugar, un foco de calor no es un incendio. Se trata de un píxel de 375 m más caliente que su entorno en el momento del paso del satélite, por lo que una quema agrícola pequeña y un incendio de miles de hectáreas podrían sumar un número similar de focos. Es decir, contar focos mide la actividad de fuego detectada y no la superficie quemada.
- En segundo lugar, las nubes esconden el fuego. Un año más nublado registraría menos focos sin necesariamente tener menos fuego, sobre todo en la Amazonía, por lo que el déficit amazónico de 2026 podría deberse en parte a la nubosidad.
- Asimismo, S-NPP solo realiza dos pasadas al día (alrededor de las 13:30 y la 01:30, hora local), de modo que los fuegos breves que ocurren entre pasadas no son detectados.
- Por otra parte, los datos de 2026 son casi en tiempo real, por lo que INPE podría corregirlos o completarlos, mientras que la serie 2012–2025 se encuentra reprocesada. En 2026 se identificaron 5 días sin la pasada diurna (entre ellos el 12 de octubre, en plena temporada) y 4 días entre julio y octubre sin la nocturna. Si se tratara de vacíos en los datos, 2026 estaría ligeramente subestimado, por lo que los récords encontrados serían conservadores. En los días completos, la calibración muestra diferencias menores al 1 %.
- Del mismo modo, la serie de 2012 empieza el 20 de enero, fecha de inicio de VIIRS S-NPP, por lo que su mes de enero suma 700 focos frente a alrededor de 1 680 en promedio. Así, 2012 estaría subestimado en cerca de 1 000 focos (alrededor de 1,4 % de su total). Sin embargo, esto no cambia ningún veredicto, ya que 2012 es el máximo previo solo en San Martín, Huánuco y Pasco, donde 2026 se encuentra muy por debajo.
- También debe considerarse que el archivo «Perú» de FIRMS utiliza su propio límite de país, mientras que aquí los focos se reasignaron con los polígonos del INEI, de modo que algunos focos de frontera podrían quedar de uno u otro lado.
- En relación con el dNBR, en la puna y el matorral el NBR previo es bajo, por lo que el umbral de 0,27, calibrado en bosques, subestima considerablemente el área quemada. En ese sentido, la cifra de hectáreas depende del umbral (de 199 a 2 013 ha). Además, la imagen posterior fue tomada solo dos días después del último foco, por lo que podría faltar superficie si el fuego siguió activo. Cabe resaltar también que un solo incendio no representa a todo el departamento.
- Finalmente, este análisis describe dónde y cuándo 2026 rompe la serie histórica, pero no explica por qué ocurre esto (sequía, viento, quemas agrícolas o cambios en el uso del suelo). Es decir, se trata de una asociación y no de una relación causal.

---

## 8. Utilidad para la toma de decisiones

Considerando todo lo anterior, los resultados de este trabajo podrían ser útiles para la gestión pública en varios sentidos:

- En primer lugar, el promedio nacional puede resultar engañoso, siendo que un país «por debajo de lo normal» convive con departamentos en su máximo histórico. Por ello, las alertas, declaratorias y presupuestos de prevención deberían evaluarse por departamento y en relación con su propia línea base, y no con un umbral nacional.
- En segundo lugar, la temporada de incendios se habría desplazado hacia la sierra y hacia octubre. El exceso de 2026 se concentra en Arequipa, Lima, Apurímac, Áncash, Huancavelica y Ayacucho, particularmente en octubre, por lo que sería en estos lugares y en este periodo donde convendría reforzar las brigadas, el control de las quemas agrícolas y la comunicación del riesgo.
- Por otra parte, un año con menos focos en la Amazonía no implica que se deba bajar la guardia, ya que esto podría deberse a una mayor nubosidad o a un año más húmedo, y no necesariamente a una menor deforestación.
- Finalmente, las cifras de hectáreas quemadas deben venir acompañadas de su método. Para un mismo incendio la cifra puede ir de 199 a 2 013 ha según el umbral, por lo que cualquier reporte debería indicar las fechas, las nubes, el umbral y la zona.

*Herramienta académica independiente, que no reemplaza los reportes del COEN, INDECI, SERFOR ni SERNANP.*

---

## 9. Reproducción del análisis

Para reproducir el análisis se requiere contar con [uv](https://docs.astral.sh/uv/) y Python 3.12 o superior. Cabe resaltar que todo el procesamiento corre en CPU.

```bash
git clone https://github.com/<usuario>/incendios-record.git
cd incendios-record
uv sync
uv run python ejecutar_todo.py          # los 7 pasos en orden (~10 min con la descarga)
```

Asimismo, los pasos pueden ejecutarse de forma individual, empezando por `uv run python src/01_descargar.py` y continuando con `02_…` hasta `07_tablero.py`. Entre las opciones disponibles se encuentran las siguientes:

- `uv run python src/01_descargar.py --actualizar` vuelve a descargar el mes en curso de INPE.
- `uv run python src/05_dnbr_caso.py --departamento LIMA` repite el caso dNBR en otro departamento.
- La fecha de corte y los años de análisis se modifican únicamente en `src/config.py`.

En el caso de Windows, se recomienda clonar el repositorio en una ruta corta (por ejemplo, `Documents\GitHub`), ya que en carpetas muy profundas Windows no puede cargar las librerías de `shapely` debido al límite de 260 caracteres en la ruta.

Para publicar el tablero en GitHub Pages, se debe ir a *Settings → Pages* y elegir la rama `main` y la carpeta `/docs`. De esta forma, el tablero quedará disponible en `https://<usuario>.github.io/incendios-record/`.

Por último, debe mencionarse que los datos crudos (`data/raw/`, alrededor de 90 MB) no se incluyen en el repositorio, ya que se generan nuevamente en el paso 1. Sin embargo, sí se incluye `data/processed/focos_2012_2026.parquet`, que contiene los focos ya limpios, con el fin de que se pueda ejecutar el análisis desde el paso 3 sin necesidad de descargar nada.

## 10. Estructura del repositorio

```
incendios-record/
├── ejecutar_todo.py            corre los 7 pasos
├── src/
│   ├── config.py               años, fecha de corte, sensor y CRS: las decisiones en un solo lugar
│   ├── estilo.py               paleta y estilo de los gráficos
│   ├── 01_descargar.py … 07_tablero.py
│   └── plantilla_tablero.html  plantilla del tablero (HTML + SVG + JS, sin librerías)
├── data/processed/             focos limpios (parquet), rásteres de densidad, dNBR (GeoTIFF)
├── outputs/figuras/            mapas y gráficos del README
├── outputs/tablas/             paneles, récords, sensibilidad, calibración, hectáreas dNBR
└── docs/index.html             tablero interactivo autocontenido
```

## 11. Uso de Claude Code

Todo el código fue escrito con Claude Code, siguiendo la recomendación presentada en clase: *«Con Claude Code, pero ustedes deciden el método.»* En ese sentido, las decisiones que modificaron los resultados se tomaron a partir de la revisión de los datos y no por defecto:

- La revisión de las etiquetas de satélite de INPE permitió identificar que `NPP-375D` corresponde a las pasadas nocturnas del mismo S-NPP.
- La calibración frente a FIRMS NRT arrojó inicialmente una diferencia de +10,7 %. A partir de ello, se investigó esta diferencia y se encontraron los duplicados de INPE 2026, lo cual llevó a definir una regla uniforme que la redujo a −0,9 %.
- La revisión del mapa dNBR mostró que el umbral de 0,27 no capturaba la cicatriz visible en la imagen, razón por la cual se optó por el umbral de 0,10, la condición de conexión con los focos y el RdNBR como análisis de sensibilidad.
- Finalmente, la revisión del mapa de récords mostró que Callao, con casi ningún foco, distorsionaba la escala, lo cual llevó a establecer la regla de muestra mínima.

## Referencias

- Key, C. H. y Benson, N. C. (2006). Landscape Assessment: Ground measure of severity, the Composite Burn Index; and remote sensing of severity, the Normalized Burn Ratio. USDA Forest Service, RMRS-GTR-164-CD.
- Miller, J. D. y Thode, A. E. (2007). Quantifying burn severity in a heterogeneous landscape with a relative version of the delta Normalized Burn Ratio (dNBR). *Remote Sensing of Environment*, 109(1), 66–80.
- Schroeder, W., Oliva, P., Giglio, L. y Csiszar, I. (2014). The New VIIRS 375 m active fire detection data product. *Remote Sensing of Environment*, 143, 85–96.
- NASA FIRMS: <https://firms.modaps.eosdis.nasa.gov/> · INPE Queimadas: <https://terrabrasilis.dpi.inpe.br/queimadas/> · Microsoft Planetary Computer: <https://planetarycomputer.microsoft.com/>
