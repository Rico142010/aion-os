# Demo gratuita de AION STUDIO en Render

El archivo `render.yaml` deja lista una instancia gratuita para pruebas con PayPal Sandbox. Al desplegarse, Render asignará una URL pública HTTPS `*.onrender.com`; no hace falta comprar un dominio.

## Publicar el código

1. Crea en GitHub un repositorio **privado** llamado `aion-studio-demo` (inicialízalo con un README para crear la rama `main`). No subas el archivo `.env`; `.gitignore` lo excluye.
2. Vincula GitHub en Render y elige **New → Blueprint**. Conecta el repositorio que contiene `render.yaml` y confirma la creación del servicio `aion-studio`.
3. Cuando Render solicite las variables `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET`, cópialas desde tu `.env` directamente al formulario de Render. No las pegues en GitHub ni en el chat. El Blueprint ya incluye los IDs de producto y planes Sandbox de AION STUDIO.
4. Espera a que termine el primer despliegue y abre el subdominio HTTPS que muestra Render.

## Registrar el webhook Sandbox

En la REST app de PayPal Developer, agrega un webhook con esta URL exacta, sustituyendo el dominio por el asignado por Render:

`https://TU-SUBDOMINIO.onrender.com/api/integrations/paypal/webhook`

Selecciona estos eventos: `BILLING.SUBSCRIPTION.ACTIVATED`, `BILLING.SUBSCRIPTION.UPDATED`, `BILLING.SUBSCRIPTION.CANCELLED`, `BILLING.SUBSCRIPTION.SUSPENDED`, `BILLING.SUBSCRIPTION.EXPIRED`, `BILLING.SUBSCRIPTION.PAYMENT.FAILED`, `PAYMENT.SALE.COMPLETED` y `PAYMENT.SALE.FAILED`. Copia el ID de webhook que genere PayPal a la variable `PAYPAL_WEBHOOK_ID` en Render y reinicia/re-despliega el servicio.

## Límites de esta demo

El nivel gratuito duerme el servicio tras 15 minutos sin tráfico y su sistema de archivos es temporal. La base de datos SQLite, las cuentas de prueba y los archivos locales pueden perderse al dormir, reiniciar o desplegar de nuevo. Úsalo para una demostración y para verificar el flujo Sandbox; no almacenes datos importantes ni cobres a clientes reales. Consulta [las limitaciones del plan gratuito de Render](https://render.com/docs/free).
