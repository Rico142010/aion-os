# AION STUDIO

MVP ejecutable de una plataforma de operaciones de contenido para creadores. Incluye registro e inicio de sesión, espacios de marca, memoria de voz/audiencia, proyectos, generación de ideas y guiones/storyboards/SEO con OpenAI, biblioteca de enlaces y notas, registro manual de métricas, workflows y ejecución manual de flujos. Los datos persisten en SQLite.

## Requisitos

- Python 3.11 o superior
- (Opcional) una clave de API para un proveedor compatible con Chat Completions
- (Opcional) credenciales OAuth de Google para conectar un canal de YouTube
- Docker y Docker Compose, si se prefiere ejecutar en contenedor

## Inicio local

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Abre <http://localhost:8000>, crea una cuenta con contraseña de al menos 10 caracteres y configura tu marca. La app crea el esquema SQLite automáticamente al primer arranque. En Windows, puedes copiar `.env.example` a `.env` manualmente; la app lee variables de entorno y Docker Compose carga `.env`.

En Windows también puedes ejecutar `INICIAR_AION_STUDIO.bat` para crear el entorno virtual, instalar dependencias, preparar `.env` si no existe e iniciar la aplicación.

Para que el texto generado use IA real, configura `AI_PROVIDER`, `AI_API_KEY`, `AI_BASE_URL` y `AI_MODEL`. OpenAI viene seleccionado por defecto en `https://api.openai.com/v1`; `OPENAI_API_KEY` y `OPENAI_MODEL` siguen admitidos para instalaciones anteriores. AION admite proveedores que implementen el endpoint compatible `/chat/completions`; usa HTTPS para proveedores remotos. Sin clave, el resto de la app funciona y la generación muestra un error claro; no devuelve resultados ficticios.

Si OpenAI devuelve `credit_balance_exhausted`, el administrador de la cuenta API debe añadir saldo o corregir los límites de gasto en la organización/proyecto de esa clave. También se puede cambiar el proveedor compatible configurando las cuatro variables `AI_*` y reiniciando AION. Una generación fallida libera la cuota interna de AION y se puede reintentar después de corregir la configuración. El plan de ChatGPT no paga las llamadas a la API.

## Docker

```sh
docker compose up --build
```

La base de datos se guarda en el volumen `aion-data`. En producción cambia `SESSION_SECRET` por una cadena aleatoria robusta y utiliza HTTPS con un proxy inverso. El contenedor expone el puerto 8000.

## Variables de entorno

| Variable | Requerida | Uso |
|---|---:|---|
| `PORT` | No | Puerto HTTP (8000 por defecto). |
| `DATABASE_PATH` | No | Ruta de SQLite; `./data/aion.db` por defecto. |
| `AI_PROVIDER` | No | Etiqueta del proveedor, `openai` por defecto. |
| `AI_API_KEY` | Para IA | Clave del proveedor seleccionado. En OpenAI, `OPENAI_API_KEY` sigue siendo compatible como alternativa. |
| `AI_BASE_URL` | No | Base HTTPS del endpoint compatible; OpenAI por defecto: `https://api.openai.com/v1`. |
| `AI_MODEL` | No | Modelo publicado por el proveedor; por defecto `gpt-4o-mini`. `OPENAI_MODEL` sigue siendo compatible. |
| `OPENAI_API_KEY` | Alternativa | Variable heredada para instalaciones OpenAI; `AI_API_KEY` tiene prioridad. |
| `OPENAI_MODEL` | Alternativa | Nombre de modelo heredado para OpenAI; `AI_MODEL` tiene prioridad. |
| `YOUTUBE_CLIENT_ID` | Para YouTube | ID del cliente OAuth tipo aplicación web de Google Cloud. |
| `YOUTUBE_CLIENT_SECRET` | Para YouTube | Secreto del cliente OAuth web de Google Cloud. Guárdalo solo en `.env`. |
| `YOUTUBE_REDIRECT_URI` | Para YouTube | Debe coincidir exactamente con la URI autorizada en Google Cloud; local: `http://localhost:8000/api/integrations/youtube/callback`. |
| `YOUTUBE_TOKEN_ENCRYPTION_KEY` | Para YouTube | Clave aleatoria Base64 URL-safe de 32 bytes para cifrar credenciales OAuth en SQLite. Manténla privada y respáldala de forma segura. |

