(function () {
    const datosEl = document.getElementById('msort-datos');
    const arbolEl = document.getElementById('msort-arbol');
    if (!datosEl || !arbolEl) return;

    // El rastro lo genera el algoritmo en Python; aquí solo se dibuja.
    const datos = JSON.parse(datosEl.textContent);
    const eventos = datos.eventos;
    const n = datos.n;
    let paso = 0; // índice del evento mostrado (0 = arreglo original)
    let temporizador = null;

    const faseEl = document.getElementById('msort-fase');
    const mensajeEl = document.getElementById('msort-mensaje');
    const pasoEl = document.getElementById('msort-paso');
    const comparacionesEl = document.getElementById('msort-comparaciones');
    const botones = {
        anterior: document.getElementById('msort-anterior'),
        siguiente: document.getElementById('msort-siguiente'),
        reproducir: document.getElementById('msort-reproducir'),
        final: document.getElementById('msort-final'),
        reiniciar: document.getElementById('msort-reiniciar'),
    };

    const FASES = {
        inicio: 'Arreglo original',
        dividir: 'Fase 1 · Dividir',
        base: 'Fase 1 · Caso base',
        combinar: 'Fase 2 · Combinar',
        comparar: 'Fase 2 · Combinar',
        resto: 'Fase 2 · Combinar',
        combinado: 'Fase 2 · Combinar',
        fin: 'Arreglo ordenado',
    };

    // Una fila por nivel de división; cada fila usa n columnas para que cada
    // bloque quede justo debajo de la parte de la que salió.
    const filas = [];
    for (let nivel = 0; nivel < datos.niveles; nivel++) {
        const fila = document.createElement('div');
        fila.className = 'msort-fila';
        const etiqueta = document.createElement('span');
        etiqueta.className = 'msort-nivel';
        etiqueta.textContent = 'Nivel ' + nivel;
        const bloques = document.createElement('div');
        bloques.className = 'msort-bloques';
        bloques.style.gridTemplateColumns = 'repeat(' + n + ', minmax(0, 1fr))';
        fila.append(etiqueta, bloques);
        arbolEl.appendChild(fila);
        filas.push(bloques);
    }

    function dibujar() {
        const evento = eventos[paso];
        filas.forEach((bloques) => { bloques.textContent = ''; });

        const marcas = {};
        evento.marcas.forEach((marca) => {
            marcas[marca.nodo + ':' + marca.indice] = marca.tipo;
        });

        evento.nodos.forEach((nodo) => {
            const bloque = document.createElement('div');
            bloque.className = 'msort-bloque estado-' + nodo.estado;
            bloque.style.gridColumn = (nodo.inicio + 1) + ' / ' + (nodo.fin + 1);
            const tamano = nodo.fin - nodo.inicio;
            for (let i = 0; i < tamano; i++) {
                const celda = document.createElement('span');
                celda.className = 'msort-celda';
                if (i < nodo.valores.length) {
                    celda.textContent = nodo.valores[i];
                    const tipo = marcas[nodo.id + ':' + i];
                    if (tipo) celda.classList.add('is-' + tipo);
                } else {
                    celda.classList.add('is-vacia'); // hueco que se llenará al combinar
                }
                bloque.appendChild(celda);
            }
            filas[nodo.nivel].appendChild(bloque);
        });

        faseEl.textContent = FASES[evento.accion] || '';
        mensajeEl.textContent = evento.mensaje;
        pasoEl.textContent = paso + ' / ' + (eventos.length - 1);
        comparacionesEl.textContent = evento.comparaciones;

        const alFinal = paso === eventos.length - 1;
        botones.anterior.disabled = paso === 0;
        botones.reiniciar.disabled = paso === 0;
        botones.siguiente.disabled = alFinal;
        botones.final.disabled = alFinal;
        botones.reproducir.disabled = alFinal;
        if (alFinal) detener();
    }

    function ir(nuevoPaso) {
        paso = Math.max(0, Math.min(eventos.length - 1, nuevoPaso));
        dibujar();
    }

    function detener() {
        if (temporizador !== null) {
            window.clearInterval(temporizador);
            temporizador = null;
        }
        botones.reproducir.textContent = 'Reproducir';
    }

    botones.siguiente.addEventListener('click', () => { detener(); ir(paso + 1); });
    botones.anterior.addEventListener('click', () => { detener(); ir(paso - 1); });
    botones.final.addEventListener('click', () => { detener(); ir(eventos.length - 1); });
    botones.reiniciar.addEventListener('click', () => { detener(); ir(0); });
    botones.reproducir.addEventListener('click', () => {
        if (temporizador !== null) { detener(); return; }
        botones.reproducir.textContent = 'Pausar';
        temporizador = window.setInterval(() => ir(paso + 1), 1100);
    });

    dibujar();
})();
