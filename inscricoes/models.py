from django.conf import settings
from django.db import models


class Sala(models.Model):
    nome = models.CharField(max_length=60)
    bloco = models.CharField(max_length=60)
    capacidade = models.PositiveIntegerField()

    class Meta:
        ordering = ["nome"]
        verbose_name = "Sala"
        verbose_name_plural = "Salas"

    def __str__(self):
        return f"{self.nome} ({self.bloco})"


class Evento(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    inscricoes_abertas = models.BooleanField(default=True)
    organizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_organizados",
    )

    class Meta:
        ordering = ["data_inicio"]
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def __str__(self):
        return self.nome


class Atividade(models.Model):
    class Tipo(models.TextChoices):
        PALESTRA = "PA", "Palestra"
        TREINAMENTO = "TR", "Treinamento"
        APRESENTACAO = "AP", "Apresentação"

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="atividades"
    )
    titulo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=2, choices=Tipo.choices)
    descricao = models.TextField(blank=True)
    responsavel = models.CharField(max_length=100)
    sala = models.ForeignKey(
        Sala, on_delete=models.PROTECT, related_name="atividades"
    )
    inicio = models.DateTimeField()
    fim = models.DateTimeField()

    class Meta:
        ordering = ["inicio"]
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"

    def __str__(self):
        return self.titulo

    def vagas_restantes(self):
        ocupadas = self.inscricoes.count()
        return self.sala.capacidade - ocupadas


class InscricaoEvento(models.Model):
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="inscricoes"
    )
    participante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscricoes_em_eventos",
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("evento", "participante")
        verbose_name = "Inscrição em evento"
        verbose_name_plural = "Inscrições em eventos"

    def __str__(self):
        return f"{self.participante} em {self.evento}"


class InscricaoAtividade(models.Model):
    inscricao_evento = models.ForeignKey(
        InscricaoEvento,
        on_delete=models.CASCADE,
        related_name="inscricoes_atividades",
    )
    atividade = models.ForeignKey(
        Atividade, on_delete=models.CASCADE, related_name="inscricoes"
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("inscricao_evento", "atividade")
        verbose_name = "Inscrição em atividade"
        verbose_name_plural = "Inscrições em atividades"

    def __str__(self):
        return f"{self.inscricao_evento.participante} em {self.atividade}"