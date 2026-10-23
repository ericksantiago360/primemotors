# djangomarketplace


ls
cd magicbeautybox

1 #activar  enviroment:

 source env/bin/activate  
 
2 # acceder al proyecto:
 cd magicbeautybox  

3# ejecutar el servidor

 python  manage.py runserver


http://127.0.0.1:8000/login

 username
 
 password:

## Chatbot (Claude)

El widget de chat (esquina inferior derecha) solo aparece para usuarios con sesión iniciada. Llama a `POST /chatbot/chat/`, que consulta la API de Claude con el inventario de vehículos disponibles. Sin sesión responde 401.

Configura en `.env`:

- `ANTHROPIC_API_KEY`: tu API key de Anthropic. Sin ella el chatbot responde con error 503.
- `CHATBOT_MODEL` (opcional): por defecto `claude-opus-5-5`.

Pruebas: `python manage.py test chatbot`




 

