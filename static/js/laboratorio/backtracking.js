(function () {
    const datosEl = document.getElementById('reinas-datos');
    const tableroEl = document.getElementById('tablero');
    if (!datosEl || !tableroEl) return;

    // El rastro lo genera el algoritmo en Python; aquí solo se reproduce.
    const datos = JSON.parse(datosEl.textContent);
    const eventos = datos.eventos;
    const n = datos.n;
    let paso = 0; // cantidad de eventos ya mostrados (0 = tablero vacío)
    let temporizador = null;

    const mensajeEl = document.getElementById('reinas-mensaje');
    const pasoEl = document.getElementById('reinas-paso');
    const botones = {
        anterior: document.getElementById('reinas-anterior'),
        siguiente: document.getElementById('reinas-siguiente'),
        reproducir: document.getElementById('reinas-reproducir'),
        final: document.getElementById('reinas-final'),
        reiniciar: document.getElementById('reinas-reiniciar'),
    };
    const contadores = {
        intentar: document.getElementById('cont-intentos'),
        colocar: document.getElementById('cont-colocaciones'),
        conflicto: document.getElementById('cont-conflictos'),
        retroceder: document.getElementById('cont-retrocesos'),
    };

    const celdas = [];
    for (let fila = 0; fila < n; fila++) {
        for (let columna = 0; columna < n; columna++) {
            const celda = document.createElement('div');
            celda.className = 'celda ' + ((fila + columna) % 2 === 0 ? 'clara' : 'oscura');
            tableroEl.appendChild(celda);
            celdas.push(celda);
        }
    }
    tableroEl.style.gridTemplateColumns = 'repeat(' + n + ', 1fr)';

    function contarHasta(accion, hasta) {
        let total = 0;
        for (let i = 0; i < hasta; i++) {
            if (eventos[i].accion === accion) total++;
        }
        return total;
    }

    function dibujar() {
        celdas.forEach((celda) => {
            celda.className = celda.className.replace(/\s*(intento|conflicto|atacante|reina|retiro|solucion)\b/g, '');
            celda.textContent = '';
            celda.removeAttribute('aria-label');
        });
        const evento = paso > 0 ? eventos[paso - 1] : null;
        const reinas = evento ? evento.tablero : [];
        const esSolucion = evento && evento.accion === 'solucion';

        reinas.forEach((columna, fila) => {
            const celda = celdas[fila * n + columna];
            celda.classList.add('reina');
            if (esSolucion) celda.classList.add('solucion');
            celda.textContent = '♛';
            celda.setAttribute('aria-label', 'Reina en fila ' + (fila + 1) + ', columna ' + (columna + 1));
        });

        if (evento && evento.columna !== null && evento.fila !== null) {
            const celda = celdas[evento.fila * n + evento.columna];
            if (evento.accion === 'intentar') celda.classList.add('intento');
            if (evento.accion === 'conflicto') {
                celda.classList.add('conflicto');
                celda.textContent = '✕';
                const [filaAtacante, columnaAtacante] = evento.conflicto_con;
                celdas[filaAtacante * n + columnaAtacante].classList.add('atacante');
            }
            if (evento.accion === 'retroceder') {
                celda.classList.add('retiro');
                celda.textContent = '↩';
            }
        }

        mensajeEl.textContent = evento
            ? evento.mensaje
            : 'Pulsa «Siguiente» para empezar. El tablero está vacío.';
        pasoEl.textContent = paso + ' / ' + eventos.length;
        Object.keys(contadores).forEach((accion) => {
            contadores[accion].textContent = contarHasta(accion, paso);
        });
        botones.anterior.disabled = paso === 0;
        botones.reiniciar.disabled = paso === 0;
        const alFinal = paso === eventos.length;
        botones.siguiente.disabled = alFinal;
        botones.final.disabled = alFinal;
        if (alFinal) detener();
        botones.reproducir.disabled = alFinal;
    }

    function ir(nuevoPaso) {
        paso = Math.max(0, Math.min(eventos.length, nuevoPaso));
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
    botones.final.addEventListener('click', () => { detener(); ir(eventos.length); });
    botones.reiniciar.addEventListener('click', () => { detener(); ir(0); });
    botones.reproducir.addEventListener('click', () => {
        if (temporizador !== null) { detener(); return; }
        botones.reproducir.textContent = 'Pausar';
        temporizador = window.setInterval(() => ir(paso + 1), 600);
    });

    dibujar();
})();