## Funciones disponibles y límites honestos

- **Research:** genera hipótesis e ideas contextualizadas con IA. No consulta demanda, tendencias ni datos de competidores en vivo; verifica las ideas en fuentes reales.
- **Estudio creativo:** persiste proyectos y genera texto de guion, storyboard y paquete SEO con IA. No renderiza vídeo, voz, imágenes o miniaturas en esta versión.
- **Biblioteca:** guarda metadatos, enlaces y notas. La carga binaria de archivos requiere un bucket S3 compatible.
- **Analítica y monetización:** permite añadir y consultar registros manuales. No se conecta a paneles sociales y no infiere ingresos.
- **Autopilot:** guarda workflows y los ejecuta bajo demanda. Los workflows no se ejecutan en segundo plano; para programación real hace falta un worker persistente.
- **Publicación:** no publica directamente. Hace falta registrar aplicaciones OAuth y obtener permisos de publicación en cada red.

## Credenciales necesarias para completar conectores

- **YouTube:** proyecto de Google Cloud, YouTube Data API habilitada, OAuth Client ID/Secret y consentimiento para canales del usuario. Para métricas privadas/publicación, solicitar los scopes oficiales pertinentes y pasar la revisión requerida.
- **Instagram/Facebook:** aplicación Meta, App ID/Secret, cuenta profesional vinculada a una página, permisos de Instagram Graph API y Facebook Login/OAuth; la revisión de permisos puede ser necesaria.
- **TikTok:** aplicación TikTok for Developers, client key/secret, Content Posting API aprobada, OAuth y scopes solicitados por el producto. La publicación queda sujeta a revisión y limitaciones de la plataforma.
- **Almacenamiento de activos:** bucket S3 compatible, región, credenciales de acceso y política CORS.
- **Voz, imagen y vídeo:** credenciales de los proveedores elegidos (por ejemplo, proveedor de TTS y proveedor de generación audiovisual); no se presupone ni simula una integración.

### Conectar YouTube en este MVP local

1. En Google Cloud Console crea o selecciona un proyecto y habilita **YouTube Data API v3** y **YouTube Analytics API**.
2. Configura la pantalla de consentimiento OAuth como aplicación externa (o interna si aplica) y añade tu cuenta como usuario de prueba mientras siga en modo de prueba.
3. Crea un ID de cliente OAuth de tipo **Aplicación web**. Añade esta URI autorizada de redirección exactamente: `http://localhost:8000/api/integrations/youtube/callback`.
4. Copia el Client ID y Client Secret en `YOUTUBE_CLIENT_ID=` y `YOUTUBE_CLIENT_SECRET=` dentro de `.env`. No los compartas por chat. Reinicia AION STUDIO.
5. En AION, abre **Integraciones → YouTube → Conectar con Google**, elige la cuenta que administra el canal y concede los permisos solicitados. AION pide `youtube.readonly`, `youtube.upload` y `yt-analytics.readonly`.
6. Usa **Leer métricas del canal** para cargar reportes diarios de vistas, likes, comentarios, suscriptores ganados y minutos vistos. Usa **Publicar vídeo** para elegir un archivo (límite local de 128 MB), título y privacidad. La privacidad inicial sugerida es `private`.

Google puede restringir la autorización al modo de prueba, invalidar autorizaciones de prueba después de siete días y mantener privados los vídeos subidos desde proyectos OAuth no auditados. Para publicar a público de forma fiable, el proyecto debe cumplir la verificación/auditoría de Google. Los tokens OAuth se cifran con AES-256-GCM; la clave se mantiene en `.env`, ignorado por Git. Para producción multiusuario, mueve esa clave a un servicio de secretos y usa un backend HTTPS público.

## Estructura

```text
app.py              API HTTP, autenticación, persistencia SQLite y adaptador OpenAI
static/index.html   Entrada de la interfaz
static/app.js       UI y llamadas al API
static/styles.css   Interfaz adaptable
tests/test_app.py   Pruebas de flujo principal en API
Dockerfile          Imagen de ejecución
docker-compose.yml  Ejecución local persistente
```

