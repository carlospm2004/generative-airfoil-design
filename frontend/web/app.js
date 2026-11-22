// Airfoil AI: interfaz web.
// Todas las peticiones van a /api/..., que nginx reenvía al servicio de la API.

const API = "/api";
const MAX_COMPARAR = 5;
const COLORES_COMPARAR = ["#e5501b", "#18212c", "#2f7ea8", "#6f8f2f", "#8a5cb8"];
const TINTA = "#18212c";
const GRAFITO = "#5a646f";
const NARANJA = "#e5501b";
const FUENTE = "Barlow, system-ui, sans-serif";

const estado = {
  familias: [],          // [{familia, n_perfiles}]
  todos: null,           // catálogo completo, se carga una vez (comparador y mapa)
  catalogo: [],          // resultado de los filtros
  orden: { columna: "nombre", ascendente: true },
  comparar: cargarComparador(),
};

// ---------------------------------------------------------------- utilidades

const $ = (id) => document.getElementById(id);

async function pedir(ruta, parametros = {}) {
  const url = new URL(API + ruta, window.location.origin);
  for (const [clave, valor] of Object.entries(parametros)) {
    if (Array.isArray(valor)) valor.forEach((v) => url.searchParams.append(clave, v));
    else if (valor !== null && valor !== undefined && valor !== "") url.searchParams.set(clave, valor);
  }
  const respuesta = await fetch(url);
  if (!respuesta.ok) {
    let detalle = `error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      if (typeof cuerpo.detail === "string") detalle = cuerpo.detail;
    } catch { /* la respuesta no es JSON */ }
    const error = new Error(detalle);
    error.status = respuesta.status;
    throw error;
  }
  return respuesta.json();
}

function mensajeError(error) {
  if (error.status === 404) return error.message;
  if (error.status) return `La API ha respondido con un error: ${error.message}.`;
  return "No se puede conectar con la API. Comprueba que los servicios están en marcha con docker compose ps.";
}

const formato1 = new Intl.NumberFormat("es-ES", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const formato2 = new Intl.NumberFormat("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const formato4 = new Intl.NumberFormat("es-ES", { minimumFractionDigits: 4, maximumFractionDigits: 4 });

// Fracción de cuerda -> "12,0 %"
function pct(valor, formato = formato1) {
  return valor === null || valor === undefined ? "—" : `${formato.format(valor * 100)} %`;
}

function elemento(etiqueta, propiedades = {}, ...hijos) {
  const nodo = document.createElement(etiqueta);
  for (const [clave, valor] of Object.entries(propiedades)) {
    if (clave === "texto") nodo.textContent = valor;
    else if (clave === "clase") nodo.className = valor;
    else if (clave.startsWith("on")) nodo.addEventListener(clave.slice(2), valor);
    else nodo.setAttribute(clave, valor);
  }
  for (const hijo of hijos) if (hijo !== null && hijo !== undefined) nodo.append(hijo);
  return nodo;
}

function retrasar(funcion, ms) {
  let temporizador;
  return (...argumentos) => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => funcion(...argumentos), ms);
  };
}

function hayPlotly(contenedor) {
  if (window.Plotly) return true;
  contenedor.replaceChildren(elemento("p", { clase: "aviso", texto: "No se ha podido cargar la librería de gráficos (Plotly). Comprueba la conexión a internet y recarga la página." }));
  return false;
}

async function cargarTodos() {
  if (!estado.todos) estado.todos = await pedir("/perfiles");
  return estado.todos;
}

// Interpolación lineal; xs debe estar ordenado de menor a mayor
function interpolar(x, xs, ys) {
  if (x <= xs[0]) return ys[0];
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
  let i = 1;
  while (xs[i] < x) i++;
  const t = (x - xs[i - 1]) / (xs[i] - xs[i - 1] || 1);
  return ys[i - 1] + t * (ys[i] - ys[i - 1]);
}

// Separa extradós e intradós (orden Selig: BS -> extradós -> BA -> intradós -> BS)
// y calcula, en una rejilla común, las dos superficies y la línea media.
function superficies(x, y) {
  let iBA = 0;
  for (let i = 1; i < x.length; i++) if (x[i] < x[iBA]) iBA = i;
  const xe = x.slice(0, iBA + 1).reverse();
  const ye = y.slice(0, iBA + 1).reverse();
  const xi = x.slice(iBA);
  const yi = y.slice(iBA);
  const rejilla = Array.from({ length: 201 }, (_, k) => k / 200);
  const extrados = rejilla.map((v) => interpolar(v, xe, ye));
  const intrados = rejilla.map((v) => interpolar(v, xi, yi));
  const media = rejilla.map((_, k) => (extrados[k] + intrados[k]) / 2);
  return { rejilla, extrados, intrados, media };
}

// ---------------------------------------------------------------- comparador (estado)

function cargarComparador() {
  try {
    const guardado = JSON.parse(localStorage.getItem("comparador") || "[]");
    return Array.isArray(guardado) ? guardado.slice(0, MAX_COMPARAR) : [];
  } catch {
    return [];
  }
}

function guardarComparador() {
  try { localStorage.setItem("comparador", JSON.stringify(estado.comparar)); } catch { /* sin almacenamiento */ }
  const contador = $("contador-comparador");
  contador.textContent = estado.comparar.length;
  contador.hidden = estado.comparar.length === 0;
}

function enComparador(archivo) {
  return estado.comparar.includes(archivo);
}

function alternarComparador(archivo) {
  if (enComparador(archivo)) {
    estado.comparar = estado.comparar.filter((a) => a !== archivo);
  } else if (estado.comparar.length < MAX_COMPARAR) {
    estado.comparar.push(archivo);
  } else {
    return false;
  }
  guardarComparador();
  return true;
}

// ---------------------------------------------------------------- catálogo

function parametrosFiltro() {
  const familias = [...document.querySelectorAll("#lista-familias input:checked")].map((c) => c.value);
  const fraccion = (id) => {
    const valor = $(id).value.trim().replace(",", ".");
    return valor === "" ? null : Number(valor) / 100;
  };
  return {
    familia: familias,
    espesor_min: fraccion("espesor-min"),
    espesor_max: fraccion("espesor-max"),
    curvatura_min: fraccion("curvatura-min"),
    curvatura_max: fraccion("curvatura-max"),
  };
}

async function iniciarCatalogo() {
  try {
    estado.familias = await pedir("/familias");
  } catch (error) {
    mostrarAvisoCatalogo(mensajeError(error));
    return;
  }

  const lista = $("lista-familias");
  lista.replaceChildren(...estado.familias.map((f) =>
    elemento("label", {},
      elemento("span", { clase: "nombre" }, elemento("input", { type: "checkbox", value: f.familia }), f.familia),
      elemento("span", { clase: "n", texto: f.n_perfiles }),
    ),
  ));

  const actualizar = retrasar(actualizarCatalogo, 250);
  lista.addEventListener("change", actualizar);
  for (const id of ["espesor-min", "espesor-max", "curvatura-min", "curvatura-max"]) $(id).addEventListener("input", actualizar);
  $("buscar").addEventListener("input", pintarTabla);
  $("quitar-filtros").addEventListener("click", () => {
    lista.querySelectorAll("input").forEach((c) => { c.checked = false; });
    for (const id of ["espesor-min", "espesor-max", "curvatura-min", "curvatura-max", "buscar"]) $(id).value = "";
    actualizarCatalogo();
  });
  document.querySelectorAll("#tabla-perfiles thead button").forEach((boton) =>
    boton.addEventListener("click", () => {
      const columna = boton.dataset.orden;
      estado.orden = {
        columna,
        ascendente: estado.orden.columna === columna ? !estado.orden.ascendente : true,
      };
      pintarTabla();
    }),
  );

  await actualizarCatalogo();
}

function mostrarAvisoCatalogo(texto) {
  const aviso = $("aviso-catalogo");
  aviso.textContent = texto;
  aviso.hidden = !texto;
}

async function actualizarCatalogo() {
  try {
    estado.catalogo = await pedir("/perfiles", parametrosFiltro());
    mostrarAvisoCatalogo("");
  } catch (error) {
    estado.catalogo = [];
    mostrarAvisoCatalogo(mensajeError(error));
  }
  pintarTabla();
}

function filasVisibles() {
  const texto = $("buscar").value.trim().toLowerCase();
  const { columna, ascendente } = estado.orden;
  const filas = texto
    ? estado.catalogo.filter((p) => p.nombre.toLowerCase().includes(texto) || p.archivo.toLowerCase().includes(texto))
    : [...estado.catalogo];
  filas.sort((a, b) => {
    const va = a[columna];
    const vb = b[columna];
    if (va === null) return 1;      // los vacíos siempre al final
    if (vb === null) return -1;
    const comparacion = typeof va === "string" ? va.localeCompare(vb, "es", { numeric: true }) : va - vb;
    return ascendente ? comparacion : -comparacion;
  });
  return filas;
}

function pintarTabla() {
  const filas = filasVisibles();
  const total = estado.familias.reduce((suma, f) => suma + f.n_perfiles, 0);

  const recuento = $("recuento");
  recuento.replaceChildren(
    `${filas.length.toLocaleString("es-ES")} ${filas.length === 1 ? "perfil" : "perfiles"} `,
    elemento("span", { clase: "total", texto: `de ${total.toLocaleString("es-ES")}` }),
  );

  document.querySelectorAll("#tabla-perfiles thead button").forEach((boton) => {
    if (boton.dataset.orden === estado.orden.columna) boton.setAttribute("aria-sort", estado.orden.ascendente ? "ascending" : "descending");
    else boton.removeAttribute("aria-sort");
  });

  const cuerpo = $("cuerpo-tabla");
  if (filas.length === 0 && $("aviso-catalogo").hidden) {
    cuerpo.replaceChildren(elemento("tr", {}, elemento("td", { colspan: 7, texto: "Ningún perfil cumple estos filtros. Amplía los rangos o quita alguna familia." })));
    return;
  }

  cuerpo.replaceChildren(...filas.map((p) => {
    const marcado = enComparador(p.archivo);
    const boton = elemento("button", {
      type: "button",
      clase: "marcar-comparar",
      "aria-pressed": String(marcado),
      "aria-label": `${marcado ? "Quitar" : "Añadir"} ${p.nombre} ${marcado ? "del" : "al"} comparador`,
      title: marcado ? "Quitar del comparador" : "Añadir al comparador",
      texto: marcado ? "✓" : "+",
      onclick: (evento) => {
        evento.stopPropagation();
        if (!alternarComparador(p.archivo)) {
          mostrarAvisoCatalogo(`El comparador ya tiene ${MAX_COMPARAR} perfiles. Quita alguno antes de añadir otro.`);
          return;
        }
        mostrarAvisoCatalogo("");
        pintarTabla();
      },
    });
    const celdaNum = (valor) => elemento("td", { clase: valor === null ? "num vacio" : "num", texto: pct(valor) });
    return elemento("tr", { onclick: () => { window.location.hash = `#/perfil/${encodeURIComponent(p.archivo)}`; } },
      elemento("td", { clase: "col-comparar" }, boton),
      elemento("td", { clase: "nombre-perfil" },
        elemento("a", { href: `#/perfil/${encodeURIComponent(p.archivo)}`, texto: p.nombre }),
        elemento("span", { clase: "sub", texto: p.archivo }),
      ),
      elemento("td", { texto: p.familia }),
      celdaNum(p.t_max),
      celdaNum(p.x_t_max),
      celdaNum(p.f_max),
      celdaNum(p.x_f_max),
    );
  }));
}

