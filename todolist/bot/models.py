import secrets
import string

from django.db import models


class TgUser(models.Model):
    tg_user_id = models.BigIntegerField(verbose_name='tg_id', unique=True)
    tg_chat_id = models.BigIntegerField(verbose_name='tg_chat_id')
    user = models.ForeignKey(verbose_name='internal user',
                             to='core.User',
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True,
                             default=None)
    username = models.CharField(
        verbose_name='tg_username', max_length=256, null=True, blank=True, default=None
    )

    verification_code = models.CharField(verbose_name='verification code', max_length=16, null=True)

    # in_operation = models.BooleanField(verbose_name='in operation', default=False)
    # operation_buff = models.CharField(verbose_name='operation buffer', null=True, blank=True)

    def generate_verification_code(self):
        verification_code = ''.join(
            secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(16)
        )
        self.verification_code = verification_code

