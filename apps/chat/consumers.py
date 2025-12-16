# apps/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appointment_id = self.scope['url_route']['kwargs']['appointment_id']
        self.room_group_name = f'chat_{self.appointment_id}'
        self.user = self.scope.get('user')

        if self.user.is_anonymous:
            await self.close()
        else:
            # Unirse al grupo de la sala
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo de la sala
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recibir mensaje desde WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_name = self.user.first_name if self.user.first_name else self.user.username

        # Enviar mensaje al grupo de la sala
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_name
            }
        )

    # Recibir mensaje desde el grupo de la sala
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Enviar mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))