// ---------------------------------------------------------------- ficha

async function mostrarPerfil(archivo) {
  const vista = $("vista-perfil");
  const grafico = $("grafico-ficha");
  $("ficha-nombre").textContent = "Cargando…";
  for (const id of ["ficha-familia", "ficha-archivo", "ficha-descripcion"]) $(id).textContent = "";
  $("ficha-datos").replaceChildren();
  $("ficha-comparar").hidden = true;

  let perfil;
  let coordenadas;
  try {
    [perfil, coordenadas] = await Promise.all([
      pedir(`/perfiles/${encodeURIComponent(archivo)}`),
      pedir(`/perfiles/${encodeURIComponent(archivo)}/coordenadas`),
    ]);
  } catch (error) {
    $("ficha-nombre").textContent = "Perfil no encontrado";
    $("ficha-descripcion").textContent = mensajeError(error);
    if (window.Plotly) Plotly.purge(grafico);
    grafico.replaceChildren();
    return;
  }
  if (vista.hidden) return; // el usuario ya se ha ido a otra vista

  document.title = `${perfil.nombre} · Airfoil AI`;
  $("ficha-nombre").textContent = perfil.nombre;
  $("ficha-familia").textContent = perfil.familia;
  $("ficha-archivo").textContent = perfil.archivo;
  $("ficha-descripcion").textContent = perfil.descripcion ?? "Sin descripción en la base de datos de la UIUC.";

  const boton = $("ficha-comparar");
  const pintarBoton = () => {
    const marcado = enComparador(archivo);
    const lleno = !marcado && estado.comparar.length >= MAX_COMPARAR;
    boton.textContent = marcado ? "Quitar del comparador" : lleno ? `Comparador lleno (${MAX_COMPARAR})` : "Añadir al comparador";
    boton.disabled = lleno;
    boton.classList.toggle("activo", marcado);
  };
  boton.onclick = () => { alternarComparador(archivo); pintarBoton(); };
  boton.hidden = false;
  pintarBoton();

  const dato = (titulo, valor, detalle) =>
    elemento("div", {}, elemento("dt", { texto: titulo }), elemento("dd", {}, valor, detalle ? elemento("small", { texto: detalle }) : null));
  $("ficha-datos").replaceChildren(
    dato("Espesor máximo", pct(perfil.t_max), `en x = ${pct(perfil.x_t_max, formato1)}`),
    dato("Curvatura máxima", pct(perfil.f_max, formato2), perfil.x_f_max === null ? "sin curvatura positiva" : `en x = ${pct(perfil.x_f_max)}`),
    dato("Curvatura mínima", pct(perfil.f_min, formato2), perfil.f_min < -0.005 ? "reflex o curvatura negativa" : null),
    dato("Espesor del borde de salida", pct(perfil.espesor_bs, formato2), perfil.espesor_bs < 1e-6 ? "borde cerrado" : "borde abierto"),
    dato("Área de la sección", formato4.format(perfil.area), "c²"),
    dato("Simétrico", perfil.simetrico ? "Sí" : "No"),
  );

  if (hayPlotly(grafico)) dibujarFicha(grafico, perfil, coordenadas);
}

