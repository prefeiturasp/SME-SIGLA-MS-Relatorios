from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Modelo base abstrato com campos comuns.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True
        ordering = ['-criado_em']
