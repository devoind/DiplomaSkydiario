from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bot.models import TgUser


class TgUserSerializer(serializers.ModelSerializer):
    verification_code = serializers.CharField(write_only=True, max_length=16)

    class Meta:
        model = TgUser
        fields = ['tg_user_id', 'username', 'verification_code', 'user_id']
        read_only_fields = ['tg_user_id', 'username']

    def validate(self, attrs):
        verification_code = attrs.get('verification_code')
        tg_user = TgUser.objects.filter(verification_code=verification_code).first()
        if not tg_user:
            raise ValidationError(detail={'verification_code': 'invalid'})
        attrs['tg_user'] = tg_user
        return attrs