function dibujarFicha(grafico, perfil, coordenadas) {
  const { x, y } = coordenadas;
  const s = superficies(x, y);
  const anotaciones = [];
  const formas = [];
  const etiqueta = { font: { family: FUENTE, size: 13, color: TINTA }, bgcolor: "rgba(247,248,249,0.85)", borderpad: 2 };

  // Cota del espesor máximo, en su posición
  const kt = Math.round(perfil.x_t_max * 200);
  formas.push({ type: "line", x0: perfil.x_t_max, x1: perfil.x_t_max, y0: s.intrados[kt], y1: s.extrados[kt], line: { color: GRAFITO, width: 1.5 } });
  anotaciones.push({ ...etiqueta, x: perfil.x_t_max, y: s.extrados[kt], yshift: 16, showarrow: false, text: `t = ${pct(perfil.t_max)}` });

  // Curvatura máxima, si la hay
  if (perfil.x_f_max !== null) {
    const kf = Math.round(perfil.x_f_max * 200);
    anotaciones.push({ ...etiqueta, x: perfil.x_f_max, y: s.media[kf], ax: 0, ay: 0, showarrow: false, yshift: -14, font: { ...etiqueta.font, color: NARANJA }, text: `f = ${pct(perfil.f_max, formato2)}` });
  }

  const trazas = [
    { x: [0, 1], y: [0, 0], mode: "lines", line: { color: GRAFITO, width: 1, dash: "dot" }, hoverinfo: "skip" },
    {
      x, y, mode: "lines", fill: "toself", fillcolor: "rgba(24,33,44,0.06)",
      line: { color: TINTA, width: 3 }, hovertemplate: "x = %{x:.4f}<br>y = %{y:.4f}<extra></extra>",
    },
    { x: s.rejilla, y: s.media, mode: "lines", line: { color: NARANJA, width: 2, dash: "dash" }, hoverinfo: "skip" },
  ];
  if (perfil.x_f_max !== null) {
    const kf = Math.round(perfil.x_f_max * 200);
    trazas.push({ x: [perfil.x_f_max], y: [s.media[kf]], mode: "markers", marker: { color: NARANJA, size: 8 }, hoverinfo: "skip" });
  }

  Plotly.react(grafico, trazas, {
    ...disenoBase(),
    showlegend: false,
    shapes: formas,
    annotations: anotaciones,
    xaxis: { ...ejeBase("x/c"), range: [-0.03, 1.03] },
    yaxis: { ...ejeBase("y/c"), scaleanchor: "x", scaleratio: 1 },
  }, configuracionBase());
}