## Pruebas

```sh
python -m unittest discover -s tests -v
```

## Preparación para despliegue

El contenedor es adecuado para demo/uso inicial de una sola instancia. Antes de abrir el servicio al público: usa HTTPS, limita el alta de cuentas según tu modelo de negocio, añade protección CSRF explícita si cambias el atributo SameSite, configura respaldos, monitoreo y rotación de secretos, y migra a PostgreSQL/cola de trabajos/almacenamiento de objetos al escalar. La implementación actual usa el servidor HTTP estándar de Python y SQLite, por lo que no se presenta como arquitectura de producción multiinstancia.

## Suscripciones de PayPal

La interfaz ya incluye botones de suscripción Creator y Studio. El servidor confirma cada suscripción consultando la API de PayPal y actualiza la cuenta mediante webhooks con firma validada. El precio y la moneda vienen del plan que se configura en PayPal; AION no inventa ni simula cargos. Los botones se mantienen desactivados hasta que se completen credenciales, IDs de ambos planes y el ID del webhook.

### Activación de prueba (Sandbox)

1. En https://developer.paypal.com/dashboard/ selecciona Sandbox y crea una REST app asociada a una cuenta Business Sandbox. Copia su Client ID y Secret al archivo .env local: PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET. Nunca los publiques en el chat o el navegador.
2. Elige la moneda y los importes mensuales. Define PAYPAL_CURRENCY, PAYPAL_PRICE_CREATOR y PAYPAL_PRICE_STUDIO en .env; después ejecuta python paypal_setup.py. El script crea el producto y los planes mensuales Creator y Studio en Sandbox y guarda sus IDs en el mismo .env. Solo corre en Sandbox para evitar crear planes Live por accidente.
3. Despliega AION detrás de HTTPS con una URL pública. En la app REST de PayPal añade un webhook a https://TU-DOMINIO/api/integrations/paypal/webhook y suscríbelo a BILLING.SUBSCRIPTION.ACTIVATED, BILLING.SUBSCRIPTION.UPDATED, BILLING.SUBSCRIPTION.CANCELLED, BILLING.SUBSCRIPTION.SUSPENDED, BILLING.SUBSCRIPTION.EXPIRED, BILLING.SUBSCRIPTION.PAYMENT.FAILED, PAYMENT.SALE.COMPLETED y PAYMENT.SALE.FAILED. Copia el Webhook ID a PAYPAL_WEBHOOK_ID.
4. Define PAYPAL_MODE=sandbox, verifica que las credenciales y planes sean de Sandbox y reinicia AION. Para completar un pago de prueba usa una cuenta Buyer Sandbox, no la cuenta real del vendedor.
5. Prueba el alta, la confirmación en la pantalla Plan y facturación, y cancela o suspende la suscripción de prueba para comprobar el webhook.

PayPal no puede enviar webhooks a localhost; se necesita una URL pública HTTPS para sincronizar cancelaciones y fallos de cobro. El Client Secret nunca se envía al navegador. Antes de aceptar clientes, configura HTTPS, una política de privacidad, términos de renovación/cancelación, soporte y pruebas de reembolso.

### Activación Live

Crea/configura por separado la REST app, los dos planes y el webhook en Live. Cambia PAYPAL_MODE=live y reemplaza los valores PayPal del archivo .env por sus equivalentes Live. No reutilices Client IDs, secretos ni Plan IDs de Sandbox. Realiza una compra real de bajo monto solo después de validar el precio, la moneda, impuestos y condiciones con tu cuenta comercial.

Variables para ejecutar paypal_setup.py en Sandbox: PAYPAL_MODE, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_PRODUCT_ID, PAYPAL_CURRENCY, PAYPAL_PRICE_CREATOR y PAYPAL_PRICE_STUDIO. Variables necesarias para habilitar suscripciones en la UI: PAYPAL_MODE, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_PLAN_CREATOR, PAYPAL_PLAN_STUDIO y PAYPAL_WEBHOOK_ID. Si falta una variable de ejecución, no se muestran botones de cobro activos. AION no almacena datos de tarjeta.
