"""Catálogo del Laboratorio de algoritmos."""

INTERACTIVOS = [
    {"slug": "merge-sort", "nombre": "Merge Sort", "endpoint": "laboratorio.ejercicios_ordenados",
     "descripcion": "Ordena los ejercicios de práctica por dificultad o por posición.",
     "concepto": "Divide y vencerás · recursividad · O(n log n)"},
    {"slug": "programacion-dinamica", "nombre": "Programación dinámica", "endpoint": "laboratorio.laboratorio_programacion_dinamica",
     "descripcion": "Cuenta de cuántas formas se sube una escalera y compara recursión con memoización.",
     "concepto": "Subproblemas superpuestos · memoización · optimización"},
    {"slug": "backtracking", "nombre": "Backtracking: las 4 reinas", "endpoint": "laboratorio.laboratorio_backtracking",
     "descripcion": "Observa cómo el algoritmo prueba posiciones, descarta conflictos y retrocede en un tablero de 4 × 4.",
     "concepto": "Retroceso · poda · restricciones · caso base"},
    {"slug": "voraz", "nombre": "Algoritmo voraz: siguiente ejercicio", "endpoint": "laboratorio.laboratorio_voraz",
     "descripcion": "Descubre cómo Nivora elige la pregunta que te conviene repasar con tu progreso real.",
     "concepto": "Selección local · criterio de prioridad · O(n)"},
    {"slug": "eficiencia", "nombre": "Análisis de eficiencia: Merge Sort vs Quick Sort", "endpoint": "laboratorio.laboratorio_eficiencia",
     "descripcion": "Mide las operaciones reales de ambos algoritmos y comprueba las recurrencias con el código de Nivora.",
     "concepto": "Big O · recurrencias · mejor, promedio y peor caso"},
]

GRAFO_EJEMPLO = {
    "vertices": ["A", "B", "C", "D", "E"],
    "aristas": [("A", "B", 4), ("A", "C", 2), ("B", "C", 1),
                ("B", "D", 5), ("C", "D", 8), ("C", "E", 10), ("D", "E", 2)],
}

EDUCATIVOS = [
    {"slug": "kruskal", "nombre": "Kruskal", "endpoint": "laboratorio.laboratorio_educativo",
     "descripcion": "Construye un árbol de expansión mínima eligiendo aristas de menor peso sin crear ciclos.",
     "concepto": "Grafos ponderados · árbol de expansión mínima · Union-Find",
     "que_es": "Kruskal encuentra un árbol de expansión mínima (MST): conecta todos los vértices de un grafo no dirigido y conexo con el menor costo total, sin formar ciclos.",
     "pasos": ["Ordenar todas las aristas de menor a mayor peso.", "Tomar la arista más barata que conecte componentes diferentes.", "Descartar una arista si sus extremos ya están conectados, porque formaría un ciclo.", "Detenerse al elegir V − 1 aristas, donde V es el número de vértices."],
     "idea": "La decisión voraz consiste en elegir la arista más barata disponible que no forme un ciclo.",
     "ejercicio": "Si A–B pesa 4, A–C pesa 2 y B–C pesa 1, ¿cuál se elige primero? ¿Por qué no se pueden aceptar las tres aristas?",
     "respuesta": "Primero se elige B–C, con peso 1. Si después se aceptan A–B y A–C, la tercera arista cerraría el ciclo A–B–C–A.",
     "complejidad": "O(E log E) por ordenar las E aristas. Las operaciones Union-Find son casi constantes amortizadas.",
     "codigo_modulo": "services.algoritmos.kruskal", "funcion": "kruskal"},
    {"slug": "prim", "nombre": "Prim", "endpoint": "laboratorio.laboratorio_educativo",
     "descripcion": "Amplía un árbol desde un vértice inicial agregando la conexión más barata hacia uno nuevo.",
     "concepto": "Grafos ponderados · expansión progresiva · MST",
     "que_es": "Prim también encuentra un árbol de expansión mínima. Comienza en un vértice y va creciendo un único árbol, incorporando cada vez el vértice no visitado que puede conectarse con el menor peso.",
     "pasos": ["Elegir un vértice inicial y marcarlo como visitado.", "Buscar la arista de menor peso que salga del conjunto visitado hacia un vértice no visitado.", "Agregar esa arista y el nuevo vértice al árbol.", "Repetir hasta conectar todos los vértices."],
     "idea": "La decisión voraz es escoger la conexión más barata que permita ampliar el árbol sin volver a un vértice visitado.",
     "ejercicio": "Desde A, con A–B = 4 y A–C = 2, ¿qué vértice se incorpora primero? Si C–B = 1, ¿qué conexión se considera después?",
     "respuesta": "Se incorpora C mediante A–C (2). Después, la conexión más barata hacia un vértice no visitado es C–B (1), por lo que se incorpora B.",
     "complejidad": "Con cola de prioridad y lista de adyacencia: O(E log V).",
     "codigo_modulo": "services.algoritmos.prim", "funcion": "prim"},
    {"slug": "union-find", "nombre": "Union-Find", "endpoint": "laboratorio.laboratorio_educativo",
     "descripcion": "Mantiene grupos de elementos y permite saber si dos vértices ya están conectados.",
     "concepto": "Conjuntos disjuntos · Find · Union · compresión de caminos",
     "que_es": "Union-Find, también llamada estructura de conjuntos disjuntos, mantiene una colección de grupos que no se solapan. Es útil para comprobar si dos vértices pertenecen al mismo componente de un grafo.",
     "pasos": ["Find(x): encuentra el representante del grupo al que pertenece x.", "Union(a, b): combina los grupos de a y b si son diferentes.", "Compresión de caminos: durante Find, acerca los nodos directamente a su representante.", "Unión por rango: conecta el árbol de menor rango debajo del de mayor rango para mantenerlo bajo."],
     "idea": "En Kruskal, si Find(a) y Find(b) devuelven el mismo representante, agregar la arista a–b formaría un ciclo.",
     "ejercicio": "Inicialmente A, B y C están separados. Ejecuta Union(A, B). ¿Qué resultado tendría Connected(A, B)? ¿Y Connected(A, C)?",
     "respuesta": "Connected(A, B) devuelve True porque ambos quedaron en el mismo conjunto. Connected(A, C) devuelve False porque C sigue separado.",
     "complejidad": "Con compresión de caminos y unión por rango, las operaciones tienen costo amortizado O(α(n)), donde α es la inversa de Ackermann.",
     "codigo_modulo": "services.algoritmos.union_find", "funcion": "UnionFind"},
]

COMPARACION_MST = [
    {"aspecto": "Cómo crece", "kruskal": "Une componentes mediante aristas", "prim": "Amplía un solo árbol desde un inicio"},
    {"aspecto": "Elección", "kruskal": "Arista más barata que no forme ciclo", "prim": "Arista más barata hacia un vértice no visitado"},
    {"aspecto": "Estructura habitual", "kruskal": "Lista de aristas + Union-Find", "prim": "Lista de adyacencia + cola de prioridad"},
    {"aspecto": "Complejidad habitual", "kruskal": "O(E log E)", "prim": "O(E log V) con heap"},
]
