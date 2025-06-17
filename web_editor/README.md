Esta carpeta contiene el editor web utilizado para crear y modificar figuras irregulares.
El archivo `figuras_irregulares.html` permite dibujar rectángulos, triángulos, círculos y flechas sobre un lienzo con cuadriculado numerado.
Ahora también calcula el centro de gravedad (CG) de las figuras de dos formas:

1. **CG Local**: realiza el cálculo en el propio navegador.
2. **CG Backend**: envía las figuras a `server.py` para que el backend realice el cálculo.

Para iniciar el servidor backend ejecuta:

```bash
python3 server.py
```

Luego abre `figuras_irregulares.html` en tu navegador. Con el botón *CG Backend* se consultará el resultado al servidor.

Las figuras pueden moverse con el botón izquierdo del ratón y redimensionarse manteniendo presionado el botón derecho. Con `Ctrl` + rueda del ratón se modifica el grosor de la línea seleccionada.
