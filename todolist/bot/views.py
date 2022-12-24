from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bot.models import TgUser
from bot.serializers import TgUserSerializer
from bot.tg.client import TgClient
from todolist.settings import TG_BOT_TOKEN


class VerificationView(GenericAPIView):
    model = TgUser
    serializer_class = TgUserSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = TgUser.objects.filter(verification_code=request.data.get('verification_code')).first()

        instance.user = self.request.user
        instance.save(update_fields=['user'])
        serialized_instance = self.get_serializer(instance)

        tg_client = TgClient(token=TG_BOT_TOKEN)
        tg_client.send_message(chat_id=instance.tg_chat_id, text='Verification completed successfully')

        return Response(serialized_instance.data)