// ---------------------------------------------------------------- comparador

async function mostrarComparador() {
  const aviso = $("aviso-comparar");
  aviso.hidden = true;

  try {
    const todos = await cargarTodos();
    $("opciones-perfiles").replaceChildren(...todos.map((p) => elemento("option", { value: p.archivo, label: `${p.nombre} (${p.familia})` })));
  } catch (error) {
    aviso.textContent = mensajeError(error);
    aviso.hidden = false;
    return;
  }

  const lista = $("seleccion");
  const grafico = $("grafico-comparar");
  const tabla = $("tabla-comparar");

  if (estado.comparar.length === 0) {
    lista.replaceChildren(elemento("li", { texto: "Todavía no hay perfiles. Añádelos con el buscador o con el botón + del catálogo." }));
    if (window.Plotly) Plotly.purge(grafico);
    grafico.hidden = true;
    tabla.replaceChildren();
    return;
  }
  grafico.hidden = false;

  let datos;
  try {
    datos = await Promise.all(estado.comparar.map(async (archivo) => {
      const [perfil, coordenadas] = await Promise.all([
        pedir(`/perfiles/${encodeURIComponent(archivo)}`),
        pedir(`/perfiles/${encodeURIComponent(archivo)}/coordenadas`),
      ]);
      return { perfil, coordenadas };
    }));
  } catch (error) {
    aviso.textContent = mensajeError(error);
    aviso.hidden = false;
    return;
  }
  if ($("vista-comparar").hidden) return;

  lista.replaceChildren(...datos.map(({ perfil }, i) =>
    elemento("li", {},
      elemento("span", { clase: "color", style: `background:${COLORES_COMPARAR[i]}` }),
      elemento("a", { href: `#/perfil/${encodeURIComponent(perfil.archivo)}`, texto: perfil.nombre }),
      elemento("button", {
        type: "button", "aria-label": `Quitar ${perfil.nombre} del comparador`, title: "Quitar", texto: "×",
        onclick: () => { alternarComparador(perfil.archivo); mostrarComparador(); },
      }),
    ),
  ));

  if (hayPlotly(grafico)) {
    Plotly.react(grafico, datos.map(({ perfil, coordenadas }, i) => ({
      x: coordenadas.x, y: coordenadas.y, mode: "lines", name: perfil.nombre,
      line: { color: COLORES_COMPARAR[i], width: 2.5 },
      hovertemplate: `${perfil.nombre}<br>x = %{x:.4f}<br>y = %{y:.4f}<extra></extra>`,
    })), {
      ...disenoBase(),
      showlegend: false,
      xaxis: { ...ejeBase("x/c"), range: [-0.03, 1.03] },
      yaxis: { ...ejeBase("y/c"), scaleanchor: "x", scaleratio: 1 },
    }, configuracionBase());
  }

  const filas = [
    ["Familia", (p) => p.familia],
    ["Espesor máximo", (p) => pct(p.t_max)],
    ["Posición del espesor máximo", (p) => pct(p.x_t_max)],
    ["Curvatura máxima", (p) => pct(p.f_max, formato2)],
    ["Posición de la curvatura máxima", (p) => pct(p.x_f_max)],
    ["Curvatura mínima", (p) => pct(p.f_min, formato2)],
    ["Espesor del borde de salida", (p) => pct(p.espesor_bs, formato2)],
    ["Área de la sección (c²)", (p) => formato4.format(p.area)],
    ["Simétrico", (p) => (p.simetrico ? "Sí" : "No")],
  ];
  tabla.replaceChildren(
    elemento("thead", {}, elemento("tr", {},
      elemento("th", { scope: "col" }, elemento("span", { clase: "oculto", texto: "Característica" })),
      ...datos.map(({ perfil }, i) => elemento("th", { scope: "col", clase: "num", style: `color:${COLORES_COMPARAR[i]}`, texto: perfil.nombre })),
    )),
    elemento("tbody", {}, ...filas.map(([titulo, valor]) =>
      elemento("tr", {},
        elemento("th", { scope: "row", texto: titulo }),
        ...datos.map(({ perfil }) => elemento("td", { clase: "num", texto: valor(perfil) })),
      ),
    )),
  );
}

