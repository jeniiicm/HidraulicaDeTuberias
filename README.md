
# Hidráulica en tuberías — Streamlit

Aplicación para ejercicios de hidráulica en tuberías.

## Calcula

- Área de la sección
- Caudal / velocidad
- Número de Reynolds
- Régimen de flujo
- Rugosidad relativa
- Factor de fricción de Darcy:
  - Poiseuille
  - Blasius
  - Colebrook
- Pérdida de carga por Darcy–Weisbach
- Carga de velocidad
- Diagrama de Moody aproximado

## Ejecutar en tu computadora

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Publicar con GitHub + Streamlit Community Cloud

1. Crea un repositorio en GitHub.
2. Sube `main.py` y `requirements.txt`.
3. En Streamlit Community Cloud crea una app nueva desde ese repositorio.
4. Selecciona `main.py` como archivo principal.
5. Deploy.

Una vez publicada, la app funciona desde el navegador sin que tu computadora tenga que estar encendida.