function iniciarComparador() {
  $("form-anadir").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const aviso = $("aviso-comparar");
    const campo = $("anadir-perfil");
    const texto = campo.value.trim().toLowerCase();
    if (!texto) return;
    const todos = await cargarTodos();
    const encontrado = todos.find((p) => p.archivo.toLowerCase() === texto)
      ?? todos.find((p) => p.archivo.toLowerCase() === `${texto}.dat` || p.nombre.toLowerCase() === texto);
    if (!encontrado) {
      aviso.textContent = `No hay ningún perfil llamado «${campo.value.trim()}». Elige uno de la lista que aparece al escribir.`;
      aviso.hidden = false;
      return;
    }
    if (enComparador(encontrado.archivo)) {
      aviso.textContent = `${encontrado.nombre} ya está en el comparador.`;
      aviso.hidden = false;
      return;
    }
    if (!alternarComparador(encontrado.archivo)) {
      aviso.textContent = `El comparador ya tiene ${MAX_COMPARAR} perfiles. Quita alguno antes de añadir otro.`;
      aviso.hidden = false;
      return;
    }
    campo.value = "";
    mostrarComparador();
  });
}

// ---------------------------------------------------------------- mapa

async function mostrarMapa() {
  const grafico = $("grafico-mapa");
  let todos;
  try {
    todos = await cargarTodos();
  } catch (error) {
    grafico.replaceChildren(elemento("p", { clase: "aviso", texto: mensajeError(error) }));
    return;
  }

  const selector = $("mapa-familia");
  if (selector.options.length === 0) {
    if (estado.familias.length === 0) estado.familias = await pedir("/familias");
    selector.replaceChildren(
      elemento("option", { value: "", texto: "Ninguna" }),
      ...estado.familias.map((f) => elemento("option", { value: f.familia, texto: `${f.familia} (${f.n_perfiles})` })),
    );
    selector.addEventListener("change", () => pintarMapa(todos));
  }
  if ($("vista-mapa").hidden) return;
  pintarMapa(todos);
}

function pintarMapa(todos) {
  const grafico = $("grafico-mapa");
  if (!hayPlotly(grafico)) return;
  const familia = $("mapa-familia").value;

  const traza = (perfiles, nombre, color, tamano) => ({
    x: perfiles.map((p) => p.f_max * 100),
    y: perfiles.map((p) => p.t_max * 100),
    customdata: perfiles.map((p) => [p.archivo, p.nombre, p.familia]),
    mode: "markers", type: "scattergl", name: nombre,
    marker: { color, size: tamano, line: { width: 0 } },
    hovertemplate: "<b>%{customdata[1]}</b><br>%{customdata[2]}<br>Curvatura %{x:.2f} %<br>Espesor %{y:.1f} %<extra></extra>",
  });

  const resto = familia ? todos.filter((p) => p.familia !== familia) : todos;
  const trazas = [traza(resto, "Resto", familia ? "rgba(90,100,111,0.25)" : "rgba(24,33,44,0.55)", 6)];
  if (familia) trazas.push(traza(todos.filter((p) => p.familia === familia), familia, NARANJA, 9));

  Plotly.react(grafico, trazas, {
    ...disenoBase(),
    showlegend: false,
    xaxis: { ...ejeBase("Curvatura máxima (% de la cuerda)"), zeroline: true, zerolinecolor: "#c8ced4" },
    yaxis: { ...ejeBase("Espesor máximo (% de la cuerda)") },
    hovermode: "closest",
  }, configuracionBase());

  if (!grafico.dataset.escuchando) {
    grafico.on("plotly_click", (evento) => {
      const punto = evento.points[0];
      if (punto) window.location.hash = `#/perfil/${encodeURIComponent(punto.customdata[0])}`;
    });
    grafico.dataset.escuchando = "1";
  }
}

// ---------------------------------------------------------------- Plotly común

function disenoBase() {
  return {
    font: { family: FUENTE, size: 13, color: TINTA },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 64, r: 20, t: 24, b: 64 },
    hoverlabel: { font: { family: FUENTE } },
  };
}

function ejeBase(titulo) {
  return {
    title: { text: titulo, font: { size: 13, color: GRAFITO } },
    gridcolor: "#e1e5e9", zeroline: false, linecolor: "#c8ced4",
    tickfont: { color: GRAFITO },
  };
}

function configuracionBase() {
  return {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d", "toggleSpikelines"],
  };
}

// ---------------------------------------------------------------- navegación

function navegar() {
  const ruta = window.location.hash.replace(/^#\/?/, "") || "catalogo";
  const [vista, ...resto] = ruta.split("/");
  const vistas = { catalogo: "vista-catalogo", perfil: "vista-perfil", comparar: "vista-comparar", mapa: "vista-mapa" };
  const actual = vistas[vista] ? vista : "catalogo";

  for (const [nombre, id] of Object.entries(vistas)) $(id).hidden = nombre !== actual;
  document.querySelectorAll(".pestanas a").forEach((a) => {
    const activa = a.dataset.vista === actual || (actual === "perfil" && a.dataset.vista === "catalogo");
    if (activa) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  document.title = "Airfoil AI";
  window.scrollTo(0, 0);

  if (actual === "perfil") mostrarPerfil(decodeURIComponent(resto.join("/")));
  if (actual === "comparar") mostrarComparador();
  if (actual === "mapa") mostrarMapa();
  if (actual === "catalogo" && estado.catalogo.length) pintarTabla(); // refleja cambios del comparador
}

window.addEventListener("hashchange", navegar);
guardarComparador();
iniciarComparador();
iniciarCatalogo();
navegar();
